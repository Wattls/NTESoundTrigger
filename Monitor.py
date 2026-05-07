import multiprocessing
import threading
import numpy as np
from types import SimpleNamespace
from Logger import logger

try:
    from matplotlib.animation import FuncAnimation
    import matplotlib.pyplot as plt
    import matplotlib
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import tkinter as tk
    matplotlib.use('TkAgg')
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def _plot(sq, mq, n, d_th, c_th):
    fig, ax = plt.subplots(1, 1, figsize=(7, 3))
    x = np.arange(n, dtype=np.int64)
    d_vals = np.zeros(n, dtype=np.float64)
    c_vals = np.zeros(n, dtype=np.float64)

    ax.axhline(y=d_th, color='grey', linestyle='--', linewidth=2, zorder=2)
    if c_th is not None:
        ax.axhline(y=c_th, color='orange', linestyle='--', linewidth=2, zorder=2)
    ln1, = ax.plot(x, d_vals, '-', linewidth=1, color='blue', zorder=3, label='dodge')
    ln2, = ax.plot(x, c_vals, '-', linewidth=1, color='red', zorder=3, label='counter')
    ax.set_yticks(np.arange(0, 0.5, 0.1))
    ax.set_xlim(0, n - 1)
    ax.set_ylim(0, max(0.4, d_th * 1.5, (c_th or 0) * 1.5))
    ax.grid()
    ax.legend(loc='upper right')

    running = True
    after_id = None

    def init():
        return ln1, ln2

    def tick(_):
        nonlocal running
        while not sq.empty():
            data = sq.get()
            if data is None:
                running = False
                ani.event_source.stop()
                plt.close(fig)
                root.after(0, root.quit)
                return ln1, ln2
            if data['tag'] == 'dodge':
                d_vals[:-1] = d_vals[1:]
                d_vals[-1] = data['score']
                ln1.set_data(x, d_vals)
            elif data['tag'] == 'counter':
                c_vals[:-1] = c_vals[1:]
                c_vals[-1] = data['score']
                ln2.set_data(x, c_vals)
        return ln1, ln2

    ani = FuncAnimation(fig, tick, init_func=init, blit=True,
                        cache_frame_data=False, interval=200)

    notice = "★ 本项目开源免费，请勿付费购买 ★\nGitHub: https://github.com/Wattls/NTESoundTrigger\n\n"
    history = [notice]

    def poll_text():
        nonlocal running, after_id
        if not running:
            return
        try:
            while True:
                msg = mq.get_nowait()
                if msg is None:
                    running = False
                    return
                history.append(msg)
                txt = "\n".join(history[-20:])
                tb.delete('1.0', tk.END)
                tb.insert(tk.END, txt + "\n")
                tb.see(tk.END)
        except:
            pass
        if running:
            after_id = root.after(100, poll_text)

    root = tk.Tk()
    root.title("NTE - 开源免费项目")
    root.attributes('-topmost', True)

    def on_close():
        nonlocal running, after_id
        running = False
        if after_id is not None:
            root.after_cancel(after_id)
        plt.close(fig)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    tb = tk.Text(root, height=5)
    tb.pack(fill=tk.BOTH, expand=True)

    threading.Thread(target=poll_text, daemon=True).start()
    root.mainloop()


def start_monitor(n, d_th, c_th=None):
    if not HAS_MPL:
        return SimpleNamespace(sq=None, mq=None, proc=None,
                               put_score=lambda *a: None,
                               put_msg=lambda *a: None,
                               close=lambda: None)

    sq = multiprocessing.Queue()
    mq = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_plot, args=(sq, mq, n, d_th, c_th))
    proc.start()

    def put_score(score, tag='dodge'):
        sq.put({'tag': tag, 'score': score})

    def put_msg(txt):
        mq.put(txt)

    def close():
        sq.put(None)
        mq.put(None)
        proc.join(timeout=2)
        if proc.is_alive():
            logger.warning("monitor stuck, killing")
            proc.terminate()
            proc.join()

    return SimpleNamespace(sq=sq, mq=mq, proc=proc,
                           put_score=put_score, put_msg=put_msg, close=close)
