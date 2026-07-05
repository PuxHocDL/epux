from __future__ import annotations

import json
from typing import Any

import requests

from .config import LLMSettings


class LLMError(RuntimeError):
    pass


SYSTEM_BASE = (
    "You are the AI engine of EPux, a vocabulary & IELTS writing coach for a Vietnamese learner "
    "who works in IT. All explanations, meanings and feedback aimed at the learner must be in "
    "Vietnamese; English is used only for the target-language material itself (terms, examples, "
    "essays). Always return valid JSON only, no markdown fences, no commentary."
)


class LLMClient:
    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_env()

    @property
    def configured(self) -> bool:
        return self.settings.configured

    def status(self) -> dict[str, Any]:
        s = self.settings
        return {
            "configured": s.configured,
            "provider": s.provider,
            "endpoint": s.endpoint,
            "model": s.deployment,
        }

    def ping(self) -> dict[str, Any]:
        try:
            reply = self.chat("Reply with JSON.", 'Return {"ok": true}', max_tokens=20)
            return {"ok": bool(reply.get("ok")), "error": ""}
        except LLMError as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------ core

    def _request(self, messages: list[dict[str, str]], *, temperature: float, max_tokens: int) -> str:
        s = self.settings
        if not s.configured:
            raise LLMError("Chưa cấu hình LLM. Kiểm tra file .env (AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT...).")
        if s.provider == "azure":
            url = f"{s.endpoint}/openai/deployments/{s.deployment}/chat/completions?api-version={s.api_version}"
            headers = {"api-key": s.api_key, "Content-Type": "application/json"}
        else:
            url = f"{s.endpoint}/chat/completions"
            headers = {"Authorization": f"Bearer {s.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        if s.provider != "azure":
            payload["model"] = s.deployment
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
        except requests.RequestException as exc:
            raise LLMError(f"Không gọi được LLM: {exc}") from exc
        if response.status_code == 401:
            raise LLMError("LLM từ chối API key (401). Kiểm tra lại .env.")
        if not response.ok:
            detail = ""
            try:
                detail = response.json().get("error", {}).get("message", "")
            except Exception:
                detail = response.text[:200]
            raise LLMError(f"LLM trả lỗi {response.status_code}: {detail}")
        data = response.json()
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError) as exc:
            raise LLMError("Phản hồi LLM không đúng định dạng.") from exc

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.4,
        max_tokens: int = 3000,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": f"{SYSTEM_BASE}\n\n{system}"},
            {"role": "user", "content": user},
        ]
        raw = self._request(messages, temperature=temperature, max_tokens=max_tokens)
        data = _extract_json(raw)
        if not isinstance(data, dict):
            raise LLMError("LLM không trả về JSON object.")
        return data

    # -------------------------------------------------------------- features

    def suggest_topics(self, known_topics: list[str], level: str, count: int = 8) -> list[dict[str, Any]]:
        user = (
            f"Suggest {count} vocabulary topics that appear often in the IELTS exam and are valuable "
            f"for a {level} learner working in IT.\n"
            f"Topics the learner already has (avoid duplicates): {json.dumps(known_topics, ensure_ascii=False)}\n"
            "Mix classic IELTS themes (environment, education, health, technology, work, globalization...) "
            "with a few tied to daily life / IT work.\n"
            'Return {"topics": [{"name": "English topic name", "name_vi": "tên tiếng Việt", '
            '"description_vi": "1 câu: vì sao chủ đề này hay gặp trong IELTS", '
            '"sample_words": ["3-4 từ ví dụ"]}]}'
        )
        data = self.chat("You curate IELTS vocabulary topics.", user, temperature=0.7)
        topics = data.get("topics")
        if not isinstance(topics, list):
            raise LLMError("LLM không trả về danh sách chủ đề.")
        return [t for t in topics if isinstance(t, dict) and str(t.get("name", "")).strip()]

    def generate_vocab(
        self,
        topic: str,
        level: str,
        count: int,
        known_terms: list[str],
        band_hint: str = "",
    ) -> list[dict[str, Any]]:
        hint = f"All items must be {band_hint} difficulty.\n" if band_hint else (
            f"Difficulty: centered on {level}, with 1-2 easier items and 1-2 more advanced (C1/C2) items.\n"
        )
        user = (
            f"Create {count} English vocabulary cards on the topic \"{topic}\" for a Vietnamese learner "
            f"preparing for IELTS (current level {level}).\n"
            + hint
            + "Prefer word/collocation choices that actually score in IELTS (topic-specific, precise). "
            "Include some collocations or phrasal verbs, not only single words.\n"
            f"NEVER include these terms the learner already knows: {json.dumps(sorted(known_terms)[:400], ensure_ascii=False)}\n"
            'Return {"words": [{"term": "...", "ipa": "/.../", "pos": "noun|verb|adj|adv|phrase|idiom", '
            '"meaning_vi": "nghĩa tiếng Việt ngắn gọn", "example": "natural English example sentence", '
            '"example_vi": "dịch câu ví dụ", "collocations": ["2-3 collocations"], '
            '"band": "A2|B1|B2|C1|C2", "is_gem": true nếu là từ/idiom đắt giá hiếm gặp giúp ăn điểm}]}'
        )
        data = self.chat("You create high-quality bilingual vocabulary cards.", user, temperature=0.6, max_tokens=4000)
        words = data.get("words")
        if not isinstance(words, list):
            raise LLMError("LLM không trả về danh sách từ.")
        seen = {t.lower() for t in known_terms}
        clean: list[dict[str, Any]] = []
        for item in words:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term", "")).strip()
            if not term or term.lower() in seen:
                continue
            seen.add(term.lower())
            clean.append(item)
        return clean

    def enrich_word(self, term: str, level: str) -> dict[str, Any]:
        user = (
            f"Create one complete vocabulary card for: \"{term}\" (learner level {level}).\n"
            'Return {"term": "...", "ipa": "/.../", "pos": "...", "meaning_vi": "...", '
            '"example": "...", "example_vi": "...", "collocations": ["..."], '
            '"band": "A2|B1|B2|C1|C2", "is_gem": bool, "topic": "most fitting IELTS topic, in English"}'
        )
        return self.chat("You create high-quality bilingual vocabulary cards.", user)

    def writing_prompt(self, kind: str, level: str, target_band: str, recent_prompts: list[str]) -> dict[str, Any]:
        if kind == "daily":
            brief = (
                "Create a short daily-life writing task (60-120 words expected) for practising how to "
                "describe everyday activities, routines, plans or work life. The learner works in IT, "
                "so sometimes (not always) tie it to office/dev life. Practical, not exam-style."
            )
        else:
            brief = (
                "Create one IELTS Writing Task 2 question (opinion/discussion/problem-solution) on a "
                "topic that commonly appears in the real exam."
            )
        user = (
            f"{brief}\nLearner level: {level}, target band {target_band}.\n"
            f"Avoid repeating these recent prompts: {json.dumps(recent_prompts[-10:], ensure_ascii=False)}\n"
            'Return {"title": "short title", "prompt": "the task, in English", '
            '"guidance_vi": "2-3 câu tiếng Việt gợi ý cách triển khai + 2 mẫu câu nên dùng", '
            '"min_words": number}'
        )
        return self.chat("You write English writing tasks.", user, temperature=0.8)

    def grade_writing(
        self,
        prompt: str,
        content: str,
        kind: str,
        level: str,
        target_band: str,
    ) -> dict[str, Any]:
        scale = (
            "Use the official IELTS Writing band descriptors (0-9, steps of 0.5)."
            if kind == "ielts"
            else "It is a short daily practice, but still score it on the IELTS 0-9 scale so progress is comparable."
        )
        user = (
            f"Grade this piece of writing.\nTask: {prompt}\n---\nLearner text:\n{content}\n---\n"
            f"{scale} Learner level {level}, target band {target_band}. Be honest, not flattering.\n"
            'Return {"overall_band": number, "criteria": {"task_response": number, "coherence": number, '
            '"lexical_resource": number, "grammar": number}, '
            '"summary_vi": "3-4 câu nhận xét tổng quan bằng tiếng Việt", '
            '"errors": [{"quote": "đoạn sai trích nguyên văn", "fix": "cách viết đúng", "explain_vi": "giải thích ngắn"}], '
            '"improved_version": "the same text rewritten at ~target band, keep the learner\'s ideas", '
            '"vocab_upgrades": [{"term": "từ/cụm đắt giá nên dùng", "meaning_vi": "...", "example": "..."}]}'
        )
        return self.chat("You are a strict but constructive IELTS examiner.", user, max_tokens=4000)

    def generate_patterns(self, theme: str, level: str, count: int, known_patterns: list[str]) -> list[dict[str, Any]]:
        user = (
            f"Give {count} reusable English sentence patterns for the theme \"{theme}\" "
            f"(learner level {level}). Patterns must be practical for describing daily activities, "
            "work life, or usable directly in IELTS writing/speaking.\n"
            f"Avoid these existing patterns: {json.dumps(known_patterns[:100], ensure_ascii=False)}\n"
            'Return {"patterns": [{"pattern": "e.g. No sooner had I ... than ...", '
            '"use_vi": "dùng khi nào, sắc thái gì (tiếng Việt)", '
            '"examples": ["2 example sentences"], "band": "B1|B2|C1"}]}'
        )
        data = self.chat("You teach English sentence patterns.", user, temperature=0.7)
        patterns = data.get("patterns")
        if not isinstance(patterns, list):
            raise LLMError("LLM không trả về danh sách mẫu câu.")
        return [p for p in patterns if isinstance(p, dict) and str(p.get("pattern", "")).strip()]

    def check_pattern_sentence(self, pattern: str, sentence: str) -> dict[str, Any]:
        user = (
            f"The learner is practising the sentence pattern: \"{pattern}\"\n"
            f"Their sentence: \"{sentence}\"\n"
            "Check: did they use the pattern correctly? Grammar? Naturalness?\n"
            'Return {"score": 0-100, "ok": bool, "feedback_vi": "nhận xét ngắn tiếng Việt", '
            '"corrected": "câu đã sửa (hoặc nguyên văn nếu đúng)"}'
        )
        return self.chat("You check pattern practice sentences.", user, max_tokens=500)


def _extract_json(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start_candidates = [idx for idx in (raw.find("{"), raw.find("[")) if idx >= 0]
    if not start_candidates:
        raise LLMError("Không tìm thấy JSON trong phản hồi LLM.")
    start = min(start_candidates)
    end = max(raw.rfind("}"), raw.rfind("]"))
    if end <= start:
        raise LLMError("JSON từ LLM bị cắt cụt.")
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError("JSON từ LLM không hợp lệ.") from exc
