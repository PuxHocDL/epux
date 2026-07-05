from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .audio import play_wav
from .config import AppConfig, default_config_path, default_db_path
from .db import Database
from .notifications import reminder_loop, send_review_reminder
from .ollama import OllamaClient
from .pronunciation import record_and_assess
from .sample_data import SAMPLE_WORDS


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

console = Console(legacy_windows=False)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "tui"

    try:
        if command == "tui":
            run_tui(args)
        elif command == "add":
            cmd_add(args)
        elif command == "list":
            cmd_list(args)
        elif command == "review":
            cmd_review(args)
        elif command == "record":
            cmd_record(args)
        elif command == "play":
            cmd_play(args)
        elif command == "seed":
            cmd_seed()
        elif command == "suggest":
            cmd_suggest(args)
        elif command == "complete":
            cmd_complete(args)
        elif command == "quiz":
            cmd_quiz(args)
        elif command == "remind":
            cmd_remind(args)
        elif command == "paths":
            cmd_paths()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        console.print("\n[yellow]Đã dừng.[/]")
    except Exception as exc:
        console.print(f"[red]Lỗi:[/] {exc}")
        raise SystemExit(1) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="epux",
        description="EPux - học từ vựng tiếng Anh local-first trong terminal.",
    )
    sub = parser.add_subparsers(dest="command")

    tui = sub.add_parser("tui", help="Mở giao diện terminal.")
    tui.add_argument(
        "--tab",
        choices=["dashboard", "add", "quiz", "review", "library", "settings"],
        default="dashboard",
        help="Mở thẳng vào tab mong muốn.",
    )
    tui.add_argument("--review-now", action="store_true", help="Vào tab ôn tập và lấy thẻ đầu tiên.")
    tui.add_argument("--quiz-now", action="store_true", help="Vào tab kiểm tra và tạo câu hỏi mới.")

    add = sub.add_parser("add", help="Thêm một từ/cụm từ.")
    add.add_argument("term")
    add.add_argument("-m", "--meaning", default="")
    add.add_argument("-e", "--example", default="")
    add.add_argument("-n", "--notes", default="")
    add.add_argument("-t", "--tags", default="")

    list_cmd = sub.add_parser("list", help="Liệt kê từ vựng.")
    list_cmd.add_argument("--due", action="store_true", help="Chỉ hiện từ đến hạn.")
    list_cmd.add_argument("--limit", type=int, default=30)
    list_cmd.add_argument("--query", default="")

    review = sub.add_parser("review", help="Chấm một thẻ: 0=lại, 1=khó, 2=ổn, 3=dễ.")
    review.add_argument("word_id", type=int)
    review.add_argument("rating", type=int, choices=[0, 1, 2, 3])

    record = sub.add_parser("record", help="Thu âm và chấm phát âm local.")
    record.add_argument("target")
    record.add_argument("--seconds", type=int, default=None)
    record.add_argument("--word-id", type=int, default=None)

    play = sub.add_parser("play", help="Phát lại file WAV.")
    play.add_argument("wav_path")

    sub.add_parser("seed", help="Nạp bộ từ mẫu.")

    suggest = sub.add_parser("suggest", help="Dùng Ollama local để tạo và lưu từ mới.")
    suggest.add_argument("--topic", default="daily life")
    suggest.add_argument("--level", default="B1")
    suggest.add_argument("--count", type=int, default=8)

    complete = sub.add_parser("complete", help="Gợi ý từ/cụm từ từ vài ký tự đầu.")
    complete.add_argument("prefix")
    complete.add_argument("--level", default="B1")
    complete.add_argument("--count", type=int, default=8)
    complete.add_argument("--ai", action="store_true", help="Hỏi thêm Ollama local.")

    quiz = sub.add_parser("quiz", help="Làm bài kiểm tra trắc nghiệm trong terminal.")
    quiz.add_argument("--count", type=int, default=10)

    remind = sub.add_parser("remind", help="Gửi nhắc học bằng cửa sổ popup hoặc Windows toast.")
    remind.add_argument("--daemon", action="store_true", help="Chạy vòng lặp nhắc học.")
    remind.add_argument("--once", action="store_true", help="Gửi một thông báo nếu có từ đến hạn.")
    remind.add_argument("--window", action="store_true", help="Hiện cửa sổ popup pixel xanh lá.")
    remind.add_argument("--toast", action="store_true", help="Dùng Windows toast thay vì cửa sổ.")
    remind.add_argument("--both", action="store_true", help="Gửi cả toast và cửa sổ popup.")

    sub.add_parser("paths", help="In đường dẫn config/database/recordings.")
    return parser


def run_tui(args: argparse.Namespace | None = None) -> None:
    try:
        from .tui import EPuxApp
    except ImportError as exc:
        console.print("[red]Thiếu dependency giao diện.[/]")
        console.print("Chạy: [bold]pip install -r requirements.txt[/]")
        raise SystemExit(1) from exc

    tab_map = {
        "dashboard": "dashboard_tab",
        "add": "add_tab",
        "quiz": "quiz_tab",
        "review": "review_tab",
        "library": "library_tab",
        "settings": "settings_tab",
    }
    launch_tab = tab_map.get(getattr(args, "tab", "dashboard"), "dashboard_tab")
    app = EPuxApp(
        Database(),
        AppConfig.load(),
        launch_tab=launch_tab,
        launch_review=bool(getattr(args, "review_now", False)),
        launch_quiz=bool(getattr(args, "quiz_now", False)),
    )
    app.run()


def cmd_add(args: argparse.Namespace) -> None:
    db = Database()
    try:
        item = db.add_word(args.term, args.meaning, args.example, args.notes, args.tags)
        console.print(f"[green]Đã lưu:[/] #{item.id} {item.term}")
    finally:
        db.close()


def cmd_list(args: argparse.Namespace) -> None:
    db = Database()
    try:
        rows = db.due_words(args.limit) if args.due else db.list_words(args.limit, args.query)
        table = Table(title="EPux Vocabulary")
        table.add_column("ID", justify="right")
        table.add_column("Term", style="cyan")
        table.add_column("Meaning")
        table.add_column("Reps", justify="right")
        table.add_column("Due")
        for item in rows:
            table.add_row(str(item.id), item.term, item.meaning, str(item.repetitions), item.due_at)
        console.print(table)
    finally:
        db.close()


def cmd_review(args: argparse.Namespace) -> None:
    db = Database()
    try:
        item = db.review_word(args.word_id, args.rating)
        console.print(f"[green]Đã cập nhật:[/] {item.term} -> due {item.due_at}")
    finally:
        db.close()


def cmd_record(args: argparse.Namespace) -> None:
    db = Database()
    config = AppConfig.load()
    try:
        console.print(f"[cyan]Thu âm:[/] {args.target}")
        assessment = record_and_assess(
            db=db,
            config=config,
            target_text=args.target,
            word_id=args.word_id,
            seconds=args.seconds,
        )
        score = "chưa có STT" if assessment.score is None else f"{assessment.score:.0f}/100"
        console.print(f"[green]Đã lưu WAV:[/] {assessment.metrics.wav_path}")
        console.print(f"[bold]Điểm:[/] {score}")
        console.print(f"[bold]Transcript:[/] {assessment.transcription.text or '(trống)'}")
        console.print(f"[bold]Feedback:[/] {assessment.feedback}")
    finally:
        db.close()


def cmd_play(args: argparse.Namespace) -> None:
    play_wav(Path(args.wav_path))


def cmd_seed() -> None:
    db = Database()
    try:
        count = db.add_words(SAMPLE_WORDS)
        console.print(f"[green]Đã nạp {count} thẻ mẫu.[/]")
    finally:
        db.close()


def cmd_suggest(args: argparse.Namespace) -> None:
    config = AppConfig.load()
    client = OllamaClient(config)
    if not client.is_available():
        raise RuntimeError(f"Không kết nối được Ollama tại {config.ollama_url}.")

    words = client.suggest_words(args.topic, args.level, args.count)
    db = Database()
    try:
        saved = db.add_words((w.term, w.meaning, w.example, w.notes, w.tags) for w in words)
        console.print(f"[green]Đã lưu {saved} từ mới từ Ollama.[/]")
    finally:
        db.close()


def cmd_complete(args: argparse.Namespace) -> None:
    db = Database()
    try:
        rows = db.suggest_words_by_prefix(args.prefix, args.count)
        table = Table(title=f"Suggestions for {args.prefix!r}")
        table.add_column("Source", style="cyan")
        table.add_column("Term")
        table.add_column("Meaning")
        for item in rows:
            table.add_row("local", item.term, item.meaning)

        if args.ai:
            config = AppConfig.load()
            client = OllamaClient(config)
            if client.is_available():
                local_terms = {item.term.lower() for item in rows}
                for word in client.suggest_prefix(args.prefix, args.level, args.count):
                    if word.term.lower() in local_terms:
                        continue
                    table.add_row("ollama", word.term, word.meaning)
            else:
                console.print(f"[yellow]Ollama chưa sẵn sàng tại {config.ollama_url}.[/]")

        console.print(table)
    finally:
        db.close()


def cmd_quiz(args: argparse.Namespace) -> None:
    db = Database()
    try:
        score = 0
        total = max(1, args.count)
        for index in range(1, total + 1):
            word, prompt, options, correct_answer, mode = db.build_quiz_question()
            prompt_label = "Chọn nghĩa đúng cho" if mode == "term_to_meaning" else "Chọn từ đúng với nghĩa"
            console.print(f"\n[bold cyan]Câu {index}/{total}[/]  {prompt_label}: [bold]{prompt}[/]")
            labels = ["A", "B", "C", "D"]
            for pos, option in enumerate(options):
                console.print(f"  [bold]{labels[pos]}[/]. {option}")

            answer = console.input("Chọn A/B/C/D: ").strip().upper()
            if answer not in labels[: len(options)]:
                console.print("[yellow]Bỏ qua câu này.[/]")
                continue
            selected = options[labels.index(answer)]
            correct = selected == correct_answer
            db.log_quiz_answer(
                word_id=word.id,
                prompt=prompt,
                selected_answer=selected,
                correct_answer=correct_answer,
                is_correct=correct,
            )
            if correct:
                score += 1
                db.review_word(word.id, 2)
                console.print("[green]Đúng.[/]")
            else:
                db.review_word(word.id, 0)
                console.print(f"[red]Chưa đúng.[/] Đáp án: {correct_answer}")
            if word.example:
                console.print(f"[dim]Ví dụ: {word.example}[/]")

        console.print(f"\n[bold]Kết quả:[/] {score}/{total}")
    finally:
        db.close()


def cmd_remind(args: argparse.Namespace) -> None:
    db = Database()
    config = AppConfig.load()
    mode = "window"
    if args.toast:
        mode = "toast"
    if args.both:
        mode = "both"
    if args.window:
        mode = "window"
    try:
        due = db.stats()["due"]
        if args.once or not args.daemon:
            if due:
                sent = send_review_reminder(due, mode=mode)
                console.print("[green]Đã gửi nhắc học.[/]" if sent else f"[yellow]Bạn có {due} từ cần ôn.[/]")
            else:
                console.print("[cyan]Chưa có từ đến hạn.[/]")
            return

        console.print(
            f"[cyan]EPux reminder đang chạy ({mode}).[/] Mỗi {config.reminder_minutes} phút, "
            "Ctrl+C để dừng."
        )
        reminder_loop(db, config, mode=mode)
    finally:
        db.close()


def cmd_paths() -> None:
    config = AppConfig.load()
    table = Table(title="EPux local paths")
    table.add_column("Loại", style="cyan")
    table.add_column("Đường dẫn")
    table.add_row("Config", str(default_config_path()))
    table.add_row("Database", str(default_db_path()))
    table.add_row("Recordings", str(config.recordings_dir()))
    console.print(table)


if __name__ == "__main__":
    main(sys.argv[1:])
