from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from random import choice, shuffle
from typing import Any

from .config import default_db_path
from .srs import format_dt, parse_dt, schedule_review, utc_now

RARITIES = ["D", "C", "B", "A", "S", "SS", "SSS"]


@dataclass
class VocabItem:
    id: int
    user_id: int
    term: str
    meaning: str
    example: str
    example_vi: str
    ipa: str
    pos: str
    collocations: list[str]
    notes: str
    tags: str
    topic: str
    band: str
    rarity: str
    is_gem: bool
    is_toeic: bool
    toeic_part: str
    owned: bool
    owned_at: str
    stars: int
    dupes: int
    source: str
    ease: float
    interval_days: float
    repetitions: int
    lapses: int
    stability: float
    due_at: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Writing:
    id: int
    user_id: int
    kind: str
    title: str
    prompt: str
    content: str
    word_count: int
    overall_band: float | None
    feedback: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def local_day_bounds(offset_days: int = 0) -> tuple[str, str, str]:
    local_now = datetime.now().astimezone()
    day = (local_now + timedelta(days=offset_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    start = day
    end = day + timedelta(days=1)
    return format_dt(start), format_dt(end), day.strftime("%Y-%m-%d")


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = DELETE")
        self.migrate()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------- migration

    def migrate(self) -> None:
        self._conn.executescript(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                term TEXT NOT NULL,
                meaning TEXT NOT NULL DEFAULT '',
                example TEXT NOT NULL DEFAULT '',
                example_vi TEXT NOT NULL DEFAULT '',
                ipa TEXT NOT NULL DEFAULT '',
                pos TEXT NOT NULL DEFAULT '',
                collocations TEXT NOT NULL DEFAULT '[]',
                notes TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '',
                topic TEXT NOT NULL DEFAULT '',
                band TEXT NOT NULL DEFAULT '',
                rarity TEXT NOT NULL DEFAULT 'C',
                is_gem INTEGER NOT NULL DEFAULT 0,
                owned INTEGER NOT NULL DEFAULT 0,
                owned_at TEXT NOT NULL DEFAULT '',
                stars INTEGER NOT NULL DEFAULT 0,
                dupes INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'manual',
                ease REAL NOT NULL DEFAULT 2.5,
                interval_days REAL NOT NULL DEFAULT 0,
                repetitions INTEGER NOT NULL DEFAULT 0,
                lapses INTEGER NOT NULL DEFAULT 0,
                stability REAL NOT NULL DEFAULT 0,
                due_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_toeic INTEGER NOT NULL DEFAULT 0,
                toeic_part TEXT NOT NULL DEFAULT '',
                UNIQUE(user_id, term)
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
                rating INTEGER NOT NULL,
                reviewed_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quiz_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
                prompt TEXT NOT NULL,
                selected_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                name_vi TEXT NOT NULL DEFAULT '',
                description_vi TEXT NOT NULL DEFAULT '',
                sample_words TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS writings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                kind TEXT NOT NULL DEFAULT 'daily',
                title TEXT NOT NULL DEFAULT '',
                prompt TEXT NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER NOT NULL DEFAULT 0,
                overall_band REAL,
                feedback TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme TEXT NOT NULL,
                pattern TEXT NOT NULL UNIQUE,
                use_vi TEXT NOT NULL DEFAULT '',
                examples TEXT NOT NULL DEFAULT '[]',
                band TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS challenge_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                tier TEXT NOT NULL,
                claimed_at TEXT NOT NULL,
                UNIQUE(user_id, date, code)
            );

            CREATE TABLE IF NOT EXISTS packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                tier TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                opened_at TEXT,
                word_id INTEGER REFERENCES words(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS meta (
                user_id INTEGER NOT NULL REFERENCES users(id),
                key TEXT,
                value TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (user_id, key)
            );

            CREATE TABLE IF NOT EXISTS arena_defenses (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                word_ids TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS arena_ratings (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                rating INTEGER NOT NULL DEFAULT 1000,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS arena_battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attacker_id INTEGER NOT NULL REFERENCES users(id),
                defender_id INTEGER NOT NULL REFERENCES users(id),
                attacker_power INTEGER NOT NULL,
                defender_power INTEGER NOT NULL,
                quiz_correct INTEGER NOT NULL,
                quiz_total INTEGER NOT NULL,
                result TEXT NOT NULL,
                attacker_delta INTEGER NOT NULL,
                defender_delta INTEGER NOT NULL,
                pack_tier TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            '''
        )
        self._conn.commit()

    # ------------------------------------------------------------- auth

    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

    def create_user(self, username: str, password_hash: str) -> int:
        now = format_dt(utc_now())
        cur = self._conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, now)
        )
        self._conn.commit()
        return cur.lastrowid

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    # ----------------------------------------------------------------- words

    def add_word(
        self,
        user_id: int,
        term: str,
        *,
        meaning: str = "",
        example: str = "",
        example_vi: str = "",
        ipa: str = "",
        pos: str = "",
        collocations: list[str] | None = None,
        notes: str = "",
        tags: str = "",
        topic: str = "",
        band: str = "",
        rarity: str = "C",
        is_gem: bool = False,
        is_toeic: bool = False,
        toeic_part: str = "",
        source: str = "manual",
    ) -> VocabItem:
        now = format_dt(utc_now())
        term = term.strip()
        if not term:
            raise ValueError("Từ vựng không được để trống.")
        if rarity not in RARITIES:
            rarity = "C"
        self._conn.execute(
            '''
            INSERT INTO words (user_id, term, meaning, example, example_vi, ipa, pos, collocations, notes,
                               tags, topic, band, rarity, is_gem, is_toeic, toeic_part, source, due_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, term) DO UPDATE SET
                meaning = CASE WHEN excluded.meaning != '' THEN excluded.meaning ELSE words.meaning END,
                example = CASE WHEN excluded.example != '' THEN excluded.example ELSE words.example END,
                example_vi = CASE WHEN excluded.example_vi != '' THEN excluded.example_vi ELSE words.example_vi END,
                ipa = CASE WHEN excluded.ipa != '' THEN excluded.ipa ELSE words.ipa END,
                pos = CASE WHEN excluded.pos != '' THEN excluded.pos ELSE words.pos END,
                collocations = CASE WHEN excluded.collocations != '[]' THEN excluded.collocations ELSE words.collocations END,
                notes = CASE WHEN excluded.notes != '' THEN excluded.notes ELSE words.notes END,
                tags = CASE WHEN excluded.tags != '' THEN excluded.tags ELSE words.tags END,
                topic = CASE WHEN excluded.topic != '' THEN excluded.topic ELSE words.topic END,
                band = CASE WHEN excluded.band != '' THEN excluded.band ELSE words.band END,
                is_toeic = CASE WHEN excluded.is_toeic != 0 THEN excluded.is_toeic ELSE words.is_toeic END,
                toeic_part = CASE WHEN excluded.toeic_part != '' THEN excluded.toeic_part ELSE words.toeic_part END,
                updated_at = excluded.updated_at
            ''',
            (
                user_id, term, meaning.strip(), example.strip(), example_vi.strip(), ipa.strip(), pos.strip(),
                json.dumps(collocations or [], ensure_ascii=False), notes.strip(), tags.strip(),
                topic.strip(), band.strip(), rarity, int(is_gem), int(is_toeic), toeic_part, source, now, now, now,
            ),
        )
        self._conn.commit()
        item = self.get_word_by_term(user_id, term)
        if item is None:
            raise RuntimeError("Không thể lưu từ vựng.")
        return item

    def update_word(self, user_id: int, word_id: int, data: dict[str, Any]) -> VocabItem:
        allowed = {
            "term", "meaning", "example", "example_vi", "ipa", "pos", "notes",
            "tags", "topic", "band", "rarity", "is_toeic", "toeic_part"
        }
        sets: list[str] = []
        values: list[Any] = []
        for key, value in data.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = ?")
            values.append(str(value).strip() if key not in ("is_toeic",) else int(value))
        if "collocations" in data and isinstance(data["collocations"], list):
            sets.append("collocations = ?")
            values.append(json.dumps(data["collocations"], ensure_ascii=False))
        if not sets:
            raise ValueError("Không có trường nào để cập nhật.")
        sets.append("updated_at = ?")
        values.append(format_dt(utc_now()))
        values.extend([word_id, user_id])
        self._conn.execute(f"UPDATE words SET {', '.join(sets)} WHERE id = ? AND user_id = ?", values)
        self._conn.commit()
        item = self.get_word(user_id, word_id)
        if item is None:
            raise ValueError(f"Không tìm thấy word_id={word_id}.")
        return item

    def delete_word(self, user_id: int, word_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM words WHERE id = ? AND user_id = ?", (word_id, user_id))
        self._conn.commit()
        return cur.rowcount > 0

    def get_word(self, user_id: int, word_id: int) -> VocabItem | None:
        row = self._conn.execute("SELECT * FROM words WHERE id = ? AND user_id = ?", (word_id, user_id)).fetchone()
        return self._item_from_row(row) if row else None

    def get_word_by_term(self, user_id: int, term: str) -> VocabItem | None:
        row = self._conn.execute(
            "SELECT * FROM words WHERE lower(term) = lower(?) AND user_id = ?", (term.strip(), user_id)
        ).fetchone()
        return self._item_from_row(row) if row else None

    def list_words(
        self,
        user_id: int,
        *,
        query: str = "",
        topic: str = "",
        rarity: str = "",
        owned: bool | None = None,
        limit: int = 500,
    ) -> list[VocabItem]:
        clauses: list[str] = ["user_id = ?"]
        params: list[Any] = [user_id]
        if query.strip():
            like = f"%{query.strip()}%"
            clauses.append("(term LIKE ? OR meaning LIKE ? OR topic LIKE ? OR tags LIKE ?)")
            params.extend([like, like, like, like])
        if topic.strip():
            clauses.append("topic = ?")
            params.append(topic.strip())
        if rarity.strip():
            clauses.append("rarity = ?")
            params.append(rarity.strip())
        if owned is not None:
            clauses.append("owned = ?")
            params.append(int(owned))
        where = f"WHERE {' AND '.join(clauses)}"
        rows = self._conn.execute(
            f"SELECT * FROM words {where} ORDER BY created_at DESC, term ASC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def all_terms(self, user_id: int) -> list[str]:
        rows = self._conn.execute("SELECT term FROM words WHERE user_id = ?", (user_id,)).fetchall()
        return [row["term"] for row in rows]

    def due_words(self, user_id: int, limit: int = 50) -> list[VocabItem]:
        now = format_dt(utc_now())
        rows = self._conn.execute(
            "SELECT * FROM words WHERE due_at <= ? AND user_id = ? ORDER BY due_at ASC LIMIT ?",
            (now, user_id, limit),
        ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def due_count(self, user_id: int) -> int:
        now = format_dt(utc_now())
        return self._conn.execute(
            "SELECT count(*) FROM words WHERE due_at <= ? AND user_id = ?", (now, user_id)
        ).fetchone()[0]

    def topics_in_words(self, user_id: int) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT topic FROM words WHERE topic != '' AND user_id = ? ORDER BY topic", (user_id,)
        ).fetchall()
        return [row["topic"] for row in rows]

    def set_owned(self, user_id: int, word_id: int) -> None:
        self._conn.execute(
            "UPDATE words SET owned = 1, owned_at = ?, stars = max(stars, 1) WHERE id = ? AND user_id = ?",
            (format_dt(utc_now()), word_id, user_id),
        )
        self._conn.commit()

    def add_dupe(self, user_id: int, word_id: int) -> VocabItem:
        self._conn.execute("UPDATE words SET dupes = dupes + 1 WHERE id = ? AND user_id = ?", (word_id, user_id))
        self._conn.commit()
        item = self.get_word(user_id, word_id)
        assert item is not None
        return item

    def upgrade_card(self, user_id: int, word_id: int, max_stars: int = 5) -> VocabItem:
        item = self.get_word(user_id, word_id)
        if item is None:
            raise ValueError("Không tìm thấy thẻ này.")
        if not item.owned:
            raise ValueError("Bạn chưa sở hữu thẻ này.")
        if item.stars >= max_stars:
            raise ValueError("Thẻ đã đạt cấp sao tối đa.")
        cost = item.stars
        if item.dupes < cost:
            raise ValueError(f"Cần {cost} bản sao để nâng sao (đang có {item.dupes}).")
        self._conn.execute(
            "UPDATE words SET stars = stars + 1, dupes = dupes - ? WHERE id = ? AND user_id = ?",
            (cost, word_id, user_id),
        )
        self._conn.commit()
        fresh = self.get_word(user_id, word_id)
        assert fresh is not None
        return fresh

    def unowned_words(self, user_id: int, rarity: str = "") -> list[VocabItem]:
        if rarity:
            rows = self._conn.execute(
                "SELECT * FROM words WHERE owned = 0 AND user_id = ? AND rarity = ?", (user_id, rarity)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM words WHERE owned = 0 AND user_id = ?", (user_id,)).fetchall()
        return [self._item_from_row(row) for row in rows]

    def words_by_rarity(self, user_id: int, rarity: str) -> list[VocabItem]:
        rows = self._conn.execute("SELECT * FROM words WHERE rarity = ? AND user_id = ?", (rarity, user_id)).fetchall()
        return [self._item_from_row(row) for row in rows]

    def last_review_at(self, user_id: int, word_id: int) -> str | None:
        row = self._conn.execute(
            "SELECT max(reviewed_at) AS ts FROM reviews WHERE word_id = ? AND user_id = ?", (word_id, user_id)
        ).fetchone()
        return row["ts"] if row and row["ts"] else None

    # ---------------------------------------------------------------- review

    def review_word(self, user_id: int, word_id: int, rating: int) -> VocabItem:
        item = self.get_word(user_id, word_id)
        if item is None:
            raise ValueError(f"Không tìm thấy word_id={word_id}.")
        result = schedule_review(
            rating,
            ease=item.ease,
            repetitions=item.repetitions,
            lapses=item.lapses,
            stability=item.stability,
        )
        reviewed_at = format_dt(utc_now())
        self._conn.execute(
            '''
            UPDATE words SET ease = ?, interval_days = ?, repetitions = ?, lapses = ?,
                             stability = ?, due_at = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            ''',
            (
                result.ease, result.interval_days, result.repetitions, result.lapses,
                result.stability, format_dt(result.due_at), reviewed_at, word_id, user_id,
            ),
        )
        self._conn.execute(
            "INSERT INTO reviews (user_id, word_id, rating, reviewed_at) VALUES (?, ?, ?, ?)",
            (user_id, word_id, rating, reviewed_at),
        )
        self._conn.commit()
        updated = self.get_word(user_id, word_id)
        assert updated is not None
        return updated

    # ------------------------------------------------------------------ quiz

    def build_quiz_question(self, user_id: int) -> dict[str, Any]:
        candidates = [w for w in self._quiz_candidates(user_id, 100) if w.meaning.strip()]
        if len(candidates) < 4:
            raise ValueError("Cần ít nhất 4 từ có nghĩa để tạo quiz.")
        mode = choice(["term_to_meaning", "meaning_to_term"])
        target = choice(candidates[: min(len(candidates), 15)])
        if mode == "meaning_to_term":
            prompt = target.meaning
            correct = target.term
            pool = [w.term for w in candidates if w.id != target.id and w.term]
        else:
            prompt = target.term
            correct = target.meaning
            pool = [w.meaning for w in candidates if w.id != target.id and w.meaning]
        distractors: list[str] = []
        for value in pool:
            if value != correct and value not in distractors:
                distractors.append(value)
            if len(distractors) >= 3:
                break
        options = [correct] + distractors
        shuffle(options)
        return {
            "word_id": target.id,
            "mode": mode,
            "prompt": prompt,
            "options": options,
            "correct": correct,
            "example": target.example,
            "ipa": target.ipa,
        }

    def _quiz_candidates(self, user_id: int, limit: int) -> list[VocabItem]:
        due = self.due_words(user_id, limit)
        if len(due) >= min(limit, 8):
            return due
        seen = {w.id for w in due}
        extra = [w for w in self.list_words(user_id, limit=limit) if w.id not in seen]
        return due + extra

    def log_quiz_answer(
        self, user_id: int, *, word_id: int, prompt: str, selected: str, correct: str, is_correct: bool
    ) -> None:
        self._conn.execute(
            '''
            INSERT INTO quiz_logs (user_id, word_id, prompt, selected_answer, correct_answer, is_correct, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (user_id, word_id, prompt, selected, correct, int(is_correct), format_dt(utc_now())),
        )
        self._conn.commit()

    # ---------------------------------------------------------------- topics
    # Note: topics are global
    def upsert_topics(self, topics: list[dict[str, Any]]) -> int:
        now = format_dt(utc_now())
        count = 0
        for t in topics:
            name = str(t.get("name", "")).strip()
            if not name:
                continue
            self._conn.execute(
                '''
                INSERT INTO topics (name, name_vi, description_vi, sample_words, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    name_vi = excluded.name_vi,
                    description_vi = excluded.description_vi,
                    sample_words = excluded.sample_words
                ''',
                (
                    name,
                    str(t.get("name_vi", "")).strip(),
                    str(t.get("description_vi", "")).strip(),
                    json.dumps(t.get("sample_words", []), ensure_ascii=False),
                    now,
                ),
            )
            count += 1
        self._conn.commit()
        return count

    def list_topics(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM topics ORDER BY created_at DESC").fetchall()
        result = []
        for row in rows:
            # Word count per topic might be tricky for multi-user. We'll just skip word_count or count total across users.
            word_count = self._conn.execute(
                "SELECT count(*) FROM words WHERE topic = ?", (row["name"],)
            ).fetchone()[0]
            result.append(
                {
                    "id": row["id"],
                    "name": row["name"],
                    "name_vi": row["name_vi"],
                    "description_vi": row["description_vi"],
                    "sample_words": _load_json_list(row["sample_words"]),
                    "word_count": word_count,
                }
            )
        return result

    # -------------------------------------------------------------- writings

    def add_writing(
        self,
        user_id: int,
        *,
        kind: str,
        title: str,
        prompt: str,
        content: str,
        overall_band: float | None,
        feedback: dict[str, Any],
    ) -> Writing:
        cur = self._conn.execute(
            '''
            INSERT INTO writings (user_id, kind, title, prompt, content, word_count, overall_band, feedback, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                user_id, kind, title, prompt, content, len(content.split()), overall_band,
                json.dumps(feedback, ensure_ascii=False), format_dt(utc_now()),
            ),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM writings WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._writing_from_row(row)

    def list_writings(self, user_id: int, limit: int = 50) -> list[Writing]:
        rows = self._conn.execute(
            "SELECT * FROM writings WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit,)
        ).fetchall()
        return [self._writing_from_row(row) for row in rows]

    def recent_prompts(self, user_id: int, limit: int = 10) -> list[str]:
        rows = self._conn.execute(
            "SELECT prompt FROM writings WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit,)
        ).fetchall()
        return [row["prompt"] for row in rows]

    # -------------------------------------------------------------- patterns
    # Note: patterns are global
    def add_patterns(self, theme: str, patterns: list[dict[str, Any]]) -> int:
        now = format_dt(utc_now())
        count = 0
        for p in patterns:
            pattern = str(p.get("pattern", "")).strip()
            if not pattern:
                continue
            self._conn.execute(
                '''
                INSERT INTO patterns (theme, pattern, use_vi, examples, band, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(pattern) DO UPDATE SET
                    theme = excluded.theme,
                    use_vi = excluded.use_vi,
                    examples = excluded.examples,
                    band = excluded.band
                ''',
                (
                    theme,
                    pattern,
                    str(p.get("use_vi", "")).strip(),
                    json.dumps(p.get("examples", []), ensure_ascii=False),
                    str(p.get("band", "")).strip(),
                    now,
                ),
            )
            count += 1
        self._conn.commit()
        return count

    def list_patterns(self, theme: str = "") -> list[dict[str, Any]]:
        if theme:
            rows = self._conn.execute(
                "SELECT * FROM patterns WHERE theme = ? ORDER BY created_at DESC", (theme,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM patterns ORDER BY created_at DESC").fetchall()
        return [
            {
                "id": row["id"],
                "theme": row["theme"],
                "pattern": row["pattern"],
                "use_vi": row["use_vi"],
                "examples": _load_json_list(row["examples"]),
                "band": row["band"],
            }
            for row in rows
        ]

    def pattern_themes(self) -> list[str]:
        rows = self._conn.execute("SELECT DISTINCT theme FROM patterns ORDER BY theme").fetchall()
        return [row["theme"] for row in rows]

    def all_pattern_texts(self) -> list[str]:
        rows = self._conn.execute("SELECT pattern FROM patterns").fetchall()
        return [row["pattern"] for row in rows]

    # ------------------------------------------------------ challenges/packs

    def claims_for_date(self, user_id: int, date_str: str) -> set[str]:
        rows = self._conn.execute(
            "SELECT code FROM challenge_claims WHERE user_id = ? AND date = ?", (user_id, date_str,)
        ).fetchall()
        return {row["code"] for row in rows}

    def claim_challenge(self, user_id: int, date_str: str, code: str, tier: str) -> bool:
        try:
            self._conn.execute(
                "INSERT INTO challenge_claims (user_id, date, code, tier, claimed_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, date_str, code, tier, format_dt(utc_now())),
            )
        except sqlite3.IntegrityError:
            return False
        self._conn.commit()
        return True

    def add_pack(self, user_id: int, tier: str, source: str) -> int:
        cur = self._conn.execute(
            "INSERT INTO packs (user_id, tier, source, created_at) VALUES (?, ?, ?, ?)",
            (user_id, tier, source, format_dt(utc_now())),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    def unopened_packs(self, user_id: int) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM packs WHERE user_id = ? AND opened_at IS NULL ORDER BY created_at ASC", (user_id,)
        ).fetchall()
        return [
            {"id": row["id"], "tier": row["tier"], "source": row["source"], "created_at": row["created_at"]}
            for row in rows
        ]

    def get_unopened_pack(self, user_id: int, pack_id: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM packs WHERE id = ? AND user_id = ? AND opened_at IS NULL", (pack_id, user_id)
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "tier": row["tier"], "source": row["source"]}

    def mark_pack_opened(self, user_id: int, pack_id: int, word_id: int) -> None:
        self._conn.execute(
            "UPDATE packs SET opened_at = ?, word_id = ? WHERE id = ? AND user_id = ?",
            (format_dt(utc_now()), word_id, pack_id, user_id),
        )
        self._conn.commit()

    # ------------------------------------------------------------------ meta

    def get_meta(self, user_id: int, key: str, default: str = "") -> str:
        row = self._conn.execute("SELECT value FROM meta WHERE key = ? AND user_id = ?", (key, user_id)).fetchone()
        return row["value"] if row else default

    def set_meta(self, user_id: int, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO meta (user_id, key, value) VALUES (?, ?, ?) ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value",
            (user_id, key, value),
        )
        self._conn.commit()

    # ----------------------------------------------------------------- stats

    def count_between(self, user_id: int, table: str, column: str, start: str, end: str, extra: str = "") -> int:
        assert table in {"reviews", "quiz_logs", "words", "writings"}
        column_map = {"reviews": "reviewed_at", "quiz_logs": "created_at", "words": column, "writings": "created_at"}
        col = column_map.get(table, column)
        sql = f"SELECT count(*) FROM {table} WHERE user_id = ? AND {col} >= ? AND {col} < ?"
        if extra:
            sql += f" AND {extra}"
        return self._conn.execute(sql, (user_id, start, end)).fetchone()[0]

    def today_progress(self, user_id: int) -> dict[str, int]:
        start, end, _ = local_day_bounds()
        return {
            "reviews": self.count_between(user_id, "reviews", "reviewed_at", start, end),
            "quiz_correct": self.count_between(user_id, "quiz_logs", "created_at", start, end, "is_correct = 1"),
            "quiz_total": self.count_between(user_id, "quiz_logs", "created_at", start, end),
            "new_words": self.count_between(user_id, "words", "created_at", start, end),
            "writings": self.count_between(user_id, "writings", "created_at", start, end, "overall_band IS NOT NULL"),
        }

    def activity_dates(self, user_id: int) -> set[str]:
        dates: set[str] = set()
        for sql in (
            "SELECT reviewed_at AS ts FROM reviews WHERE user_id = ?",
            "SELECT created_at AS ts FROM quiz_logs WHERE user_id = ?",
            "SELECT created_at AS ts FROM writings WHERE user_id = ?",
        ):
            for row in self._conn.execute(sql, (user_id,)):
                parsed = parse_dt(row["ts"])
                if parsed:
                    dates.add(parsed.astimezone().strftime("%Y-%m-%d"))
        return dates

    def streak(self, user_id: int) -> int:
        dates = self.activity_dates(user_id)
        if not dates:
            return 0
        streak = 0
        offset = 0
        _, _, today = local_day_bounds()
        if today not in dates:
            offset = -1
        while True:
            _, _, day = local_day_bounds(offset - streak)
            if day in dates:
                streak += 1
            else:
                break
        return streak

    def xp(self, user_id: int) -> int:
        reviews = self._conn.execute("SELECT count(*) FROM reviews WHERE user_id = ?", (user_id,)).fetchone()[0]
        quiz_ok = self._conn.execute("SELECT count(*) FROM quiz_logs WHERE is_correct = 1 AND user_id = ?", (user_id,)).fetchone()[0]
        words = self._conn.execute("SELECT count(*) FROM words WHERE user_id = ?", (user_id,)).fetchone()[0]
        writings = self._conn.execute("SELECT count(*) FROM writings WHERE overall_band IS NOT NULL AND user_id = ?", (user_id,)).fetchone()[0]
        owned = self._conn.execute("SELECT count(*) FROM words WHERE owned = 1 AND user_id = ?", (user_id,)).fetchone()[0]
        extra_stars = self._conn.execute(
            "SELECT coalesce(sum(stars - 1), 0) FROM words WHERE owned = 1 AND user_id = ?", (user_id,)
        ).fetchone()[0]
        return reviews * 2 + quiz_ok * 3 + words * 5 + writings * 25 + owned * 10 + extra_stars * 20

    def stats(self, user_id: int) -> dict[str, Any]:
        total = self._conn.execute("SELECT count(*) FROM words WHERE user_id = ?", (user_id,)).fetchone()[0]
        owned = self._conn.execute("SELECT count(*) FROM words WHERE owned = 1 AND user_id = ?", (user_id,)).fetchone()[0]
        total_stars = self._conn.execute(
            "SELECT coalesce(sum(stars), 0) FROM words WHERE owned = 1 AND user_id = ?", (user_id,)
        ).fetchone()[0]
        mastered = self._conn.execute("SELECT count(*) FROM words WHERE stability >= 21 AND user_id = ?", (user_id,)).fetchone()[0]
        by_rarity = {
            row["rarity"]: {"total": row["total"], "owned": row["owned_count"]}
            for row in self._conn.execute(
                "SELECT rarity, count(*) AS total, sum(owned) AS owned_count FROM words WHERE user_id = ? GROUP BY rarity", (user_id,)
            )
        }
        reviews = self._conn.execute("SELECT count(*) FROM reviews WHERE user_id = ?", (user_id,)).fetchone()[0]
        writings = self._conn.execute("SELECT count(*) FROM writings WHERE user_id = ?", (user_id,)).fetchone()[0]
        avg_band = self._conn.execute(
            "SELECT avg(overall_band) FROM writings WHERE overall_band IS NOT NULL AND user_id = ? "
            "AND id IN (SELECT id FROM writings WHERE user_id = ? ORDER BY created_at DESC LIMIT 5)", (user_id, user_id)
        ).fetchone()[0]
        return {
            "total_words": total,
            "owned_cards": owned,
            "total_stars": total_stars,
            "mastered": mastered,
            "due": self.due_count(user_id),
            "by_rarity": by_rarity,
            "reviews": reviews,
            "writings": writings,
            "recent_avg_band": round(avg_band, 1) if avg_band else None,
            "streak": self.streak(user_id),
            "xp": self.xp(user_id),
        }

    # ----------------------------------------------------------------- arena

    def ensure_arena_rating(self, user_id: int) -> dict[str, Any]:
        row = self._conn.execute("SELECT * FROM arena_ratings WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return dict(row)
        self._conn.execute(
            "INSERT INTO arena_ratings (user_id, rating, wins, losses) VALUES (?, 1000, 0, 0)", (user_id,)
        )
        self._conn.commit()
        return {"user_id": user_id, "rating": 1000, "wins": 0, "losses": 0}

    def set_arena_defense(self, user_id: int, word_ids: list[int]) -> dict[str, Any]:
        now = format_dt(utc_now())
        self._conn.execute(
            '''
            INSERT INTO arena_defenses (user_id, word_ids, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET word_ids = excluded.word_ids, updated_at = excluded.updated_at
            ''',
            (user_id, json.dumps(word_ids, ensure_ascii=False), now),
        )
        self._conn.commit()
        self.ensure_arena_rating(user_id)
        return {"user_id": user_id, "word_ids": word_ids, "updated_at": now}

    def get_arena_defense(self, user_id: int) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT * FROM arena_defenses WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return None
        return {"user_id": user_id, "word_ids": _load_json_ints(row["word_ids"]), "updated_at": row["updated_at"]}

    def list_arena_opponents(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            '''
            SELECT u.id AS user_id, u.username AS username, d.word_ids AS word_ids,
                   coalesce(r.rating, 1000) AS rating, coalesce(r.wins, 0) AS wins, coalesce(r.losses, 0) AS losses
            FROM arena_defenses d
            JOIN users u ON u.id = d.user_id
            LEFT JOIN arena_ratings r ON r.user_id = d.user_id
            WHERE d.user_id != ? AND d.word_ids != '[]'
            ORDER BY rating DESC
            LIMIT ?
            ''',
            (user_id, limit),
        ).fetchall()
        opponents = []
        for row in rows:
            word_ids = _load_json_ints(row["word_ids"])
            cards = [self._item_from_row(r) for r in self._conn.execute(
                f"SELECT * FROM words WHERE id IN ({','.join('?' * len(word_ids))})", word_ids
            ).fetchall()] if word_ids else []
            opponents.append({
                "user_id": row["user_id"],
                "username": row["username"],
                "rating": row["rating"],
                "wins": row["wins"],
                "losses": row["losses"],
                "card_count": len(cards),
                "rarities": [c.rarity for c in cards],
            })
        return opponents

    def words_by_ids(self, user_id: int, word_ids: list[int]) -> list[VocabItem]:
        if not word_ids:
            return []
        rows = self._conn.execute(
            f"SELECT * FROM words WHERE user_id = ? AND id IN ({','.join('?' * len(word_ids))})",
            (user_id, *word_ids),
        ).fetchall()
        by_id = {row["id"]: self._item_from_row(row) for row in rows}
        return [by_id[wid] for wid in word_ids if wid in by_id]

    def record_arena_battle(
        self,
        *,
        attacker_id: int,
        defender_id: int,
        attacker_power: int,
        defender_power: int,
        quiz_correct: int,
        quiz_total: int,
        result: str,
        attacker_delta: int,
        defender_delta: int,
        pack_tier: str,
    ) -> dict[str, Any]:
        now = format_dt(utc_now())
        cur = self._conn.execute(
            '''
            INSERT INTO arena_battles (attacker_id, defender_id, attacker_power, defender_power, quiz_correct,
                                       quiz_total, result, attacker_delta, defender_delta, pack_tier, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (attacker_id, defender_id, attacker_power, defender_power, quiz_correct, quiz_total,
             result, attacker_delta, defender_delta, pack_tier, now),
        )
        self._conn.execute(
            "UPDATE arena_ratings SET rating = max(0, rating + ?), wins = wins + ?, losses = losses + ? WHERE user_id = ?",
            (attacker_delta, 1 if result == "win" else 0, 0 if result == "win" else 1, attacker_id),
        )
        self._conn.execute(
            "UPDATE arena_ratings SET rating = max(0, rating + ?), wins = wins + ?, losses = losses + ? WHERE user_id = ?",
            (defender_delta, 0 if result == "win" else 1, 1 if result == "win" else 0, defender_id),
        )
        self._conn.commit()
        return {
            "id": cur.lastrowid,
            "attacker_id": attacker_id,
            "defender_id": defender_id,
            "attacker_power": attacker_power,
            "defender_power": defender_power,
            "quiz_correct": quiz_correct,
            "quiz_total": quiz_total,
            "result": result,
            "attacker_delta": attacker_delta,
            "defender_delta": defender_delta,
            "pack_tier": pack_tier,
            "created_at": now,
        }

    def arena_history(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            '''
            SELECT b.*, ua.username AS attacker_name, ud.username AS defender_name
            FROM arena_battles b
            JOIN users ua ON ua.id = b.attacker_id
            JOIN users ud ON ud.id = b.defender_id
            WHERE b.attacker_id = ? OR b.defender_id = ?
            ORDER BY b.created_at DESC, b.id DESC
            LIMIT ?
            ''',
            (user_id, user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def arena_leaderboard(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            '''
            SELECT u.username AS username, r.user_id AS user_id, r.rating AS rating, r.wins AS wins, r.losses AS losses
            FROM arena_ratings r
            JOIN users u ON u.id = r.user_id
            ORDER BY r.rating DESC
            LIMIT ?
            ''',
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def daily_activity(self, user_id: int, days: int = 14) -> list[dict[str, Any]]:
        result = []
        for offset in range(-(days - 1), 1):
            start, end, date_str = local_day_bounds(offset)
            result.append(
                {
                    "date": date_str,
                    "reviews": self.count_between(user_id, "reviews", "reviewed_at", start, end),
                    "new_words": self.count_between(user_id, "words", "created_at", start, end),
                    "writings": self.count_between(user_id, "writings", "created_at", start, end),
                }
            )
        return result

    # --------------------------------------------------------------- private

    @staticmethod
    def _item_from_row(row: sqlite3.Row) -> VocabItem:
        return VocabItem(
            id=row["id"],
            user_id=row["user_id"],
            term=row["term"],
            meaning=row["meaning"],
            example=row["example"],
            example_vi=row["example_vi"],
            ipa=row["ipa"],
            pos=row["pos"],
            collocations=_load_json_list(row["collocations"]),
            notes=row["notes"],
            tags=row["tags"],
            topic=row["topic"],
            band=row["band"],
            rarity=row["rarity"] if row["rarity"] in RARITIES else "C",
            is_gem=bool(row["is_gem"]),
            is_toeic=bool(row["is_toeic"]),
            toeic_part=row["toeic_part"],
            owned=bool(row["owned"]),
            owned_at=row["owned_at"],
            stars=int(row["stars"]),
            dupes=int(row["dupes"]),
            source=row["source"],
            ease=float(row["ease"]),
            interval_days=float(row["interval_days"]),
            repetitions=int(row["repetitions"]),
            lapses=int(row["lapses"]),
            stability=float(row["stability"]),
            due_at=row["due_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _writing_from_row(row: sqlite3.Row) -> Writing:
        try:
            feedback = json.loads(row["feedback"])
        except json.JSONDecodeError:
            feedback = {}
        return Writing(
            id=row["id"],
            user_id=row["user_id"],
            kind=row["kind"],
            title=row["title"],
            prompt=row["prompt"],
            content=row["content"],
            word_count=row["word_count"],
            overall_band=row["overall_band"],
            feedback=feedback if isinstance(feedback, dict) else {},
            created_at=row["created_at"],
        )


def _load_json_list(raw: str) -> list[str]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return [str(item) for item in data]
    return []


def _load_json_ints(raw: str) -> list[int]:
    try:
        data = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    if isinstance(data, list):
        return [int(item) for item in data]
    return []
