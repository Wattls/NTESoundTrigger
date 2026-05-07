import multiprocessing
import threading
import time
import webbrowser
from collections import deque
from scipy.signal import savgol_filter
import numpy as np
from types import SimpleNamespace
from Logger import logger

try:
    from matplotlib.animation import FuncAnimation
    import matplotlib.pyplot as plt
    import matplotlib
    from matplotlib import patheffects
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import tkinter as tk
    matplotlib.use('TkAgg')
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def _plot(sq, mq, n, d_th, c_th):
    plt.style.use('dark_background')
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams.update({
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'lines.linewidth': 2.2,
        'lines.antialiased': True,
    })

    bg_dark = '#1E1E2E'
    bg_widget = '#2A2A3A'
    dodge_c = '#00F0FF'
    counter_c = '#FF6B4A'

    fig, ax = plt.subplots(1, 1, figsize=(7, 3), dpi=120)
    fig.set_facecolor(bg_dark)
    ax.set_facecolor(bg_dark)
    x = np.arange(n, dtype=np.int64)
    d_vals = deque([0.0] * n, maxlen=n)
    c_vals = deque([0.0] * n, maxlen=n)

    # ================== 阈值线 ==================
    # 闪避阈值线
    dodge_line = ax.axhline(y=d_th, color=dodge_c, linestyle=(0, (5, 2.5)), linewidth=3, alpha=0.9, zorder=2)
    
    # 反击阈值线
    if c_th is not None:
        counter_line = ax.axhline(y=c_th, color=counter_c, linestyle=(0, (5, 2.5)), linewidth=3, alpha=0.9, zorder=2)
    # ===============================================

    ln1, = ax.plot(x, list(d_vals), '-', color=dodge_c, label='闪避', zorder=3)
    ln2, = ax.plot(x, list(c_vals), '-', color=counter_c, label='反击', zorder=3)

    ln1.set_path_effects([patheffects.withStroke(linewidth=4, foreground=dodge_c, alpha=0.2)])
    ln2.set_path_effects([patheffects.withStroke(linewidth=4, foreground=counter_c, alpha=0.2)])

    ax.set_xlim(0, n - 1)
    ax.set_ylim(0, max(0.4, d_th * 1.5, (c_th or 0) * 1.5))
    ax.set_xticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#A0A0C0')
    ax.spines['bottom'].set_color('#A0A0C0')
    ax.tick_params(axis='both', colors='#C0C0E0')
    ax.grid(True, color='#3A3A4A', linestyle='--', linewidth=0.6, alpha=0.7)
    legend = ax.legend(facecolor=bg_widget, edgecolor='#333333', loc='upper right', framealpha=0.8, fancybox=True)
    for t in legend.get_texts():
        t.set_color('white')

    running = True
    after_id = None
    blink = [0.0]
    hl_state = [None]
    c_peak = 0.0
    c_hold_cnt = 0
    PEAK_HOLD_LEN = 8
    DECAY_FACTOR = 0.82

    def init():
        return ln1, ln2

    def tick(_):
        nonlocal running, c_peak, c_hold_cnt
        while not sq.empty():
            data = sq.get()
            if data is None:
                running = False
                ani.event_source.stop()
                plt.close(fig)
                root.after(0, root.quit)
                return ln1, ln2
            if data['tag'] == 'dodge':
                d_vals.append(data['score'])
                if data['score'] >= d_th:
                    blink[0] = 1.0
            elif data['tag'] == 'counter':
                score = data['score']
                
                if score >= c_peak:
                    # 新高峰到来，立即更新并重置保持
                    c_peak = score
                    c_hold_cnt = PEAK_HOLD_LEN
                elif c_hold_cnt > 0:
                    # 保持峰值阶段
                    c_hold_cnt -= 1
                    score = c_peak
                else:
                    # 保持结束后平滑衰减（指数衰减，更自然）
                    c_peak = max(score, c_peak * DECAY_FACTOR)
                    score = c_peak
                
                c_vals.append(score)
                
                # 阈值判断使用原始分数
                if c_th is not None and data['score'] >= c_th:
                    blink[0] = 1.0

        y_d = list(d_vals)
        y_c = list(c_vals)
        win = min(5, len(y_d)) if len(y_d) > 3 else 3
        if win % 2 == 0:
            win -= 1
        y_d_s = savgol_filter(y_d, win, 2) if win >= 3 else y_d
        y_c_s = savgol_filter(y_c, win, 2) if win >= 3 else y_c

        ln1.set_data(x, y_d_s)
        ln2.set_data(x, y_c_s)

        for c in ax.collections:
            c.remove()
        ax.fill_between(x, 0, y_d_s, color=dodge_c, alpha=0.15, zorder=1)
        if c_th is not None:
            ax.fill_between(x, 0, y_c_s, color=counter_c, alpha=0.15, zorder=1)

        if blink[0] > 0:
            a = 0.3 + 0.7 * abs(np.sin(blink[0] * 12))
            ax.lines[2].set_alpha(a)
            if c_th is not None:
                ax.lines[3].set_alpha(a)
            blink[0] -= 0.02
        else:
            ax.lines[2].set_alpha(0.8)
            if c_th is not None:
                ax.lines[3].set_alpha(0.8)

        if hl_state[0] == 0:
            ln1.set_alpha(1.0)
            ln1.set_linewidth(3)
            ln2.set_alpha(0.15)
        elif hl_state[0] == 1:
            ln2.set_alpha(1.0)
            ln2.set_linewidth(3)
            ln1.set_alpha(0.15)
        else:
            ln1.set_alpha(1.0)
            ln1.set_linewidth(2)
            ln2.set_alpha(1.0)
            ln2.set_linewidth(2)
        return ln1, ln2

    ani = FuncAnimation(fig, tick, init_func=init, blit=False,
                        cache_frame_data=False, interval=80)

    root = tk.Tk()
    root.title("NTE - Sound Trigger Monitor")
    root.attributes('-topmost', True)
    root.configure(bg=bg_dark)

    def on_close():
        nonlocal running, after_id
        running = False
        if after_id is not None:
            root.after_cancel(after_id)
        plt.close(fig)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    def open_repo(e=None):
        webbrowser.open("https://github.com/Wattls/NTESoundTrigger")

    notice_label = tk.Label(
        root, text="✨ 开源免费 · 点击访问 GitHub ✨",
        fg="#AAD4FF", font=("Microsoft YaHei", 10, "bold"),
        bg=bg_widget, cursor="hand2", padx=10, pady=5, relief="flat")
    notice_label.pack(fill=tk.X, pady=(0, 5))
    notice_label.bind("<Button-1>", open_repo)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

    tooltip = tk.Label(
        root, text='', bg=bg_widget, fg='#E0E0FF',
        font=("Microsoft YaHei", 9), relief="solid", borderwidth=1,
        padx=10, pady=5, highlightthickness=0)
    last_tip = [0.0]

    def on_move(event):
        if event.inaxes is not ax:
            tooltip.place_forget()
            last_tip[0] = 0.0
            return
        now = time.time()
        if now - last_tip[0] < 0.05:
            return
        last_tip[0] = now
        idx = int(np.clip(event.xdata, 0, n - 1))
        dv = d_vals[idx]
        cv = c_vals[idx]
        txt = f'闪避: {dv:.4f}  反击: {cv:.4f}'
        tx = root.winfo_pointerx() - root.winfo_rootx() + 15
        ty = root.winfo_pointery() - root.winfo_rooty() - 15
        tooltip.config(text=txt)
        tooltip.place(x=tx, y=ty)

    def on_click(event):
        if event.inaxes is None:
            hl_state[0] = None
            return
        idx = int(np.clip(event.xdata, 0, n - 1))
        dd = abs(d_vals[idx] - event.ydata)
        dc = abs(c_vals[idx] - event.ydata)
        if dd < dc:
            hl_state[0] = 0 if hl_state[0] != 0 else None
        else:
            hl_state[0] = 1 if hl_state[0] != 1 else None

    fig.canvas.mpl_connect('motion_notify_event', on_move)
    fig.canvas.mpl_connect('button_press_event', on_click)

    log_frame = tk.Frame(root, bg=bg_dark)
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    tk.Label(log_frame, text="📋 事件日志", fg="#A0A0C0", bg=bg_dark,
             font=("Microsoft YaHei", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))

    tb = tk.Text(
        log_frame, height=5, bg='#0D1117', fg='#D0D0E0',
        insertbackground='#C0C0E0', borderwidth=0, font=("Consolas", 9),
        wrap='word', relief='flat', padx=8, pady=4)
    tb.tag_config('dodge', foreground='#00F0FF')
    tb.tag_config('counter', foreground='#FF6B4A')

    def _insert_msg(msg, tag=None):
        tb.insert(tk.END, msg + '\n', tag)
        line_count = int(float(tb.index('end-1c').split('.')[0]))
        if line_count > 20:
            tb.delete('1.0', '2.0')
        tb.see(tk.END)

    def _poll_loop():
        while running:
            try:
                msg = mq.get(timeout=0.1)
                if msg is None:
                    break
                tag = None
                if '闪避' in msg:
                    tag = 'dodge'
                elif '反击' in msg:
                    tag = 'counter'
                root.after(0, _insert_msg, msg, tag)
            except:
                pass

    threading.Thread(target=_poll_loop, daemon=True).start()
    tb.pack(fill=tk.BOTH, expand=True)

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
