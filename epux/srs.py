from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Lịch ôn dựa trên đường cong lãng quên R(t) = 0.9^(t / S):
# S (stability, tính bằng ngày) là khoảng thời gian mà xác suất còn nhớ rớt xuống 90%,
# và cũng chính là interval tới lần ôn kế tiếp. Mỗi lần nhớ thành công S tăng theo ease;
# quên thì S co lại và thẻ quay về pha "learning" với các bước ngắn (phút/giờ) —
# phù hợp người online thường xuyên.

LEARNING_STEPS_MINUTES = [10, 60, 480]  # 10 phút -> 1 giờ -> 8 giờ
GRADUATE_STABILITY = 1.0  # ngày, sau khi qua hết learning steps
EASY_GRADUATE_STABILITY = 2.5
MIN_EASE = 1.3
MAX_EASE = 3.0
MAX_STABILITY = 365.0


@dataclass
class ReviewResult:
    ease: float
    interval_days: float
    repetitions: int
    lapses: int
    stability: float
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


def retention(stability_days: float, elapsed_days: float) -> float:
    """Xác suất còn nhớ sau elapsed_days theo đường cong lãng quên."""
    if stability_days <= 0:
        return 0.0
    return math.pow(0.9, max(0.0, elapsed_days) / stability_days)


def schedule_review(
    rating: int,
    *,
    ease: float,
    repetitions: int,
    lapses: int,
    stability: float,
    now: datetime | None = None,
    fuzz: bool = True,
) -> ReviewResult:
    """Rating: 0=quên, 1=khó, 2=ổn, 3=dễ."""
    now = now or utc_now()
    rating = max(0, min(3, rating))
    ease = min(MAX_EASE, max(MIN_EASE, ease or 2.5))
    stability = max(0.001, stability or 0.001)
    in_learning = repetitions < len(LEARNING_STEPS_MINUTES)

    if rating == 0:
        # Quên: về đầu learning, stability co lại nhưng không mất sạch (residual memory).
        new_stability = max(0.007, stability * 0.4)
        minutes = LEARNING_STEPS_MINUTES[0]
        return ReviewResult(
            ease=max(MIN_EASE, ease - 0.2),
            interval_days=minutes / 1440,
            repetitions=0,
            lapses=lapses + 1,
            stability=new_stability,
            due_at=now + timedelta(minutes=minutes),
        )

    if in_learning:
        if rating == 3:
            interval_days = _fuzzed(EASY_GRADUATE_STABILITY, fuzz)
            return ReviewResult(
                ease=min(MAX_EASE, ease + 0.15),
                interval_days=interval_days,
                repetitions=len(LEARNING_STEPS_MINUTES) + 1,
                lapses=lapses,
                stability=EASY_GRADUATE_STABILITY,
                due_at=now + timedelta(days=interval_days),
            )
        step = repetitions if rating == 1 else repetitions + 1
        if step >= len(LEARNING_STEPS_MINUTES):
            stability = max(stability, GRADUATE_STABILITY)
            interval_days = _fuzzed(stability, fuzz)
            return ReviewResult(
                ease=ease,
                interval_days=interval_days,
                repetitions=step + 1,
                lapses=lapses,
                stability=stability,
                due_at=now + timedelta(days=interval_days),
            )
        minutes = LEARNING_STEPS_MINUTES[step]
        return ReviewResult(
            ease=max(MIN_EASE, ease - 0.15) if rating == 1 else ease,
            interval_days=minutes / 1440,
            repetitions=step,
            lapses=lapses,
            stability=stability,
            due_at=now + timedelta(minutes=minutes),
        )

    # Pha review: stability tăng theo ease.
    if rating == 1:
        new_ease = max(MIN_EASE, ease - 0.15)
        new_stability = stability * 1.2
    elif rating == 2:
        new_ease = ease
        new_stability = stability * ease
    else:
        new_ease = min(MAX_EASE, ease + 0.15)
        new_stability = stability * ease * 1.35

    new_stability = min(MAX_STABILITY, max(GRADUATE_STABILITY, new_stability))
    interval_days = _fuzzed(new_stability, fuzz)
    return ReviewResult(
        ease=new_ease,
        interval_days=interval_days,
        repetitions=repetitions + 1,
        lapses=lapses,
        stability=new_stability,
        due_at=now + timedelta(days=interval_days),
    )


def preview_intervals(*, ease: float, repetitions: int, lapses: int, stability: float) -> dict[int, str]:
    """Nhãn hiển thị trên 4 nút chấm của màn ôn tập."""
    labels: dict[int, str] = {}
    for rating in range(4):
        result = schedule_review(
            rating,
            ease=ease,
            repetitions=repetitions,
            lapses=lapses,
            stability=stability,
            fuzz=False,
        )
        labels[rating] = format_interval(result.interval_days)
    return labels


def format_interval(days: float) -> str:
    minutes = days * 1440
    if minutes < 60:
        return f"{max(1, round(minutes))} phút"
    if minutes < 1440:
        hours = minutes / 60
        return f"{hours:.0f} giờ" if hours >= 3 else f"{hours:.1f} giờ"
    if days < 30:
        return f"{days:.0f} ngày" if days >= 10 else f"{days:.1f} ngày"
    return f"{days / 30:.1f} tháng"


def _fuzzed(days: float, fuzz: bool) -> float:
    if not fuzz or days < 1:
        return days
    return days * random.uniform(0.95, 1.05)
