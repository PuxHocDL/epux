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


def test_find_passage_does_not_false_positive_on_embedded_substrings():
    # Regression test: a naive `"rest" in "deforestation"` substring check used to
    # match the "sleep" passage (keyword "rest") against "deforestation" (which
    # contains the letters "forest"). find_passage must match whole words only.
    assert vs.find_passage("deforestation")["id"] == "deforestation"
    assert vs.find_passage("ancient Egypt")["id"] == "ancient-egypt"
    assert vs.find_passage("mental health")["id"] == "mental-health"
    assert vs.find_passage("public health")["id"] == "public-health"


def test_find_passage_self_consistency_across_full_bank():
    # Every passage's own id/topic/title/keywords should route back to itself.
    mismatches = []
    for p in vs.PASSAGES:
        for probe in (p["id"].replace("-", " "), p["topic"], p["title"]):
            hit = vs.find_passage(probe)
            if hit is None or hit["id"] != p["id"]:
                mismatches.append((probe, p["id"], hit["id"] if hit else None))
    assert mismatches == []


def test_passage_bank_has_broad_topic_coverage():
    assert len(vs.PASSAGES) >= 40


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


def test_oxford_3000_baseline_is_large_and_mostly_disjoint_from_target_pools():
    baseline = vs.known_baseline_words("b2")
    assert len(baseline) > 1000
    target_pool = {w.lower() for w in vs.OXFORD_B2_WORDS + vs.OXFORD_C1_WORDS}
    # A handful of words legitimately appear in both: Oxford tags the same
    # spelling at different CEFR levels for different senses/parts of speech
    # (e.g. "novel" the A2 noun "a book" vs "novel" the C1 adjective "original").
    # A large overlap would indicate a real transcription bug; a small one is
    # expected polysemy in the source data.
    assert len(baseline & target_pool) <= 10


def test_known_baseline_empty_for_low_tiers():
    assert vs.known_baseline_words("a1") == set()
    assert vs.known_baseline_words("a2") == set()
    assert vs.known_baseline_words("b1") == set()
    assert len(vs.known_baseline_words("b2")) > 0
    assert len(vs.known_baseline_words("c1")) > 0


def test_awl_lists_are_nonempty_and_disjoint_from_too_easy():
    assert len(vs.AWL_CORE) > 100
    assert len(vs.AWL_ADVANCED) > 100
    awl_all = set(vs.AWL_CORE) | set(vs.AWL_ADVANCED)
    assert not (awl_all & set(vs.TOO_EASY_WORDS))


def test_sample_academic_words_respects_count_and_tier():
    sample = vs.sample_academic_words(8, tier="core")
    assert len(sample) == 8
    assert set(sample) <= set(vs.AWL_CORE)

    sample_mixed = vs.sample_academic_words(8, tier="mixed")
    assert set(sample_mixed) <= set(vs.AWL_CORE) | set(vs.AWL_ADVANCED)
