from __future__ import annotations

import json
import re
from typing import Any

import requests

from . import descriptors, task1, task2
from .config import LLMSettings


class LLMError(RuntimeError):
    pass


# Azure GPT-4o occasionally emits Vietnamese text as UTF-8 bytes re-decoded as Latin-1
# (a mojibake pattern common in its Vietnamese web-crawl training data) — e.g. "giữa" comes
# back as "giá»«a". Runs of 2+ consecutive Latin-1-supplement chars that themselves decode
# cleanly as UTF-8 are almost certainly this artifact, so we repair them defensively.
_MOJIBAKE_RUN = re.compile(f"[{chr(0x80)}-{chr(0xFF)}]{{2,}}")


def _fix_mojibake_run(match: "re.Match[str]") -> str:
    run = match.group(0)
    try:
        fixed = run.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return run
    if len(fixed) >= len(run):
        return run
    if any(ord(c) < 0x20 or 0x7F <= ord(c) <= 0x9F for c in fixed):
        return run
    return fixed


def _repair_mojibake(data: Any) -> Any:
    if isinstance(data, str):
        return _MOJIBAKE_RUN.sub(_fix_mojibake_run, data) if data else data
    if isinstance(data, list):
        return [_repair_mojibake(v) for v in data]
    if isinstance(data, dict):
        return {k: _repair_mojibake(v) for k, v in data.items()}
    return data


SYSTEM_BASE = (
    "You are the AI engine of EPux, a personal vocabulary & IELTS writing coach for one Vietnamese "
    "learner who works in IT. You combine three roles: a senior IELTS examiner who has marked "
    "thousands of scripts, a lexicographer who cares about collocation, register and nuance, and a "
    "patient tutor who knows the typical errors of Vietnamese learners (articles, verb tense, "
    "plural -s, prepositions, word-for-word translation from Vietnamese).\n"
    "Principles: (1) Reason deeply before answering â€” analyse first, conclude after; never give "
    "generic advice that could apply to any learner or any text. (2) Ground every judgement in "
    "concrete evidence, quoting the learner's own words where possible. (3) Teach precise, natural, "
    "high-value English; avoid memorised 'IELTS words' and clichÃ©s such as 'delve into', "
    "'a plethora of', 'in this day and age', 'every coin has two sides', 'last but not least'.\n"
    "All explanations, meanings and feedback aimed at the learner must be in Vietnamese (concise, "
    "thÃ¢n thiá»‡n, xÆ°ng 'báº¡n'); English is used only for the target-language material itself (terms, "
    "examples, essays). Always return valid JSON only, no markdown fences, no commentary."
)

SCORING_METHOD = (
    "Scoring method — follow exactly, per criterion:\n"
    "1. Read the verbatim band descriptor bullets given above for this criterion.\n"
    "2. Find the ONE band whose bullets the text matches most closely as a whole, not just one lucky "
    "phrase.\n"
    "3. Check the bullets of the band directly ABOVE: identify the specific bullet the text fails to "
    "meet, and use it as a 'why not higher' reason. If the text meets that band's bullets too, move up "
    "and repeat until you find the band it fails to fully meet.\n"
    "4. Check the bullets of the band directly BELOW: confirm the text clearly clears them, and use "
    "that as a 'why not lower' reason.\n"
    "5. If the text sits cleanly between two neighbouring bands (meets some but not all of the higher "
    "band's bullets), award the half band between them.\n"
    "Known failure modes in LLM-based essay grading — actively resist them:\n"
    "- Do not default to band 6-6.5 out of politeness. LLM graders are documented to over-rate weak "
    "writing; if the text actually matches the band 4-5 bullets (thin/repetitive ideas, only basic "
    "vocabulary, frequent errors, little real organisation), say so plainly instead of rounding up.\n"
    "- Do not reward length, formal-sounding openers, or fluent-looking sentences on their own — match "
    "against what the bullets actually claim (precision, range, accuracy, development), not surface "
    "polish. A long, confident-sounding sentence with a wrong collocation or unsupported claim is still "
    "a weakness, not a strength.\n"
    "- Judge Lexical Resource on precision and collocation, not on rare/impressive-looking words; judge "
    "Grammar on range AND accuracy together, not accuracy alone (a text of only simple, correct "
    "sentences cannot reach band 7+ on Grammar, per the band 7 bullet requiring complex structures).\n"
    "- If the essay reads as a memorised generic template with no real connection to the specifics of "
    "THIS task, or is essentially copied from a model/sample answer, flag it in the relevant _check "
    "block (see 'Band 0' rule below) instead of scoring it as the learner's own developed response.\n"
    "Being strict is not the same as being harsh: do not manufacture faults to avoid seeming lenient. "
    "If the text genuinely matches a high band's bullets (clear position throughout, logical "
    "organisation, a wide range of accurate structures, precise vocabulary), award that band "
    "confidently. A trait a band's own bullets explicitly allow — e.g. band 7 Task Response permits 'a "
    "tendency to over-generalise and/or supporting ideas may lack focus' — is NOT a valid reason to "
    "mark below that band; only weigh it against reaching band 8+, where that allowance disappears.\n"
)

GRADING_V2_SCHEMA = (
    'Also return these IELTS Grading V2 fields: '
    '"band_range": {"low": number, "high": number, "reason_vi": "vì sao khoảng điểm này hợp lý"}, '
    '"confidence": "low|medium|high", '
    '"limiting_factors": [{"criterion": "task_response|coherence|lexical_resource|grammar", '
    '"issue_vi": "yếu tố đang chặn band", "evidence": "trích từ bài hoặc mô tả bằng chứng", '
    '"band_cap": number_or_null}], '
    '"descriptor_match": {'
    '"task_response": {"band": number, "matched_features_vi": ["đặc điểm descriptor bài đã khớp"], '
    '"missing_features_vi": ["đặc điểm còn thiếu để lên band kế"], "evidence": ["trích dẫn cụ thể"]}, '
    '"coherence": {"band": number, "matched_features_vi": [], "missing_features_vi": [], "evidence": []}, '
    '"lexical_resource": {"band": number, "matched_features_vi": [], "missing_features_vi": [], "evidence": []}, '
    '"grammar": {"band": number, "matched_features_vi": [], "missing_features_vi": [], "evidence": []}}, '
    '"why_not_higher": ["3-5 lý do cụ thể vì sao chưa lên band kế tiếp"], '
    '"why_not_lower": ["2-4 lý do cụ thể vì sao vẫn giữ được band hiện tại"], '
    '"band_up_routes": {"quick_fixes": ["3-5 sửa nhanh ngay trong bài này"], '
    '"next_practice": ["3-5 bài tập/việc luyện cho bài sau"], '
    '"language_upgrades": ["4-6 mẫu câu, collocation hoặc cách diễn đạt nên học"], '
    '"strategy": ["2-4 chiến lược riêng cho dạng đề này"], '
    '"avoid_next_time": ["2-4 lỗi cần tránh lần sau"]}. '
    "For each criterion, first match the learner's evidence to the public IELTS descriptor features, "
    "then decide the band. Explain why the answer is not 0.5 higher and not 0.5 lower. "
    "If a task-specific failure creates a band cap, state it in limiting_factors. "
    "Make band_up_routes generous and practical, not just 2 generic tips. "
)


class LLMClient:
    def __init__(self, settings: LLMSettings | None = None) -> None:
        self.settings = settings or LLMSettings.from_env()

    @property
    def configured(self) -> bool:
        return self.settings.configured

    def status(self) -> dict[str, Any]:
        s = self.settings
        return {
            "configured": s.configured,
            "provider": s.provider,
            "endpoint": s.endpoint,
            "model": s.deployment,
        }

    def ping(self) -> dict[str, Any]:
        try:
            reply = self.chat("Reply with JSON.", 'Return {"ok": true}', max_tokens=20)
            return {"ok": bool(reply.get("ok")), "error": ""}
        except LLMError as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------------ core

    def _request(self, messages: list[dict[str, str]], *, temperature: float, max_tokens: int) -> str:
        s = self.settings
        if not s.configured:
            raise LLMError("ChÆ°a cáº¥u hÃ¬nh LLM. Kiá»ƒm tra file .env (AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT...).")
        if s.provider == "azure":
            url = f"{s.endpoint}/openai/deployments/{s.deployment}/chat/completions?api-version={s.api_version}"
            headers = {"api-key": s.api_key, "Content-Type": "application/json"}
        else:
            url = f"{s.endpoint}/chat/completions"
            headers = {"Authorization": f"Bearer {s.api_key}", "Content-Type": "application/json"}
        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        if s.provider != "azure":
            payload["model"] = s.deployment
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
        except requests.RequestException as exc:
            raise LLMError(f"Không gọi được LLM: {exc}") from exc
        if response.status_code == 401:
            raise LLMError("LLM tá»« chá»‘i API key (401). Kiá»ƒm tra láº¡i .env.")
        if not response.ok:
            detail = ""
            try:
                detail = response.json().get("error", {}).get("message", "")
            except Exception:
                detail = response.text[:200]
            raise LLMError(f"LLM tráº£ lá»—i {response.status_code}: {detail}")
        data = response.json()
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError) as exc:
            raise LLMError("Pháº£n há»“i LLM khÃ´ng Ä‘Ãºng Ä‘á»‹nh dáº¡ng.") from exc

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.4,
        max_tokens: int = 3000,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": f"{SYSTEM_BASE}\n\n{system}"},
            {"role": "user", "content": user},
        ]
        raw = self._request(messages, temperature=temperature, max_tokens=max_tokens)
        data = _extract_json(raw)
        if not isinstance(data, dict):
            raise LLMError("LLM không trả về JSON object.")
        return _repair_mojibake(data)

    # -------------------------------------------------------------- features

    def suggest_topics(self, known_topics: list[str], level: str, count: int = 8) -> list[dict[str, Any]]:
        user = (
            f"Suggest {count} vocabulary topics that appear often in the IELTS and TOEIC exams and are valuable "
            f"for a {level} learner working in IT.\n"
            f"Topics the learner already has (avoid duplicates AND near-duplicates): {json.dumps(known_topics, ensure_ascii=False)}\n"
            "Make the set genuinely varied: a few classic IELTS macro-themes still missing from the "
            "learner's list (environment, education, health, urbanisation, media, crime, culture...), "
            "a few sharper sub-angles of big themes (e.g. 'renewable energy' or 'urban housing' instead "
            "of yet another generic 'environment'), and 1-2 tied to daily life / IT work.\n"
            'Return {"topics": [{"name": "English topic name", "name_vi": "tÃªn tiáº¿ng Viá»‡t", '
            '"description_vi": "1 câu: vì sao chủ đề này hay gặp trong IELTS", '
            '"sample_words": ["3-4 từ ví dụ"]}]}'
        )
        data = self.chat("You curate IELTS vocabulary topics.", user, temperature=0.7)
        topics = data.get("topics")
        if not isinstance(topics, list):
            raise LLMError("LLM không trả về danh sách chủ đề.")
        return [t for t in topics if isinstance(t, dict) and str(t.get("name", "")).strip()]

    def generate_vocab(
        self,
        topic: str,
        level: str,
        count: int,
        known_terms: list[str],
        band_hint: str = "",
        context: str = "",
    ) -> list[dict[str, Any]]:
        hint = f"All items must be {band_hint} difficulty.\n" if band_hint else (
            f"Difficulty: centered on {level}, with 1-2 easier items and 1-2 more advanced items.\n"
        )
        context_str = f"preparing for the {context} exam" if context else "preparing for both IELTS and TOEIC exams"
        user = (
            f"Create {count} English vocabulary cards on the topic \"{topic}\" for a Vietnamese learner "
            f"{context_str} (target level {level}).\n"
            + hint
            + "Work in two steps (think silently, output only the final JSON):\n"
            f"STEP 1 â€” brainstorm {count} DIFFERENT sub-aspects of the topic (causes, effects, people, "
            "places, actions, feelings, problems, solutions, everyday situations, policy, tech angle...). "
            "One card per sub-aspect, so the set never clusters around a single idea.\n"
            "STEP 2 â€” for each sub-aspect pick the single most useful item, keeping this mix across the set:\n"
            "- roughly 40% collocations or fixed phrases (verb+noun, adj+noun...) â€” the strongest "
            "band-score currency in IELTS and TOEIC;\n"
            "- 1-2 phrasal verbs and 1 idiom that natives actually use (skip if count < 6);\n"
            "- the rest single words spread across noun / verb / adjective / adverb â€” not all nouns;\n"
            "- at least 2 items suited to formal writing (Task 2) and 2 to everyday speaking or business contexts (TOEIC).\n"
            "Choose precise, topic-specific items that real examiners reward â€” not vague words like "
            "'important', 'good', 'problem', and none of the banned clichÃ©s.\n"
            f"NEVER include these terms the learner already knows: {json.dumps(sorted(known_terms)[:400], ensure_ascii=False)}\n"
            'Return {"words": [{"term": "...", "ipa": "/.../", '
            '"pos": "noun|verb|adj|adv|phrase|phrasal verb|idiom", '
            '"meaning_vi": "nghĩa tiếng Việt ngắn gọn", '
            '"example": "natural English sentence showing the term in its typical context", '
            '"example_vi": "dịch câu ví dụ", "collocations": ["2-3 collocations"], '
            '"usage_note_vi": "1-2 câu: sắc thái/register, khác gì từ đồng nghĩa gần nhất, lỗi người Việt hay mắc khi dùng từ này", '
            '"band": "A2|B1|B2|C1|C2", "is_gem": true nếu là từ/idiom đắt giá hiếm gặp giúp ăn điểm, '
            '"is_toeic": true nếu từ này thường gặp trong TOEIC, "toeic_part": "Tên phần thi TOEIC thường gặp (vd: Part 5, Part 7) hoặc để trống"}]}'
        )
        data = self.chat("You create high-quality bilingual vocabulary cards.", user, temperature=0.85, max_tokens=4000)
        words = data.get("words")
        if not isinstance(words, list):
            raise LLMError("LLM không trả về danh sách từ.")
        seen = {t.lower() for t in known_terms}
        clean: list[dict[str, Any]] = []
        for item in words:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term", "")).strip()
            if not term or term.lower() in seen:
                continue
            seen.add(term.lower())
            clean.append(item)
        return clean

    def enrich_word(self, term: str, level: str) -> dict[str, Any]:
        user = (
            f"Create one complete vocabulary card for: \"{term}\" (learner level {level}, preparing for IELTS & TOEIC).\n"
            "Make the example show the term in its most typical, natural context (not a made-up "
            "textbook sentence), and pick collocations the learner can lift straight into writing or business communication.\n"
            'Return {"term": "...", "ipa": "/.../", "pos": "...", "meaning_vi": "...", '
            '"example": "...", "example_vi": "...", "collocations": ["..."], '
            '"usage_note_vi": "1-2 câu: sắc thái/register, khác gì từ đồng nghĩa gần nhất, lỗi người Việt hay mắc khi dùng từ này", '
            '"band": "A2|B1|B2|C1|C2", "is_gem": bool, "topic": "most fitting IELTS/TOEIC topic, in English", '
            '"is_toeic": true/false, "toeic_part": "TÃªn pháº§n thi TOEIC hoáº·c Ä‘á»ƒ trá»‘ng"}'
        )
        return self.chat("You create high-quality bilingual vocabulary cards.", user)

    def writing_prompt(self, kind: str, level: str, target_band: str, recent_prompts: list[str]) -> dict[str, Any]:
        if kind == "daily":
            brief = (
                "Create a short daily-life writing task (60-120 words expected). Rotate between genres "
                "so practice stays fresh: describing a routine/place/person, narrating something that "
                "happened (past tenses), plans & intentions, a short opinion on an everyday matter, a "
                "work email or chat message, explaining a small process. The learner works in IT, so "
                "sometimes (not always) tie it to office/dev life. Practical, not exam-style."
            )
        else:
            brief = (
                "Create one IELTS Writing Task 2 question that could realistically appear in the exam. "
                "Rotate BOTH the question type (opinion / discussion / advantages-disadvantages / "
                "problem-solution / two-part) AND the topic domain (education, environment, technology, "
                "health, work, cities, media, culture, crime, family, globalisation...) â€” pick whichever "
                "type and domain are least represented in the recent prompts below."
            )
        user = (
            f"{brief}\nLearner level: {level}, target band {target_band}.\n"
            "Also prepare the learner: a smart approach to THIS specific task (including the trap "
            "most people fall into), a short outline, and 3-4 structures/phrases worth practising in "
            "this exact essay at the target band â€” task-specific, no template openers.\n"
            f"Avoid repeating these recent prompts (same topic or same type counts as repeating): "
            f"{json.dumps(recent_prompts[-10:], ensure_ascii=False)}\n"
            'Return {"title": "short title", "prompt": "the task, in English", '
            '"question_type": "opinion|discussion|advantages-disadvantages|problem-solution|two-part|daily genre name", '
            '"guidance_vi": "2-3 câu tiếng Việt: cách tiếp cận thông minh cho đề NÀY + bẫy thường gặp", '
            '"outline_vi": ["dàn ý 3-4 gạch đầu dòng tiếng Việt"], '
            '"target_language": [{"phrase": "cấu trúc/cụm từ tiếng Anh nên thử dùng", "note_vi": "dùng để làm gì trong bài này"}], '
            '"min_words": number}'
        )
        return self.chat("You write English writing tasks.", user, temperature=0.9)

    def grade_writing(
        self,
        prompt: str,
        content: str,
        kind: str,
        level: str,
        target_band: str,
        target_language: list[str] | None = None,
    ) -> dict[str, Any]:
        scale = (
            "Use the official IELTS Writing band descriptors (0-9, steps of 0.5)."
            if kind == "ielts"
            else "It is a short daily practice, but still score it on the IELTS 0-9 scale so progress is comparable."
        )
        tl_note = (
            "The learner was encouraged to try these structures in this piece: "
            f"{json.dumps(target_language, ensure_ascii=False)} â€” in summary_vi, say which ones they "
            "attempted and whether they used them well.\n"
            if target_language
            else ""
        )
        user = (
            f"Grade this piece of writing.\nTask: {prompt}\n---\nLearner text:\n{content}\n---\n"
            f"{scale} Learner level {level}, target band {target_band}. Be honest, not flattering.\n"
            + tl_note +
            "Work like a real examiner, in this order (reason silently, output only the final JSON):\n"
            "1. Read the whole text once for meaning: does it actually answer THIS task? Is the "
            "position clear, are ideas developed or just stated?\n"
            "2. Assess each criterion separately against the official descriptors, quoting the "
            "learner's own words as evidence. Judge Lexical Resource on precision and collocation, "
            "not on rare words; judge Grammar on range AND accuracy, not accuracy alone.\n"
            "3. Collect EVERY real error in the text â€” aim to be exhaustive, not 2-3 examples â€” and "
            "classify each one.\n"
            "4. Decide bands honestly: use half bands, do not default to 6.0-6.5, do not inflate; "
            "criteria may legitimately differ from each other by 1.0+.\n"
            'Return {"overall_band": number, '
            '"criteria": {"task_response": number, "coherence": number, "lexical_resource": number, "grammar": number}, '
            '"criteria_feedback": {'
            '"task_response": {"comment_vi": "nhận xét CÓ DẪN CHỨNG trích từ bài", "to_next_band_vi": "việc cụ thể để lên 0.5-1.0 band ở tiêu chí này"}, '
            '"coherence": {"comment_vi": "...", "to_next_band_vi": "..."}, '
            '"lexical_resource": {"comment_vi": "...", "to_next_band_vi": "..."}, '
            '"grammar": {"comment_vi": "...", "to_next_band_vi": "..."}}, '
            '"summary_vi": "3-4 câu tổng quan: bài đang ở đâu, điều gì kéo band xuống nhiều nhất", '
            '"strengths_vi": ["2-3 điểm bạn làm TỐT, trích dẫn cụ thể — để giữ và phát huy"], '
            '"errors": [{"quote": "đoạn sai trích nguyên văn", "fix": "cách viết đúng", '
            '"type": "grammar|vocab|spelling|coherence|task", '
            '"explain_vi": "vÃ¬ sao sai + quy táº¯c Ä‘á»ƒ láº§n sau khÃ´ng máº¯c láº¡i"}], '
            '"improved_version": "the same text rewritten at ~target band, keep the learner\'s ideas and roughly the same length", '
            '"improved_notes_vi": ["3-4 thay đổi then chốt trong bản viết lại và vì sao chúng nâng band"], '
            '"band_up_plan_vi": ["2-3 hành động ưu tiên nhất cho các bài sau, cụ thể tới mức làm được ngay"], '
            '"vocab_upgrades": [{"term": "tá»«/cá»¥m Ä‘áº¯t giÃ¡ nÃªn dÃ¹ng", "meaning_vi": "...", "example": "...", '
            '"replaces_vi": "thay cho từ/cách diễn đạt nào bạn đã dùng trong bài"}]}'
        )
        return self.chat("You are a strict but constructive IELTS examiner.", user, max_tokens=4000)

    # ------------------------------------------------------------ IELTS Task 1

    def task1_prompt(
        self, chart_type: str, level: str, target_band: str, recent_prompts: list[str]
    ) -> dict[str, Any]:
        shape = {
            "line": '"kind": "line", "categories": ["1999","2001",...] (time points, 4-7 of them), '
                    '"series": [{"name": "USA", "values": [20, 35, ...]}] (2-4 series, values align with categories)',
            "bar": '"kind": "bar", "categories": ["Germany","Italy",...] (3-6 groups), '
                   '"series": [{"name": "1990", "values": [..]}] (1-3 series, values align with categories)',
            "pie": '"kind": "pie", "pies": [{"title": "Australia 1980 (100 units)", '
                   '"slices": [{"label": "Coal", "value": 50}, ...]}] (2 or 4 pies, same slice labels in each, '
                   '3-5 slices per pie)',
            "table": '"kind": "table", "columns": ["City","Date opened","Km of route"], '
                     '"rows": [["London","1863","394"], ...] (4-6 rows, 3-4 columns)',
        }[chart_type]
        user = (
            f"{task1.prompt_knowledge(chart_type)}\n\n"
            f"Invent ONE realistic IELTS Writing Task 1 question of type: {chart_type}.\n"
            "It must look like a real exam question: a plausible real-world topic (population, energy, "
            "transport, education, spending, employment, tourism, environment, technology...), realistic "
            "units, and — this is the important part — data with something worth reporting.\n"
            "HARD REQUIREMENT on the numbers: they must NOT all move in parallel. At least one series "
            "must behave differently from the rest — it crosses another series, or peaks and then "
            "declines, or falls while the others rise, or stays flat while the others move. Vary the "
            "step sizes too (real data is uneven, not +20 every time). A learner must be able to write a "
            "meaningful overview and a real comparison from this data; if every line just rises "
            "smoothly by the same amount, the task is worthless — redo the numbers.\n"
            f"Learner level {level}, target band {target_band}.\n"
            f"Avoid repeating these recent tasks (same topic counts as repeating): "
            f"{json.dumps(recent_prompts[-8:], ensure_ascii=False)}\n"
            "Return JSON:\n"
            '{"title": "short title", '
            '"prompt": "the full task statement in English, ending with: Summarise the information by '
            'selecting and reporting the main features, and make comparisons where relevant.", '
            f'"chart": {{"title": "chart title shown above the figure", "unit": "e.g. % of population, '
            f'millions of tonnes", {shape}}}, '
            '"guidance_vi": "2-3 câu tiếng Việt: đặc điểm nổi bật nhất của bộ số liệu NÀY nên cho vào '
            'overview, và bẫy riêng của đề này", '
            '"outline_vi": ["dàn ý 4 gạch đầu dòng: intro / overview / detail 1 / detail 2"], '
            '"target_language": [{"phrase": "cấu trúc tiếng Anh nên thử dùng trong bài này", '
            '"note_vi": "dùng để làm gì"}], '
            '"min_words": 150}'
        )
        data = self.chat(
            "You write IELTS Writing Task 1 exam questions together with the data behind the figure.",
            user,
            temperature=0.9,
            max_tokens=2000,
        )
        chart = data.get("chart")
        if not isinstance(chart, dict) or not chart.get("kind"):
            raise LLMError("LLM không trả về dữ liệu biểu đồ hợp lệ.")
        return data

    def grade_task1(
        self,
        prompt: str,
        chart: dict[str, Any],
        content: str,
        chart_type: str,
        level: str,
        target_band: str,
        word_count: int = 0,
    ) -> dict[str, Any]:
        user = (
            f"{task1.prompt_knowledge(chart_type)}\n\n"
            f"{descriptors.task1_rubric()}\n\n"
            f"{SCORING_METHOD}\n"
            "Grade this IELTS Writing Task 1 answer against the descriptor tables above (0-9, half "
            "bands). The first criterion is TASK ACHIEVEMENT (not Task Response).\n"
            f"Task: {prompt}\n"
            f"The data behind the figure (the learner saw it as a chart, you see it as JSON — use it to "
            f"check every number they quote):\n{json.dumps(chart, ensure_ascii=False)}\n---\n"
            f"Learner's answer ({word_count} words — this count is authoritative, do not recount):\n"
            f"{content}\n---\n"
            f"Learner level {level}, target band {target_band}. Be honest, not flattering.\n"
            "Work like a real examiner, in this order (reason silently, output only the final JSON):\n"
            "1. Task Achievement first, and be strict about it: is there a real OVERVIEW (a clear "
            "statement of the big picture, no figures)? A missing overview means the text cannot meet "
            "band 6+ (which require 'an overview with information appropriately selected'), so Task "
            "Achievement is capped at 5. Are the key features selected, or did they just list "
            "everything? Is every figure they quote actually correct against the data above (a wrong "
            "figure counts against the band 6 bullet 'details may be ... inaccurate')? Did they add "
            "opinions, causes or a conclusion (all out of scope for Task 1, and count as 'format may "
            "be inappropriate')? Is it at least 150 words (the app enforces a word-count penalty on top "
            "of your band separately, so score the writing itself here)?\n"
            "2. Then Coherence and Cohesion, Lexical Resource, Grammatical Range and Accuracy, each "
            "matched against its own table above, quoting the learner's own words as evidence. Judge "
            "Lexical Resource on the precision of the data-describing language (rise/fall verbs, "
            "adverbs of degree, comparison), not on rare words.\n"
            "3. Collect EVERY real error — be exhaustive — and classify each one. A wrong number or a "
            "misread of the chart is type \"data\".\n"
            "4. Decide bands honestly using the method above: half bands, no defaulting to 6.0-6.5, "
            "criteria may differ by 1.0+.\n"
            "5. Compute overall_band as the average of the four criterion bands, rounded to the nearest IELTS half-band.\n"
            + GRADING_V2_SCHEMA +
            'Return {"overall_band": number, '
            '"criteria": {"task_response": number, "coherence": number, "lexical_resource": number, "grammar": number}, '
            '"task1_check": {"has_overview": bool, "overview_quote": "câu overview bạn tìm thấy trong bài, '
            'hoặc \\"\\" nếu không có", "data_accurate": bool, "word_count_ok": bool, '
            '"opinion_free": bool, "is_memorized_or_offtopic": true nếu bài đọc như một mẫu học thuộc '
            'chung chung không thực sự bám đề này hoặc chép gần nguyên văn bài mẫu, '
            '"verdict_vi": "1-2 câu: bài này pass/fail ở 4 điểm sống còn trên, vì sao"}, '
            '"criteria_feedback": {'
            '"task_response": {"comment_vi": "nhận xét CÓ DẪN CHỨNG trích từ bài", "to_next_band_vi": "việc cụ thể để lên band"}, '
            '"coherence": {"comment_vi": "...", "to_next_band_vi": "..."}, '
            '"lexical_resource": {"comment_vi": "...", "to_next_band_vi": "..."}, '
            '"grammar": {"comment_vi": "...", "to_next_band_vi": "..."}}, '
            '"summary_vi": "3-4 câu: bài đang ở đâu, điều gì kéo band xuống nhiều nhất", '
            '"strengths_vi": ["2-3 điểm làm TỐT, trích dẫn cụ thể"], '
            '"errors": [{"quote": "đoạn sai trích nguyên văn", "fix": "cách viết đúng", '
            '"type": "grammar|vocab|spelling|coherence|task|data", '
            '"explain_vi": "vì sao sai + quy tắc để lần sau không mắc lại"}], '
            '"improved_version": "the same answer rewritten at ~target band: same 4-paragraph structure, '
            'correct figures, 160-190 words", '
            '"improved_notes_vi": ["3-4 thay đổi then chốt và vì sao chúng nâng band"], '
            '"band_up_plan_vi": ["2-3 việc ưu tiên cho bài Task 1 sau"], '
            '"vocab_upgrades": [{"term": "từ/cụm mô tả số liệu đắt giá", "meaning_vi": "...", "example": "...", '
            '"replaces_vi": "thay cho cách diễn đạt nào bạn đã dùng"}]}'
        )
        return self.chat(
            "You are a strict but constructive IELTS examiner marking Writing Task 1.",
            user,
            temperature=0.2,
            max_tokens=4000,
        )

    # ------------------------------------------------------------ IELTS Task 2

    def grade_task2(
        self,
        prompt: str,
        essay_type: str,
        content: str,
        level: str,
        target_band: str,
        word_count: int = 0,
        model_answer: str | None = None,
    ) -> dict[str, Any]:
        model_note = (
            "A band-9 model answer for this exact task is provided for reference — use it to judge "
            f"how well the learner addressed the task, not to copy from:\n{model_answer}\n---\n"
            if model_answer
            else ""
        )
        user = (
            f"{task2.prompt_knowledge(essay_type)}\n\n"
            f"{descriptors.task2_rubric()}\n\n"
            f"{SCORING_METHOD}\n"
            "Grade this IELTS Writing Task 2 essay against the descriptor tables above (0-9, half "
            "bands). The first criterion is TASK RESPONSE.\n"
            f"Task: {prompt}\n---\n"
            f"{model_note}"
            f"Learner's essay ({word_count} words — this count is authoritative, do not recount):\n"
            f"{content}\n---\n"
            f"Learner level {level}, target band {target_band}. Be honest, not flattering.\n"
            "Work like a real examiner, in this order (reason silently, output only the final JSON):\n"
            "1. Task Response first, and be strict: is the writer's POSITION clear and consistent "
            "(reading only intro + conclusion should reveal it)? Per the band 4 bullet, an unclear "
            "position caps Task Response at 4-5. Are ALL parts of the prompt answered (discuss both "
            "views = both views AND the writer's own opinion; problem+solution = both; two-part = both "
            "questions), with roughly balanced space — per band 6, addressing parts unevenly already "
            "caps below 7? Are the ideas relevant to THIS task and developed with explanation/examples "
            "('fully extended and well supported' = band 9) or just stated ('largely undeveloped' = "
            "band 3)? Is it at least 250 words (the app enforces a word-count penalty on top of your "
            "band separately, so score the writing itself here)?\n"
            "2. Then Coherence & Cohesion (4-paragraph structure, topic sentences, paragraph unity, "
            "linking words, referencing), Lexical Resource (precision and collocation, not rare "
            "words), and Grammatical Range & Accuracy, each matched against its own table above — "
            "quoting the learner's own words as evidence.\n"
            "3. Collect EVERY real error — be exhaustive — and classify each one.\n"
            "4. Decide bands honestly using the method above: half bands, no defaulting to 6.0-6.5, "
            "criteria may differ by 1.0+.\n"
            "5. Compute overall_band as the average of the four criterion bands, rounded to the nearest IELTS half-band.\n"
            + GRADING_V2_SCHEMA +
            'Return {"overall_band": number, '
            '"criteria": {"task_response": number, "coherence": number, "lexical_resource": number, "grammar": number}, '
            '"task2_check": {"clear_position": bool, "position_quote": "câu thể hiện quan điểm bạn '
            'tìm thấy, hoặc \\"\\" nếu không có", "all_parts_addressed": bool, "ideas_relevant": bool, '
            '"word_count_ok": bool, "is_memorized_or_offtopic": true nếu bài đọc như một mẫu học thuộc '
            'chung chung không thực sự bám đề này hoặc chép gần nguyên văn bài mẫu, '
            '"verdict_vi": "1-2 câu: bài này pass/fail ở 4 điểm sống còn trên, vì sao"}, '
            '"criteria_feedback": {'
            '"task_response": {"comment_vi": "nhận xét CÓ DẪN CHỨNG trích từ bài", "to_next_band_vi": "việc cụ thể để lên band"}, '
            '"coherence": {"comment_vi": "...", "to_next_band_vi": "..."}, '
            '"lexical_resource": {"comment_vi": "...", "to_next_band_vi": "..."}, '
            '"grammar": {"comment_vi": "...", "to_next_band_vi": "..."}}, '
            '"summary_vi": "3-4 câu: bài đang ở đâu, điều gì kéo band xuống nhiều nhất", '
            '"strengths_vi": ["2-3 điểm làm TỐT, trích dẫn cụ thể"], '
            '"errors": [{"quote": "đoạn sai trích nguyên văn", "fix": "cách viết đúng", '
            '"type": "grammar|vocab|spelling|coherence|task", '
            '"explain_vi": "vì sao sai + quy tắc để lần sau không mắc lại"}], '
            '"improved_version": "the same essay rewritten at ~target band: same 4-paragraph '
            'structure, clear position, 270-300 words", '
            '"improved_notes_vi": ["3-4 thay đổi then chốt và vì sao chúng nâng band"], '
            '"band_up_plan_vi": ["2-3 việc ưu tiên cho bài Task 2 sau"], '
            '"vocab_upgrades": [{"term": "từ/cụm đắt giá nên dùng", "meaning_vi": "...", "example": "...", '
            '"replaces_vi": "thay cho cách diễn đạt nào bạn đã dùng"}]}'
        )
        return self.chat(
            "You are a strict but constructive IELTS examiner marking Writing Task 2.",
            user,
            temperature=0.2,
            max_tokens=4000,
        )

    def generate_patterns(self, theme: str, level: str, count: int, known_patterns: list[str]) -> list[dict[str, Any]]:
        user = (
            f"Give {count} reusable English sentence patterns for the theme \"{theme}\" "
            f"(learner level {level}).\n"
            "Spread them across DIFFERENT functions â€” contrast, cause-effect, concession, "
            "condition/hypothesis, emphasis (inversion, cleft), comparison, hedging an opinion, "
            "describing change over time â€” so the set is genuinely varied, and mix difficulty: mostly "
            "solid B1-B2 workhorses plus 1-2 truly C1 structures.\n"
            "Patterns must be practical for daily activities, work life, or usable directly in IELTS "
            "writing/speaking. No memorised template openers ('It is undeniable that...').\n"
            f"Avoid these existing patterns: {json.dumps(known_patterns[:100], ensure_ascii=False)}\n"
            'Return {"patterns": [{"pattern": "e.g. No sooner had I ... than ...", '
            '"use_vi": "dùng khi nào, sắc thái gì (tiếng Việt)", '
            '"examples": ["2 example sentences: 1 đời thường + 1 kiểu IELTS"], "band": "B1|B2|C1"}]}'
        )
        data = self.chat("You teach English sentence patterns.", user, temperature=0.7)
        patterns = data.get("patterns")
        if not isinstance(patterns, list):
            raise LLMError("LLM không trả về danh sách mẫu câu.")
        return [p for p in patterns if isinstance(p, dict) and str(p.get("pattern", "")).strip()]

    def check_pattern_sentence(self, pattern: str, sentence: str) -> dict[str, Any]:
        user = (
            f"The learner is practising the sentence pattern: \"{pattern}\"\n"
            f"Their sentence: \"{sentence}\"\n"
            "Check three things in order: (1) is the pattern's structure used correctly, "
            "(2) grammar of the rest of the sentence, (3) does it sound natural to a native speaker. "
            "Explain WHAT is wrong and WHY, not just that it is wrong.\n"
            'Return {"score": 0-100, "ok": bool, '
            '"feedback_vi": "nhận xét ngắn: đúng/sai ở đâu, vì sao", '
            '"corrected": "câu đã sửa (hoặc nguyên văn nếu đúng)", '
            '"upgrade": "một phiên bản hay hơn / band cao hơn của chính câu đó", '
            '"tip_vi": "1 mẹo nhớ nhanh về mẫu câu này"}'
        )
        return self.chat("You check pattern practice sentences.", user, max_tokens=800)


def _extract_json(raw: str) -> Any:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    start_candidates = [idx for idx in (raw.find("{"), raw.find("[")) if idx >= 0]
    if not start_candidates:
        raise LLMError("KhÃ´ng tÃ¬m tháº¥y JSON trong pháº£n há»“i LLM.")
    start = min(start_candidates)
    end = max(raw.rfind("}"), raw.rfind("]"))
    if end <= start:
        raise LLMError("JSON tá»« LLM bá»‹ cáº¯t cá»¥t.")
    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError("JSON tá»« LLM khÃ´ng há»£p lá»‡.") from exc

