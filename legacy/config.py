from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_data_dir


APP_NAME = "EPux"


def app_data_dir() -> Path:
    root = Path(os.environ.get("EPUX_HOME", user_data_dir(APP_NAME, appauthor=False)))
    root.mkdir(parents=True, exist_ok=True)
    (root / "recordings").mkdir(parents=True, exist_ok=True)
    return root


def app_config_dir() -> Path:
    root = Path(os.environ.get("EPUX_CONFIG_HOME", user_config_dir(APP_NAME, appauthor=False)))
    root.mkdir(parents=True, exist_ok=True)
    return root


def default_db_path() -> Path:
    return app_data_dir() / "epux.sqlite3"


def default_config_path() -> Path:
    return app_config_dir() / "config.json"


@dataclass
class AppConfig:
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"
    daily_new_words: int = 8
    reminder_minutes: int = 60
    notify_quiet_start: str = "22:00"
    notify_quiet_end: str = "07:00"
    recording_seconds: int = 4
    sample_rate: int = 16000
    speech_backend: str = "auto"
    vosk_model_path: str = ""
    faster_whisper_model: str = ""
    whisper_cpp_path: str = ""
    whisper_cpp_model_path: str = ""
    tts_enabled: bool = True

    @classmethod
    def load(cls, path: Path | None = None) -> "AppConfig":
        path = path or default_config_path()
        if not path.exists():
            config = cls()
            config.save(path)
            return config

        try:
            raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = path.with_suffix(".broken.json")
            path.replace(backup)
            config = cls()
            config.save(path)
            return config

        fields = cls.__dataclass_fields__
        clean = {key: value for key, value in raw.items() if key in fields}
        return cls(**clean)

    def save(self, path: Path | None = None) -> None:
        path = path or default_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def recordings_dir(self) -> Path:
        path = app_data_dir() / "recordings"
        path.mkdir(parents=True, exist_ok=True)
        return path
