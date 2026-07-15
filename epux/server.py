from __future__ import annotations

import os
import random
import secrets
import threading
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta

from fastapi import Body, FastAPI, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
import jwt
import bcrypt

from . import game, task1, task2
from .config import AppConfig, default_db_path
from .db import Database
from .llm import LLMClient, LLMError
from .srs import parse_dt, preview_intervals, retention, utc_now

WEB_DIR = Path(__file__).parent / "web"

app = FastAPI(title="EPux", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
config = AppConfig.load()
llm = LLMClient()
db_lock = threading.RLock()

# ------------------------------------------------------------------- auth config

def _load_secret_key() -> str:
    """JWT signing key — never hard-coded, since this repo is public.

    Prefers EPUX_SECRET_KEY; otherwise generates one and keeps it in the data
    directory (a Modal Volume in production), so sessions survive restarts.
    """
    from_env = os.environ.get("EPUX_SECRET_KEY", "").strip()
    if from_env:
        return from_env
    key_file = default_db_path().parent / "secret_key"
    if key_file.is_file():
        existing = key_file.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    key = secrets.token_urlsafe(48)
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key, encoding="utf-8")
    return key


SECRET_KEY = _load_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Xác thực thất bại")
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

# ------------------------------------------------------------------- utils

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

def _word_from_llm(user_id: int, data: dict[str, Any], *, topic: str, source: str) -> Any:
    band = str(data.get("band", ""))
    is_gem = bool(data.get("is_gem"))
    is_toeic = bool(data.get("is_toeic"))
    toeic_part = str(data.get("toeic_part", ""))
    return db.add_word(
        user_id,
        str(data.get("term", "")),
        meaning=str(data.get("meaning_vi", "") or data.get("meaning", "")),
        example=str(data.get("example", "")),
        example_vi=str(data.get("example_vi", "")),
        ipa=str(data.get("ipa", "")),
        pos=str(data.get("pos", "")),
        collocations=[str(c) for c in data.get("collocations", []) if c],
        notes=str(data.get("usage_note_vi", "") or data.get("notes", "")),
        topic=topic or str(data.get("topic", "")),
        band=band,
        rarity=game.rarity_for_band(band, is_gem),
        is_gem=is_gem,
        is_toeic=is_toeic,
        toeic_part=toeic_part,
        source=source,
    )

# ------------------------------------------------------------------- auth api

@app.post("/api/auth/register")
def register(payload: dict[str, str] = Body(...)) -> dict[str, Any]:
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    if not username or len(password) < 4:
        raise HTTPException(status_code=400, detail="Tên đăng nhập và mật khẩu (ít nhất 4 ký tự) là bắt buộc.")
    
    with db_lock:
        if db.get_user_by_username(username):
            raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại.")
        hashed = get_password_hash(password)
        user_id = db.create_user(username, hashed)
        
    access_token = create_access_token(data={"sub": str(user_id)})
    return {"access_token": access_token, "token_type": "bearer", "username": username}

@app.post("/api/auth/login")
def login(payload: dict[str, str] = Body(...)) -> dict[str, Any]:
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    
    with db_lock:
        user = db.get_user_by_username(username)
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu.")
            
    access_token = create_access_token(data={"sub": str(user["id"])})
    return {"access_token": access_token, "token_type": "bearer", "username": username}

@app.get("/api/auth/me")
def get_me(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        return {"username": user["username"]}

# ------------------------------------------------------------------- pages

@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


# --------------------------------------------------------------- dashboard

@app.get("/api/dashboard")
def dashboard(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        stats = db.stats(user_id)
        progress = db.today_progress(user_id)
        # game.build_challenges currently doesn't take user_id, it just reads config.
        # But challenge_claims is user specific, so game methods need updating.
        # Since we haven't rewritten game.py yet, we'll patch it later. We pass user_id to it.
        challenges = game.build_challenges(db, config, user_id)
        packs = db.unopened_packs(user_id)
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
def stats(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {"stats": db.stats(user_id), "activity": db.daily_activity(user_id, 14), "level": game.level_from_xp(db.xp(user_id))}


# ------------------------------------------------------------------- words

@app.get("/api/words")
def list_words(query: str = "", topic: str = "", rarity: str = "", owned: str = "", user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    owned_filter = {"1": True, "0": False}.get(owned)
    with db_lock:
        words = db.list_words(user_id, query=query, topic=topic, rarity=rarity, owned=owned_filter)
        topics = db.topics_in_words(user_id)
    return {"words": [w.to_dict() for w in words], "topics": topics}


@app.post("/api/words")
def add_word(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    term = str(payload.get("term", "")).strip()
    if not term:
        raise HTTPException(status_code=400, detail="Từ vựng không được để trống.")
    use_ai = bool(payload.get("ai_enrich", True))
    if use_ai and llm.configured:
        data = _run_llm(llm.enrich_word, term, config.level)
        with db_lock:
            word = _word_from_llm(user_id, data, topic=str(payload.get("topic", "")), source="manual+ai")
    else:
        with db_lock:
            word = db.add_word(
                user_id,
                term,
                meaning=str(payload.get("meaning", "")),
                example=str(payload.get("example", "")),
                notes=str(payload.get("notes", "")),
                topic=str(payload.get("topic", "")),
                source="manual",
            )
    return {"word": word.to_dict()}


@app.get("/api/words/{word_id}")
def word_detail(word_id: int, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        word = db.get_word(user_id, word_id)
        if word is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy từ này.")
        last_review = db.last_review_at(user_id, word_id)
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
def update_word(word_id: int, payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    try:
        with db_lock:
            word = db.update_word(user_id, word_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"word": word.to_dict()}


@app.delete("/api/words/{word_id}")
def delete_word(word_id: int, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        ok = db.delete_word(user_id, word_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy từ này.")
    return {"ok": True}


@app.post("/api/words/generate")
def generate_words(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    topic = str(payload.get("topic", "")).strip() or "high-frequency IELTS vocabulary"
    count = max(1, min(20, int(payload.get("count", config.daily_new_words))))
    level = str(payload.get("level", "")).strip() or config.level
    context = str(payload.get("context", "")).strip()
    with db_lock:
        known = db.all_terms(user_id)
    items = _run_llm(llm.generate_vocab, topic, level, count, known, context=context)
    with db_lock:
        words = [_word_from_llm(user_id, item, topic=topic, source="auto") for item in items]
    return {"words": [w.to_dict() for w in words], "topic": topic}


# ------------------------------------------------------------------ topics

@app.get("/api/topics")
def topics(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {"topics": db.list_topics()}


@app.post("/api/topics/suggest")
def suggest_topics(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    with db_lock:
        known = [t["name"] for t in db.list_topics()]
    suggestions = _run_llm(llm.suggest_topics, known, config.level)
    with db_lock:
        db.upsert_topics(suggestions)
        return {"topics": db.list_topics()}


# ------------------------------------------------------------------ review

@app.get("/api/review/next")
def review_next(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        due = db.due_words(user_id, 1)
        remaining = db.due_count(user_id)
    if not due:
        return {"word": None, "remaining": 0}
    word = due[0]
    labels = preview_intervals(
        ease=word.ease, repetitions=word.repetitions, lapses=word.lapses, stability=word.stability
    )
    return {"word": word.to_dict(), "remaining": remaining, "intervals": labels}


@app.post("/api/review/{word_id}")
def review_word(word_id: int, payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    rating = int(payload.get("rating", -1))
    if rating not in (0, 1, 2, 3):
        raise HTTPException(status_code=400, detail="Rating phải là 0-3.")
    try:
        with db_lock:
            word = db.review_word(user_id, word_id, rating)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"word": word.to_dict()}


# -------------------------------------------------------------------- quiz

@app.get("/api/quiz/question")
def quiz_question(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    try:
        with db_lock:
            question = db.build_quiz_question(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return question


@app.post("/api/quiz/answer")
def quiz_answer(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    word_id = int(payload.get("word_id", 0))
    selected = str(payload.get("selected", ""))
    correct = str(payload.get("correct", ""))
    prompt = str(payload.get("prompt", ""))
    is_correct = selected == correct
    with db_lock:
        db.log_quiz_answer(
            user_id, word_id=word_id, prompt=prompt, selected=selected, correct=correct, is_correct=is_correct
        )
        db.review_word(user_id, word_id, 2 if is_correct else 0)
    return {"is_correct": is_correct, "correct": correct}


# ----------------------------------------------------------------- writing

@app.post("/api/writing/prompt")
def writing_prompt(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    kind = str(payload.get("kind", "daily"))
    if kind not in ("daily", "ielts"):
        kind = "daily"
    with db_lock:
        recent = db.recent_prompts(user_id)
    data = _run_llm(llm.writing_prompt, kind, config.level, config.target_band, recent)
    data["kind"] = kind
    return data


@app.post("/api/writing/grade")
def writing_grade(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    content = str(payload.get("content", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    kind = str(payload.get("kind", "daily"))
    title = str(payload.get("title", "")).strip()
    target_language = [str(t) for t in payload.get("target_language", []) if t]
    if len(content.split()) < 20:
        raise HTTPException(status_code=400, detail="Bài viết quá ngắn (tối thiểu 20 từ).")
    if not prompt:
        raise HTTPException(status_code=400, detail="Thiếu đề bài.")
    feedback = _run_llm(
        llm.grade_writing, prompt, content, kind, config.level, config.target_band,
        target_language=target_language,
    )
    band = feedback.get("overall_band")
    try:
        band_value = float(band) if band is not None else None
    except (TypeError, ValueError):
        band_value = None
    with db_lock:
        writing = db.add_writing(
            user_id, kind=kind, title=title, prompt=prompt, content=content,
            overall_band=band_value, feedback=feedback,
        )
    return {"writing": writing.to_dict()}


@app.get("/api/writing/history")
def writing_history(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {"writings": [w.to_dict() for w in db.list_writings(user_id)]}


# ----------------------------------------------------------------- task 1

@app.get("/api/task1/knowledge")
def task1_knowledge(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    return {"knowledge": task1.KNOWLEDGE, "bank": task1.bank_public()}


@app.get("/api/task1/model/{item_id}")
def task1_model(item_id: str, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    model = task1.model_answer(item_id)
    if not model:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề này.")
    return model


@app.post("/api/task1/generate")
def task1_generate(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    chart_type = str(payload.get("chart_type", "line"))
    if chart_type not in ("line", "bar", "pie", "table"):
        raise HTTPException(status_code=400, detail="Dạng biểu đồ AI tự vẽ được: line, bar, pie, table.")
    with db_lock:
        recent = db.recent_prompts(user_id)
    data = _run_llm(llm.task1_prompt, chart_type, config.level, config.target_band, recent)
    data["kind"] = "task1"
    data["chart_type"] = chart_type
    return data


@app.post("/api/task1/grade")
def task1_grade(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    content = str(payload.get("content", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    title = str(payload.get("title", "")).strip()
    chart_type = str(payload.get("chart_type", "line"))
    bank_id = str(payload.get("bank_id", "")).strip()
    chart = payload.get("chart") or {}

    if bank_id:
        item = task1.BANK_BY_ID.get(bank_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy đề này.")
        # The bank's figure is an image, so the examiner grades against the band-9 model answer,
        # which carries all the correct figures.
        prompt = item["question"]
        title = item["title"]
        chart_type = item["type"]
        chart = {"note": "The figure is an exam image. These are the correct figures, taken from the "
                         "band-9 model answer — check the learner's numbers against it.",
                 "model_answer": item["model"]}

    if not prompt:
        raise HTTPException(status_code=400, detail="Thiếu đề bài.")
    if len(content.split()) < 20:
        raise HTTPException(status_code=400, detail="Bài viết quá ngắn (tối thiểu 20 từ).")

    word_count = len(content.split())
    feedback = _run_llm(
        llm.grade_task1, prompt, chart, content, chart_type, config.level, config.target_band,
        word_count=word_count,
    )
    # LLMs cannot count words reliably — decide this one here.
    check = feedback.get("task1_check")
    if isinstance(check, dict):
        check["word_count_ok"] = word_count >= 150
        check["word_count"] = word_count

    band = feedback.get("overall_band")
    try:
        band_value = float(band) if band is not None else None
    except (TypeError, ValueError):
        band_value = None
    with db_lock:
        writing = db.add_writing(
            user_id, kind="task1", title=title, prompt=prompt, content=content,
            overall_band=band_value, feedback=feedback,
        )
    return {"writing": writing.to_dict(), "model": task1.model_answer(bank_id) if bank_id else None}


# ----------------------------------------------------------------- task 2

@app.get("/api/task2/knowledge")
def task2_knowledge(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    return {"knowledge": task2.KNOWLEDGE, "bank": task2.bank_public()}


@app.get("/api/task2/model/{item_id}")
def task2_model(item_id: str, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    model = task2.model_answer(item_id)
    if not model:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề này.")
    return model


@app.post("/api/task2/generate")
def task2_generate(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    with db_lock:
        recent = db.recent_prompts(user_id)
    # Reuse the Task 2 essay-question generator (kind="ielts").
    data = _run_llm(llm.writing_prompt, "ielts", config.level, config.target_band, recent)
    data["kind"] = "task2"
    return data


@app.post("/api/task2/grade")
def task2_grade(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    content = str(payload.get("content", "")).strip()
    prompt = str(payload.get("prompt", "")).strip()
    title = str(payload.get("title", "")).strip()
    essay_type = str(payload.get("essay_type", "opinion"))
    bank_id = str(payload.get("bank_id", "")).strip()
    model_text = None

    if bank_id:
        item = task2.BANK_BY_ID.get(bank_id)
        if not item:
            raise HTTPException(status_code=404, detail="Không tìm thấy đề này.")
        prompt = item["question"]
        title = item["title"]
        essay_type = item["type"]
        model_text = item["model"]

    if not prompt:
        raise HTTPException(status_code=400, detail="Thiếu đề bài.")
    if len(content.split()) < 40:
        raise HTTPException(status_code=400, detail="Bài viết quá ngắn (tối thiểu 40 từ).")

    word_count = len(content.split())
    feedback = _run_llm(
        llm.grade_task2, prompt, essay_type, content, config.level, config.target_band,
        word_count=word_count, model_answer=model_text,
    )
    # LLMs cannot count words reliably — decide this one here.
    check = feedback.get("task2_check")
    if isinstance(check, dict):
        check["word_count_ok"] = word_count >= 250
        check["word_count"] = word_count

    band = feedback.get("overall_band")
    try:
        band_value = float(band) if band is not None else None
    except (TypeError, ValueError):
        band_value = None
    with db_lock:
        writing = db.add_writing(
            user_id, kind="task2", title=title, prompt=prompt, content=content,
            overall_band=band_value, feedback=feedback,
        )
    return {"writing": writing.to_dict(), "model": task2.model_answer(bank_id) if bank_id else None}


# ---------------------------------------------------------------- patterns

@app.get("/api/patterns")
def patterns(theme: str = "", user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {"patterns": db.list_patterns(theme), "themes": db.pattern_themes()}


@app.post("/api/patterns/generate")
def patterns_generate(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
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
def patterns_practice(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    pattern = str(payload.get("pattern", "")).strip()
    sentence = str(payload.get("sentence", "")).strip()
    if not pattern or not sentence:
        raise HTTPException(status_code=400, detail="Thiếu mẫu câu hoặc câu của bạn.")
    return _run_llm(llm.check_pattern_sentence, pattern, sentence)


# -------------------------------------------------------- challenges/packs

@app.get("/api/challenges")
def challenges(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {
            "challenges": game.build_challenges(db, config, user_id),
            "packs": db.unopened_packs(user_id),
            "pack_names": game.PACK_NAMES_VI,
        }


@app.post("/api/challenges/{code}/claim")
def claim_challenge(code: str, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    try:
        with db_lock:
            reward = game.claim_challenge(db, config, user_id, code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return reward


@app.post("/api/packs/{pack_id}/open")
def open_pack(pack_id: int, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    try:
        with db_lock:
            result = game.open_pack(db, llm, config, user_id, pack_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@app.get("/api/collection")
def collection(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        cards = db.list_words(user_id, limit=5000)
        stats = db.stats(user_id)
    return {
        "cards": [w.to_dict() for w in cards],
        "by_rarity": stats["by_rarity"],
        "total_stars": stats["total_stars"],
        "rarities": game.RARITY_ORDER,
        "max_stars": game.MAX_STARS,
    }


@app.post("/api/cards/{word_id}/upgrade")
def upgrade_card(word_id: int, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    try:
        with db_lock:
            word = db.upgrade_card(user_id, word_id, max_stars=game.MAX_STARS)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"word": word.to_dict()}


@app.post("/api/collection/expand")
def collection_expand(payload: dict[str, Any] = Body(default={}), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    total = max(5, min(30, int(payload.get("count", 15))))
    with db_lock:
        topics = list(dict.fromkeys(db.topics_in_words(user_id) + [t["name"] for t in db.list_topics()]))
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
            known = db.all_terms(user_id)
        try:
            items = llm.generate_vocab(topic, config.level, per_topic, known)
        except LLMError:
            continue
        with db_lock:
            created.extend(_word_from_llm(user_id, item, topic=topic, source="auto") for item in items)
    if not created:
        raise HTTPException(status_code=503, detail="LLM không sinh được từ mới, thử lại sau nhé.")
    return {"added": len(created), "topics": chosen, "words": [w.to_dict() for w in created]}


# -------------------------------------------------------------------- arena

@app.get("/api/arena/status")
def arena_status(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return game.arena_status(db, user_id)


@app.post("/api/arena/defense")
def arena_defense(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    word_ids = [int(w) for w in payload.get("word_ids", [])]
    try:
        with db_lock:
            return game.set_defense(db, user_id, word_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/arena/opponents")
def arena_opponents(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {"opponents": game.list_opponents(db, user_id)}


@app.post("/api/arena/attack/{defender_id}/prepare")
def arena_attack_prepare(defender_id: int, user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    try:
        with db_lock:
            return game.prepare_attack(db, user_id, defender_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/arena/attack/{defender_id}/resolve")
def arena_attack_resolve(
    defender_id: int, payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)
) -> dict[str, Any]:
    answers = payload.get("answers", [])
    if not isinstance(answers, list):
        answers = []
    try:
        with db_lock:
            return game.resolve_attack(db, user_id, defender_id, answers)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/arena/history")
def arena_history(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {"battles": db.arena_history(user_id)}


@app.get("/api/arena/leaderboard")
def arena_leaderboard(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    with db_lock:
        return {"leaderboard": db.arena_leaderboard()}


# ------------------------------------------------------------------ config

@app.get("/api/config")
def get_config(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
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
def put_config(payload: dict[str, Any] = Body(...), user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    config.update(payload)
    return get_config(user_id)


@app.post("/api/llm/test")
def llm_test(user_id: int = Depends(get_current_user)) -> dict[str, Any]:
    _llm_guard()
    return llm.ping()


# ------------------------------------------------------------------- admin
# Chỉ dùng để can thiệp thủ công (vd: tặng pack) qua đúng kết nối DB đang chạy —
# tránh ghi trực tiếp vào file sqlite trên Modal Volume trong lúc app đang sống,
# vì container đang chạy không tự reload Volume nên các ghi ngoài luồng dễ bị mất.
def _require_admin_secret(x_admin_secret: str | None) -> None:
    expected = os.environ.get("EPUX_ADMIN_SECRET", "")
    if not expected or x_admin_secret != expected:
        raise HTTPException(status_code=403, detail="Không có quyền admin.")


@app.post("/api/admin/grant-pack")
def admin_grant_pack(
    payload: dict[str, Any] = Body(...), x_admin_secret: Optional[str] = Header(default=None)
) -> dict[str, Any]:
    _require_admin_secret(x_admin_secret)
    username = str(payload.get("username", "")).strip()
    tier = str(payload.get("tier", "bronze"))
    count = max(1, min(20, int(payload.get("count", 1))))
    if tier not in ("bronze", "silver", "gold"):
        raise HTTPException(status_code=400, detail="Tier không hợp lệ (bronze|silver|gold).")
    with db_lock:
        target = db.get_user_by_username(username)
        if not target:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        pack_ids = [db.add_pack(target["id"], tier, source="admin:gift") for _ in range(count)]
        unopened_total = len(db.unopened_packs(target["id"]))
    return {
        "username": username,
        "tier": tier,
        "granted": len(pack_ids),
        "pack_ids": pack_ids,
        "unopened_total": unopened_total,
    }


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def serve(port: int | None = None, open_browser: bool = True) -> None:
    import webbrowser
    import requests
    import uvicorn

    port = port or config.server_port
    url = f"http://127.0.0.1:{port}"

    try:
        if requests.get(f"{url}/api/config", timeout=1.5).status_code in (200, 401):
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
