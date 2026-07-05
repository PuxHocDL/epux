from __future__ import annotations

import json
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig


@dataclass
class TranscriptionResult:
    text: str
    backend: str
    detail: str = ""


class LocalSpeechRecognizer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def transcribe(self, wav_path: str | Path) -> TranscriptionResult:
        wav_path = Path(wav_path)
        backend = self.config.speech_backend.lower().strip() or "auto"

        errors: list[str] = []
        if backend in {"auto", "vosk"}:
            result = self._try_vosk(wav_path)
            if result.text or backend == "vosk":
                return result
            if result.detail:
                errors.append(result.detail)

        if backend in {"auto", "faster-whisper", "faster_whisper"}:
            result = self._try_faster_whisper(wav_path)
            if result.text or backend in {"faster-whisper", "faster_whisper"}:
                return result
            if result.detail:
                errors.append(result.detail)

        if backend in {"auto", "whisper.cpp", "whisper_cpp"}:
            result = self._try_whisper_cpp(wav_path)
            if result.text or backend in {"whisper.cpp", "whisper_cpp"}:
                return result
            if result.detail:
                errors.append(result.detail)

        if backend in {"auto", "pocketsphinx", "sphinx"}:
            result = self._try_pocketsphinx(wav_path)
            if result.text or backend in {"pocketsphinx", "sphinx"}:
                return result
            if result.detail:
                errors.append(result.detail)

        detail = " | ".join(errors) if errors else "Chưa cấu hình backend STT local."
        return TranscriptionResult("", "none", detail)

    def _try_vosk(self, wav_path: Path) -> TranscriptionResult:
        if not self.config.vosk_model_path:
            return TranscriptionResult("", "vosk", "Chưa đặt vosk_model_path trong config.")
        model_path = Path(self.config.vosk_model_path)
        if not model_path.exists():
            return TranscriptionResult("", "vosk", f"Không thấy Vosk model: {model_path}")

        try:
            from vosk import KaldiRecognizer, Model
        except ImportError:
            return TranscriptionResult("", "vosk", "Chưa cài vosk.")

        try:
            with wave.open(str(wav_path), "rb") as wav:
                if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                    return TranscriptionResult("", "vosk", "Vosk cần WAV mono 16-bit.")
                recognizer = KaldiRecognizer(Model(str(model_path)), wav.getframerate())
                chunks: list[str] = []
                while True:
                    data = wav.readframes(4000)
                    if not data:
                        break
                    if recognizer.AcceptWaveform(data):
                        part = json.loads(recognizer.Result()).get("text", "")
                        if part:
                            chunks.append(part)
                final = json.loads(recognizer.FinalResult()).get("text", "")
                if final:
                    chunks.append(final)
            return TranscriptionResult(" ".join(chunks).strip(), "vosk")
        except Exception as exc:
            return TranscriptionResult("", "vosk", str(exc))

    def _try_faster_whisper(self, wav_path: Path) -> TranscriptionResult:
        if not self.config.faster_whisper_model:
            return TranscriptionResult("", "faster-whisper", "Chưa đặt faster_whisper_model trong config.")

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return TranscriptionResult("", "faster-whisper", "Chưa cài faster-whisper.")

        try:
            model = WhisperModel(self.config.faster_whisper_model, device="cpu", compute_type="int8")
            segments, _info = model.transcribe(str(wav_path), language="en", beam_size=3)
            text = " ".join(segment.text.strip() for segment in segments).strip()
            return TranscriptionResult(text, "faster-whisper")
        except Exception as exc:
            return TranscriptionResult("", "faster-whisper", str(exc))

    def _try_whisper_cpp(self, wav_path: Path) -> TranscriptionResult:
        exe = self.config.whisper_cpp_path
        model = self.config.whisper_cpp_model_path
        if not exe or not model:
            return TranscriptionResult("", "whisper.cpp", "Chưa đặt whisper_cpp_path và whisper_cpp_model_path.")
        if not Path(exe).exists():
            return TranscriptionResult("", "whisper.cpp", f"Không thấy whisper.cpp executable: {exe}")
        if not Path(model).exists():
            return TranscriptionResult("", "whisper.cpp", f"Không thấy whisper.cpp model: {model}")

        with tempfile.TemporaryDirectory(prefix="epux_whisper_") as tmp:
            out_base = Path(tmp) / "transcript"
            command = [
                exe,
                "-m",
                model,
                "-f",
                str(wav_path),
                "-l",
                "en",
                "-otxt",
                "-of",
                str(out_base),
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, text=True, timeout=180)
                text_path = out_base.with_suffix(".txt")
                if text_path.exists():
                    return TranscriptionResult(text_path.read_text(encoding="utf-8").strip(), "whisper.cpp")
                return TranscriptionResult("", "whisper.cpp", "whisper.cpp không tạo file .txt.")
            except Exception as exc:
                return TranscriptionResult("", "whisper.cpp", str(exc))

    def _try_pocketsphinx(self, wav_path: Path) -> TranscriptionResult:
        try:
            import speech_recognition as sr
        except ImportError:
            return TranscriptionResult("", "pocketsphinx", "Chưa cài SpeechRecognition.")

        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(str(wav_path)) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_sphinx(audio, language="en-US")
            return TranscriptionResult(text.strip(), "pocketsphinx")
        except Exception as exc:
            return TranscriptionResult("", "pocketsphinx", str(exc))
