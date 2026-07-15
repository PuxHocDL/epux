"""IELTS Writing Task 2 knowledge base + question bank.

Mirrors ``task1.py``:

* ``KNOWLEDGE`` — the method (4-paragraph essay, the four marking criteria, essay
  types, idea-generation perspectives, linking language, referencing, band-killing
  traps). Shown to the learner *and* injected into the LLM grading prompt.
* ``BANK`` — 12 real Task 2 questions (from the IELTSTutors band-9 collection) with
  full band-9 model answers and the skill each one showcases.

The official band-descriptor table image lives in ``web/task2/`` and is served from
``/static/task2/``. Task 2 has no chart to draw, so it is the only asset here.
"""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------- method

TYPES: dict[str, dict[str, str]] = {
    "opinion": {"label_vi": "Nêu ý kiến (agree/disagree)", "label_en": "Opinion",
                "cue": "To what extent do you agree or disagree?"},
    "discussion": {"label_vi": "Thảo luận hai quan điểm", "label_en": "Discussion",
                   "cue": "Discuss both views and give your own opinion."},
    "advantages": {"label_vi": "Lợi / hại (outweigh)", "label_en": "Advantages–Disadvantages",
                   "cue": "Do the advantages outweigh the disadvantages?"},
    "problem": {"label_vi": "Vấn đề & giải pháp", "label_en": "Problem–Solution",
                "cue": "What are the problems and what are the solutions?"},
    "two_part": {"label_vi": "Câu hỏi trực tiếp / hai phần", "label_en": "Two-part / direct",
                 "cue": "Two direct questions to answer."},
    "positive_negative": {"label_vi": "Tích cực hay tiêu cực", "label_en": "Positive–Negative",
                          "cue": "Is this a positive or a negative development?"},
}

# The 4-paragraph skeleton — the backbone for every Task 2 type.
STRUCTURE: list[dict[str, str]] = [
    {
        "name": "1. Introduction (2 câu)",
        "body_vi": "Câu 1 diễn đạt lại đề bằng từ của bạn (paraphrase, KHÔNG chép). Câu 2 là "
                   "THESIS — nêu rõ quan điểm của bạn VÀ hé lộ bố cục 2 đoạn thân bài. Nếu chỉ đọc "
                   "mở bài + kết bài mà giám khảo vẫn biết chính xác bạn nghĩ gì thì thesis đạt.",
        "example": "While some believe that money is the best type of gift, I agree with those who "
                   "suggest other gifts are more suitable.",
    },
    {
        "name": "2. Body 1 (topic sentence + phát triển)",
        "body_vi": "Mở bằng TOPIC SENTENCE nêu ý chính của đoạn. Sau đó phát triển: giải thích vì "
                   "sao + ví dụ/lý do. Cả đoạn chỉ xoay quanh một ý (paragraph unity) — không nhét "
                   "câu lạc đề.",
        "example": "Many people believe that money makes an excellent present. Proponents of this "
                   "view may suggest that young people already have what they need… For example, …",
    },
    {
        "name": "3. Body 2 (topic sentence + phát triển)",
        "body_vi": "Đoạn thân bài thứ hai, cấu trúc y hệt đoạn 1. Mẹo band cao: để LẬP LUẬN MẠNH "
                   "NHẤT (thường là quan điểm bạn đồng tình) ở đoạn 2 — đây là quy ước của viết học "
                   "thuật tiếng Anh.",
        "example": "On the other hand, I am in agreement with those who believe that actual gifts "
                   "are better than money. An important reason is that…",
    },
    {
        "name": "4. Conclusion (1-2 câu)",
        "body_vi": "Mở bằng tín hiệu ('In conclusion,'). Tóm tắt các lập luận chính VÀ nhắc lại "
                   "quan điểm của bạn. Có thể chốt bằng một lời khuyên / cảnh báo / dự đoán. Không "
                   "thêm ý mới.",
        "example": "In conclusion, whereas many believe that financial gifts may increase "
                   "independence, I side with those who suggest gifts showing an understanding of "
                   "the young person are more beneficial.",
    },
]

CRITERIA: list[dict[str, Any]] = [
    {
        "key": "task_response",
        "name_vi": "Task Response — Trả lời đề",
        "points_vi": [
            "Viết TỐI THIỂU 250 từ trong 40 phút — dưới 250 bị trừ thẳng.",
            "Câu đầu là bản paraphrase tốt của đề, không chép.",
            "QUAN ĐIỂM (position) phải rõ và xuyên suốt: chỉ đọc mở + kết vẫn biết bạn nghĩ gì. "
            "Không rõ quan điểm → TR chặn trần ở band 5, khó lên 7.",
            "Trả lời ĐỦ MỌI PHẦN của đề (discuss both views = cả hai quan điểm + ý kiến; problem "
            "+ solution = cả vấn đề lẫn giải pháp; chia đất tương đối đều).",
            "Ý chính phải LIÊN QUAN tới đề — ý lạc đề thì không quá band 5. Mỗi ý phải có giải "
            "thích / ví dụ / lý do chống lưng, không nêu suông.",
        ],
    },
    {
        "key": "coherence",
        "name_vi": "Coherence & Cohesion — Mạch lạc & liên kết",
        "points_vi": [
            "Mỗi đoạn thân bài mở bằng một TOPIC SENTENCE nêu ý chính.",
            "Paragraph unity: mọi câu trong đoạn phải phục vụ ý chính của đoạn — bỏ câu lạc đề.",
            "Ý tiến triển tự nhiên, mượt mà từ câu này sang câu kia.",
            "Dùng đa dạng từ nối (however, secondly, furthermore, for instance…) — đúng chức năng, "
            "không lạm dụng.",
            "Referencing & substitution (he, this, these ideas, such people…) để tránh lặp danh từ.",
        ],
    },
    {
        "key": "lexical_resource",
        "name_vi": "Lexical Resource — Vốn từ",
        "points_vi": [
            "Register học thuật: tránh viết tắt ('don't'), tránh giọng nói chuyện ('a lot of stuff').",
            "PRECISION (chính xác) quan trọng hơn từ 'kêu': 'a significant and sustained rise' hơn "
            "hẳn 'a rise'.",
            "Range: đừng lặp lại một từ trong cùng câu / nhóm câu — dùng đồng nghĩa, paraphrase.",
            "Word formation đúng họ từ ('interested' chứ không 'interesting in stories').",
            "Collocation đúng ('preparing FOR an exam', không 'preparing AT').",
        ],
    },
    {
        "key": "grammar",
        "name_vi": "Grammatical Range & Accuracy — Ngữ pháp",
        "points_vi": [
            "Trộn câu đơn / ghép / phức. Câu phức = ít nhất 1 mệnh đề độc lập + 1 mệnh đề phụ thuộc.",
            "Dùng nhiều loại mệnh đề phức: điều kiện, quan hệ, thời gian, danh ngữ, tương phản.",
            "Độ chính xác: lỗi càng ít, band càng cao; lỗi không được làm khó hiểu.",
            "Danh từ: số ít/nhiều và mạo từ (a/an/the) — lỗi kinh điển của người Việt.",
            "Cụm danh từ phức (relative clause, prepositional phrase) để nhồi thông tin vào một câu.",
            "Dấu câu chuẩn, nhất là trong câu dài nhiều mệnh đề.",
        ],
    },
]

RULES_VI: list[str] = [
    "40 phút, tối thiểu 250 từ — viết ~270-300 từ là vừa (Task 2 nặng gấp đôi Task 1 khi tính điểm).",
    "Cấu trúc 4 đoạn: mở bài (paraphrase + thesis) → thân 1 → thân 2 → kết bài.",
    "Quan điểm phải RÕ và nhất quán ở cả mở bài lẫn kết bài. Đây là điều kiện để vượt band 5.",
    "Trả lời ĐỦ mọi phần của đề, chia đất tương đối đều giữa các phần.",
    "Mỗi đoạn thân bài = 1 topic sentence + phát triển bằng giải thích/ví dụ; giữ paragraph unity.",
    "Để lập luận mạnh nhất ở body 2.",
    "Không thêm ý mới ở kết bài; kết bài chỉ tóm tắt + chốt quan điểm.",
    "Với đề nêu một 'sự thật' rồi mới hỏi (vd 'Ngày nay… While some say…'), đừng bàn phần sự thật — "
    "chỉ bàn phần được hỏi.",
]

TYPE_TIPS: dict[str, list[str]] = {
    "opinion": [
        "'To what extent do you agree/disagree?' chỉ có MỘT phần → được phép viết một chiều (chỉ "
        "bảo vệ quan điểm của mình) nếu muốn.",
        "Vẫn nên cân nhắc nêu một mặt đối lập rồi bác lại, hoặc chọn quan điểm cân bằng (đồng ý "
        "một phần) — miễn là quan điểm cuối cùng rõ ràng.",
        "Thesis phải nói rõ mức độ đồng ý (hoàn toàn / một phần) và hé lộ 2 lý do sẽ triển khai.",
        "Giữ đúng quan điểm đó từ đầu đến cuối — đừng đồng ý ở đoạn này rồi phản đối ở đoạn kia.",
    ],
    "discussion": [
        "'Discuss both views and give your opinion' có HAI phần bắt buộc: bàn cả hai quan điểm + "
        "nêu ý kiến của bạn. Thiếu ý kiến của bạn → mất điểm Task Response nặng.",
        "Body 1 bàn quan điểm A, body 2 bàn quan điểm B — chia đất tương đối đều.",
        "Nếu bạn nghiêng về một bên, đặt quan điểm bạn đồng tình ở body 2 và lồng ý kiến vào đó.",
        "Dùng 'Proponents of this view argue…' để tả quan điểm KHÔNG phải của bạn mà không bị "
        "hiểu nhầm là ý kiến bản thân.",
    ],
    "advantages": [
        "'Do the advantages outweigh the disadvantages?' → phải CÂN nặng nhẹ và kết luận bên nào "
        "thắng, không chỉ liệt kê.",
        "Một cách chắc ăn: body 1 nói mặt yếu hơn, body 2 nói mặt bạn cho là nặng hơn.",
        "Thesis nêu luôn kết luận (lợi > hại hay ngược lại). Kết bài khẳng định lại.",
        "Nếu đề nhắc cụ thể (vd 'tác động lên dân địa phương và môi trường') thì phải bàn đúng "
        "những khía cạnh đó.",
    ],
    "problem": [
        "'What are the problems/causes and what are the solutions?' có HAI phần — mỗi phần chia "
        "đất tương đối đều.",
        "Cách 1: body 1 = (một vấn đề + giải pháp của nó), body 2 = (vấn đề khác + giải pháp). "
        "Cách 2: body 1 = tất cả vấn đề, body 2 = tất cả giải pháp. Cả hai đều được.",
        "Nêu nguyên nhân/vấn đề trong thesis theo đúng thứ tự sẽ triển khai — cho giám khảo thấy "
        "bố cục.",
        "Giải pháp phải khớp với vấn đề đã nêu, kèm ví dụ thực tế nếu có.",
    ],
    "two_part": [
        "Đề gồm hai câu hỏi trực tiếp — TRẢ LỜI CẢ HAI, mỗi câu một đoạn thân bài.",
        "Đọc kỹ hai câu hỏi khác nhau chỗ nào; đừng gộp thành một.",
        "Thesis ngắn gọn báo trước bạn sẽ trả lời cả hai câu.",
        "Không cần 'quan điểm' kiểu agree/disagree, nhưng câu trả lời phải rõ ràng và có ví dụ.",
    ],
    "positive_negative": [
        "'Is this a positive or a negative development?' → phải chốt nghiêng về tích cực hay tiêu "
        "cực (hoặc cân bằng), không lấp lửng.",
        "Rất giống dạng opinion: thesis nêu lập trường, 2 đoạn thân bài chống lưng.",
        "Nếu chọn cân bằng thì body 1 mặt tích cực, body 2 mặt tiêu cực, và kết bài cân nhắc bên "
        "nào trội hơn.",
        "Dùng góc nhìn (cá nhân / xã hội / kinh tế / môi trường) để nghĩ ý nhanh.",
    ],
}

PERSPECTIVES_VI: list[dict[str, str]] = [
    {"name": "Cá nhân", "q": "Ở góc độ từng người thì sao? (lợi/hại với bản thân họ)"},
    {"name": "Xã hội / văn hoá", "q": "Tác động lên cộng đồng, xã hội, giá trị văn hoá?"},
    {"name": "Kinh tế", "q": "Ảnh hưởng tới tiền bạc, việc làm, tăng trưởng?"},
    {"name": "Môi trường", "q": "Có hại/lợi gì cho môi trường?"},
    {"name": "Công nghệ", "q": "Liên quan tới công nghệ, thiết bị, hạ tầng số?"},
    {"name": "Chính trị", "q": "Chính phủ, luật pháp, quyền lực có dính líu không?"},
    {"name": "Giáo dục", "q": "Tác động tới việc học, nhà trường, kiến thức?"},
    {"name": "Sức khoẻ", "q": "Ảnh hưởng thể chất / tinh thần?"},
]

LANGUAGE: list[dict[str, Any]] = [
    {"group_vi": "Nêu ý kiến", "items": ["I believe (that)…", "In my opinion,…", "I side with those who…",
                                          "I am in agreement with…", "It is my belief that…"]},
    {"group_vi": "Tương phản", "items": ["However,", "On the other hand,", "Nevertheless,",
                                          "Although / Even though (+ mệnh đề)", "Despite / In spite of (+ danh từ)",
                                          "whereas / while"]},
    {"group_vi": "Thêm ý", "items": ["Furthermore,", "Moreover,", "In addition,", "Additionally,",
                                      "Not only… but also…"]},
    {"group_vi": "Nhân quả", "items": ["Due to (+ danh từ),", "Therefore,", "Consequently,",
                                        "As a result,", "…, which leads to…", "This is because…"]},
    {"group_vi": "Ví dụ", "items": ["For example,", "For instance,", "One example is…",
                                     "This can be seen in / by…"]},
    {"group_vi": "Trình tự", "items": ["Firstly,", "Secondly,", "Lastly,", "To begin with,",
                                        "First and foremost,"]},
    {"group_vi": "Kết luận", "items": ["In conclusion,", "To conclude,", "In summary,", "Overall,"]},
    {"group_vi": "Tả quan điểm không phải của mình",
     "items": ["Proponents of this view argue that…", "Those who support this believe…",
               "It is often argued that…", "Some people claim that…"]},
    {"group_vi": "Referencing (tránh lặp)",
     "items": ["this / these (nhắc lại ý vừa nêu)", "such people / such measures",
               "the former … the latter …", "they / their (dùng cho 'a person' khi không muốn he/she)",
               "one (thay danh từ vừa nhắc)"]},
]

TRAPS_VI: list[str] = [
    "Không nêu quan điểm rõ (hoặc quan điểm mâu thuẫn giữa các đoạn) → Task Response chặn trần band 5.",
    "Ý lạc đề, không liên quan tới câu hỏi → cũng không quá band 5 ở Task Response.",
    "Thiếu một phần của đề (chỉ bàn một quan điểm trong 'discuss both', quên phần 'solution'…).",
    "Chép nguyên đề bài làm câu mở → phần chép không tính là từ của bạn.",
    "Nhồi quá nhiều ý, ý nào cũng nông → nên chọn 2 ý tâm đắc và phát triển sâu.",
    "Câu lạc đề trong đoạn (phá vỡ paragraph unity) → tụt Coherence.",
    "Học thuộc câu mở sáo rỗng ('It is undeniable that…', 'In this day and age…') → giám khảo nhận ra ngay.",
    "Viết dưới 250 từ.",
]

GLOSSARY_VI: list[dict[str, str]] = [
    {"term": "Thesis statement", "def": "Câu (thường cuối mở bài) nêu rõ quan điểm của bạn và hé lộ bố cục bài."},
    {"term": "Topic sentence", "def": "Câu đầu mỗi đoạn thân bài, nêu ý chính của đoạn đó."},
    {"term": "Body paragraph", "def": "Đoạn thân bài (thường 2 đoạn) chứa các lập luận chính. Mở bài không phải body."},
    {"term": "Paragraph unity", "def": "Mọi câu trong một đoạn đều phục vụ ý chính của đoạn; không có câu lạc đề."},
    {"term": "Paraphrase", "def": "Diễn đạt lại một thông điệp bằng từ vựng / ngữ pháp khác mà giữ nguyên nghĩa."},
    {"term": "Complex noun phrase", "def": "Danh từ + thông tin bổ sung (mệnh đề quan hệ, cụm giới từ), vd 'the vast majority of people who visited'."},
    {"term": "Referencing", "def": "Dùng he/this/these ideas… để nhắc lại một thứ đã nêu, tránh lặp từ."},
    {"term": "Counter argument", "def": "Lập luận của phía bạn KHÔNG đồng tình — thường đặt ở body 1 rồi bác lại."},
]

KNOWLEDGE: dict[str, Any] = {
    "intro_vi": "Task 2 là bài luận 250+ từ trong 40 phút, tính điểm gấp đôi Task 1. Bạn được cho "
                "một ý kiến / vấn đề và phải phản hồi bằng lập luận LOGIC, có tổ chức, quan điểm rõ "
                "ràng. Công thức band cao: 4 đoạn, quan điểm nhất quán, mỗi ý được chống lưng bằng "
                "giải thích và ví dụ.",
    "structure": STRUCTURE,
    "criteria": CRITERIA,
    "rules_vi": RULES_VI,
    "type_tips": TYPE_TIPS,
    "perspectives": PERSPECTIVES_VI,
    "language": LANGUAGE,
    "traps_vi": TRAPS_VI,
    "glossary": GLOSSARY_VI,
    "types": TYPES,
    "band_image": "/static/task2/band-descriptors.png",
}


def prompt_knowledge(essay_type: str) -> str:
    """Compact English digest of the Task 2 method for LLM prompts."""
    tips = TYPE_TIPS.get(essay_type, [])
    return (
        "IELTS Writing Task 2 method (band 9):\n"
        "- 4 paragraphs: introduction (paraphrase the prompt + a THESIS that states the writer's "
        "position and previews the two body paragraphs), body 1 and body 2 (each: a topic sentence "
        "+ development through explanation and examples, with paragraph unity), conclusion (signal, "
        "summary of arguments, restated position, no new ideas).\n"
        "- The position must be clear and consistent: reading only the intro and conclusion must "
        "reveal it. No clear position caps Task Response at band 5.\n"
        "- ALL parts of the prompt must be answered (discuss both views = both views + the writer's "
        "opinion; problem+solution = both), with roughly equal space.\n"
        "- Ideas must be relevant to the task and developed, not just stated; irrelevant ideas also "
        "cap Task Response at 5.\n"
        "- 250+ words in 40 minutes; formal academic register; put the strongest argument in body 2.\n"
        + ("Type-specific (" + essay_type + "): " + " ".join(tips) if tips else "")
    )


# ----------------------------------------------------------------------- bank
# 12 real Task 2 questions with their band-9 model answers (IELTSTutors collection).

BANK: list[dict[str, Any]] = [
    {
        "id": "gifts-young-people",
        "type": "discussion",
        "title": "Gifts for young people",
        "skill_vi": "Cấu trúc bài (structure)",
        "question": "Some people think that money is the best gift to give to young people, while "
                    "others think other types of gifts are better for young people. Discuss both "
                    "views and give your opinion.",
        "focus_vi": "Bài mẫu chuẩn để học bộ khung 4 đoạn và cách dùng thesis để sắp xếp thứ tự bài.",
        "model": (
            "It can be a struggle to select an appropriate gift for a young relative or the child "
            "of a friend. While some believe that money is the best type of gift, I agree with "
            "those who suggest other gifts are more suitable.\n\n"
            "Many people believe that money makes an excellent present. Proponents of this view may "
            "suggest that young people already have what they need in terms of toys and gadgets and "
            "so giving them more will not be of benefit. They also argue that the young may actually "
            "learn valuable skills from the process of choosing to save or spend their money. For "
            "example, if the young person chooses to spend the money, they will learn the value of "
            "things that they wish to buy and what they can or cannot afford. This could make them "
            "more financially mature and independent.\n\n"
            "On the other hand, I am in agreement with those who believe that actual gifts are "
            "better than money. An important reason is that money is quite an impersonal gift since "
            "it shows no understanding of the interests of the receiver. It is therefore more "
            "appropriate to give something that shows the adult understands the desires of the young "
            "person, such as a piece of jewelry or the shirt of his/her favourite sports club. "
            "Furthermore, an educational gift, such as a book, or a useful gift, such as a watch, "
            "allows the young person to develop or improve his/her skills and so is directly "
            "beneficial.\n\n"
            "In conclusion, whereas many believe that financial gifts may increase independence and "
            "be popular, I side with those who suggest gifts showing an understanding of the young "
            "person or which are educational are more beneficial. It is clearly important to "
            "consider the needs and interests of young people when selecting gifts."
        ),
    },
    {
        "id": "status-possessions",
        "type": "opinion",
        "title": "Status and possessions",
        "skill_vi": "Nghĩ ý liên quan (relevant ideas)",
        "question": "A person's worth nowadays seems to be judged according to social status and "
                    "material possessions. Old-fashioned values, such as honour, kindness and "
                    "trust, no longer seem important. To what extent do you agree or disagree with "
                    "this opinion?",
        "focus_vi": "Học cách chọn ý LIÊN QUAN tới đề và cách dùng quan điểm cân bằng (đồng ý một phần).",
        "model": (
            "Status and money are highly valued in today's society and have certainly changed our "
            "values to some extent. However, in everyday life I don't believe a person's worth is "
            "judged that differently compared to in the past.\n\n"
            "It is apparent that most celebrities today are admired or envied solely for their "
            "material wealth or position in various social hierarchies. Many of these people are "
            "known to turn their backs on friends, cheat on their spouses or spend their evenings "
            "over-indulging in alcohol and/or drugs. Things like owning a mansion, driving an "
            "expensive car and getting into A-list parties are exalted above old-fashioned values. "
            "Ultimately, though, it is the many readers of gossip magazines and celebrity blogs who "
            "reinforce these ideas.\n\n"
            "Nevertheless, I do believe that in their day-to-day lives most people still believe in "
            "values such as honour, kindness and trust. In some way most of us want to form loving "
            "families, raise our children to be good citizens, stand up for the downtrodden and "
            "protect our communities from harm. We still form friendships, romances and business "
            "partnerships based on old-fashioned criteria. For example, when our trust is abused or "
            "we are unfairly treated, we see that as a major violation of our relationship and we "
            "judge the wrongdoer accordingly.\n\n"
            "In conclusion, while status and possessions as a measure of a person's worth have "
            "become more popular, the behavior of most ordinary people shows that the old values "
            "are still strong. It is unlikely that honour, kindness, and trust will ever be replaced "
            "while parents continue to teach their children to respect them."
        ),
    },
    {
        "id": "learning-english",
        "type": "opinion",
        "title": "Learning English abroad",
        "skill_vi": "Paragraph unity",
        "question": "Studying the English language in an English speaking country is the best but "
                    "not the only way to learn the language. To what extent do you agree or disagree?",
        "focus_vi": "Học paragraph unity: mọi câu trong đoạn đều bám topic sentence, không lạc đề.",
        "model": (
            "These days, there are many effective ways to learn a foreign language. It is clear that "
            "a student can learn English to a high level in his/her home country; however, studying "
            "in an English speaking country can lead to faster language learning due to immersion in "
            "the culture.\n\n"
            "These days, students in non-English-speaking countries commonly learn English to an "
            "acceptable level in high schools and universities in their own countries. Although their "
            "spoken English may not be that accurate or fluent, their knowledge of grammar is often "
            "quite good, which is extremely important when students come to an English speaking "
            "country to try and perfect their use of the language. In addition to this, studying the "
            "basics of English at secondary school in one's home country is less stressful than "
            "learning the language while overseas. This is because students living at home do not "
            "have the anxiety caused by problems such as finding accommodation, financing a foreign "
            "trip and trying to survive in a foreign country where day to day living away from "
            "support networks of friends and family may cause stress.\n\n"
            "On the other hand, there are several obvious advantages to learning English in English "
            "speaking countries. Every day there are frequent chances to practice listening to and "
            "speaking with native speakers, which leads to faster learning. If a student chooses to "
            "live with a local host family which does not speak her first language, she can immerse "
            "herself in the language and experience the culture first-hand, helping to improve "
            "fluency. Furthermore, if students attend an English language school full-time, the "
            "teachers will be native speakers. In this case, not only do the student's speaking and "
            "listening skills improve, but attention can be given to developing reading and writing "
            "skills as well.\n\n"
            "In conclusion, even though it is clearly desirable to study English in an English-"
            "speaking country, a reasonable level of English can be achieved at home if a student is "
            "hardworking and motivated to improve. Hopefully in the future, more students will have "
            "the opportunity to study languages abroad."
        ),
    },
    {
        "id": "obesity",
        "type": "problem",
        "title": "Obesity in rich countries",
        "skill_vi": "Từ nối (linking words)",
        "question": "Obesity is a serious problem in many countries, especially in rich countries. "
                    "What causes obesity and how can it be solved?",
        "focus_vi": "Học một loạt từ nối đúng chức năng (Due to, therefore, Consequently, despite…).",
        "model": (
            "With the advent of urbanisation and the rise in popularity of fast food, there have "
            "been accompanying issues with rising obesity rates, especially in developed countries "
            "such as the UK and the USA. It is clear that obesity rates are higher in developed "
            "countries because their citizens are wealthier; however, there are a number of ways in "
            "which the obesity epidemic can be ameliorated.\n\n"
            "To begin with, it should be unsurprising that fast food is incredibly popular in "
            "wealthy countries. Due to the high levels of development in these countries, consumers "
            "possess more money and can therefore consume vast amounts of fast food without "
            "seriously diminishing their income. For example, the American Dietary Association found "
            "that compared to the average Indian household, the average American household has a six "
            "times larger budget for food per month. Consequently, it is to be expected that obesity "
            "rates are much higher in countries with larger amounts of wealth.\n\n"
            "However, despite the severity of the obesity problem, there are a number of ways in "
            "which developed countries could battle it more effectively. Firstly, developed "
            "governments could put far more pressure on fast food outlets to provide healthy "
            "alternatives to hamburgers, French fries and soft drinks. Secondly, public exercise "
            "initiatives could be advertised and promoted far more vigorously. Lastly, modules that "
            "inform teenagers about healthy dietary requirements could be taught at schools.\n\n"
            "In conclusion, although obesity is a serious issue in the developed world, if we can "
            "make fast food companies accountable for damage to health and promote exercise, the "
            "situation will surely improve in the coming years."
        ),
    },
    {
        "id": "parents-who-work",
        "type": "discussion",
        "title": "Parents who both work",
        "skill_vi": "Ngữ pháp (grammar)",
        "question": "In today's competitive world, many families find it necessary for both parents "
                    "to go out to work. While some say the children in these families benefit from "
                    "the additional income, others feel they lack support because of their parents' "
                    "absence. Discuss both these views and give your own opinion.",
        "focus_vi": "Học cấu trúc câu phức: mệnh đề quan hệ, câu điều kiện, cụm danh từ phức.",
        "model": (
            "In the past, a typical family consisted of a father who went out to work and a mother "
            "who stayed at home and looked after the children; however, nowadays, it is the norm for "
            "both parents to work. This situation can affect children both positively and "
            "negatively.\n\n"
            "Some people think that the children of working parents are in an advantageous position "
            "as their parents are able to afford more luxuries such as new clothes, video games or "
            "mobile phones. Proponents of this view argue that children are able to enjoy and "
            "experience more from life due to their parents' extra wealth, for example, by going on "
            "foreign holidays.\n\n"
            "On the other hand, there are those who claim that when both parents work, their "
            "children do not get enough support and attention. This may mean that these children "
            "might not do as well at school because there is no one at home to provide support with "
            "such things as homework or exam revision. Young people may procrastinate or play games "
            "if their parents are not there to make sure they study. The absence of parents at home "
            "could also make it easier for children to get involved in such things as drugs or "
            "underage drinking. A responsible guardian at home can make sure that the young person "
            "does not get involved in dangerous activities with the wrong people.\n\n"
            "In conclusion, I believe that we cannot change the fact that both parents have to work "
            "nowadays; it is not an ideal situation, but if parents make time for their children in "
            "the evenings and at the weekends, then the children will not suffer in any way. It must "
            "be stated that the extra income generated by both parents working makes for a much "
            "higher standard of living which benefits the whole family."
        ),
    },
    {
        "id": "international-tourism",
        "type": "advantages",
        "title": "International tourism",
        "skill_vi": "Từ vựng (vocabulary)",
        "question": "International tourism has brought enormous benefit to many places. At the same "
                    "time, there is concern about its impact on local inhabitants and the "
                    "environment. Do the disadvantages of international tourism outweigh the "
                    "advantages?",
        "focus_vi": "Học tránh lặp từ bằng đồng nghĩa/paraphrase (tourists → holidaymakers, tourism → the travel sector…).",
        "model": (
            "The travel industry has experienced a major boom over recent decades, which has helped "
            "some economically weaker nations to improve their failing economies. While questions "
            "have been raised regarding the negative impacts that accompany the growth in the travel "
            "sector, these definitely do not outweigh the associated benefits.\n\n"
            "On the one hand, the rising influx of holidaymakers is associated with increased "
            "incidences of crimes and antisocial activities like drugs, human trafficking and "
            "gambling, which affect the values of the indigenous society. The local population is "
            "also affected by the growth in property prices. Environmentalists are also concerned "
            "regarding environmental remodelling that is associated with increased tourist "
            "activities in natural reserves. In this context, it is worth mentioning that, by "
            "enforcing strict law and order and implementing strict legislation, governments can "
            "control most of these negative impacts of tourism.\n\n"
            "On the other hand, the economic boost that accompanies a successful travel industry is "
            "quite well recognised. Thailand is a good example of the benefits of tourism as the "
            "Thai economy revolves around tourism and the country had been able to uplift its "
            "socio-economic status through its flourishing hospitality sector. Egypt is another "
            "nation that is heavily dependent on its hospitality sector. The growth in the number of "
            "incoming tourists leads to innumerable prospects in terms of local entrepreneurship and "
            "employment. This is also associated with international investment and infrastructure "
            "development. The national authorities, in order to ensure the safety of the "
            "international visitors, provide better law and order enforcement, improved "
            "transportation and healthcare facilities, which in turn benefit the local population.\n\n"
            "In conclusion, it can be said that, even though growth in the travel industry has "
            "accompanying negative social and environmental impacts, these do not outweigh the "
            "contributions made by this sector towards social development. However, to be successful, "
            "the government must make sure that tourism development is regulated and eco-friendly and "
            "only then can it really benefit the local community."
        ),
    },
    {
        "id": "attitude-in-tests",
        "type": "opinion",
        "title": "Attitude in tests",
        "skill_vi": "Referencing & substitution",
        "question": "Attitude is as important as knowledge in a test situation. To what extent do "
                    "you agree?",
        "focus_vi": "Học referencing (they, the latter, such people, it) để tránh lặp và viết gọn.",
        "model": (
            "Students react in different ways to different pressures; however, for many students, "
            "examinations and tests are a time of nervousness and panic. For this reason, I believe "
            "that these kinds of assessments are not a true test of the candidate's knowledge of a "
            "subject but also of his/her character.\n\n"
            "Candidates taking a test with no understanding of the subject are unlikely to do very "
            "well. Without understanding what they are being asked to respond to, they are forced to "
            "rely only on common sense, presenting an answer that may or may not be correct. In "
            "comparison with studious and prepared candidates, it is obvious that the latter would "
            "perform better. Therefore, even if the candidate performs well in test situations, "
            "he/she is unlikely to do well without knowledge of the subject.\n\n"
            "However, a counterargument can be made by considering knowledgeable but nervous "
            "candidates who lack confidence in their own abilities. Such people could find "
            "themselves sitting in the test but unable to organise any of their thoughts, finding "
            "that the time allotted for the test has gone before having time to write more than a "
            "few lines. Now compare the candidates who have written fluently and at length with "
            "candidates who have managed only a few lines, and it becomes considerably more "
            "difficult to assess whether attitude is as important as knowledge because knowledgeable "
            "candidates who lack confidence may significantly underperform.\n\n"
            "It is clear that candidates with a confident attitude but a lack of knowledge as well "
            "as others who have knowledge but lack confidence are likely to perform poorly in "
            "examinations. It is up to the individual, the school and the parents to create students "
            "who are both knowledgeable and who have the right attitude to succeed in exams."
        ),
    },
    {
        "id": "sports-public-health",
        "type": "discussion",
        "title": "Sports facilities & public health",
        "skill_vi": "Nêu rõ quan điểm (including your opinion)",
        "question": "Some people say that the best way to improve public health is to increase the "
                    "number of sports facilities. Others, however, say that this would have little "
                    "effect on public health and that other measures are required. Discuss both "
                    "these views and give your own opinion.",
        "focus_vi": "Học cách để quan điểm RÕ ở cả mở bài lẫn kết bài (thiếu quan điểm → TR chặn band 5).",
        "model": (
            "Whether building more sport facilities and gyms is the best way to improve public "
            "health is debatable. In my opinion, it is important to build more sports centers but "
            "the government needs to take other measures too.\n\n"
            "There is no denying the fact that playing sports and games improves a person's physical "
            "and mental health. When we engage ourselves in a sport, the circulation of blood "
            "through our body improves ensuring that every cell gets adequate oxygen. Sports and "
            "games also improve our mental health and intellectual skills. According to a famous "
            "Persian proverb, wisdom can only be found in a healthy body. Obviously if the body is "
            "not healthy, the mind cannot be healthy either. Lack of adequate facilities is one of "
            "the reasons that prevent people from playing sports. By building more sports facilities "
            "in towns and villages we can encourage more and more people to get physically active.\n\n"
            "On the flip side, there is very little we can achieve by simply increasing the number "
            "of sports clubs and gyms. Nutrition is as important as physical activity. If people do "
            "not eat right they will not be healthy even if they spend hours in the gym. Studies "
            "after studies have shown that unhealthy eating habits are on the rise among young "
            "people. There are also lots of people who cannot afford healthy food. They will not "
            "gain much from building more sports facilities. I am not saying that the government "
            "should not build more gyms or sports centers. However, I believe that ensuring everyone "
            "can afford healthy food and creating awareness about the importance of eating right are "
            "more important.\n\n"
            "To conclude, while it is true that sports centers play an important role in improving "
            "public health, claiming that building more of them is the best way to achieve public "
            "health is a mistake. I am not against the government building more sports facilities; "
            "however, it is my belief that authorities must also ensure that everyone can afford "
            "nutritious food."
        ),
    },
    {
        "id": "endangered-animals",
        "type": "problem",
        "title": "Endangered animals",
        "skill_vi": "Cấu trúc bài vấn đề–giải pháp",
        "question": "More and more wild animals are on the verge of extinction and others are on "
                    "the endangered list. What are the reasons for this? What can be done to solve "
                    "these problems?",
        "focus_vi": "Học cách tổ chức bài problem-solution: mỗi đoạn = một vấn đề kèm giải pháp của nó.",
        "model": (
            "Many species today are becoming extinct or are at risk of becoming so. There are many "
            "reasons for this state of affairs and in this essay I will suggest solutions for the "
            "problem of habitat destruction due to illegal logging and the degradation of waterways "
            "by industrial waste.\n\n"
            "A major factor leading to the extinction of species in tropical countries is the "
            "destruction of habitat due to illegal logging. Many tropical countries set aside large "
            "areas of forest as national parks, however, illegal loggers destroy these habitats to "
            "obtain rare hardwoods. The orangutan, found in Indonesia and Malaysia, is a prime "
            "example of an animal being pushed to extinction because of this. They are protected by "
            "law in both countries, but the jungle in which they live is cut down by unscrupulous "
            "businessmen, often with links to the government and security forces. It is essential "
            "that more money is spent on recruiting and training forest rangers whose duty it is to "
            "protect natural parks. However, this solution will be useless until the corrupt "
            "government officers and security forces who are involved in the trade in rare wood are "
            "prosecuted and handed harsher penalties in order to put off other would be corrupt "
            "officials.\n\n"
            "Industrial pollution in waterways can poison the water and eventually lead to the death "
            "of most life in the affected river. Many rivers in Europe were declared dead in the "
            "early twentieth century due to the unregulated dumping of industrial waste. However, "
            "this was turned around by waste management laws being strictly enforced and polluting "
            "businesses being prosecuted, which clearly worked as fish have since returned to the "
            "waterways. Monitoring of waste and stricter laws need to be implemented in developing "
            "nations which are making the same mistakes that were made in Europe. Again, the key to "
            "improving the situation is investment in monitoring and harsher penalties for those "
            "found to be breaking the law.\n\n"
            "In summary, two major threats to wildlife are habitat destruction due to illegal "
            "logging, and the pollution of rivers by industry. Both of these problems can be solved "
            "if the government is willing to spend the money and hunt down those breaking the law."
        ),
    },
    {
        "id": "violence-on-tv",
        "type": "opinion",
        "title": "Violence on television",
        "skill_vi": "Phát triển ý (developing ideas)",
        "question": "Violence on television has a negative impact on children's behaviour. To what "
                    "extent do you agree or disagree?",
        "focus_vi": "Học cách phát triển một topic sentence bằng giải thích + ví dụ (topic → explain → example).",
        "model": (
            "These days almost every house contains a television and it is reasonable to assume that "
            "television programs impact the behaviour of the young and impressionable. It is my "
            "belief that violence on television leads to violent behaviour for some children and "
            "fearful and withdrawn behaviour for others.\n\n"
            "Watching violent programs leads some children to copy violent behaviour. Many programs "
            "contain extremely realistic scenes of violence and it has been shown that children who "
            "watch these types of programs may think violence is normal. For example, if a child "
            "watches a scene depicting violent bullying occurring in a school he/she may think it is "
            "acceptable and so copy the behaviour. Additionally, after watching violent television, "
            "many children exhibit higher levels of aggression which can result in injuries or "
            "emotional problems. For instance, recently in the news there was the story of a child "
            "who broke his playmate's back by replicating dangerous fighting moves that he had seen "
            "on television earlier that day.\n\n"
            "Furthermore, if children witness television violence they may become withdrawn and "
            "afraid of others. It has been shown that while older children may copy violent "
            "behaviour, toddlers are more likely to become anxious, impacting their behaviour. Such "
            "children may refuse to go outside for fear of violence, which could affect their social "
            "development as they will be less likely to mix with other children and learn social "
            "skills.\n\n"
            "In conclusion, TV violence clearly negatively affects the behaviour of children. While "
            "older children may become normalized to violent behaviour or even copy it, younger ones "
            "may become anxious and display fearful behaviour. Parents should carefully consider what "
            "they allow their children to watch on television and should not let children watch "
            "television unattended."
        ),
    },
    {
        "id": "exploiting-animals",
        "type": "discussion",
        "title": "Exploiting animals",
        "skill_vi": "Cấu trúc bài (structure 2)",
        "question": "Some people say it is acceptable to use animals for our benefit, others say it "
                    "is wrong to exploit them. Discuss both points of view and give your opinion.",
        "focus_vi": "Củng cố khung bài: thesis nêu thứ tự lập luận, mỗi topic sentence khớp đúng thứ tự đó.",
        "model": (
            "The exploitation of animals is an issue which is often in the western media these days. "
            "An increasing number of people believe it is wrong to use animals for any reason; "
            "however, I agree with those who accept the use of animals for certain purposes.\n\n"
            "A growing number of people disagree with the exploitation of animals on ethical and "
            "environmental grounds. Many people believe that animals have the same rights as humans "
            "since animals think and feel emotion and pain as humans do. In the same way that people "
            "shouldn't be exploited because of this, neither should animals. Moreover, the "
            "exploitation of cattle and sheep for their meat creates a huge amount of methane from "
            "the animals themselves. Also, the shipping of meat around the world creates a lot of "
            "carbon dioxide. Both of these gases are increasing global warming and as responsible "
            "citizens of the earth we should try and limit global warming as it is a threat to "
            "everyone.\n\n"
            "Although there are strong reasons against the use of animals, I believe that the use of "
            "animals for medical testing and the consumption of locally farmed animals is "
            "acceptable. Modern medicine, which saves countless lives, is tested on animals before "
            "humans. This is done in order not to endanger humans and without this, it is possible "
            "that many people would suffer. Furthermore, the consumption of locally sourced meat "
            "removes the concern of greenhouse gas emission from transportation. If the meat "
            "consumed is chicken or duck this further reduces the greenhouse emissions due to less "
            "methane being produced by these animals.\n\n"
            "In conclusion, although there are ethical and environmental reasons for not exploiting "
            "animals, I believe that medical testing on animals benefits society and the consumption "
            "of locally produced meat does not have a negative environmental impact. Government and "
            "business should ensure that animals are responsibly used and that no abuse occurs."
        ),
    },
    {
        "id": "studying-abroad",
        "type": "opinion",
        "title": "Studying abroad",
        "skill_vi": "Từ nối & referencing",
        "question": "Many students today may study abroad for a part or for all of their course. "
                    "Although studying abroad has many benefits for the individual student, it also "
                    "has a number of disadvantages. To what extent do you agree or disagree with this?",
        "focus_vi": "Tổng hợp: từ nối đúng chức năng + referencing (this, it, one, these effects, for these reasons).",
        "model": (
            "Recently a large increase can be seen in the number of students going abroad to study. "
            "This is partly because people are better off and partly due to the diverse range of "
            "different grants and scholarships which are available for overseas students. Although "
            "foreign study may not be advisable for some because of personal or financial reasons, I "
            "believe the majority of students benefit a great deal from overseas study.\n\n"
            "Studying in a foreign country has a number of benefits. For example, it could give "
            "students access to knowledge and facilities such as libraries and science labs which "
            "are not found in the student's country of origin. Furthermore, students may have access "
            "to a wider range of courses in foreign countries than they do at home, which could help "
            "them to find one that fits more closely with their individual interests and "
            "requirements. In studying these courses in a foreign tongue, the student is likely to "
            "develop their language skills very quickly.\n\n"
            "On the other hand, studying abroad can have certain drawbacks. These can be categorized "
            "into personal and professional. Firstly, studying abroad obviously requires the student "
            "to leave their family and friends for a long period, which may make the student lonely "
            "if they are unused to spending time away from their support network. Secondly, studying "
            "in a foreign country is almost always more expensive than studying in the student's "
            "home country. Studying in a foreign country, moreover, means the student will probably "
            "be studying in a foreign language, which may limit their performance and make studying "
            "and exams more stressful. These effects, however, are usually only temporary since the "
            "student will typically return home after a year or two.\n\n"
            "Overall, students who study abroad usually become proficient in the language quickly "
            "and they have lots of experiences and opportunities that they would not encounter at "
            "home. For these reasons students should seriously consider studying in a foreign country."
        ),
    },
]

BANK_BY_ID: dict[str, dict[str, Any]] = {item["id"]: item for item in BANK}


def bank_public() -> list[dict[str, Any]]:
    """Bank without model answers — the learner should write before seeing them."""
    return [
        {
            "id": it["id"],
            "type": it["type"],
            "title": it["title"],
            "question": it["question"],
            "skill_vi": it.get("skill_vi", ""),
            "focus_vi": it.get("focus_vi", ""),
            "model_words": len(it["model"].split()),
        }
        for it in BANK
    ]


def model_answer(item_id: str) -> dict[str, Any] | None:
    it = BANK_BY_ID.get(item_id)
    if not it:
        return None
    return {"id": it["id"], "model": it["model"], "words": len(it["model"].split())}
