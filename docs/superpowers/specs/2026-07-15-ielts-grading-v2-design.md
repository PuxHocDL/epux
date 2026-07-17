# IELTS Grading V2 Design

## Goal

Improve Task 1 and Task 2 grading so EPux gives an IELTS-like exam band while also giving richer tutor guidance for improving the next essay.

## Source Of Truth

The grading prompt should align with the public IELTS Writing Band Descriptors, updated May 2023. Task 1 uses Task Achievement, Coherence and Cohesion, Lexical Resource, and Grammatical Range and Accuracy. Task 2 uses Task Response instead of Task Achievement. Each criterion contributes 25% to the writing task band.

## Product Behavior

The app will show two layers of result:

1. Exam band: one main band score, plus four criterion bands.
2. Tutor diagnosis: a band range, confidence level, descriptor evidence, limiting factors, why the answer is not higher, why it is not lower, and multiple routes for raising the band.

The main score remains conservative and descriptor-based. The tutor layer explains uncertainty and gives more paths forward, so a learner can understand the score rather than only seeing a number.

## Grading Data Model

The LLM response keeps the current fields for backwards compatibility:

- `overall_band`
- `criteria`
- `criteria_feedback`
- `summary_vi`
- `strengths_vi`
- `errors`
- `improved_version`
- `improved_notes_vi`
- `band_up_plan_vi`
- `vocab_upgrades`

It adds:

- `band_range`: `{ "low": number, "high": number, "reason_vi": string }`
- `confidence`: `"low" | "medium" | "high"`
- `limiting_factors`: `[{ "criterion": string, "issue_vi": string, "evidence": string, "band_cap": number | null }]`
- `descriptor_match`: object keyed by criterion, each with `band`, `matched_features_vi`, `missing_features_vi`, `evidence`
- `why_not_higher`: array of concrete Vietnamese reasons
- `why_not_lower`: array of concrete Vietnamese reasons
- `band_up_routes`: object with arrays `quick_fixes`, `next_practice`, `language_upgrades`, `strategy`, `avoid_next_time`

Task-specific checks remain:

- Task 1: overview, data accuracy, no personal opinion, word count.
- Task 2: clear position, all parts addressed, relevant and developed ideas, word count.

## Scoring Rules

The prompt must force this order:

1. Identify task-specific gates and possible band caps.
2. Match each criterion to descriptor features, with evidence from the learner text.
3. Choose criterion bands in half-band steps.
4. Calculate the overall band as the mean of the four criteria rounded to the nearest IELTS half-band.
5. Explain uncertainty with `band_range` and `confidence`.
6. Generate multiple improvement routes, not only two or three generic tips.

Server-side code will not trust the LLM for word count. It will keep overriding `word_count_ok` and `word_count` from the actual submitted text.

## UI

The result screen should remain scannable:

- Keep the top band tiles.
- Rename the first criterion label based on kind: Task Achievement for Task 1, Task Response for Task 2.
- Add a compact band range and confidence line near the score.
- Expand "Phan tich tung tieu chi" to show descriptor match, missing features, and evidence.
- Add "Vi sao chua len band cao hon" and "Vi sao khong thap hon".
- Add a richer "Duong len band tiep theo" section with grouped routes.

No new dependency is required.

## Testing

Add focused tests for pure helpers:

- IELTS half-band rounding.
- Feedback normalization preserving current fields and filling safe defaults for new fields.
- Task 1/Task 2 labels rendered correctly in JS helpers where feasible through static checks.

Manual verification:

- Run unit tests.
- Start the app or inspect generated HTML functions.
- Deploy to `modal_8`.
- Verify production HTML cache-buster and JS contain Grading V2 strings.

