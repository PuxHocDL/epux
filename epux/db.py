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
    """(start_utc_iso, end_utc_iso, local_date_str) cho một ngày theo giờ máy."""
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
        self._conn.execute("PRAGMA journal_mode = WAL")
        self.migrate()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------- migration

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
                interval_days REAL NOT NULL DEFAULT 0,
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

            CREATE TABLE IF NOT EXISTS quiz_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                tier TEXT NOT NULL,
                claimed_at TEXT NOT NULL,
                UNIQUE(date, code)
            );

            CREATE TABLE IF NOT EXISTS packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tier TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                opened_at TEXT,
                word_id INTEGER REFERENCES words(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            );
            """
        )
        new_columns = {
            "ipa": "TEXT NOT NULL DEFAULT ''",
            "pos": "TEXT NOT NULL DEFAULT ''",
            "example_vi": "TEXT NOT NULL DEFAULT ''",
            "collocations": "TEXT NOT NULL DEFAULT '[]'",
            "topic": "TEXT NOT NULL DEFAULT ''",
            "band": "TEXT NOT NULL DEFAULT ''",
            "rarity": "TEXT NOT NULL DEFAULT 'C'",
            "is_gem": "INTEGER NOT NULL DEFAULT 0",
            "owned": "INTEGER NOT NULL DEFAULT 0",
            "owned_at": "TEXT NOT NULL DEFAULT ''",
            "stars": "INTEGER NOT NULL DEFAULT 0",
            "dupes": "INTEGER NOT NULL DEFAULT 0",
            "source": "TEXT NOT NULL DEFAULT 'manual'",
            "stability": "REAL NOT NULL DEFAULT 0",
        }
        existing = {row["name"] for row in self._conn.execute("PRAGMA table_info(words)")}
        for name, decl in new_columns.items():
            if name not in existing:
                self._conn.execute(f"ALTER TABLE words ADD COLUMN {name} {decl}")
        # Thẻ từ bản cũ: suy ra stability từ interval_days.
        self._conn.execute(
            "UPDATE words SET stability = max(interval_days, 0.001) WHERE stability <= 0"
        )
        # Thẻ đã sở hữu trước khi có hệ sao: về 1 sao.
        self._conn.execute("UPDATE words SET stars = 1 WHERE owned = 1 AND stars < 1")
        self._conn.commit()

    # ----------------------------------------------------------------- words

    def add_word(
        self,
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
        source: str = "manual",
    ) -> VocabItem:
        now = format_dt(utc_now())
        term = term.strip()
        if not term:
            raise ValueError("Từ vựng không được để trống.")
        if rarity not in RARITIES:
            rarity = "C"
        self._conn.execute(
            """
            INSERT INTO words (term, meaning, example, example_vi, ipa, pos, collocations, notes,
                               tags, topic, band, rarity, is_gem, source, due_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(term) DO UPDATE SET
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
                updated_at = excluded.updated_at
            """,
            (
                term, meaning.strip(), example.strip(), example_vi.strip(), ipa.strip(), pos.strip(),
                json.dumps(collocations or [], ensure_ascii=False), notes.strip(), tags.strip(),
                topic.strip(), band.strip(), rarity, int(is_gem), source, now, now, now,
            ),
        )
        self._conn.commit()
        item = self.get_word_by_term(term)
        if item is None:
            raise RuntimeError("Không thể lưu từ vựng.")
        return item

    def update_word(self, word_id: int, data: dict[str, Any]) -> VocabItem:
        allowed = {
            "term", "meaning", "example", "example_vi", "ipa", "pos", "notes",
            "tags", "topic", "band", "rarity",
        }
        sets: list[str] = []
        values: list[Any] = []
        for key, value in data.items():
            if key not in allowed:
                continue
            sets.append(f"{key} = ?")
            values.append(str(value).strip())
        if "collocations" in data and isinstance(data["collocations"], list):
            sets.append("collocations = ?")
            values.append(json.dumps(data["collocations"], ensure_ascii=False))
        if not sets:
            raise ValueError("Không có trường nào để cập nhật.")
        sets.append("updated_at = ?")
        values.append(format_dt(utc_now()))
        values.append(word_id)
        self._conn.execute(f"UPDATE words SET {', '.join(sets)} WHERE id = ?", values)
        self._conn.commit()
        item = self.get_word(word_id)
        if item is None:
            raise ValueError(f"Không tìm thấy word_id={word_id}.")
        return item

    def delete_word(self, word_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def get_word(self, word_id: int) -> VocabItem | None:
        row = self._conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        return self._item_from_row(row) if row else None

    def get_word_by_term(self, term: str) -> VocabItem | None:
        row = self._conn.execute(
            "SELECT * FROM words WHERE lower(term) = lower(?)", (term.strip(),)
        ).fetchone()
        return self._item_from_row(row) if row else None

    def list_words(
        self,
        *,
        query: str = "",
        topic: str = "",
        rarity: str = "",
        owned: bool | None = None,
        limit: int = 500,
    ) -> list[VocabItem]:
        clauses: list[str] = []
        params: list[Any] = []
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
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._conn.execute(
            f"SELECT * FROM words {where} ORDER BY created_at DESC, term ASC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def all_terms(self) -> list[str]:
        rows = self._conn.execute("SELECT term FROM words").fetchall()
        return [row["term"] for row in rows]

    def due_words(self, limit: int = 50) -> list[VocabItem]:
        now = format_dt(utc_now())
        rows = self._conn.execute(
            "SELECT * FROM words WHERE due_at <= ? ORDER BY due_at ASC LIMIT ?",
            (now, limit),
        ).fetchall()
        return [self._item_from_row(row) for row in rows]

    def due_count(self) -> int:
        now = format_dt(utc_now())
        return self._conn.execute(
            "SELECT count(*) FROM words WHERE due_at <= ?", (now,)
        ).fetchone()[0]

    def topics_in_words(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT topic FROM words WHERE topic != '' ORDER BY topic"
        ).fetchall()
        return [row["topic"] for row in rows]

    def set_owned(self, word_id: int) -> None:
        self._conn.execute(
            "UPDATE words SET owned = 1, owned_at = ?, stars = max(stars, 1) WHERE id = ?",
            (format_dt(utc_now()), word_id),
        )
        self._conn.commit()

    def add_dupe(self, word_id: int) -> VocabItem:
        self._conn.execute("UPDATE words SET dupes = dupes + 1 WHERE id = ?", (word_id,))
        self._conn.commit()
        item = self.get_word(word_id)
        assert item is not None
        return item

    def upgrade_card(self, word_id: int, max_stars: int = 5) -> VocabItem:
        """Gộp bản sao để nâng sao: lên sao n+1 tốn n bản sao."""
        item = self.get_word(word_id)
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
            "UPDATE words SET stars = stars + 1, dupes = dupes - ? WHERE id = ?",
            (cost, word_id),
        )
        self._conn.commit()
        fresh = self.get_word(word_id)
        assert fresh is not None
        return fresh

    def unowned_words(self, rarity: str = "") -> list[VocabItem]:
        if rarity:
            rows = self._conn.execute(
                "SELECT * FROM words WHERE owned = 0 AND rarity = ?", (rarity,)
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT * FROM words WHERE owned = 0").fetchall()
        return [self._item_from_row(row) for row in rows]

    def words_by_rarity(self, rarity: str) -> list[VocabItem]:
        rows = self._conn.execute("SELECT * FROM words WHERE rarity = ?", (rarity,)).fetchall()
        return [self._item_from_row(row) for row in rows]

    def last_review_at(self, word_id: int) -> str | None:
        row = self._conn.execute(
            "SELECT max(reviewed_at) AS ts FROM reviews WHERE word_id = ?", (word_id,)
        ).fetchone()
        return row["ts"] if row and row["ts"] else None

    # ---------------------------------------------------------------- review

    def review_word(self, word_id: int, rating: int) -> VocabItem:
        item = self.get_word(word_id)
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
            """
            UPDATE words SET ease = ?, interval_days = ?, repetitions = ?, lapses = ?,
                             stability = ?, due_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                result.ease, result.interval_days, result.repetitions, result.lapses,
                result.stability, format_dt(result.due_at), reviewed_at, word_id,
            ),
        )
        self._conn.execute(
            "INSERT INTO reviews (word_id, rating, reviewed_at) VALUES (?, ?, ?)",
            (word_id, rating, reviewed_at),
        )
        self._conn.commit()
        updated = self.get_word(word_id)
        assert updated is not None
        return updated

    # ------------------------------------------------------------------ quiz

    def build_quiz_question(self) -> dict[str, Any]:
        candidates = [w for w in self._quiz_candidates(100) if w.meaning.strip()]
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

    def _quiz_candidates(self, limit: int) -> list[VocabItem]:
        due = self.due_words(limit)
        if len(due) >= min(limit, 8):
            return due
        seen = {w.id for w in due}
        extra = [w for w in self.list_words(limit=limit) if w.id not in seen]
        return due + extra

    def log_quiz_answer(
        self, *, word_id: int, prompt: str, selected: str, correct: str, is_correct: bool
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO quiz_logs (word_id, prompt, selected_answer, correct_answer, is_correct, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (word_id, prompt, selected, correct, int(is_correct), format_dt(utc_now())),
        )
        self._conn.commit()

    # ---------------------------------------------------------------- topics

    def upsert_topics(self, topics: list[dict[str, Any]]) -> int:
        now = format_dt(utc_now())
        count = 0
        for t in topics:
            name = str(t.get("name", "")).strip()
            if not name:
                continue
            self._conn.execute(
                """
                INSERT INTO topics (name, name_vi, description_vi, sample_words, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    name_vi = excluded.name_vi,
                    description_vi = excluded.description_vi,
                    sample_words = excluded.sample_words
                """,
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
        *,
        kind: str,
        title: str,
        prompt: str,
        content: str,
        overall_band: float | None,
        feedback: dict[str, Any],
    ) -> Writing:
        cur = self._conn.execute(
            """
            INSERT INTO writings (kind, title, prompt, content, word_count, overall_band, feedback, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kind, title, prompt, content, len(content.split()), overall_band,
                json.dumps(feedback, ensure_ascii=False), format_dt(utc_now()),
            ),
        )
        self._conn.commit()
        row = self._conn.execute("SELECT * FROM writings WHERE id = ?", (cur.lastrowid,)).fetchone()
        return self._writing_from_row(row)

    def list_writings(self, limit: int = 50) -> list[Writing]:
        rows = self._conn.execute(
            "SELECT * FROM writings ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._writing_from_row(row) for row in rows]

    def recent_prompts(self, limit: int = 10) -> list[str]:
        rows = self._conn.execute(
            "SELECT prompt FROM writings ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [row["prompt"] for row in rows]

    # -------------------------------------------------------------- patterns

    def add_patterns(self, theme: str, patterns: list[dict[str, Any]]) -> int:
        now = format_dt(utc_now())
        count = 0
        for p in patterns:
            pattern = str(p.get("pattern", "")).strip()
            if not pattern:
                continue
            self._conn.execute(
                """
                INSERT INTO patterns (theme, pattern, use_vi, examples, band, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(pattern) DO UPDATE SET
                    theme = excluded.theme,
                    use_vi = excluded.use_vi,
                    examples = excluded.examples,
                    band = excluded.band
                """,
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

    def claims_for_date(self, date_str: str) -> set[str]:
        rows = self._conn.execute(
            "SELECT code FROM challenge_claims WHERE date = ?", (date_str,)
        ).fetchall()
        return {row["code"] for row in rows}

    def claim_challenge(self, date_str: str, code: str, tier: str) -> bool:
        try:
            self._conn.execute(
                "INSERT INTO challenge_claims (date, code, tier, claimed_at) VALUES (?, ?, ?, ?)",
                (date_str, code, tier, format_dt(utc_now())),
            )
        except sqlite3.IntegrityError:
            return False
        self._conn.commit()
        return True

    def add_pack(self, tier: str, source: str) -> int:
        cur = self._conn.execute(
            "INSERT INTO packs (tier, source, created_at) VALUES (?, ?, ?)",
            (tier, source, format_dt(utc_now())),
        )
        self._conn.commit()
        return int(cur.lastrowid or 0)

    def unopened_packs(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM packs WHERE opened_at IS NULL ORDER BY created_at ASC"
        ).fetchall()
        return [
            {"id": row["id"], "tier": row["tier"], "source": row["source"], "created_at": row["created_at"]}
            for row in rows
        ]

    def get_unopened_pack(self, pack_id: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM packs WHERE id = ? AND opened_at IS NULL", (pack_id,)
        ).fetchone()
        if row is None:
            return None
        return {"id": row["id"], "tier": row["tier"], "source": row["source"]}

    def mark_pack_opened(self, pack_id: int, word_id: int) -> None:
        self._conn.execute(
            "UPDATE packs SET opened_at = ?, word_id = ? WHERE id = ?",
            (format_dt(utc_now()), word_id, pack_id),
        )
        self._conn.commit()

    # ------------------------------------------------------------------ meta

    def get_meta(self, key: str, default: str = "") -> str:
        row = self._conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def set_meta(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self._conn.commit()

    # ----------------------------------------------------------------- stats

    def count_between(self, table: str, column: str, start: str, end: str, extra: str = "") -> int:
        assert table in {"reviews", "quiz_logs", "words", "writings"}
        column_map = {"reviews": "reviewed_at", "quiz_logs": "created_at", "words": column, "writings": "created_at"}
        col = column_map.get(table, column)
        sql = f"SELECT count(*) FROM {table} WHERE {col} >= ? AND {col} < ?"
        if extra:
            sql += f" AND {extra}"
        return self._conn.execute(sql, (start, end)).fetchone()[0]

    def today_progress(self) -> dict[str, int]:
        start, end, _ = local_day_bounds()
        return {
            "reviews": self.count_between("reviews", "reviewed_at", start, end),
            "quiz_correct": self.count_between("quiz_logs", "created_at", start, end, "is_correct = 1"),
            "quiz_total": self.count_between("quiz_logs", "created_at", start, end),
            "new_words": self.count_between("words", "created_at", start, end),
            "writings": self.count_between("writings", "created_at", start, end, "overall_band IS NOT NULL"),
        }

    def activity_dates(self) -> set[str]:
        """Các ngày (giờ local) có hoạt động học — dùng tính streak."""
        dates: set[str] = set()
        for sql in (
            "SELECT reviewed_at AS ts FROM reviews",
            "SELECT created_at AS ts FROM quiz_logs",
            "SELECT created_at AS ts FROM writings",
        ):
            for row in self._conn.execute(sql):
                parsed = parse_dt(row["ts"])
                if parsed:
                    dates.add(parsed.astimezone().strftime("%Y-%m-%d"))
        return dates

    def streak(self) -> int:
        dates = self.activity_dates()
        if not dates:
            return 0
        streak = 0
        offset = 0
        _, _, today = local_day_bounds()
        if today not in dates:
            offset = -1  # hôm nay chưa học thì tính từ hôm qua, streak chưa đứt
        while True:
            _, _, day = local_day_bounds(offset - streak)
            if day in dates:
                streak += 1
            else:
                break
        return streak

    def xp(self) -> int:
        reviews = self._conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
        quiz_ok = self._conn.execute("SELECT count(*) FROM quiz_logs WHERE is_correct = 1").fetchone()[0]
        words = self._conn.execute("SELECT count(*) FROM words").fetchone()[0]
        writings = self._conn.execute("SELECT count(*) FROM writings WHERE overall_band IS NOT NULL").fetchone()[0]
        owned = self._conn.execute("SELECT count(*) FROM words WHERE owned = 1").fetchone()[0]
        extra_stars = self._conn.execute(
            "SELECT coalesce(sum(stars - 1), 0) FROM words WHERE owned = 1"
        ).fetchone()[0]
        return reviews * 2 + quiz_ok * 3 + words * 5 + writings * 25 + owned * 10 + extra_stars * 20

    def stats(self) -> dict[str, Any]:
        total = self._conn.execute("SELECT count(*) FROM words").fetchone()[0]
        owned = self._conn.execute("SELECT count(*) FROM words WHERE owned = 1").fetchone()[0]
        total_stars = self._conn.execute(
            "SELECT coalesce(sum(stars), 0) FROM words WHERE owned = 1"
        ).fetchone()[0]
        mastered = self._conn.execute("SELECT count(*) FROM words WHERE stability >= 21").fetchone()[0]
        by_rarity = {
            row["rarity"]: {"total": row["total"], "owned": row["owned_count"]}
            for row in self._conn.execute(
                "SELECT rarity, count(*) AS total, sum(owned) AS owned_count FROM words GROUP BY rarity"
            )
        }
        reviews = self._conn.execute("SELECT count(*) FROM reviews").fetchone()[0]
        writings = self._conn.execute("SELECT count(*) FROM writings").fetchone()[0]
        avg_band = self._conn.execute(
            "SELECT avg(overall_band) FROM writings WHERE overall_band IS NOT NULL "
            "AND id IN (SELECT id FROM writings ORDER BY created_at DESC LIMIT 5)"
        ).fetchone()[0]
        return {
            "total_words": total,
            "owned_cards": owned,
            "total_stars": total_stars,
            "mastered": mastered,
            "due": self.due_count(),
            "by_rarity": by_rarity,
            "reviews": reviews,
            "writings": writings,
            "recent_avg_band": round(avg_band, 1) if avg_band else None,
            "streak": self.streak(),
            "xp": self.xp(),
        }

    def daily_activity(self, days: int = 14) -> list[dict[str, Any]]:
        result = []
        for offset in range(-(days - 1), 1):
            start, end, date_str = local_day_bounds(offset)
            result.append(
                {
                    "date": date_str,
                    "reviews": self.count_between("reviews", "reviewed_at", start, end),
                    "new_words": self.count_between("words", "created_at", start, end),
                    "writings": self.count_between("writings", "created_at", start, end),
                }
            )
        return result

    # --------------------------------------------------------------- private

    @staticmethod
    def _item_from_row(row: sqlite3.Row) -> VocabItem:
        return VocabItem(
            id=row["id"],
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
