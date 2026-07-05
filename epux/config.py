from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "EPux"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def app_data_dir() -> Path:
    root = Path(os.environ.get("EPUX_HOME", user_data_dir(APP_NAME, appauthor=False)))
    root.mkdir(parents=True, exist_ok=True)
    return root


def app_config_dir() -> Path:
    root = Path(os.environ.get("EPUX_CONFIG_HOME", user_config_dir(APP_NAME, appauthor=False)))
    root.mkdir(parents=True, exist_ok=True)
    return root


def default_db_path() -> Path:
    return app_data_dir() / "epux.sqlite3"


def default_config_path() -> Path:
    return app_config_dir() / "config.json"


def load_env() -> None:
    """Load .env for LLM credentials.

    Search order: real env vars win, then CWD/.env, project root .env, config dir .env.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for candidate in (Path.cwd() / ".env", PROJECT_ROOT / ".env", app_config_dir() / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)


@dataclass
class LLMSettings:
    """Resolved from environment. Azure OpenAI first, plain OpenAI-compatible as fallback."""

    provider: str = ""  # "azure" | "openai" | ""
    api_key: str = ""
    endpoint: str = ""
    deployment: str = ""
    api_version: str = ""

    @classmethod
    def from_env(cls) -> "LLMSettings":
        load_env()
        azure_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
        if azure_key and azure_endpoint:
            return cls(
                provider="azure",
                api_key=azure_key,
                endpoint=azure_endpoint.rstrip("/"),
                deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o").strip(),
                api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview").strip(),
            )
        openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if openai_key:
            return cls(
                provider="openai",
                api_key=openai_key,
                endpoint=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/"),
                deployment=os.environ.get("OPENAI_MODEL", "gpt-4o").strip(),
            )
        return cls()

    @property
    def configured(self) -> bool:
        return bool(self.provider)


@dataclass
class AppConfig:
    level: str = "B2"  # trình độ hiện tại, LLM dùng để chọn độ khó từ vựng
    target_band: str = "6.5"  # band IELTS mục tiêu
    daily_new_words: int = 8
    server_port: int = 8765
    reminder_minutes: int = 45
    notify_quiet_start: str = "23:00"
    notify_quiet_end: str = "07:00"

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
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")

    def update(self, data: dict[str, Any]) -> "AppConfig":
        fields = self.__dataclass_fields__
        for key, value in data.items():
            if key not in fields:
                continue
            current = getattr(self, key)
            try:
                setattr(self, key, type(current)(value))
            except (TypeError, ValueError):
                continue
        self.save()
        return self
