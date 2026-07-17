from epux.server import (
    _criteria_average,
    _normalize_grading_feedback,
    _round_half_band,
    _word_count_band_cap,
)


def test_round_half_band():
    assert _round_half_band(6.24) == 6.0
    assert _round_half_band(6.25) == 6.5
    assert _round_half_band(6.74) == 6.5
    assert _round_half_band(6.75) == 7.0


def test_criteria_average_rounds_to_half_band():
    criteria = {
        "task_response": 6.0,
        "coherence": 6.5,
        "lexical_resource": 6.0,
        "grammar": 5.5,
    }
    assert _criteria_average(criteria) == 6.0


def test_normalize_task2_feedback_adds_defaults_and_word_count():
    feedback = {
        "overall_band": 7.0,
        "criteria": {
            "task_response": 6.5,
            "coherence": 6.5,
            "lexical_resource": 7.0,
            "grammar": 6.0,
        },
        "task2_check": {},
    }
    out = _normalize_grading_feedback(feedback, task_kind="task2", word_count=249)
    assert out["overall_band"] == 6.5
    assert out["task2_check"]["word_count"] == 249
    assert out["task2_check"]["word_count_ok"] is False
    assert out["band_range"]["low"] == 6.0
    assert out["band_range"]["high"] == 7.0
    assert out["confidence"] in {"low", "medium", "high"}
    assert isinstance(out["band_up_routes"]["quick_fixes"], list)


def test_word_count_band_cap_thresholds():
    assert _word_count_band_cap(250, 250) is None
    assert _word_count_band_cap(230, 250) == 6.0  # 92% -> mild cap
    assert _word_count_band_cap(190, 250) == 5.0  # 76% -> stricter cap
    assert _word_count_band_cap(100, 250) == 4.0  # 40% -> severe cap


def test_normalize_applies_word_count_cap_and_records_limiting_factor():
    feedback = {
        "criteria": {
            "task_response": 8.0,
            "coherence": 7.5,
            "lexical_resource": 7.0,
            "grammar": 7.5,
        },
        "task2_check": {},
    }
    out = _normalize_grading_feedback(feedback, task_kind="task2", word_count=100)
    assert out["criteria"]["task_response"] == 4.0
    assert out["overall_band"] == _criteria_average(
        {"task_response": 4.0, "coherence": 7.5, "lexical_resource": 7.0, "grammar": 7.5}
    )
    assert out["band_range"]["low"] <= out["overall_band"] <= out["band_range"]["high"]
    reasons = [f["criterion"] for f in out["limiting_factors"]]
    assert "task_response" in reasons


def test_normalize_does_not_cap_when_length_is_sufficient():
    feedback = {
        "criteria": {
            "task_response": 8.0,
            "coherence": 7.5,
            "lexical_resource": 7.0,
            "grammar": 7.5,
        },
        "task2_check": {},
    }
    out = _normalize_grading_feedback(feedback, task_kind="task2", word_count=300)
    assert out["criteria"]["task_response"] == 8.0
    assert out["limiting_factors"] == []
