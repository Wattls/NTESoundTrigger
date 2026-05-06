import time, random
import threading
import pydirectinput

_lock = threading.Lock()


class KB:
    def dodge(self):
        with _lock:
            log = []
            log.append('右键↓')
            pydirectinput.mouseDown(button='right')
            time.sleep(0.1 + random.random() * 0.2)
            log.append('右键↑')
            pydirectinput.mouseUp(button='right')
            time.sleep(0.1)
            log.append('Shift↓')
            pydirectinput.keyDown('shift')
            time.sleep(0.1 + random.random() * 0.1)
            log.append('Shift↑')
            pydirectinput.keyUp('shift')
            return log

    def hit(self):
        with _lock:
            log = []
            key = random.choice(['1', '2', '3', '4'])
            log.append(f'{key}↓')
            pydirectinput.keyDown(key)
            time.sleep(0.1)
            log.append('左键↓')
            pydirectinput.mouseDown(button='left')
            time.sleep(0.05)
            log.append('左键↑')
            pydirectinput.mouseUp(button='left')
            log.append(f'{key}↑')
            pydirectinput.keyUp(key)
            return log
