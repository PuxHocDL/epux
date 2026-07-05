from __future__ import annotations

import sys
import time
import webbrowser
from datetime import datetime, time as dtime
from typing import Callable

from .config import AppConfig
from .db import Database


def send_toast(title: str, message: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        from winotify import Notification

        toast = Notification(app_id="EPux", title=title, msg=message)
        toast.show()
        return True
    except Exception:
        return False


def send_window_notification(title: str, message: str, *, due_count: int | None, url: str) -> bool:
    """Cửa sổ nhắc học nhỏ kiểu pixel, nút bấm mở thẳng web app."""
    try:
        import tkinter as tk
        from tkinter import font
    except Exception:
        return False

    try:
        root = tk.Tk()
        root.title(title)
        root.configure(bg="#020603")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        width, height = 460, 240
        x = max(0, root.winfo_screenwidth() - width - 32)
        y = max(0, root.winfo_screenheight() - height - 72)
        root.geometry(f"{width}x{height}+{x}+{y}")

        try:
            pixel_font = font.Font(family="Consolas", size=11, weight="bold")
            body_font = font.Font(family="Consolas", size=10)
            big_font = font.Font(family="Consolas", size=18, weight="bold")
        except Exception:
            pixel_font = ("Courier New", 11, "bold")
            body_font = ("Courier New", 10)
            big_font = ("Courier New", 18, "bold")

        shell = tk.Frame(root, bg="#020603", highlightbackground="#39ff88", highlightthickness=2)
        shell.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(shell, text="EPux // REVIEW ALERT", bg="#020603", fg="#39ff88",
                 font=pixel_font, anchor="w").pack(fill="x", padx=14, pady=(12, 4))
        count_text = "--" if due_count is None else str(due_count)
        tk.Label(shell, text=f"{count_text} WORDS DUE", bg="#020603", fg="#9dff57",
                 font=big_font, anchor="w").pack(fill="x", padx=14, pady=(2, 8))
        tk.Label(shell, text=message, bg="#020603", fg="#d8ffe0", font=body_font,
                 justify="left", wraplength=410, anchor="w").pack(fill="x", padx=14, pady=(0, 12))

        button_bar = tk.Frame(shell, bg="#020603")
        button_bar.pack(fill="x", padx=14, pady=(4, 14), side="bottom")

        def close() -> None:
            root.destroy()

        def open_app() -> None:
            try:
                webbrowser.open(url)
            finally:
                close()

        def make_button(text: str, command: Callable[[], None]) -> tk.Button:
            return tk.Button(
                button_bar, text=text, command=command,
                bg="#071009", fg="#d8ffe0", activebackground="#0c1d10",
                activeforeground="#39ff88", highlightbackground="#39ff88",
                relief="solid", bd=1, font=pixel_font, padx=12, pady=6,
            )

        make_button("REVIEW NOW", open_app).pack(side="left", padx=(0, 8))
        make_button("DISMISS", close).pack(side="right")
        root.bind("<Escape>", lambda _e: close())
        root.bind("<Return>", lambda _e: open_app())
        root.lift()
        root.focus_force()
        root.mainloop()
        return True
    except Exception:
        return False


def send_review_reminder(due_count: int, *, mode: str, url: str) -> bool:
    title = "EPux: đến giờ ôn từ"
    message = f"Bạn có {due_count} từ đang đến hạn theo đường cong lãng quên.\nBấm REVIEW NOW để ôn ngay."
    if mode == "toast":
        return send_toast(title, message)
    if mode == "both":
        sent = send_toast(title, message)
        return send_window_notification(title, message, due_count=due_count, url=url) or sent
    return send_window_notification(title, message, due_count=due_count, url=url)


def in_quiet_hours(now: datetime, quiet_start: str, quiet_end: str) -> bool:
    start = _parse_clock(quiet_start)
    end = _parse_clock(quiet_end)
    current = now.time().replace(second=0, microsecond=0)
    if start < end:
        return start <= current < end
    return current >= start or current < end


def dynamic_interval_minutes(base_minutes: int, due_count: int) -> int:
    """Càng nhiều thẻ đến hạn, nhắc càng dày (nhưng không dày hơn 15 phút/lần)."""
    if due_count >= 40:
        return max(15, base_minutes // 4)
    if due_count >= 20:
        return max(15, base_minutes // 2)
    return max(15, base_minutes)


def reminder_loop(
    db: Database,
    config: AppConfig,
    *,
    stop: Callable[[], bool] | None = None,
    mode: str = "window",
) -> None:
    stop = stop or (lambda: False)
    url = f"http://127.0.0.1:{config.server_port}"
    last_sent_at: float = 0.0

    while not stop():
        now = datetime.now()
        if not in_quiet_hours(now, config.notify_quiet_start, config.notify_quiet_end):
            due_count = db.due_count()
            interval = dynamic_interval_minutes(config.reminder_minutes, due_count) * 60
            elapsed = time.monotonic() - last_sent_at
            if due_count and (last_sent_at == 0.0 or elapsed >= interval):
                sent = send_review_reminder(due_count, mode=mode, url=url)
                if not sent:
                    print(f"[EPux] Bạn có {due_count} từ cần ôn -> {url}", flush=True)
                last_sent_at = time.monotonic()
        time.sleep(30)


def _parse_clock(value: str) -> dtime:
    try:
        hour, minute = value.split(":", 1)
        return dtime(int(hour), int(minute))
    except Exception:
        return dtime(0, 0)
