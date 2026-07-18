from epux import vocab_sources as vs
from epux.llm import _difficulty_anchor


def test_difficulty_anchor_empty_for_low_tiers():
    assert _difficulty_anchor("A1") == ""
    assert _difficulty_anchor("A2 (common everyday word)") == ""
    assert _difficulty_anchor("B1") == ""


def test_difficulty_anchor_present_for_b2_and_up():
    for hint in ("B2", "C1", "C1-C2 (advanced, impressive in IELTS)",
                 "C2 rare idiom or striking collocation that would wow an IELTS examiner"):
        anchor = _difficulty_anchor(hint)
        assert anchor
        assert "Difficulty anchor" in anchor
        for word in vs.TOO_EASY_WORDS[:5]:
            assert word in anchor


def test_difficulty_anchor_defaults_to_b2_tier_when_no_code_found():
    assert _difficulty_anchor("") != ""
    assert _difficulty_anchor("some free-text level") != ""


def test_difficulty_anchor_picks_harder_pool_for_c_tiers():
    anchor_b2 = _difficulty_anchor("B2")
    anchor_c1 = _difficulty_anchor("C1")
    assert "B2-tier" in anchor_b2
    assert "C1/C2-tier" in anchor_c1
