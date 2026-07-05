from __future__ import annotations

import argparse
import sys

from .config import AppConfig, default_config_path, default_db_path


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "serve"

    try:
        if command == "serve":
            cmd_serve(args)
        elif command == "remind":
            cmd_remind(args)
        elif command == "paths":
            cmd_paths()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\nĐã dừng.")
    except Exception as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="epux",
        description="EPux — học từ vựng & luyện writing IELTS bằng LLM, chạy local.",
    )
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="Chạy web app (mặc định).")
    serve.add_argument("--port", type=int, default=None)
    serve.add_argument("--no-browser", action="store_true", help="Không tự mở trình duyệt.")

    remind = sub.add_parser("remind", help="Nhắc học bằng popup/toast Windows.")
    remind.add_argument("--daemon", action="store_true", help="Chạy vòng lặp nhắc học nền.")
    remind.add_argument("--once", action="store_true", help="Gửi một thông báo nếu có từ đến hạn.")
    remind.add_argument("--window", action="store_true", help="Cửa sổ popup (mặc định).")
    remind.add_argument("--toast", action="store_true", help="Dùng Windows toast thay cửa sổ.")
    remind.add_argument("--both", action="store_true", help="Cả toast lẫn cửa sổ.")

    sub.add_parser("paths", help="In đường dẫn config/database.")
    return parser


def cmd_serve(args: argparse.Namespace) -> None:
    from .server import serve

    # Chạy `epux` không subcommand thì Namespace không có port/no_browser.
    serve(
        port=getattr(args, "port", None),
        open_browser=not getattr(args, "no_browser", False),
    )


def cmd_remind(args: argparse.Namespace) -> None:
    from .db import Database
    from .notifications import reminder_loop, send_review_reminder

    db = Database()
    config = AppConfig.load()
    mode = "window"
    if args.toast:
        mode = "toast"
    if args.both:
        mode = "both"
    url = f"http://127.0.0.1:{config.server_port}"
    try:
        if args.once or not args.daemon:
            due = db.due_count()
            if due:
                sent = send_review_reminder(due, mode=mode, url=url)
                print("Đã gửi nhắc học." if sent else f"Bạn có {due} từ cần ôn -> {url}")
            else:
                print("Chưa có từ đến hạn.")
            return
        print(f"EPux reminder đang chạy ({mode}). Nhắc mỗi ~{config.reminder_minutes} phút, "
              "dày hơn khi nhiều thẻ đến hạn. Ctrl+C để dừng.")
        reminder_loop(db, config, mode=mode)
    finally:
        db.close()


def cmd_paths() -> None:
    print(f"Config:   {default_config_path()}")
    print(f"Database: {default_db_path()}")


if __name__ == "__main__":
    main(sys.argv[1:])
