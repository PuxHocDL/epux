from __future__ import annotations

import math
import random
from typing import Any

from .config import AppConfig
from .db import Database, VocabItem, local_day_bounds
from .llm import LLMClient, LLMError

RARITY_ORDER = ["D", "C", "B", "A", "S", "SS", "SSS"]

# Xác suất rơi rarity theo tier pack (%).
PACK_WEIGHTS: dict[str, dict[str, float]] = {
    "bronze": {"D": 38, "C": 30, "B": 18, "A": 9, "S": 4, "SS": 0.8, "SSS": 0.2},
    "silver": {"D": 18, "C": 26, "B": 26, "A": 16, "S": 9, "SS": 4, "SSS": 1},
    "gold": {"D": 6, "C": 12, "B": 24, "A": 26, "S": 18, "SS": 10, "SSS": 4},
}

PACK_NAMES_VI = {"bronze": "Pack Đồng", "silver": "Pack Bạc", "gold": "Pack Vàng"}

# Khi pack cần sinh từ mới đúng rarity đã roll.
BAND_FOR_RARITY = {
    "D": "A2 (common everyday word)",
    "C": "B1",
    "B": "B2",
    "A": "C1",
    "S": "C1-C2 (advanced, impressive in IELTS)",
    "SS": "C2 (rare, sophisticated)",
    "SSS": "C2 rare idiom or striking collocation that would wow an IELTS examiner",
}


def rarity_for_band(band: str, is_gem: bool) -> str:
    band = (band or "").upper().strip()
    base = {"A1": "D", "A2": "D", "B1": "C", "B2": "B", "C1": "A", "C2": "S"}.get(band, "C")
    if is_gem:
        idx = min(len(RARITY_ORDER) - 2, RARITY_ORDER.index(base) + 1)
        return RARITY_ORDER[idx]
    return base


def roll_rarity(tier: str) -> str:
    weights = PACK_WEIGHTS.get(tier, PACK_WEIGHTS["bronze"])
    rarities = list(weights.keys())
    return random.choices(rarities, weights=[weights[r] for r in rarities], k=1)[0]


def level_from_xp(xp: int) -> dict[str, int]:
    level = int(math.sqrt(max(0, xp) / 60)) + 1
    current_floor = 60 * (level - 1) ** 2
    next_need = 60 * level**2
    return {"level": level, "xp": xp, "current_floor": current_floor, "next_level_xp": next_need}


# -------------------------------------------------------------- challenges


def build_challenges(db: Database, config: AppConfig, user_id: int) -> list[dict[str, Any]]:
    progress = db.today_progress(user_id)
    _, _, today = local_day_bounds()
    claimed = db.claims_for_date(user_id, today)

    defs = [
        {
            "code": "review",
            "title": "Ôn tập trí nhớ",
            "desc": "Ôn 15 thẻ theo lịch lãng quên",
            "target": 15,
            "progress": progress["reviews"],
            "tier": "bronze",
        },
        {
            "code": "quiz",
            "title": "Quiz tốc độ",
            "desc": "Trả lời đúng 10 câu quiz",
            "target": 10,
            "progress": progress["quiz_correct"],
            "tier": "bronze",
        },
        {
            "code": "new_words",
            "title": "Mở rộng vốn từ",
            "desc": f"Thêm {config.daily_new_words} từ mới hôm nay",
            "target": config.daily_new_words,
            "progress": progress["new_words"],
            "tier": "silver",
        },
        {
            "code": "writing",
            "title": "Luyện bút",
            "desc": "Hoàn thành 1 bài viết được AI chấm",
            "target": 1,
            "progress": progress["writings"],
            "tier": "gold",
        },
    ]
    for item in defs:
        item["done"] = item["progress"] >= item["target"]
        item["claimed"] = item["code"] in claimed

    done_count = sum(1 for item in defs if item["done"])
    defs.append(
        {
            "code": "all",
            "title": "Hoàn hảo",
            "desc": "Hoàn thành cả 4 thử thách trong ngày",
            "target": 4,
            "progress": done_count,
            "tier": "gold",
            "done": done_count >= 4,
            "claimed": "all" in claimed,
        }
    )
    return defs


def claim_challenge(db: Database, config: AppConfig, user_id: int, code: str) -> dict[str, Any]:
    challenges = {c["code"]: c for c in build_challenges(db, config, user_id)}
    challenge = challenges.get(code)
    if challenge is None:
        raise ValueError("Thử thách không tồn tại.")
    if not challenge["done"]:
        raise ValueError("Chưa hoàn thành thử thách này.")
    if challenge["claimed"]:
        raise ValueError(f"Đã nhận thưởng rồi. (claimed=True, code={code})")
    _, _, today = local_day_bounds()
    try:
        res = db.claim_challenge(user_id, today, code, challenge["tier"])
    except Exception as e:
        raise ValueError(f"Lỗi Exception: {type(e)} {str(e)}")
    if not res:
        raise ValueError(f"Đã nhận thưởng rồi. (db.claim_challenge returned False)")
    pack_id = db.add_pack(user_id, challenge["tier"], source=f"challenge:{code}:{today}")
    return {"pack_id": pack_id, "tier": challenge["tier"], "tier_vi": PACK_NAMES_VI[challenge["tier"]]}


# ------------------------------------------------------------------- packs


MAX_STARS = 5


def open_pack(db: Database, llm: LLMClient, config: AppConfig, user_id: int, pack_id: int) -> dict[str, Any]:
    pack = db.get_unopened_pack(user_id, pack_id)
    if pack is None:
        raise ValueError("Pack không tồn tại hoặc đã mở.")
    rolled = roll_rarity(pack["tier"])
    kind = "new"

    pool = db.words_by_rarity(user_id, rolled)
    unowned = [w for w in pool if not w.owned]
    owned = [w for w in pool if w.owned]

    word: VocabItem | None = None
    if unowned and (not owned or random.random() < 0.75):
        word = random.choice(unowned)
    elif owned or llm.configured:
        forge_first = llm.configured and (not owned or random.random() < 0.6)
        if forge_first:
            word = _generate_for_rarity(db, llm, config, user_id, rolled)
            kind = "forged" if word is not None else "new"
        if word is None and owned:
            word = random.choice(owned)
            kind = "dupe"

    if word is None:
        fallback = db.unowned_words(user_id)
        if not fallback:
            raise ValueError("Không còn thẻ để mở và LLM chưa sẵn sàng. Hãy tạo thêm từ mới trước.")
        word = random.choice(fallback)
        rolled = word.rarity
        kind = "new"

    if kind == "dupe":
        fresh = db.add_dupe(user_id, word.id)
    else:
        db.set_owned(user_id, word.id)
        fresh = db.get_word(user_id, word.id)
        assert fresh is not None
    db.mark_pack_opened(user_id, pack_id, word.id)
    return {
        "rarity": rolled,
        "tier": pack["tier"],
        "kind": kind,
        "generated": kind == "forged",
        "duplicate": kind == "dupe",
        "card": fresh.to_dict(),
    }


# --------------------------------------------------------------------- arena

MAX_ARENA_CARDS = 5
ARENA_QUIZ_QUESTIONS = 3
ARENA_QUIZ_BONUS = 0.15  # +15% sức mạnh cho mỗi câu quiz trả lời đúng

# Sức mạnh cơ bản theo rarity — khớp công thức powerOf() ở frontend (app.js) để số liệu nhất quán.
POWER_BASE = {"D": 20, "C": 40, "B": 80, "A": 150, "S": 280, "SS": 480, "SSS": 800}


def card_power(word: VocabItem) -> int:
    base = POWER_BASE.get(word.rarity, 40)
    return round(base * (1 + 0.25 * max(0, word.stars - 1)))


def deck_power(words: list[VocabItem]) -> int:
    return sum(card_power(w) for w in words)


def arena_status(db: Database, user_id: int) -> dict[str, Any]:
    rating = db.ensure_arena_rating(user_id)
    defense = db.get_arena_defense(user_id)
    cards = db.words_by_ids(user_id, defense["word_ids"]) if defense else []
    return {
        "rating": rating["rating"],
        "wins": rating["wins"],
        "losses": rating["losses"],
        "defense": [c.to_dict() for c in cards],
        "power": deck_power(cards),
        "max_cards": MAX_ARENA_CARDS,
    }


def set_defense(db: Database, user_id: int, word_ids: list[int]) -> dict[str, Any]:
    word_ids = list(dict.fromkeys(int(w) for w in word_ids))
    if not word_ids:
        raise ValueError("Chọn ít nhất 1 thẻ để xếp đội hình phòng thủ.")
    if len(word_ids) > MAX_ARENA_CARDS:
        raise ValueError(f"Chỉ được chọn tối đa {MAX_ARENA_CARDS} thẻ.")
    cards = db.words_by_ids(user_id, word_ids)
    if len(cards) != len(word_ids) or any(not c.owned for c in cards):
        raise ValueError("Một số thẻ không hợp lệ hoặc bạn chưa sở hữu.")
    db.set_arena_defense(user_id, word_ids)
    return arena_status(db, user_id)


def list_opponents(db: Database, user_id: int) -> list[dict[str, Any]]:
    db.ensure_arena_rating(user_id)
    return db.list_arena_opponents(user_id)


def prepare_attack(db: Database, user_id: int, defender_id: int) -> dict[str, Any]:
    if defender_id == user_id:
        raise ValueError("Không thể tự tấn công chính mình.")
    attacker_defense = db.get_arena_defense(user_id)
    if not attacker_defense or not attacker_defense["word_ids"]:
        raise ValueError("Bạn cần xếp đội hình phòng thủ trước khi đi tấn công.")
    defender_defense = db.get_arena_defense(defender_id)
    if not defender_defense or not defender_defense["word_ids"]:
        raise ValueError("Đối thủ chưa xếp đội hình phòng thủ.")
    defender_cards = db.words_by_ids(defender_id, defender_defense["word_ids"])

    pool = [c for c in defender_cards if c.meaning.strip() and c.term.strip()]
    if not pool:
        raise ValueError("Đội hình đối thủ chưa có đủ dữ liệu để ra quiz.")
    random.shuffle(pool)
    targets = pool[:ARENA_QUIZ_QUESTIONS]

    all_meanings = [c.meaning for c in defender_cards if c.meaning]
    all_terms = [c.term for c in defender_cards if c.term]

    questions = []
    for target in targets:
        mode = random.choice(["term_to_meaning", "meaning_to_term"])
        if mode == "meaning_to_term":
            prompt, correct = target.meaning, target.term
            pool_values = [t for t in all_terms if t != correct]
        else:
            prompt, correct = target.term, target.meaning
            pool_values = [m for m in all_meanings if m != correct]
        distractors = list(dict.fromkeys(v for v in pool_values if v))[:3]
        options = [correct] + distractors
        random.shuffle(options)
        questions.append({"word_id": target.id, "mode": mode, "prompt": prompt, "options": options})
    return {"defender_id": defender_id, "questions": questions}


def resolve_attack(
    db: Database, user_id: int, defender_id: int, answers: list[dict[str, Any]]
) -> dict[str, Any]:
    if defender_id == user_id:
        raise ValueError("Không thể tự tấn công chính mình.")
    attacker_defense = db.get_arena_defense(user_id)
    defender_defense = db.get_arena_defense(defender_id)
    if not attacker_defense or not attacker_defense["word_ids"]:
        raise ValueError("Bạn cần xếp đội hình phòng thủ trước khi đi tấn công.")
    if not defender_defense or not defender_defense["word_ids"]:
        raise ValueError("Đối thủ chưa xếp đội hình phòng thủ.")

    attacker_cards = db.words_by_ids(user_id, attacker_defense["word_ids"])
    defender_cards = db.words_by_ids(defender_id, defender_defense["word_ids"])
    defender_by_id = {c.id: c for c in defender_cards}

    # Loại trùng theo word_id và giới hạn số câu — tránh client gửi khống nhiều câu cho cùng 1 thẻ để bơm điểm.
    deduped: dict[int, dict[str, Any]] = {}
    for ans in answers:
        word_id = int(ans.get("word_id", 0))
        if word_id in defender_by_id and word_id not in deduped:
            deduped[word_id] = ans
        if len(deduped) >= ARENA_QUIZ_QUESTIONS:
            break

    reviewed = []
    quiz_correct = 0
    for word_id, ans in deduped.items():
        target = defender_by_id[word_id]
        mode = str(ans.get("mode", ""))
        selected = str(ans.get("selected", ""))
        correct = target.term if mode == "meaning_to_term" else target.meaning
        is_correct = selected == correct
        if is_correct:
            quiz_correct += 1
        reviewed.append({
            "word_id": word_id, "term": target.term, "meaning": target.meaning,
            "selected": selected, "correct": correct, "is_correct": is_correct,
        })
    quiz_total = len(reviewed)

    base_attacker_power = deck_power(attacker_cards)
    defender_power = deck_power(defender_cards)
    attacker_power = round(base_attacker_power * (1 + ARENA_QUIZ_BONUS * quiz_correct))

    db.ensure_arena_rating(user_id)
    db.ensure_arena_rating(defender_id)

    win = attacker_power > defender_power
    if win:
        attacker_delta, defender_delta = 20, -12
        pack_tier = "silver" if base_attacker_power < defender_power else "bronze"
        pack_id = db.add_pack(user_id, pack_tier, source=f"arena:{defender_id}")
    else:
        attacker_delta, defender_delta = -10, 8
        pack_tier = ""
        pack_id = None

    battle = db.record_arena_battle(
        attacker_id=user_id, defender_id=defender_id,
        attacker_power=attacker_power, defender_power=defender_power,
        quiz_correct=quiz_correct, quiz_total=quiz_total,
        result="win" if win else "loss",
        attacker_delta=attacker_delta, defender_delta=defender_delta,
        pack_tier=pack_tier,
    )
    battle["pack_id"] = pack_id
    battle["reviewed"] = reviewed
    battle["base_attacker_power"] = base_attacker_power
    return battle


def _generate_for_rarity(db: Database, llm: LLMClient, config: AppConfig, user_id: int, rarity: str) -> VocabItem | None:
    if not llm.configured:
        return None
    topics = db.topics_in_words(user_id) or ["high-frequency IELTS vocabulary"]
    topic = random.choice(topics)
    try:
        items = llm.generate_vocab(
            topic=topic,
            level=config.level,
            count=1,
            known_terms=db.all_terms(user_id),
            band_hint=BAND_FOR_RARITY.get(rarity, "B2"),
        )
    except LLMError:
        return None
    if not items:
        return None
    data = items[0]
    return db.add_word(
        user_id,
        str(data.get("term", "")),
        meaning=str(data.get("meaning_vi", "")),
        example=str(data.get("example", "")),
        example_vi=str(data.get("example_vi", "")),
        ipa=str(data.get("ipa", "")),
        pos=str(data.get("pos", "")),
        collocations=[str(c) for c in data.get("collocations", []) if c],
        notes=str(data.get("usage_note_vi", "")),
        topic=topic,
        band=str(data.get("band", "")),
        rarity=rarity,
        is_gem=bool(data.get("is_gem")),
        is_toeic=bool(data.get("is_toeic")),
        toeic_part=str(data.get("toeic_part", "")),
        source="pack",
    )
