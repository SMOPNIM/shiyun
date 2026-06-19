"""
诗云 - TUI (Terminal User Interface) 模式
"""
import curses
import json
import queue
import threading
import time
from datetime import datetime
from typing import List, Optional

from generator import (
    PRESETS,
    estimate_total,
    get_paused_state,
    get_session_stats,
    clear_paused_state,
    clear_stop,
    is_stopped,
    pause_session,
    poetry_stream_combinations,
    save_combinations,
    stop_session,
    stream_combinations,
)

PRESET_KEYS = list(PRESETS.keys())


def fmt_num(n: int) -> str:
    if n <= 0:
        return "0"
    if n >= 10 ** 18:
        return "过大"
    if n >= 10 ** 16:
        return f"{n / 10 ** 16:.2f}亿亿"
    if n >= 10 ** 12:
        return f"{n / 10 ** 12:.2f}万亿"
    if n >= 10 ** 8:
        return f"{n / 10 ** 8:.2f}亿"
    if n >= 10 ** 4:
        return f"{n / 10 ** 4:.2f}万"
    return f"{n:,}"


def estimate_length(session: "TUISession") -> int:
    if session.mode == "poetry":
        n = len(session.chars)
        plen = session.line_length * session.lines_per_poem
        raw = n ** plen
        return raw if raw <= 10 ** 18 else 10 ** 18 + 1
    return estimate_total(len(session.chars), session.max_length)


class TUISession:
    def __init__(self):
        self.session_id = "tui_" + str(int(time.time()))
        self.chars = PRESETS[PRESET_KEYS[0]]["chars"]
        self.chars_label = PRESET_KEYS[0]
        self.chars_len = len(self.chars)
        self.max_length = 2
        self.mode = "enum"
        self.line_length = 5
        self.lines_per_poem = 4
        self.running = False
        self.paused = False
        self.result_queue: queue.Queue = queue.Queue()
        self.gen_thread: Optional[threading.Thread] = None
        self.generated = 0
        self.start_time: Optional[datetime] = None


def generator_worker(session: TUISession, resume: Optional[dict] = None):
    try:
        if session.mode == "poetry":
            gen = poetry_stream_combinations(
                session.session_id, session.chars, session.max_length,
                line_length=session.line_length,
                lines_per_poem=session.lines_per_poem,
                resume_state=resume)
        else:
            gen = stream_combinations(
                session.session_id, session.chars, session.max_length,
                resume_state=resume)
        for item in gen:
            if is_stopped(session.session_id):
                break
            session.result_queue.put(item)
    except Exception as e:
        session.result_queue.put(f"!!ERR:{e}")


def run_tui(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    if curses.has_colors():
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_RED, -1)
    stdscr.timeout(150)

    session = TUISession()
    display_buf: List[str] = []

    while True:
        h, w = stdscr.getmaxyx()
        if h < 10 or w < 40:
            stdscr.clear()
            stdscr.addstr(0, 0, "终端太小，至少需要 40x10")
            stdscr.refresh()
            k = stdscr.getch()
            if k in (ord('q'), 27):
                break
            continue

        stdscr.clear()

        # === Title ===
        title = " 诗云 - 究极吟诗程序 (TUI模式) "
        try:
            stdscr.addstr(0, max(0, (w - len(title)) // 2), title,
                          curses.A_BOLD | (curses.color_pair(3) if curses.has_colors() else 0))
        except curses.error:
            pass
        _hline(stdscr, 1, w)

        # === Config ===
        row = 2
        ml = session.max_length
        mode_str = "枚举" if session.mode == "enum" else "吟诗"
        extra = f" | 行长度: {session.line_length}" if session.mode == "poetry" else ""
        cfg = f" 字符集: {session.chars_label} ({session.chars_len}字) | 模式: {mode_str} | 最大长度: {ml}{extra}"
        _puts(stdscr, row, 0, cfg[:w - 1])

        # === Stats ===
        total = estimate_length(session)
        total_str = fmt_num(total) if total <= 10 ** 18 else "过大"
        now = datetime.now()
        elapsed = (now - session.start_time).total_seconds() if session.start_time else 0
        gen = session.generated
        rate = gen / elapsed if elapsed > 0.5 else 0

        state_str = "▶ 运行" if session.running else ("⏸ 暂停" if session.paused else "◦ 空闲")
        stats = (f" 已生成: {fmt_num(gen)} | 估算: {total_str}"
                 f" | 速率: {rate:.0f}/s | 用时: {elapsed:.1f}s | {state_str}")
        _puts(stdscr, row + 1, 0, stats[:w - 1])
        _hline(stdscr, row + 2, w)

        # === Results area ===
        result_top = row + 3
        result_h = max(1, h - result_top - 3)

        # drain queue
        items_popped = 0
        while not session.result_queue.empty():
            try:
                item = session.result_queue.get_nowait()
            except queue.Empty:
                break
            items_popped += 1
            if session.mode == "poetry":
                try:
                    raw = item.replace("data: ", "", 1)
                    p = json.loads(raw)
                    if p.get("type") == "poem":
                        for pl in p.get("lines", []):
                            display_buf.append(f"  {pl}")
                        display_buf.append(f"  ─ 第{p.get('index', 0) + 1}首")
                        display_buf.append("")
                        continue
                except (json.JSONDecodeError, ValueError):
                    pass
            text = item.replace("data: ", "", 1)
            display_buf.append(text)

        if items_popped > 0:
            session.generated += items_popped

        for i in range(result_h):
            try:
                if i < len(display_buf):
                    line = display_buf[-(result_h - i)] if len(display_buf) > result_h else display_buf[i]
                    _puts(stdscr, result_top + i, 1, line[:w - 3])
                else:
                    stdscr.addch(result_top + i, 0, curses.ACS_VLINE)
                    stdscr.addch(result_top + i, w - 1, curses.ACS_VLINE)
            except curses.error:
                pass

        # trim buffer
        max_buf = max(result_h * 4, 200)
        if len(display_buf) > max_buf:
            display_buf[:len(display_buf) - max_buf] = []

        # === Status bar ===
        sb_row = h - 2
        _hline(stdscr, sb_row, w)
        if session.running:
            hint = " [P]暂停 [T]停止 [S]保存 [q]退出 "
        elif session.paused:
            hint = " [R]继续 [T]停止 [S]保存 [q]退出 "
        else:
            hint = " [C]字符集 [M]模式 [+/-]长度 [Enter]开始 [q]退出 "
        _puts(stdscr, sb_row + 1, 0, hint[:w - 1])

        # side borders
        for r in range(2, sb_row + 1):
            try:
                stdscr.addch(r, 0, curses.ACS_VLINE)
                stdscr.addch(r, w - 1, curses.ACS_VLINE)
            except curses.error:
                pass

        # count hint
        if gen > 0:
            try:
                _puts(stdscr, h - 1, max(0, w - 20), f" 共{fmt_num(gen)}条 ")
            except curses.error:
                pass

        curses.doupdate()

        # === Input ===
        key = stdscr.getch()
        if key == -1:
            continue
        if key in (ord('q'), 27):
            if session.running or session.paused:
                stop_session(session.session_id)
                if session.gen_thread:
                    session.gen_thread.join(timeout=1)
            break

        elif key == ord('c') and not session.running and not session.paused:
            idx = PRESET_KEYS.index(session.chars_label) if session.chars_label in PRESET_KEYS else 0
            idx = (idx + 1) % len(PRESET_KEYS)
            session.chars_label = PRESET_KEYS[idx]
            session.chars = PRESETS[session.chars_label]["chars"]
            session.chars_len = len(session.chars)

        elif key == ord('m') and not session.running and not session.paused:
            session.mode = "poetry" if session.mode == "enum" else "enum"

        elif key == ord('+') and not session.running and not session.paused:
            if session.mode == "poetry":
                session.line_length = min(session.line_length + 1, 20)
                session.max_length = session.line_length
            else:
                session.max_length = min(session.max_length + 1, 10)

        elif key == ord('-') and not session.running and not session.paused:
            if session.mode == "poetry":
                session.line_length = max(session.line_length - 1, 1)
                session.max_length = session.line_length
            else:
                session.max_length = max(session.max_length - 1, 1)

        elif key in (ord('\n'), ord('\r')) and not session.running and not session.paused:
            session.session_id = "tui_" + str(int(time.time()))
            session.generated = 0
            session.start_time = datetime.now()
            session.running = True
            session.paused = False
            display_buf.clear()
            while not session.result_queue.empty():
                try:
                    session.result_queue.get_nowait()
                except queue.Empty:
                    break
            if session.mode == "poetry":
                session.max_length = session.line_length
            session.gen_thread = threading.Thread(
                target=generator_worker, args=(session, None), daemon=True)
            session.gen_thread.start()

        elif key == ord('p') and session.running:
            pause_session(session.session_id)
            session.running = False
            session.paused = True

        elif key == ord('r') and session.paused:
            paused = get_paused_state(session.session_id)
            if paused:
                clear_paused_state(session.session_id)
            clear_stop(session.session_id)
            session.running = True
            session.paused = False
            session.session_id = "tui_" + str(int(time.time()))
            session.gen_thread = threading.Thread(
                target=generator_worker, args=(session, paused), daemon=True)
            session.gen_thread.start()

        elif key == ord('t'):
            stop_session(session.session_id)
            if session.gen_thread:
                session.gen_thread.join(timeout=1)
            session.running = False
            session.paused = False
            session.gen_thread = None

        elif key == ord('s') and session.generated > 0:
            _do_save(session, stdscr)


def _hline(win, y: int, w: int):
    try:
        win.hline(y, 0, curses.ACS_HLINE, w)
    except curses.error:
        pass


def _puts(win, y: int, x: int, s: str):
    try:
        win.addstr(y, x, s)
    except curses.error:
        pass


def _do_save(session: TUISession, stdscr):
    import os
    from datetime import datetime
    os.makedirs("output", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"output/shiyun_tui_{ts}.txt"
    try:
        result = save_combinations(
            session.chars, session.max_length, fname, compress=False)
        msg = f" 已保存 {result.get('count', 0)} 条 → {fname} "
    except Exception as e:
        msg = f" 保存失败: {e} "
    h, w = stdscr.getmaxyx()
    _puts(stdscr, h - 1, 0, msg[:w - 1])
    stdscr.refresh()
    curses.napms(2000)


def main():
    import sys
    if "--tui" in sys.argv:
        try:
            curses.wrapper(run_tui)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"TUI错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("用法: python app.py --tui  启动TUI模式")
        print("      python app.py        启动Web服务器")


if __name__ == "__main__":
    main()
