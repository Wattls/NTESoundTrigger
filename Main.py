import multiprocessing
import threading
import numpy as np
import librosa
from soundcard.mediafoundation import SoundcardRuntimeWarning
from Trigger import SoftKbMouseV3, DodgingTrigger, CounterAttackTrigger
from Monitor import WaveMonitor
import soundcard as sc

import warnings
warnings.filterwarnings('ignore', category=SoundcardRuntimeWarning)


SAMPLE_PATH = "./闪避波形.wav"
COUNTER_ATTACK_SAMPLE_PATH = "./承轨反击波形.wav"
THRESHOLD = 0.13
COUNTER_ATTACK_THRESHOLD = 0.12
EXPANSION_RATIO = 1.0
IS_ALLOW_SUCCESSIVE_TRIGGER = False
MONITOR_TIME = 5


if __name__ == "__main__":
    multiprocessing.freeze_support()

    kbm = SoftKbMouseV3()

    dodge_action = kbm.dodge
    counter_action = kbm.Counterattack

    shared_monitor = WaveMonitor(int(MONITOR_TIME / 0.2), THRESHOLD, COUNTER_ATTACK_THRESHOLD)

    et = DodgingTrigger(SAMPLE_PATH, dodge_action, threshold=THRESHOLD, ratio=EXPANSION_RATIO,
                        is_monitor=True,
                        is_allowed_succe_dodge=IS_ALLOW_SUCCESSIVE_TRIGGER,
                        monitor=shared_monitor,
                        monitor_type='dodge')

    ct = CounterAttackTrigger(COUNTER_ATTACK_SAMPLE_PATH, counter_action, threshold=COUNTER_ATTACK_THRESHOLD, ratio=EXPANSION_RATIO,
                             is_monitor=True,
                             is_allowed_succe_dodge=IS_ALLOW_SUCCESSIVE_TRIGGER,
                             monitor=shared_monitor,
                             monitor_type='counter')

    def audio_capture():
        loopback_speaker = sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True)
        with loopback_speaker.recorder(samplerate=32000, channels=2) as audio_recorder:
            while True:
                current_frame = np.empty(shape=(0,), dtype=np.float64)
                for index in range(int(32000 / 1600 * 0.2)):
                    stream_data = audio_recorder.record(numframes=1600)
                    read_chunks = librosa.to_mono(stream_data.T)
                    current_frame = np.append(current_frame, read_chunks)
                
                et.process_frame(current_frame)
                ct.process_frame(current_frame)

    capture_thread = threading.Thread(target=audio_capture)
    capture_thread.start()
    capture_thread.join()