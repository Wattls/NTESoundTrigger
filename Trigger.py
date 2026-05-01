import time
import random

import numpy as np

import librosa

import ctypes
from ctypes import wintypes

from Listener import GameAudioListener
from Monitor import WaveMonitor

user32 = ctypes.WinDLL('user32', use_last_error=True)
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MAPVK_VK_TO_VSC = 0

LEFT_SHIFT_KEY_CODE = 0xA0


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", wintypes.WPARAM))


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", wintypes.WPARAM))

    def __init__(self, *args, **kwds):
        super(KEYBDINPUT, self).__init__(*args, **kwds)
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk,
                                                 MAPVK_VK_TO_VSC, 0)


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT))

    _anonymous_ = ("_input",)
    _fields_ = (("type", wintypes.DWORD),
                ("_input", _INPUT))


class SoftKbMouse:
    PRESS_TIME = 0.1
    SHORT_PRESS_TIME = 0.01

    def __init__(self):
        pass


class SoftKbMouseV3(SoftKbMouse):
    def __init__(self):
        super().__init__()
        self.action_log = []

    def PressKey(self, hexKeyCode):
        x = INPUT(type=INPUT_KEYBOARD,
                  ki=KEYBDINPUT(wVk=hexKeyCode))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def ReleaseKey(self, hexKeyCode):
        x = INPUT(type=INPUT_KEYBOARD,
                  ki=KEYBDINPUT(wVk=hexKeyCode,
                                dwFlags=KEYEVENTF_KEYUP))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def Mouse(self, dx, dy, flags):
        x = INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(dx, dy, 0, flags, 0, 0))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(INPUT))

    def get_key_name(self, key_code):
        key_map = {
            0x31: '1',
            0x32: '2',
            0x33: '3',
            0x34: '4',
            LEFT_SHIFT_KEY_CODE: '左Shift'
        }
        return key_map.get(key_code, f'Key(0x{key_code:X})')

    def get_mouse_flag_name(self, flags):
        if flags == MOUSEEVENTF_RIGHTDOWN:
            return '右键按下'
        elif flags == MOUSEEVENTF_RIGHTUP:
            return '右键松开'
        elif flags == MOUSEEVENTF_LEFTDOWN:
            return '左键按下'
        elif flags == MOUSEEVENTF_LEFTUP:
            return '左键松开'
        return f'Mouse(0x{flags:X})'

    def dodge(self):
        self.action_log = []
        self.action_log.append(self.get_mouse_flag_name(MOUSEEVENTF_RIGHTDOWN))
        self.Mouse(0, 0, MOUSEEVENTF_RIGHTDOWN)
        time.sleep(0.1 + random.random() * 0.2)
        self.action_log.append(self.get_mouse_flag_name(MOUSEEVENTF_RIGHTUP))
        self.Mouse(0, 0, MOUSEEVENTF_RIGHTUP)
        time.sleep(0.1)
        self.action_log.append(self.get_key_name(LEFT_SHIFT_KEY_CODE) + '按下')
        self.PressKey(LEFT_SHIFT_KEY_CODE)
        time.sleep(0.1 + random.random() * 0.1)
        self.action_log.append(self.get_key_name(LEFT_SHIFT_KEY_CODE) + '松开')
        self.ReleaseKey(LEFT_SHIFT_KEY_CODE)
        return self.action_log

    def Counterattack(self):
        self.action_log = []
        keys = [0x31, 0x32, 0x33, 0x34]
        selected_key = random.choice(keys)
        
        self.action_log.append(self.get_key_name(selected_key) + '按下')
        self.PressKey(selected_key)
        
        time.sleep(0.1)
        
        self.action_log.append(self.get_mouse_flag_name(MOUSEEVENTF_LEFTDOWN))
        self.Mouse(0, 0, MOUSEEVENTF_LEFTDOWN)
        
        time.sleep(0.05)
        
        self.action_log.append(self.get_mouse_flag_name(MOUSEEVENTF_LEFTUP))
        self.Mouse(0, 0, MOUSEEVENTF_LEFTUP)
        
        self.action_log.append(self.get_key_name(selected_key) + '松开')
        self.ReleaseKey(selected_key)
        
        return self.action_log


class DodgingTrigger(GameAudioListener):
    monitor_time = 5

    def __init__(self, sample_path: str, action, threshold=0.1, ratio=1.0, is_monitor=False, is_allowed_succe_dodge=False, monitor=None, monitor_type='dodge'):
        self.action = action
        self.threshold = threshold
        self.is_monitor = is_monitor
        self.is_allowed_succe_dodge = is_allowed_succe_dodge
        self.monitor_type = monitor_type
        self.is_not_past_triggered = True
        self.last_frames = np.empty(shape=(0,), dtype=np.float64)
        if self.is_monitor:
            self.len_samples = int(self.monitor_time / self.sample_len)
            if monitor is not None:
                self.monitor = monitor
            else:
                self.monitor = WaveMonitor(self.len_samples, self.threshold)
            self.monitor_array = np.zeros(shape=(self.len_samples,), dtype=np.float64)
        super().__init__(sample_path, ratio)

    def process_frame(self, current_frame):
        combined_frames = np.append(self.last_frames, current_frame)
        max_score = self.matching(combined_frames)
        if self.is_monitor:
            self.monitor_array[:-1] = self.monitor_array[1:]
            self.monitor_array[-1] = max_score
            self.monitor.update_array(self.monitor_array, self.monitor_type)

        if max_score >= self.threshold:
            if self.is_not_past_triggered or self.is_allowed_succe_dodge:
                actions = self.action()
                trigger_text = "闪避触发分数: {}\n执行按键: {}".format(round(max_score, 5), " -> ".join(actions))
                if self.is_monitor:
                    self.monitor.update_message(trigger_text)
                print(trigger_text)

                self.is_not_past_triggered = False
        else:
            self.is_not_past_triggered = True

        self.last_frames = current_frame

    def online_listening(self):
        print("开始监测")

        with self.audio_instance as audio_recorder:
            while True:
                current_frame = np.empty(shape=(0,), dtype=np.float64)
                for index in range(int(self.used_sr / self.chunk_size * self.sample_len)):
                    stream_data = audio_recorder.record(numframes=self.chunk_size)
                    read_chunks = librosa.to_mono(stream_data.T)

                    current_frame = np.append(current_frame, read_chunks)

                self.process_frame(current_frame)


class CounterAttackTrigger(GameAudioListener):
    monitor_time = 5

    def __init__(self, sample_path: str, action, threshold=0.1, ratio=1.0, is_monitor=False, is_allowed_succe_dodge=False, monitor=None, monitor_type='counter'):
        self.action = action
        self.threshold = threshold
        self.is_monitor = is_monitor
        self.is_allowed_succe_dodge = is_allowed_succe_dodge
        self.monitor_type = monitor_type
        self.is_not_past_triggered = True
        self.last_frames = np.empty(shape=(0,), dtype=np.float64)
        if self.is_monitor:
            self.len_samples = int(self.monitor_time / self.sample_len)
            if monitor is not None:
                self.monitor = monitor
            else:
                self.monitor = WaveMonitor(self.len_samples, self.threshold)
            self.monitor_array = np.zeros(shape=(self.len_samples,), dtype=np.float64)
        super().__init__(sample_path, ratio)

    def process_frame(self, current_frame):
        combined_frames = np.append(self.last_frames, current_frame)
        max_score = self.matching(combined_frames)
        if self.is_monitor:
            self.monitor_array[:-1] = self.monitor_array[1:]
            self.monitor_array[-1] = max_score
            self.monitor.update_array(self.monitor_array, self.monitor_type)

        if max_score >= self.threshold:
            if self.is_not_past_triggered or self.is_allowed_succe_dodge:
                actions = self.action()
                trigger_text = "反击触发分数: {}\n执行按键: {}".format(round(max_score, 5), " -> ".join(actions))
                if self.is_monitor:
                    self.monitor.update_message(trigger_text)
                print(trigger_text)

                self.is_not_past_triggered = False
        else:
            self.is_not_past_triggered = True

        self.last_frames = current_frame

    def online_listening(self):
        print("反击监测开始")

        with self.audio_instance as audio_recorder:
            while True:
                current_frame = np.empty(shape=(0,), dtype=np.float64)
                for index in range(int(self.used_sr / self.chunk_size * self.sample_len)):
                    stream_data = audio_recorder.record(numframes=self.chunk_size)
                    read_chunks = librosa.to_mono(stream_data.T)

                    current_frame = np.append(current_frame, read_chunks)

                self.process_frame(current_frame)