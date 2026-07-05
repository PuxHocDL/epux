from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class ReviewResult:
    ease: float
    interval_days: int
    repetitions: int
    lapses: int
    due_at: datetime


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_dt(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def schedule_review(
    rating: int,
    *,
    ease: float,
    interval_days: int,
    repetitions: int,
    lapses: int,
    now: datetime | None = None,
) -> ReviewResult:
    """Small SM-2 inspired scheduler. Rating range: 0=again, 1=hard, 2=good, 3=easy."""
    now = now or utc_now()
    rating = max(0, min(3, rating))

    if rating == 0:
        return ReviewResult(
            ease=max(1.3, ease - 0.2),
            interval_days=0,
            repetitions=0,
            lapses=lapses + 1,
            due_at=now + timedelta(minutes=15),
        )

    if rating == 1:
        next_interval = max(1, round(max(1, interval_days) * 1.2))
        next_ease = max(1.3, ease - 0.15)
    elif rating == 2:
        next_interval = 1 if repetitions == 0 else max(2, round(max(1, interval_days) * ease))
        next_ease = ease
    else:
        next_interval = 3 if repetitions == 0 else max(4, round(max(1, interval_days) * (ease + 0.25)))
        next_ease = min(3.0, ease + 0.15)

    return ReviewResult(
        ease=next_ease,
        interval_days=next_interval,
        repetitions=repetitions + 1,
        lapses=lapses,
        due_at=now + timedelta(days=next_interval),
    )
