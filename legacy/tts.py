from __future__ import annotations


def speak(text: str) -> None:
    try:
        import pyttsx3
    except ImportError as exc:
        raise RuntimeError("Chưa cài pyttsx3. Chạy: pip install pyttsx3") from exc

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
