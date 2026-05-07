import multiprocessing
from Config import Config, AudioEngine, FilterBank
from Listener import Watcher
from Monitor import start_monitor
from Trigger import KB
from Logger import logger

if __name__ == "__main__":
    multiprocessing.freeze_support()
    cfg = Config()
    fb = FilterBank(cfg.HP_ORDER, cfg.HP_CUT, cfg.SR)
    n = int(cfg.MONITOR_SEC / cfg.FRAME)
    mon = start_monitor(n, cfg.DODGE_THRESH, cfg.COUNTER_THRESH)
    kbm = KB()

    dodge = Watcher(
        name="闪避", wav=cfg.DODGE_WAV, action=kbm.dodge,
        thresh=cfg.DODGE_THRESH, fb=fb, sr=cfg.SR,
        ratio=cfg.RATIO, mon=mon, tag="dodge",
        allow_repeat=cfg.ALLOW_REPEAT, win_sec=cfg.DODGE_WIN,
    )
    counter = Watcher(
        name="反击", wav=cfg.COUNTER_WAV, action=kbm.hit,
        thresh=cfg.COUNTER_THRESH, fb=fb, sr=cfg.SR,
        ratio=cfg.RATIO, mon=mon, tag="counter",
        allow_repeat=cfg.ALLOW_REPEAT, win_sec=cfg.COUNTER_WIN,
    )

    audio = AudioEngine(cfg.SR, cfg.CHANNELS, cfg.CHUNK, cfg.FRAME)

    def tick(frame):
        if mon.proc is not None and not mon.proc.is_alive():
            logger.info("monitor gone")
            audio.stop()
            return
        filtered = fb.process(frame)
        dodge.feed(filtered)
        counter.feed(filtered)

    try:
        audio.start(tick)
    except KeyboardInterrupt:
        logger.info("bye")
    finally:
        mon.close()
        logger.info("done")
