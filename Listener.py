import time
import numpy as np
from Config import load_sample
from Logger import logger


class Watcher:
    def __init__(self, name, wav, action, thresh, fb,
                 sr=32000, mon=None, tag='',
                 allow_repeat=False, cooldown=0.5):
        self.name = name
        self.action = action
        self.thresh = thresh
        self.sr = sr
        self.mon = mon
        self.tag = tag
        self.allow_repeat = allow_repeat

        self.sample = load_sample(wav, fb, sr)
        self.ref = self._norm(self.sample)

        sample_sec = len(self.sample) / sr
        win_sec = max(sample_sec, 0.5)
        max_n = int(win_sec * sr)

        fft_n = 1 << ((max_n + len(self.ref) - 1).bit_length())
        self._ref_fft = np.fft.rfft(self.ref, n=fft_n).conj()
        self._fft_n = fft_n

        self._buf = np.zeros(max_n, dtype=np.float64)
        self._pos = 0
        self._filled = 0
        self.ready = True
        self._last_fire = 0.0
        self._cooldown = cooldown

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

        score = self._match(self._norm(seg))

        if self.mon:
            self.mon.put_score(score, self.tag)

        now = time.time()
        if now - self._last_fire < self._cooldown:
            return

        if score >= self.thresh and (self.ready or self.allow_repeat):
            self._fire(score)
            self._last_fire = now
            self.ready = False
        else:
            self.ready = True

    def _fire(self, score):
        try:
            t0 = time.perf_counter()
            acts = self.action()
            t1 = time.perf_counter()
            ms = (t1 - t0) * 1000
            ts = time.strftime('%H:%M:%S', time.localtime()) + f'.{int((time.time() * 1000) % 1000):03d}'
            txt = f"[{ts}] {self.name} {score:.5f} (按键延迟{ms:.1f}ms)\n{' -> '.join(acts)}"
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
