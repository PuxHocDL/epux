from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .audio import RecordingMetrics, record_wav
from .config import AppConfig
from .db import Database, RecordingLog
from .ollama import OllamaClient
from .speech import LocalSpeechRecognizer, TranscriptionResult


@dataclass
class PronunciationAssessment:
    target_text: str
    metrics: RecordingMetrics
    transcription: TranscriptionResult
    score: float | None
    feedback: str
    log: RecordingLog


def record_and_assess(
    *,
    db: Database,
    config: AppConfig,
    target_text: str,
    word_id: int | None = None,
    seconds: int | None = None,
    use_ollama_feedback: bool = True,
) -> PronunciationAssessment:
    metrics = record_wav(target_text, config, seconds=seconds)
    return assess_existing_recording(
        db=db,
        config=config,
        target_text=target_text,
        wav_path=metrics.wav_path,
        word_id=word_id,
        metrics=metrics,
        use_ollama_feedback=use_ollama_feedback,
    )


def assess_existing_recording(
    *,
    db: Database,
    config: AppConfig,
    target_text: str,
    wav_path: Path,
    word_id: int | None = None,
    metrics: RecordingMetrics | None = None,
    use_ollama_feedback: bool = True,
) -> PronunciationAssessment:
    recognizer = LocalSpeechRecognizer(config)
    transcription = recognizer.transcribe(wav_path)
    score = text_match_score(target_text, transcription.text) if transcription.text else None
    feedback = build_feedback(target_text, transcription, score, metrics)

    if use_ollama_feedback and transcription.text and score is not None:
        client = OllamaClient(config)
        if client.is_available():
            try:
                feedback = client.pronunciation_feedback(
                    target_text,
                    transcription.text,
                    score,
                    rms=metrics.rms if metrics else None,
                    peak=metrics.peak if metrics else None,
                    seconds=metrics.seconds if metrics else None,
                )
            except Exception:
                pass

    log = db.add_recording(
        word_id=word_id,
        target_text=target_text,
        wav_path=str(wav_path),
        transcript=transcription.text,
        score=score,
        feedback=feedback,
    )
    if metrics is None:
        metrics = RecordingMetrics(wav_path=wav_path, seconds=0, sample_rate=0, rms=0, peak=0)
    return PronunciationAssessment(target_text, metrics, transcription, score, feedback, log)


def text_match_score(target: str, transcript: str) -> float:
    target_norm = _normalize_text(target)
    transcript_norm = _normalize_text(transcript)
    if not target_norm or not transcript_norm:
        return 0.0

    target_tokens = target_norm.split()
    transcript_tokens = transcript_norm.split()
    token_score = _sequence_ratio(target_tokens, transcript_tokens)
    char_score = _sequence_ratio(list(target_norm), list(transcript_norm))
    return round((token_score * 0.65 + char_score * 0.35) * 100, 1)


def build_feedback(
    target: str,
    transcription: TranscriptionResult,
    score: float | None,
    metrics: RecordingMetrics | None = None,
) -> str:
    parts: list[str] = []
    if metrics:
        if metrics.peak < 0.05:
            parts.append("Âm lượng khá nhỏ; hãy đặt mic gần hơn hoặc nói rõ hơn.")
        elif metrics.peak > 0.98:
            parts.append("Âm lượng bị chạm đỉnh; hãy nói nhỏ hơn một chút để tránh rè.")

    if not transcription.text:
        parts.append(
            "Đã lưu bản ghi âm, nhưng chưa có transcript vì STT local chưa được cấu hình. "
            f"Backend: {transcription.backend}. {transcription.detail}"
        )
        return " ".join(parts).strip()

    parts.append(f"STT local nghe được: \"{transcription.text}\".")
    if score is not None:
        if score >= 88:
            parts.append("Khớp rất tốt với câu/từ mục tiêu.")
        elif score >= 70:
            parts.append("Khá ổn; hãy nghe lại phần khác biệt trong transcript.")
        else:
            parts.append("Còn lệch nhiều; hãy nói chậm hơn và nhấn rõ âm cuối.")

    missing = _missing_tokens(target, transcription.text)
    if missing:
        parts.append("Từ/âm có thể bị thiếu: " + ", ".join(missing[:4]) + ".")
    return " ".join(parts).strip()


def _normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9' ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _sequence_ratio(left: list[str], right: list[str]) -> float:
    from difflib import SequenceMatcher

    return SequenceMatcher(None, left, right).ratio()


def _missing_tokens(target: str, transcript: str) -> list[str]:
    target_tokens = _normalize_text(target).split()
    heard = set(_normalize_text(transcript).split())
    return [token for token in target_tokens if token not in heard]
