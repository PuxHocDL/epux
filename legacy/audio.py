from __future__ import annotations

import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import AppConfig


@dataclass
class RecordingMetrics:
    wav_path: Path
    seconds: float
    sample_rate: int
    rms: float
    peak: float


def record_wav(target_text: str, config: AppConfig, *, seconds: int | None = None) -> RecordingMetrics:
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise RuntimeError("Thiếu thư viện thu âm. Chạy: pip install sounddevice numpy") from exc

    sample_rate = int(config.sample_rate)
    duration = int(seconds or config.recording_seconds)
    filename = _safe_filename(target_text) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".wav"
    wav_path = config.recordings_dir() / filename

    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()

    audio = audio.reshape(-1)
    clipped = np.clip(audio, -1.0, 1.0)
    int_audio = (clipped * 32767).astype(np.int16)

    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(int_audio.tobytes())

    rms = float(np.sqrt(np.mean(np.square(clipped)))) if clipped.size else 0.0
    peak = float(np.max(np.abs(clipped))) if clipped.size else 0.0
    return RecordingMetrics(
        wav_path=wav_path,
        seconds=duration,
        sample_rate=sample_rate,
        rms=rms,
        peak=peak,
    )


def play_wav(path: str | Path) -> None:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    if _is_windows():
        import winsound

        winsound.PlaySound(str(path), winsound.SND_FILENAME)
        return

    raise RuntimeError("Playback tự động hiện chỉ hỗ trợ Windows qua winsound.")


def _safe_filename(value: str) -> str:
    clean = "".join(ch if ch.isalnum() else "_" for ch in value.strip().lower())
    clean = "_".join(part for part in clean.split("_") if part)
    return (clean or "recording")[:48]


def _is_windows() -> bool:
    import sys

    return sys.platform == "win32"
