from epux.server import _criteria_average, _normalize_grading_feedback, _round_half_band


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
