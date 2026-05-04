import time, random
import threading
import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL('user32', use_last_error=True)
_lock = threading.Lock()
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MAPVK_VK_TO_VSC = 0
LEFT_SHIFT = 0xA0


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
        super().__init__(*args, **kwds)
        if not self.dwFlags & KEYEVENTF_UNICODE:
            self.wScan = user32.MapVirtualKeyExW(self.wVk, MAPVK_VK_TO_VSC, 0)


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (("ki", KEYBDINPUT), ("mi", MOUSEINPUT))
    _anonymous_ = ("_input",)
    _fields_ = (("type", wintypes.DWORD), ("_input", _INPUT))


class KB:
    def press(self, key):
        x = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=key))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def release(self, key):
        x = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=key, dwFlags=KEYEVENTF_KEYUP))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

    def mouse(self, dx, dy, flags):
        x = INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(dx, dy, 0, flags, 0, 0))
        user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(INPUT))

    def dodge(self):
        with _lock:
            log = []
            log.append('右键↓')
            self.mouse(0, 0, MOUSEEVENTF_RIGHTDOWN)
            time.sleep(0.1 + random.random() * 0.2)
            log.append('右键↑')
            self.mouse(0, 0, MOUSEEVENTF_RIGHTUP)
            time.sleep(0.1)
            log.append('Shift↓')
            self.press(LEFT_SHIFT)
            time.sleep(0.1 + random.random() * 0.1)
            log.append('Shift↑')
            self.release(LEFT_SHIFT)
            return log

    def hit(self):
        with _lock:
            log = []
            key = random.choice([0x31, 0x32, 0x33, 0x34])
            log.append(f'{chr(key)}↓')
            self.press(key)
            time.sleep(0.1)
            log.append('左键↓')
            self.mouse(0, 0, MOUSEEVENTF_LEFTDOWN)
            time.sleep(0.05)
            log.append('左键↑')
            self.mouse(0, 0, MOUSEEVENTF_LEFTUP)
            log.append(f'{chr(key)}↑')
            self.release(key)
            return log
