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
        idx = min(len(RARITY_ORDER) - 2, RARITY_ORDER.index(base) + 1)  # gem tối đa SS khi sinh thường
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


def build_challenges(db: Database, config: AppConfig) -> list[dict[str, Any]]:
    progress = db.today_progress()
    _, _, today = local_day_bounds()
    claimed = db.claims_for_date(today)

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


def claim_challenge(db: Database, config: AppConfig, code: str) -> dict[str, Any]:
    challenges = {c["code"]: c for c in build_challenges(db, config)}
    challenge = challenges.get(code)
    if challenge is None:
        raise ValueError("Thử thách không tồn tại.")
    if not challenge["done"]:
        raise ValueError("Chưa hoàn thành thử thách này.")
    if challenge["claimed"]:
        raise ValueError("Đã nhận thưởng rồi.")
    _, _, today = local_day_bounds()
    if not db.claim_challenge(today, code, challenge["tier"]):
        raise ValueError("Đã nhận thưởng rồi.")
    pack_id = db.add_pack(challenge["tier"], source=f"challenge:{code}:{today}")
    return {"pack_id": pack_id, "tier": challenge["tier"], "tier_vi": PACK_NAMES_VI[challenge["tier"]]}


# ------------------------------------------------------------------- packs


def open_pack(db: Database, llm: LLMClient, config: AppConfig, pack_id: int) -> dict[str, Any]:
    pack = db.get_unopened_pack(pack_id)
    if pack is None:
        raise ValueError("Pack không tồn tại hoặc đã mở.")
    rolled = roll_rarity(pack["tier"])
    generated = False

    word = _pick_unowned(db, rolled)
    if word is None:
        word = _generate_for_rarity(db, llm, config, rolled)
        generated = word is not None
    if word is None:
        # LLM lỗi/không có thẻ đúng rarity: rơi xuống thẻ chưa sở hữu bất kỳ.
        fallback = db.unowned_words()
        if not fallback:
            raise ValueError("Không còn thẻ để mở và LLM chưa sẵn sàng. Hãy tạo thêm từ mới trước.")
        word = random.choice(fallback)
        rolled = word.rarity

    db.set_owned(word.id)
    db.mark_pack_opened(pack_id, word.id)
    fresh = db.get_word(word.id)
    assert fresh is not None
    return {
        "rarity": rolled,
        "tier": pack["tier"],
        "generated": generated,
        "card": fresh.to_dict(),
    }


def _pick_unowned(db: Database, rarity: str) -> VocabItem | None:
    candidates = db.unowned_words(rarity)
    return random.choice(candidates) if candidates else None


def _generate_for_rarity(db: Database, llm: LLMClient, config: AppConfig, rarity: str) -> VocabItem | None:
    if not llm.configured:
        return None
    topics = db.topics_in_words() or ["high-frequency IELTS vocabulary"]
    topic = random.choice(topics)
    try:
        items = llm.generate_vocab(
            topic=topic,
            level=config.level,
            count=1,
            known_terms=db.all_terms(),
            band_hint=BAND_FOR_RARITY.get(rarity, "B2"),
        )
    except LLMError:
        return None
    if not items:
        return None
    data = items[0]
    return db.add_word(
        str(data.get("term", "")),
        meaning=str(data.get("meaning_vi", "")),
        example=str(data.get("example", "")),
        example_vi=str(data.get("example_vi", "")),
        ipa=str(data.get("ipa", "")),
        pos=str(data.get("pos", "")),
        collocations=[str(c) for c in data.get("collocations", []) if c],
        topic=topic,
        band=str(data.get("band", "")),
        rarity=rarity,  # pack quyết định rarity, đó là phần "gacha"
        is_gem=bool(data.get("is_gem")),
        source="pack",
    )
