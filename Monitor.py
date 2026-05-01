import multiprocessing
import threading

import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk

matplotlib.use('TkAgg')


def plotting(result_queue, text_queue, array_len: int, threshold: float, counter_threshold: float = None):
    fig, ax = plt.subplots(1, 1, figsize=(7, 3))

    stable_x_axis = np.arange(0, array_len, 1, dtype=np.int64)
    initial_array = np.zeros(shape=(array_len,), dtype=np.float64)

    ax.axhline(y=threshold, color='grey', linestyle='--', linewidth=2, zorder=2, label='Dodge Threshold')
    if counter_threshold is not None:
        ax.axhline(y=counter_threshold, color='orange', linestyle='--', linewidth=2, zorder=2, label='Counter Threshold')
    ln1, = ax.plot(stable_x_axis, initial_array, linestyle='-', linewidth=1, color='blue', zorder=3, label='Dodge')
    ln2, = ax.plot(stable_x_axis, initial_array, linestyle='-', linewidth=1, color='red', zorder=3, label='Counterattack')
    ax.set_yticks(np.arange(0, 0.5, 0.1))
    ax.set_xlim(0, initial_array.shape[0] - 1)
    ax.set_ylim(0, 0.4)
    ax.grid()
    ax.legend(loc='upper right')

    def init():
        return ln1, ln2

    def run(frame):
        while not result_queue.empty():
            data = result_queue.get()
            if data is None:
                plt.close(fig)
                return ln1, ln2

            if data['type'] == 'dodge':
                ln1.set_data(stable_x_axis, data['array'])
            elif data['type'] == 'counter':
                ln2.set_data(stable_x_axis, data['array'])
        return ln1, ln2

    ani = FuncAnimation(fig, run, frames=None, init_func=init, blit=True, cache_frame_data=False)

    history = []
    running = True
    after_id = None

    def update_text(tb, tq, root):
        nonlocal after_id
        def process_queue():
            nonlocal running, after_id
            if not running:
                return
            try:
                while True:
                    message = tq.get_nowait()
                    if message is None:
                        running = False
                        return
                    history.append(message)
                    display_text = "\n".join(history[-20:])
                    tb.delete('1.0', tk.END)
                    tb.insert(tk.END, display_text + "\n")
                    tb.see(tk.END)
            except:
                pass
            if running:
                after_id = root.after(100, process_queue)
        process_queue()

    root = tk.Tk()
    root.title("NTE Monitor")
    root.attributes('-topmost', True)

    def on_closing():
        nonlocal running, after_id
        running = False
        if after_id is not None:
            root.after_cancel(after_id)
        plt.close(fig)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    textbox = tk.Text(root, height=5)
    textbox.pack(fill=tk.BOTH, expand=True)

    text_thread = threading.Thread(target=update_text, args=(textbox, text_queue, root,), daemon=True)
    text_thread.start()

    root.mainloop()


class WaveMonitor:
    def __init__(self, array_len: int, threshold: float, counter_threshold: float = None):
        manager = multiprocessing.Manager()
        self.array_queue = manager.Queue()
        self.message_queue = manager.Queue()

        self.process = multiprocessing.Process(target=plotting, args=(self.array_queue, self.message_queue,
                                                                      array_len, threshold, counter_threshold))

        self.process.start()

    def update_array(self, updated_array: np.ndarray, data_type: str = 'dodge'):
        self.array_queue.put({'type': data_type, 'array': updated_array})

    def update_message(self, updated_text: str):
        self.message_queue.put(updated_text)

    def close(self):
        self.array_queue.put(None)
        self.message_queue.put(None)
        self.process.join()
