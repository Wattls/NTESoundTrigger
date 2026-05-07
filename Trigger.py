import time
import pydirectinput

pydirectinput.PAUSE = 0


class KB:
    def dodge(self):
        log = []
        log.append('右键↓')
        time.sleep(0.1)
        pydirectinput.mouseDown(button='right')
        time.sleep(0.01)
        log.append('右键↑')
        pydirectinput.mouseUp(button='right')
        return log

    def hit(self):
        log = []
        log.append('左键↓')
        pydirectinput.mouseDown(button='left')
        time.sleep(0.01)
        log.append('左键↑')
        pydirectinput.mouseUp(button='left')
        return log
