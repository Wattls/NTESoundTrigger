import numpy as np
from concurrent.futures import ThreadPoolExecutor
from Config import load_sample
from Logger import logger


class Watcher:
    def __init__(self, name, wav, action, thresh, fb,
                 sr=32000, ratio=1.0, mon=None, tag='',
                 allow_repeat=False, win_sec=None):
        self.name = name
        self.action = action
        self.thresh = thresh
        self.ratio = ratio
        self.sr = sr
        self.mon = mon
        self.tag = tag
        self.allow_repeat = allow_repeat

        self.sample = load_sample(wav, fb, sr)
        self.ref = self._norm(self.sample)

        sample_sec = len(self.sample) / sr
        self.win_sec = win_sec or max(sample_sec, 0.5)
        max_n = int(self.win_sec * sr)

        fft_n = 1 << ((max_n + len(self.ref) - 1).bit_length())
        self._ref_fft = np.fft.rfft(self.ref, n=fft_n).conj()
        self._fft_n = fft_n

        self._buf = np.zeros(max_n, dtype=np.float64)
        self._pos = 0
        self._filled = 0
        self.ready = True
        self._pool = ThreadPoolExecutor(max_workers=1)

    def _norm(self, wf):
        rms = np.sqrt(np.mean(wf ** 2) + 1e-6)
        return wf / rms

    def feed(self, frame):
        n = frame.shape[0]
        buf = self._buf
        size = buf.shape[0]

        if n >= size:
            buf[:] = frame[-size:]
            self._pos = 0
            self._filled = size
        else:
            end = self._pos + n
            if end <= size:
                buf[self._pos:end] = frame
            else:
                p1 = size - self._pos
                buf[self._pos:] = frame[:p1]
                buf[:end - size] = frame[p1:]
            self._pos = (self._pos + n) % size
            self._filled = min(self._filled + n, size)

        if self._filled < size:
            seg = buf[:self._filled]
        elif self._pos == 0:
            seg = buf
        else:
            seg = np.concatenate((buf[self._pos:], buf[:self._pos]))

        score = self._match(self._norm(seg)) * self.ratio

        if self.mon:
            self.mon.put_score(score, self.tag)

        if score >= self.thresh and (self.ready or self.allow_repeat):
            self._pool.submit(self._fire, score)
            self.ready = False
        else:
            self.ready = True

    def _fire(self, score):
        try:
            acts = self.action()
            txt = f"{self.name} {score:.5f}\n{' -> '.join(acts)}"
            if self.mon:
                self.mon.put_msg(txt)
            logger.info(txt)
        except Exception as e:
            logger.error("%s fail: %s", self.name, e, exc_info=True)

    def _match(self, seg):
        n = len(seg) + len(self.ref) - 1
        if n > self._fft_n:
            self._fft_n = 1 << n.bit_length()
            self._ref_fft = np.fft.rfft(self.ref, n=self._fft_n).conj()
        f = np.fft.rfft(seg, n=self._fft_n)
        corr = np.fft.irfft(f * self._ref_fft)[:n]
        return np.max(corr) / max(len(seg), len(self.ref))
