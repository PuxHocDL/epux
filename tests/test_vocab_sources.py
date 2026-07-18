from epux import vocab_sources as vs


def test_oxford_word_lists_are_nonempty_and_lowercase():
    assert len(vs.OXFORD_B2_WORDS) > 100
    assert len(vs.OXFORD_C1_WORDS) > 100
    assert all(w == w.lower() for w in vs.OXFORD_B2_WORDS)
    assert all(w == w.lower() for w in vs.OXFORD_C1_WORDS)


def test_too_easy_words_disjoint_from_target_pools():
    b2_c1 = set(vs.OXFORD_B2_WORDS) | set(vs.OXFORD_C1_WORDS)
    assert not (set(vs.TOO_EASY_WORDS) & b2_c1)


def test_sample_target_words_respects_count_and_tier():
    sample = vs.sample_target_words(10, tier="b2")
    assert len(sample) == 10
    assert set(sample) <= set(vs.OXFORD_B2_WORDS)

    sample_c1 = vs.sample_target_words(10, tier="c1")
    assert set(sample_c1) <= set(vs.OXFORD_C1_WORDS)

    sample_mixed = vs.sample_target_words(10, tier="mixed")
    assert set(sample_mixed) <= set(vs.OXFORD_B2_WORDS) | set(vs.OXFORD_C1_WORDS)


def test_sample_target_words_caps_at_pool_size():
    huge = vs.sample_target_words(100_000, tier="b2")
    assert len(huge) == len(vs.OXFORD_B2_WORDS)


def test_find_passage_matches_keyword_and_title():
    hit = vs.find_passage("renewable energy")
    assert hit is not None
    assert hit["id"] == "renewable-energy"

    hit2 = vs.find_passage("AI in the workplace")
    assert hit2 is not None
    assert hit2["id"] == "artificial-intelligence"


def test_find_passage_returns_none_for_unrelated_topic():
    assert vs.find_passage("underwater basket weaving in medieval Iceland") is None
    assert vs.find_passage("") is None


def test_every_passage_has_required_fields_and_attribution():
    for passage in vs.PASSAGES:
        assert passage["text"].strip()
        assert passage["source_url"].startswith("https://")
        assert "CC BY-SA" in passage["license"]
        assert len(passage["text"].split()) >= 80


def test_passage_public_excludes_full_text():
    for entry in vs.passage_public():
        assert "text" not in entry
        assert entry["source_url"].startswith("https://")
