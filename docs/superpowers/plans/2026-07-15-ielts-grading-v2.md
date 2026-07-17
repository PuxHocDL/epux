# IELTS Grading V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build IELTS Grading V2 with descriptor-based exam scoring and richer tutor guidance for Task 1 and Task 2.

**Architecture:** Keep the existing FastAPI and vanilla JS architecture. Strengthen the LLM JSON schema in `epux/llm.py`, normalize scoring metadata in `epux/server.py`, and render the richer diagnosis in `epux/web/app.js` with small CSS additions.

**Tech Stack:** Python 3.9+, FastAPI, vanilla JavaScript, CSS, Modal CLI.

## Global Constraints

- No new runtime dependency.
- Keep current response fields backwards compatible.
- Use authoritative server-side word count for Task 1 and Task 2.
- Overall band is the mean of four criteria rounded to the nearest IELTS half-band.
- Task 1 first criterion label is Task Achievement; Task 2 first criterion label is Task Response.

---

### Task 1: Server Grading Helpers

**Files:**
- Modify: `epux/server.py`
- Create: `tests/test_grading_helpers.py`

**Interfaces:**
- Produces: `_round_half_band(value: float) -> float`
- Produces: `_criteria_average(criteria: dict[str, Any]) -> float | None`
- Produces: `_normalize_grading_feedback(feedback: dict[str, Any], *, task_kind: str, word_count: int) -> dict[str, Any]`

- [ ] **Step 1: Write failing tests**

Create `tests/test_grading_helpers.py` with tests that import the helpers from `epux.server` and assert:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_grading_helpers.py -v`
Expected: import errors for missing helper functions.

- [ ] **Step 3: Implement helpers**

Add the helpers near the writing endpoints in `epux/server.py`. `_normalize_grading_feedback` should recompute `overall_band` from the four criteria when available, preserve LLM-provided richer fields, and fill defaults when they are missing.

- [ ] **Step 4: Use helpers in Task 1 and Task 2 endpoints**

Replace direct word-count patching and direct `overall_band` extraction with `_normalize_grading_feedback(...)` in `/api/task1/grade` and `/api/task2/grade`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_grading_helpers.py -v`
Expected: all tests pass.

### Task 2: LLM Prompt Schema

**Files:**
- Modify: `epux/llm.py`

**Interfaces:**
- Consumes: Existing `LLMClient.grade_task1(...)` and `LLMClient.grade_task2(...)`.
- Produces: Same methods returning richer JSON fields described in the spec.

- [ ] **Step 1: Update Task 1 prompt**

Extend the JSON schema string in `grade_task1` to request `band_range`, `confidence`, `limiting_factors`, `descriptor_match`, `why_not_higher`, `why_not_lower`, and `band_up_routes`.

- [ ] **Step 2: Update Task 2 prompt**

Apply the same schema additions in `grade_task2`, with Task Response wording and essay-type gate checks.

- [ ] **Step 3: Add explicit scoring instructions**

In both prompts, require descriptor evidence, band caps, half-band scoring, and average-based overall band. Keep all learner-facing explanations in Vietnamese.

- [ ] **Step 4: Syntax check**

Run: `python -m py_compile epux/llm.py`
Expected: exit code 0.

### Task 3: UI Rendering

**Files:**
- Modify: `epux/web/app.js`
- Modify: `epux/web/style.css`
- Modify: `epux/web/index.html`

**Interfaces:**
- Consumes: Existing `gradeResultHTML(w)`.
- Produces: Richer result HTML using optional new feedback fields.

- [ ] **Step 1: Add static check**

Run before editing:
`Select-String -LiteralPath epux\web\app.js -Pattern 'Đường lên band tiếp theo' -Quiet`
Expected: false.

- [ ] **Step 2: Update criterion labels**

Change `gradeResultHTML` so it detects `w.kind === "task1"` and labels the first criterion `Task Achievement`; otherwise `Task Response`.

- [ ] **Step 3: Render richer diagnosis**

Add sections for band range/confidence, limiting factors, descriptor match, why-not-higher, why-not-lower, and grouped band-up routes. Render only sections whose data exists.

- [ ] **Step 4: Add CSS**

Add compact styles for `.band-meta`, `.diagnosis-grid`, `.route-group`, `.descriptor-evidence`, and `.limiting-list`.

- [ ] **Step 5: Bump cache-buster**

Change `epux/web/index.html` from the current app JS query string to `app.js?v=20260715-grading-v2`.

- [ ] **Step 6: Static verification**

Run:
`Select-String -LiteralPath epux\web\app.js -Pattern 'Đường lên band tiếp theo|Vì sao chưa lên band cao hơn|Task Achievement'`
Expected: all three strings are found.

### Task 4: End-to-End Verification And Deploy

**Files:**
- No source edits unless verification exposes a bug.

**Interfaces:**
- Consumes: Modal profile `modal_8`.
- Produces: Redeployed app at `https://pux2--m-gpux-host-epux-web.modal.run`.

- [ ] **Step 1: Run Python tests**

Run: `pytest tests/test_grading_helpers.py -v`
Expected: all tests pass.

- [ ] **Step 2: Run syntax checks**

Run: `python -m py_compile epux/server.py epux/llm.py`
Expected: exit code 0.

- [ ] **Step 3: Deploy**

Run with UTF-8 output:
`$env:MODAL_PROFILE='modal_8'; $env:PYTHONIOENCODING='utf-8'; [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(); modal deploy modal_runner.py`
Expected: Modal deploy succeeds and returns the production URL.

- [ ] **Step 4: Verify production assets**

Check production HTML contains `app.js?v=20260715-grading-v2` and production JS contains `Đường lên band tiếp theo`.

