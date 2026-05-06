import os
import time
import threading
from typing import Callable
import numpy as np
import librosa
import soundcard as sc
from scipy.signal import butter, lfilter
from soundcard.mediafoundation import SoundcardRuntimeWarning
import warnings
from Logger import logger

warnings.filterwarnings('ignore', category=SoundcardRuntimeWarning)


class Config:
    SR = 32000
    CHANNELS = 2
    CHUNK = 1600
    FRAME = 0.2
    HP_ORDER = 4
    HP_CUT = 1000

    DODGE_WAV = "./闪避波形.wav"
    DODGE_THRESH = 0.13
    COUNTER_WAV = "./承轨反击波形.wav"
    COUNTER_THRESH = 0.12
    RATIO = 1.0
    ALLOW_REPEAT = False

    MONITOR_SEC = 5

    DODGE_WIN = None
    COUNTER_WIN = None


class FilterBank:
    def __init__(self, order, cutoff, sr):
        self.b, self.a = butter(order, cutoff, btype='highpass', output='ba', fs=sr)
        self._zi = None

    def process(self, frame):
        if self._zi is None:
            from scipy.signal import lfilter_zi
            self._zi = lfilter_zi(self.b, self.a) * frame[0]
        filtered, self._zi = lfilter(self.b, self.a, frame, zi=self._zi)
        return filtered

    def preprocess(self, wf):
        from scipy.signal import filtfilt
        return filtfilt(self.b, self.a, wf)


def load_sample(path, fb, sr):
    import glob
    base = os.path.splitext(path)[0]
    # 找任意 {base}*.npy 缓存
    matches = sorted(glob.glob(base + "*.npy"))
    for c in matches:
        data = np.load(c)
        if data.ndim > 0 and data.size > 0:
            logger.info("load %s", c)
            return data

    wf, orig_sr = librosa.load(path)
    wf = librosa.resample(wf, orig_sr=orig_sr, target_sr=sr)
    processed = fb.preprocess(wf)
    npy = base + f"_{sr}.npy"
    np.save(npy, processed)
    logger.info("cached %s", npy)
    return processed


class AudioEngine:
    def __init__(self, sr, channels, chunk_size, frame_len):
        self.sr = sr
        self.channels = channels
        self.chunk_size = chunk_size
        self.frame_len = frame_len
        self._running = threading.Event()
        self._running.set()

    def stop(self):
        self._running.clear()

    def start(self, callback: Callable[[np.ndarray], None]):
        while self._running.is_set():
            try:
                speaker = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)
                rec = speaker.recorder(samplerate=self.sr, channels=self.channels)
                with rec:
                    frames_per = int(self.sr / self.chunk_size * self.frame_len)
                    while self._running.is_set():
                        total = frames_per * self.chunk_size
                        frame = np.empty(total, dtype=np.float64)
                        for i in range(frames_per):
                            data = rec.record(numframes=self.chunk_size)
                            s = i * self.chunk_size
                            frame[s:s + self.chunk_size] = librosa.to_mono(data.T)
                        callback(frame)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                if not self._running.is_set():
                    break
                logger.error("audio error: %s, retry in 2s", e)
                time.sleep(2)
