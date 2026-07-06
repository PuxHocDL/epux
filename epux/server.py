from __future__ import annotations

import random
import threading
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import game
from .config import AppConfig
from .db import Database
from .llm import LLMClient, LLMError
from .srs import parse_dt, preview_intervals, retention, utc_now

WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(title="EPux", docs_url=None, redoc_url=None)

db = Database()
config = AppConfig.load()
llm = LLMClient()
db_lock = threading.RLock()


def _llm_guard() -> LLMClient:
    if not llm.configured:
        raise HTTPException(
            status_code=503,
            detail="Chưa cấu hình LLM. Thêm AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT vào file .env rồi khởi động lại.",
        )
    return llm


def _run_llm(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _word_from_llm(data: dict[str, Any], *, topic: str, source: str) -> Any:
    band = str(data.get("band", ""))
    is_gem = bool(data.get("is_gem"))
    return db.add_word(
        str(data.get("term", "")),
        meaning=str(data.get("meaning_vi", "") or data.get("meaning", "")),
        example=str(data.get("example", "")),
        example_vi=str(data.get("example_vi", "")),
        ipa=str(data.get("ipa", "")),
        pos=str(data.get("pos", "")),
        collocations=[str(c) for c in data.get("collocations", []) if c],
        topic=topic or str(data.get("topic", "")),
        band=band,
        rarity=game.rarity_for_band(band, is_gem),
        is_gem=is_gem,
        source=source,
    )


# ------------------------------------------------------------------- pages


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


# --------------------------------------------------------------- dashboard


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    with db_lock:
        stats = db.stats()
        progress = db.today_progress()
        challenges = game.build_challenges(db, config)
        packs = db.unopened_packs()
    return {
        "stats": stats,
        "level": game.level_from_xp(stats["xp"]),
        "today": progress,
        "challenges": challenges,
        "packs": packs,
        "pack_names": game.PACK_NAMES_VI,
        "need_daily_words": progress["new_words"] < config.daily_new_words,
        "daily_new_words": config.daily_new_words,
        "llm": llm.status(),
    }


@app.get("/api/stats")
def stats() -> dict[str, Any]:
    with db_lock:
        return {"stats": db.stats(), "activity": db.daily_activity(14), "level": game.level_from_xp(db.xp())}


# ------------------------------------------------------------------- words


@app.get("/api/words")
def list_words(query: str = "", topic: str = "", rarity: str = "", owned: str = "") -> dict[str, Any]:
    owned_filter = {"1": True, "0": False}.get(owned)
    with db_lock:
        words = db.list_words(query=query, topic=topic, rarity=rarity, owned=owned_filter)
        topics = db.topics_in_words()
    return {"words": [w.to_dict() for w in words], "topics": topics}


@app.post("/api/words")
def add_word(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    term = str(payload.get("term", "")).strip()
    if not term:
        raise HTTPException(status_code=400, detail="Từ vựng không được để trống.")
    use_ai = bool(payload.get("ai_enrich", True))
    if use_ai and llm.configured:
        data = _run_llm(llm.enrich_word, term, config.level)
        with db_lock:
            word = _word_from_llm(data, topic=str(payload.get("topic", "")), source="manual+ai")
    else:
        with db_lock:
            word = db.add_word(
                term,
                meaning=str(payload.get("meaning", "")),
                example=str(payload.get("example", "")),
                notes=str(payload.get("notes", "")),
                topic=str(payload.get("topic", "")),
                source="manual",
            )
    return {"word": word.to_dict()}


@app.get("/api/words/{word_id}")
def word_detail(word_id: int) -> dict[str, Any]:
    with db_lock:
        word = db.get_word(word_id)
        if word is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy từ này.")
        last_review = db.last_review_at(word_id)
    anchor = parse_dt(last_review) or parse_dt(word.created_at)
    elapsed_days = max(0.0, (utc_now() - anchor).total_seconds() / 86400) if anchor else 0.0
    return {
        "word": word.to_dict(),
        "srs": {
            "retention_now": round(retention(max(word.stability, 0.007), elapsed_days) * 100),
            "last_review": last_review,
            "intervals": preview_intervals(
                ease=word.ease, repetitions=word.repetitions,
                lapses=word.lapses, stability=word.stability,
            ),
        },
    }


@app.put("/api/words/{word_id}")
def update_word(word_id: int, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        with db_lock:
            word = db.update_word(word_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"word": word.to_dict()}


@app.delete("/api/words/{word_id}")
def delete_word(word_id: int) -> dict[str, Any]:
    with db_lock:
        ok = db.delete_word(word_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy từ này.")
    return {"ok": True}


@app.post("/api/words/generate")
def generate_words(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    _llm_guard()
    topic = str(payload.get("topic", "")).strip() or "high-frequency IELTS vocabulary"
    count = max(1, min(20, int(payload.get("count", config.daily_new_words))))
    with db_lock:
        known = db.all_terms()
    items = _run_llm(llm.generate_vocab, topic, config.level, count, known)
    with db_lock:
        words = [_word_from_llm(item, topic=topic, source="auto") for item in items]
    return {"words": [w.to_dict() for w in words], "topic": topic}


# ------------------------------------------------------------------ topics


@app.get("/api/topics")
def topics() -> dict[str, Any]:
    with db_lock:
        return {"topics": db.list_topics()}


@app.post("/api/topics/suggest")
def suggest_topics() -> dict[str, Any]:
    _llm_guard()
    with db_lock:
        known = [t["name"] for t in db.list_topics()]
    suggestions = _run_llm(llm.suggest_topics, known, config.level)
    with db_lock:
        db.upsert_topics(suggestions)
        return {"topics": db.list_topics()}


# ------------------------------------------------------------------ review


@app.get("/api/review/next")
def review_next() -> dict[str, Any]:
    with db_lock:
        due = db.due_words(1)
        remaining = db.due_count()
    if not due:
        return {"word": None, "remaining": 0}
    word = due[0]
    labels = preview_intervals(
        ease=word.ease, repetitions=word.repetitions, lapses=word.lapses, stability=word.stability
    )
    return {"word": word.to_dict(), "remaining": remaining, "intervals": labels}


@app.post("/api/review/{word_id}")
def review_word(word_id: int, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    rating = int(payload.get("rating", -1))
    if rating not in (0, 1, 2, 3):
        raise HTTPException(status_code=400, detail="Rating phải là 0-3.")
    try:
        with db_lock:
            word = db.review_word(word_id, rating)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"word": word.to_dict()}


# -------------------------------------------------------------------- quiz


@app.get("/api/quiz/question")
def quiz_question() -> dict[str, Any]:
    try:
        with db_lock:
            question = db.build_quiz_question()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return question


@app.post("/api/quiz/answer")
def quiz_answer(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    word_id = int(payload.get("word_id", 0))
    selected = str(payload.get("selected", ""))
    correct = str(payload.get("correct", ""))
    prompt = str(payload.get("prompt", ""))
    is_correct = selected == correct
    with db_lock:
        db.log_quiz_answer(
            word_id=word_id, prompt=prompt, selected=selected, correct=correct, is_correct=is_correct
        )
        db.review_word(word_id, 2 if is_correct else 0)
    return {"is_correct": is_correct, "correct": correct}


# ----------------------------------------------------------------- writing


@app.post("/api/writing/prompt")
def writing_prompt(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    _llm_guard()
    kind = str(payload.get("kind", "daily"))
    if kind not in ("daily", "ielts"):
        kind = "daily"
    with db_lock:
        recent = db.recent_prompts()
    data = _run_llm(llm.writing_prompt, kind, config.level, config.target_band, recent)
    data["kind"] = kind
    return data


@app.post("/api/writing/grade")
def writing_grade(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    _llm_guard()
    content = str(payload.get("content", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    kind = str(payload.get("kind", "daily"))
    title = str(payload.get("title", "")).strip()
    if len(content.split()) < 20:
        raise HTTPException(status_code=400, detail="Bài viết quá ngắn (tối thiểu 20 từ).")
    if not prompt:
        raise HTTPException(status_code=400, detail="Thiếu đề bài.")
    feedback = _run_llm(llm.grade_writing, prompt, content, kind, config.level, config.target_band)
    band = feedback.get("overall_band")
    try:
        band_value = float(band) if band is not None else None
    except (TypeError, ValueError):
        band_value = None
    with db_lock:
        writing = db.add_writing(
            kind=kind, title=title, prompt=prompt, content=content,
            overall_band=band_value, feedback=feedback,
        )
    return {"writing": writing.to_dict()}


@app.get("/api/writing/history")
def writing_history() -> dict[str, Any]:
    with db_lock:
        return {"writings": [w.to_dict() for w in db.list_writings()]}


# ---------------------------------------------------------------- patterns


@app.get("/api/patterns")
def patterns(theme: str = "") -> dict[str, Any]:
    with db_lock:
        return {"patterns": db.list_patterns(theme), "themes": db.pattern_themes()}


@app.post("/api/patterns/generate")
def patterns_generate(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    _llm_guard()
    theme = str(payload.get("theme", "")).strip() or "daily routines"
    count = max(1, min(12, int(payload.get("count", 6))))
    with db_lock:
        known = db.all_pattern_texts()
    items = _run_llm(llm.generate_patterns, theme, config.level, count, known)
    with db_lock:
        db.add_patterns(theme, items)
        return {"patterns": db.list_patterns(theme), "themes": db.pattern_themes(), "theme": theme}


@app.post("/api/patterns/practice")
def patterns_practice(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    _llm_guard()
    pattern = str(payload.get("pattern", "")).strip()
    sentence = str(payload.get("sentence", "")).strip()
    if not pattern or not sentence:
        raise HTTPException(status_code=400, detail="Thiếu mẫu câu hoặc câu của bạn.")
    return _run_llm(llm.check_pattern_sentence, pattern, sentence)


# -------------------------------------------------------- challenges/packs


@app.get("/api/challenges")
def challenges() -> dict[str, Any]:
    with db_lock:
        return {
            "challenges": game.build_challenges(db, config),
            "packs": db.unopened_packs(),
            "pack_names": game.PACK_NAMES_VI,
        }


@app.post("/api/challenges/{code}/claim")
def claim_challenge(code: str) -> dict[str, Any]:
    try:
        with db_lock:
            reward = game.claim_challenge(db, config, code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return reward


@app.post("/api/packs/{pack_id}/open")
def open_pack(pack_id: int) -> dict[str, Any]:
    # Không giữ db_lock suốt vòng LLM bên trong open_pack: chấp nhận vì chỉ 1 user local.
    try:
        with db_lock:
            result = game.open_pack(db, llm, config, pack_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@app.get("/api/collection")
def collection() -> dict[str, Any]:
    with db_lock:
        cards = db.list_words(limit=5000)  # cả thẻ chưa sở hữu -> hiện silhouette
        stats = db.stats()
    return {
        "cards": [w.to_dict() for w in cards],
        "by_rarity": stats["by_rarity"],
        "total_stars": stats["total_stars"],
        "rarities": game.RARITY_ORDER,
        "max_stars": game.MAX_STARS,
    }


@app.post("/api/cards/{word_id}/upgrade")
def upgrade_card(word_id: int) -> dict[str, Any]:
    try:
        with db_lock:
            word = db.upgrade_card(word_id, max_stars=game.MAX_STARS)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"word": word.to_dict()}


@app.post("/api/collection/expand")
def collection_expand(payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    """AI mở rộng kho thẻ: sinh từ mới trên tối đa 3 chủ đề cùng lúc."""
    _llm_guard()
    total = max(5, min(30, int(payload.get("count", 15))))
    with db_lock:
        topics = list(dict.fromkeys(db.topics_in_words() + [t["name"] for t in db.list_topics()]))
    if not topics:
        suggestions = _run_llm(llm.suggest_topics, [], config.level)
        with db_lock:
            db.upsert_topics(suggestions)
        topics = [str(t.get("name", "")) for t in suggestions if t.get("name")]
    chosen = random.sample(topics, min(3, len(topics)))
    per_topic = max(2, total // len(chosen))
    created: list[Any] = []
    for topic in chosen:
        with db_lock:
            known = db.all_terms()
        try:
            items = llm.generate_vocab(topic, config.level, per_topic, known)
        except LLMError:
            continue
        with db_lock:
            created.extend(_word_from_llm(item, topic=topic, source="auto") for item in items)
    if not created:
        raise HTTPException(status_code=503, detail="LLM không sinh được từ mới, thử lại sau nhé.")
    return {"added": len(created), "topics": chosen, "words": [w.to_dict() for w in created]}


# ------------------------------------------------------------------ config


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    return {
        "config": {
            "level": config.level,
            "target_band": config.target_band,
            "daily_new_words": config.daily_new_words,
            "server_port": config.server_port,
            "reminder_minutes": config.reminder_minutes,
            "notify_quiet_start": config.notify_quiet_start,
            "notify_quiet_end": config.notify_quiet_end,
        },
        "llm": llm.status(),
    }


@app.put("/api/config")
def put_config(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    config.update(payload)
    return get_config()


@app.post("/api/llm/test")
def llm_test() -> dict[str, Any]:
    _llm_guard()
    return llm.ping()


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def serve(port: int | None = None, open_browser: bool = True) -> None:
    import webbrowser

    import requests
    import uvicorn

    port = port or config.server_port
    url = f"http://127.0.0.1:{port}"

    # Đã có phiên EPux chạy sẵn trên port này -> chỉ cần mở lại trang.
    try:
        if requests.get(f"{url}/api/dashboard", timeout=1.5).ok:
            print(f"EPux đã chạy sẵn tại {url} — mở trình duyệt.")
            if open_browser:
                webbrowser.open(url)
            return
    except requests.RequestException:
        pass

    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    llm_state = "sẵn sàng" if llm.configured else "CHƯA cấu hình (.env)"
    print(f"EPux chạy tại {url}  |  LLM: {llm_state} ({llm.settings.provider or 'n/a'})")
    print("Giữ cửa sổ này mở trong lúc học. Ctrl+C để dừng.")
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except OSError as exc:
        raise RuntimeError(
            f"Không mở được port {port} ({exc}). Có chương trình khác đang dùng port này — "
            f"thử: epux serve --port {port + 1}"
        ) from exc
