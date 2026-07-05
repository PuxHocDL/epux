from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import requests

from .config import AppConfig


@dataclass
class OllamaWord:
    term: str
    meaning: str
    example: str
    notes: str = ""
    tags: str = "ollama"


class OllamaClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def is_available(self, timeout: float = 1.5) -> bool:
        try:
            response = requests.get(f"{self.config.ollama_url}/api/tags", timeout=timeout)
            return response.ok
        except requests.RequestException:
            return False

    def generate(self, prompt: str, *, system: str = "", timeout: float = 120.0) -> str:
        payload: dict[str, Any] = {
            "model": self.config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.35},
        }
        if system:
            payload["system"] = system

        response = requests.post(
            f"{self.config.ollama_url}/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        return str(response.json().get("response", "")).strip()

    def enrich_word(self, term: str) -> OllamaWord:
        system = (
            "You are a concise English-Vietnamese vocabulary coach. "
            "Return JSON only. Do not use markdown."
        )
        prompt = (
            "Create a compact Vietnamese learning card for this English word or phrase: "
            f"{term!r}.\n"
            "Return exactly this JSON shape: "
            '{"term":"...","meaning":"...","example":"...","notes":"...","tags":"..."}'
        )
        raw = self.generate(prompt, system=system)
        data = _extract_json_object(raw)
        return OllamaWord(
            term=str(data.get("term") or term).strip(),
            meaning=str(data.get("meaning") or "").strip(),
            example=str(data.get("example") or "").strip(),
            notes=str(data.get("notes") or "").strip(),
            tags=str(data.get("tags") or "ollama").strip(),
        )

    def suggest_words(self, topic: str, level: str = "B1", count: int = 8) -> list[OllamaWord]:
        system = (
            "You are a concise English-Vietnamese vocabulary coach. "
            "Return JSON only. Do not use markdown."
        )
        prompt = (
            f"Suggest {count} useful English vocabulary items for a Vietnamese learner.\n"
            f"Topic: {topic or 'daily life'}\n"
            f"Level: {level}\n"
            "Return a JSON array. Every item must have: term, meaning, example, notes, tags."
        )
        raw = self.generate(prompt, system=system)
        data = _extract_json_array(raw)
        words: list[OllamaWord] = []
        for item in data[:count]:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term") or "").strip()
            if not term:
                continue
            words.append(
                OllamaWord(
                    term=term,
                    meaning=str(item.get("meaning") or "").strip(),
                    example=str(item.get("example") or "").strip(),
                    notes=str(item.get("notes") or "").strip(),
                    tags=str(item.get("tags") or topic or "ollama").strip(),
                )
            )
        return words

    def suggest_prefix(self, prefix: str, level: str = "B1", count: int = 5) -> list[OllamaWord]:
        prefix = prefix.strip()
        if len(prefix) < 2:
            return []
        system = (
            "You are a concise English-Vietnamese vocabulary autocomplete engine. "
            "Return JSON only. Do not use markdown."
        )
        prompt = (
            f"The learner typed this partial English input: {prefix!r}\n"
            f"Level: {level}\n"
            f"Suggest up to {count} useful English words or phrases that start with it, "
            "or are the most likely completion if it is a partial phrase.\n"
            "The meaning and notes must be in Vietnamese. "
            "Return a JSON array. Every item must have: term, meaning, example, notes, tags."
        )
        raw = self.generate(prompt, system=system, timeout=45.0)
        data = _extract_json_array(raw)
        words: list[OllamaWord] = []
        seen: set[str] = set()
        for item in data[:count]:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term") or "").strip()
            if not term or term.lower() in seen:
                continue
            seen.add(term.lower())
            words.append(
                OllamaWord(
                    term=term,
                    meaning=_stringify(item.get("meaning") or "").strip(),
                    example=_stringify(item.get("example") or "").strip(),
                    notes=_stringify(item.get("notes") or "AI autocomplete").strip(),
                    tags=_stringify(item.get("tags") or "ai-suggest").strip(),
                )
            )
        return words

    def pronunciation_feedback(
        self,
        target: str,
        transcript: str,
        score: float,
        *,
        rms: float | None = None,
        peak: float | None = None,
        seconds: float | None = None,
    ) -> str:
        if not transcript.strip():
            return "Chưa có transcript từ STT local, nên EPux chỉ lưu bản ghi âm để bạn nghe lại."

        system = (
            "You are a practical pronunciation coach for Vietnamese speakers learning English. "
            "You evaluate from local speech-to-text output and simple local audio metrics. "
            "Return short Vietnamese feedback. No markdown table."
        )
        prompt = (
            f"Target text: {target}\n"
            f"Local STT transcript: {transcript}\n"
            f"Text match score: {score:.0f}/100\n"
            f"Audio RMS: {rms if rms is not None else 'unknown'}\n"
            f"Audio peak: {peak if peak is not None else 'unknown'}\n"
            f"Recording seconds: {seconds if seconds is not None else 'unknown'}\n"
            "Give a local AI pronunciation assessment in Vietnamese: overall score, likely missing or changed sounds, "
            "one focused drill, and one next attempt goal. Mention uncertainty if STT may be wrong."
        )
        return self.generate(prompt, system=system, timeout=60.0)


def _extract_json_object(raw: str) -> dict[str, Any]:
    data = _extract_json(raw)
    if isinstance(data, dict):
        return data
    raise ValueError("Ollama không trả về JSON object hợp lệ.")


def _extract_json_array(raw: str) -> list[Any]:
    data = _extract_json(raw)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("suggestions", "words", "items", "results", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    raise ValueError("Ollama không trả về JSON array hợp lệ.")


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
        raise ValueError("Không tìm thấy JSON trong phản hồi Ollama.")
    start = min(start_candidates)
    end = max(raw.rfind("}"), raw.rfind("]"))
    if end <= start:
        raise ValueError("JSON từ Ollama bị thiếu phần kết thúc.")
    return json.loads(raw[start : end + 1])


def _stringify(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
