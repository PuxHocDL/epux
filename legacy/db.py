from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from random import choice, shuffle

from .config import default_db_path
from .srs import format_dt, schedule_review, utc_now


@dataclass
class VocabItem:
    id: int
    term: str
    meaning: str
    example: str
    notes: str
    tags: str
    ease: float
    interval_days: int
    repetitions: int
    lapses: int
    due_at: str
    created_at: str
    updated_at: str


@dataclass
class ReviewLog:
    id: int
    word_id: int
    rating: int
    reviewed_at: str


@dataclass
class RecordingLog:
    id: int
    word_id: int | None
    target_text: str
    wav_path: str
    transcript: str
    score: float | None
    feedback: str
    created_at: str


@dataclass
class QuizLog:
    id: int
    word_id: int
    prompt: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    created_at: str


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self.migrate()

    def close(self) -> None:
        self._conn.close()

    def migrate(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL UNIQUE,
                meaning TEXT NOT NULL DEFAULT '',
                example TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                ease REAL NOT NULL DEFAULT 2.5,
                interval_days INTEGER NOT NULL DEFAULT 0,
                repetitions INTEGER NOT NULL DEFAULT 0,
                lapses INTEGER NOT NULL DEFAULT 0,
                due_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL,
                reviewed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER REFERENCES words(id) ON DELETE SET NULL,
                target_text TEXT NOT NULL,
                wav_path TEXT NOT NULL,
                transcript TEXT NOT NULL DEFAULT '',
                score REAL,
                feedback TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
                prompt TEXT NOT NULL,
                selected_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def add_word(
        self,
        term: str,
        meaning: str = "",
        example: str = "",
        notes: str = "",
        tags: str = "",
    ) -> VocabItem:
        now = format_dt(utc_now())
        term = term.strip()
        if not term:
            raise ValueError("Từ vựng không được để trống.")

        self._conn.execute(
            """
            INSERT INTO words (term, meaning, example, notes, tags, due_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(term) DO UPDATE SET
                meaning=excluded.meaning,
                example=excluded.example,
                notes=excluded.notes,
                tags=excluded.tags,
                updated_at=excluded.updated_at
            """,
            (term, meaning.strip(), example.strip(), notes.strip(), tags.strip(), now, now, now),
        )
        self._conn.commit()
        item = self.get_word_by_term(term)
        if item is None:
            raise RuntimeError("Không thể lưu từ vựng.")
        return item

    def update_word(
        self,
        word_id: int,
        term: str,
        meaning: str = "",
        example: str = "",
        notes: str = "",
        tags: str = "",
    ) -> VocabItem:
        now = format_dt(utc_now())
        term = term.strip()
        if not term:
            raise ValueError("Term cannot be empty.")
        if self.get_word(word_id) is None:
            raise ValueError(f"Cannot find word_id={word_id}.")

        duplicate = self.get_word_by_term(term)
        if duplicate is not None and duplicate.id != word_id:
            raise ValueError(f"Another card already uses this term: {term}.")

        self._conn.execute(
            """
            UPDATE words
            SET term = ?, meaning = ?, example = ?, notes = ?, tags = ?, updated_at = ?
            WHERE id = ?
            """,
            (term, meaning.strip(), example.strip(), notes.strip(), tags.strip(), now, word_id),
        )
        self._conn.commit()
        item = self.get_word(word_id)
        if item is None:
            raise RuntimeError("Could not update vocabulary card.")
        return item

    def delete_word(self, word_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def add_words(self, words: Iterable[tuple[str, str, str, str, str]]) -> int:
        count = 0
        for term, meaning, example, notes, tags in words:
            self.add_word(term, meaning, example, notes, tags)
            count += 1
        return count

    def get_word(self, word_id: int) -> VocabItem | None:
        row = self._conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        return self._item_from_row(row) if row else None

    def get_word_by_term(self, term: str) -> VocabItem | None:
        row = self._conn.execute("SELECT * FROM words WHERE lower(term) = lower(?)", (term.strip(),)).fetchone()
        return self._item_from_row(row) if row else None

    def list_words(self, limit: int = 200, query: str = "") -> list[VocabItem]:
        if query.strip():
            like = f"%{query.strip()}%"
            rows = self._conn.execute(
                """
                SELECT * FROM words
                WHERE term LIKE ? OR meaning LIKE ? OR tags LIKE ?
                ORDER BY due_at ASC, term ASC
                LIMIT ?
                """,
                (like, like, like, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM words ORDER BY due_at ASC, term ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def due_words(self, limit: int = 30) -> list[VocabItem]:
        now = format_dt(utc_now())
        rows = self._conn.execute(
            "SELECT * FROM words WHERE due_at <= ? ORDER BY due_at ASC, repetitions ASC LIMIT ?",
            (now, limit),
        ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def suggest_words_by_prefix(self, prefix: str, limit: int = 8) -> list[VocabItem]:
        prefix = prefix.strip()
        if not prefix:
            return []
        starts = f"{prefix}%"
        contains = f"%{prefix}%"
        rows = self._conn.execute(
            """
            SELECT * FROM words
            WHERE term LIKE ? OR meaning LIKE ? OR tags LIKE ?
            ORDER BY
                CASE WHEN term LIKE ? THEN 0 ELSE 1 END,
                repetitions ASC,
                term ASC
            LIMIT ?
            """,
            (contains, contains, contains, starts, limit),
        ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def quiz_candidates(self, limit: int = 80) -> list[VocabItem]:
        due = self.due_words(limit)
        if len(due) >= min(limit, 4):
            return due
        seen = {item.id for item in due}
        extra = [item for item in self.list_words(limit) if item.id not in seen]
        return due + extra

    def build_quiz_question(self, mode: str = "mixed") -> tuple[VocabItem, str, list[str], str, str]:
        candidates = [item for item in self.quiz_candidates(100) if item.meaning.strip()]
        if not candidates:
            raise ValueError("Cần ít nhất một từ có nghĩa để tạo bài kiểm tra.")
        active_mode = mode
        if active_mode not in {"term_to_meaning", "meaning_to_term"}:
            active_mode = choice(["term_to_meaning", "meaning_to_term"])

        sample_pool = candidates[: min(len(candidates), 12)]
        target = choice(sample_pool)

        if active_mode == "meaning_to_term":
            prompt = target.meaning
            correct_answer = target.term
            distractors = [item.term for item in candidates if item.term and item.id != target.id]
            if len(distractors) < 3:
                extra_terms = [
                    item.term
                    for item in self.list_words(200)
                    if item.term and item.id != target.id and item.term not in distractors
                ]
                distractors.extend(extra_terms)
        else:
            prompt = target.term
            correct_answer = target.meaning
            distractors = [item.meaning for item in candidates if item.meaning and item.id != target.id]
            if len(distractors) < 3:
                extra_meanings = [
                    item.meaning
                    for item in self.list_words(200)
                    if item.meaning and item.id != target.id and item.meaning not in distractors
                ]
                distractors.extend(extra_meanings)

        options = [correct_answer] + distractors[:3]
        shuffle(options)
        return target, prompt, options, correct_answer, active_mode

    def log_quiz_answer(
        self,
        *,
        word_id: int,
        prompt: str,
        selected_answer: str,
        correct_answer: str,
        is_correct: bool,
    ) -> QuizLog:
        created_at = format_dt(utc_now())
        cur = self._conn.execute(
            """
            INSERT INTO quiz_logs (word_id, prompt, selected_answer, correct_answer, is_correct, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (word_id, prompt, selected_answer, correct_answer, int(is_correct), created_at),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM quiz_logs WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._quiz_log_from_row(row)

    def review_word(self, word_id: int, rating: int) -> VocabItem:
        item = self.get_word(word_id)
        if item is None:
            raise ValueError(f"Không tìm thấy word_id={word_id}.")

        result = schedule_review(
            rating,
            ease=item.ease,
            interval_days=item.interval_days,
            repetitions=item.repetitions,
            lapses=item.lapses,
        )
        reviewed_at = format_dt(utc_now())
        self._conn.execute(
            """
            UPDATE words
            SET ease = ?, interval_days = ?, repetitions = ?, lapses = ?, due_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                result.ease,
                result.interval_days,
                result.repetitions,
                result.lapses,
                format_dt(result.due_at),
                reviewed_at,
                word_id,
            ),
        )
        self._conn.execute(
            "INSERT INTO reviews (word_id, rating, reviewed_at) VALUES (?, ?, ?)",
            (word_id, rating, reviewed_at),
        )
        self._conn.commit()
        updated = self.get_word(word_id)
        if updated is None:
            raise RuntimeError("Không thể cập nhật lịch ôn.")
        return updated

    def add_recording(
        self,
        *,
        word_id: int | None,
        target_text: str,
        wav_path: str,
        transcript: str = "",
        score: float | None = None,
        feedback: str = "",
    ) -> RecordingLog:
        created_at = format_dt(utc_now())
        cur = self._conn.execute(
            """
            INSERT INTO recordings (word_id, target_text, wav_path, transcript, score, feedback, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (word_id, target_text, wav_path, transcript, score, feedback, created_at),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM recordings WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._recording_from_row(row)

    def recent_recordings(self, limit: int = 20) -> list[RecordingLog]:
        rows = self._conn.execute(
            "SELECT * FROM recordings ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._recording_from_row(row) for row in rows]

    def stats(self) -> dict[str, int]:
        total = self._conn.execute("SELECT count(*) FROM words").fetchone()[0]
        due = self._conn.execute("SELECT count(*) FROM words WHERE due_at <= ?", (format_dt(utc_now()),)).fetchone()[0]
        reviews = self._conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
        recordings = self._conn.execute("SELECT count(*) FROM recordings").fetchone()[0]
        quiz = self._conn.execute("SELECT count(*) FROM quiz_logs").fetchone()[0]
        return {"total": total, "due": due, "reviews": reviews, "recordings": recordings, "quiz": quiz}

    @staticmethod
    def _item_from_row(row: sqlite3.Row) -> VocabItem:
        return VocabItem(
            id=row["id"],
            term=row["term"],
            meaning=row["meaning"],
            example=row["example"],
            notes=row["notes"],
            tags=row["tags"],
            ease=float(row["ease"]),
            interval_days=int(row["interval_days"]),
            repetitions=int(row["repetitions"]),
            lapses=int(row["lapses"]),
            due_at=row["due_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _recording_from_row(row: sqlite3.Row) -> RecordingLog:
        return RecordingLog(
            id=row["id"],
            word_id=row["word_id"],
            target_text=row["target_text"],
            wav_path=row["wav_path"],
            transcript=row["transcript"],
            score=row["score"],
            feedback=row["feedback"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _quiz_log_from_row(row: sqlite3.Row) -> QuizLog:
        return QuizLog(
            id=row["id"],
            word_id=row["word_id"],
            prompt=row["prompt"],
            selected_answer=row["selected_answer"],
            correct_answer=row["correct_answer"],
            is_correct=bool(row["is_correct"]),
            created_at=row["created_at"],
        )
