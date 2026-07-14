"""IELTS Writing Task 1 knowledge base + question bank.

Two things live here:

* ``KNOWLEDGE`` — the method (Simon's band-9 approach), shown to the learner in the
  app *and* injected into the LLM prompts so generated tasks and grading follow the
  same rules the learner is taught.
* ``BANK`` — 22 real Task 1 questions with their original chart images (extracted
  from the band-9 collection) and full band-9 model answers.

Images live in ``web/task1/<image>`` and are served from ``/static/task1/``.
"""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------- method

TYPES: dict[str, dict[str, str]] = {
    "line": {"label_vi": "Biểu đồ đường", "label_en": "Line graph"},
    "bar": {"label_vi": "Biểu đồ cột", "label_en": "Bar chart"},
    "table": {"label_vi": "Bảng số liệu", "label_en": "Table"},
    "pie": {"label_vi": "Biểu đồ tròn", "label_en": "Pie chart"},
    "map": {"label_vi": "Bản đồ / sơ đồ", "label_en": "Map / plan"},
    "process": {"label_vi": "Quy trình", "label_en": "Process diagram"},
}

# The 4-paragraph skeleton — identical for every chart type.
STRUCTURE: list[dict[str, str]] = [
    {
        "name": "1. Introduction (1 câu)",
        "body_vi": "Diễn đạt lại đề bài bằng từ của bạn. Đổi từ vựng và cấu trúc, "
                   "KHÔNG chép lại đề — chữ chép nguyên si không được tính là từ của bạn.",
        "example": "The line graph compares the percentage of people in three countries who used "
                   "the Internet between 1999 and 2009.",
    },
    {
        "name": "2. Overview (2 câu, KHÔNG có số)",
        "body_vi": "Nhìn bức tranh lớn: xu hướng chung từ đầu kỳ đến cuối kỳ, cái cao nhất / thấp "
                   "nhất, khác biệt nổi bật nhất. Đây là đoạn quyết định band Task Achievement — "
                   "thiếu overview thì TA bị chặn trần ở band 5, dù các đoạn khác hay tới đâu.",
        "example": "It is clear that the proportion of the population who used the Internet increased "
                   "in each country. Overall, a much larger percentage of Canadians and Americans had "
                   "access to the Internet in comparison with Mexicans.",
    },
    {
        "name": "3. Details 1 (số liệu)",
        "body_vi": "Bắt đầu bằng năm/nhóm ĐẦU TIÊN và so sánh các đối tượng với nhau ngay trong câu. "
                   "Không mô tả từng đường/từng cột riêng lẻ — giám khảo chấm khả năng SO SÁNH.",
        "example": "In 1999, the proportion of people using the Internet in the USA was about 20%. The "
                   "figures for Canada and Mexico were lower, at about 10% and 5% respectively.",
    },
    {
        "name": "4. Details 2 (số liệu)",
        "body_vi": "Nhóm số liệu còn lại: năm cuối, đỉnh/đáy, thay đổi lớn nhất. Mỗi đoạn detail nên "
                   "có ít nhất 3 con số.",
        "example": "By 2009, the percentage of Internet users was highest in Canada. Almost 100% of "
                   "Canadians used the Internet, compared to about 80% of Americans and only 40% of Mexicans.",
    },
]

RULES_VI: list[str] = [
    "20 phút, tối thiểu 150 từ — viết khoảng 170–190 từ là vừa đẹp (dưới 150 bị trừ thẳng).",
    "Task 1 KHÔNG có ý kiến cá nhân, KHÔNG giải thích nguyên nhân ('vì kinh tế phát triển…'), "
    "KHÔNG có kết luận kiểu Task 2. Chỉ mô tả cái biểu đồ cho thấy.",
    "Overview không chứa con số. Số liệu chỉ nằm ở 2 đoạn detail.",
    "Không mô tả tuần tự từng đường/từng cột/từng hàng — luôn so sánh chúng với nhau.",
    "Không nhồi hết mọi con số: chọn số BIẾT NÓI — mốc đầu, mốc cuối, đỉnh, đáy, thay đổi lớn nhất. "
    "Bỏ qua các số 'lưng chừng'.",
    "Thì: quá khứ đơn cho mốc quá khứ (increased, fell); 'will / is expected to' cho tương lai; "
    "hiện tại đơn nếu biểu đồ không gắn mốc thời gian; quy trình dùng hiện tại đơn + bị động.",
    "Với line/bar/table: KHÔNG dùng bị động ('the number was increased'), tiếp diễn ('was increasing') "
    "hay hoàn thành ('has increased') để tả xu hướng.",
]

TYPE_TIPS: dict[str, list[str]] = {
    "line": [
        "Line graph luôn là thay đổi theo thời gian → xương sống của bài là xu hướng.",
        "Overview: từ mốc đầu đến mốc cuối, tất cả các đường cùng tăng/cùng giảm hay trái chiều? "
        "Đường nào cao nhất, đường nào tăng nhanh nhất?",
        "Không đủ chỗ tả mọi năm: bắt buộc có năm đầu + năm cuối, cộng thêm các năm 'đặc biệt' "
        "(đỉnh, đáy, chỗ đảo chiều, chỗ hai đường cắt nhau).",
        "Mở đoạn detail đầu bằng năm đầu tiên, so sánh các đường ngay tại đó.",
    ],
    "bar": [
        "Cột có thể theo thời gian (xu hướng) hoặc chỉ so sánh các nhóm — đọc kỹ trục hoành trước khi viết.",
        "Overview: cột nào cao nhất / thấp nhất toàn biểu đồ, nhóm nào áp đảo nhóm nào.",
        "Nếu đề có 2-3 biểu đồ, đừng tả lần lượt từng cái: gom nhóm thông tin (ví dụ 'các số liệu của "
        "nước phát triển' vs 'nước đang phát triển') rồi so sánh xuyên biểu đồ.",
        "Nhóm số liệu theo ý nghĩa, không theo thứ tự cột trên hình.",
    ],
    "table": [
        "Bảng nhiều số nhìn rất ngợp — trước khi viết, khoanh số LỚN NHẤT và NHỎ NHẤT của mỗi hàng/cột. "
        "Bỏ hẳn các số lưng chừng.",
        "Overview: so sánh cả hàng / cả cột với nhau, đừng so hai ô lẻ. Nếu không so được nhóm thì so "
        "số lớn nhất với số nhỏ nhất.",
        "Chia số đã khoanh thành 2 nhóm cho 2 đoạn detail (ví dụ: đoạn 3 các số cao, đoạn 4 các số thấp).",
        "Bảng không có mốc thời gian → dùng hiện tại đơn.",
    ],
    "pie": [
        "Pie chart là TỈ TRỌNG. Ngôn ngữ đặc trưng: account for, make up, constitute, represent.",
        "Nếu có nhiều pie theo năm/theo nước: so sánh chéo giữa các pie (cái gì đổi ngôi, cái gì giữ nguyên), "
        "đừng tả lần lượt từng cái bánh.",
        "Cẩn thận bẫy tổng số: % tăng nhưng tổng giảm thì lượng tuyệt đối có thể vẫn giảm — và ngược lại.",
        "Overview: miếng lớn nhất, miếng nhỏ nhất, thay đổi tỉ trọng đáng kể nhất.",
    ],
    "map": [
        "So sánh 2 thời điểm (hoặc 2 phương án). Overview: thay đổi tổng thể lớn nhất là gì "
        "(mở rộng, hiện đại hoá, mất mảng xanh…).",
        "Ngôn ngữ vị trí: to the north/south of, in the north-eastern corner, alongside, opposite, "
        "adjacent to, surrounded by, on the site of.",
        "Ngôn ngữ thay đổi: was built / was demolished / was converted into / was replaced by / "
        "was extended / remained unchanged. Bản đồ tương lai: will be built, is going to be converted.",
        "Đi theo trật tự không gian hoặc thời gian nhất quán — đừng nhảy lung tung trên bản đồ.",
    ],
    "process": [
        "Overview: nói rõ có BAO NHIÊU giai đoạn, quy trình bắt đầu ở đâu và kết thúc ở đâu.",
        "Hiện tại đơn + BỊ ĐỘNG là mặc định ('the clay is put in a mould'), vì không cần biết ai làm.",
        "Phải nhắc đủ MỌI giai đoạn — bỏ sót là mất điểm Task Achievement.",
        "Ngôn ngữ trình tự: at the first/second/final stage, next, after that, then, once X has been done, "
        "before being…, finally.",
        "Quy trình vòng tròn (water cycle) thì nói rõ nó quay lại điểm bắt đầu.",
    ],
}

LANGUAGE: list[dict[str, Any]] = [
    {
        "group_vi": "Tăng",
        "items": ["rise / a rise", "increase / an increase", "grow / growth", "climb", "surge / a surge",
                  "jump / a jump", "rocket", "soar"],
    },
    {
        "group_vi": "Giảm",
        "items": ["fall / a fall", "drop / a drop", "decline / a decline", "decrease / a decrease",
                  "dip", "plummet", "plunge"],
    },
    {
        "group_vi": "Ổn định / dao động",
        "items": ["remain stable", "remain steady at", "stay at around", "level off", "plateau",
                  "remain unchanged", "fluctuate / a fluctuation", "vary"],
    },
    {
        "group_vi": "Đỉnh & đáy",
        "items": ["peak at", "reach a peak of", "hit a high of", "hit a low of", "bottom out",
                  "fall to a low of"],
    },
    {
        "group_vi": "Mức độ (trạng từ + tính từ)",
        "items": ["dramatically / a dramatic rise", "sharply / a sharp fall", "significantly",
                  "considerably", "markedly", "steadily / a steady increase", "gradually",
                  "slightly / a slight dip", "marginally"],
    },
    {
        "group_vi": "Cấu trúc lõi",
        "items": [
            "rose BY 10% (mức thay đổi) ≠ rose TO 30% (điểm đến)",
            "There was a sharp rise IN sales.",
            "X saw / experienced a fall in…",
            "X was responsible for / accounted for 25% of…",
            "The figure for X stood at 40%.",
            "…, reaching a peak of 1 million in 2005. (V-ing nối, có dấu phẩy trước)",
            "Sales fell, whereas / while profits rose.",
            "…, compared to about 80% of Americans.",
        ],
    },
    {
        "group_vi": "Xấp xỉ & tỉ lệ",
        "items": ["around / approximately / roughly", "just over / just under", "nearly / almost",
                  "well over", "one fifth / a quarter / half", "twice as much as",
                  "three times higher than", "265 times more"],
    },
]

TRAPS_VI: list[str] = [
    "Không có đoạn overview → Task Achievement chặn trần band 5. Đây là lỗi giết band số 1.",
    "Đưa ý kiến / suy đoán nguyên nhân ('có lẽ do kinh tế phát triển') → ngoài phạm vi Task 1.",
    "Tả lần lượt từng đường, từng cột, không hề so sánh → mất điểm ngay.",
    "Chép nguyên đề bài làm câu mở → phần chép không được tính từ.",
    "Liệt kê mọi con số như đọc bảng → bài rời rạc, không có 'key features'.",
    "Đọc sai đơn vị (nghìn vs triệu, % vs số tuyệt đối) → sai dữ liệu, tụt band nặng.",
    "Viết dưới 150 từ.",
]

KNOWLEDGE: dict[str, Any] = {
    "intro_vi": "Task 1 không phải bài luận: bạn là phóng viên số liệu. Việc duy nhất là chọn ra "
                "những đặc điểm nổi bật nhất rồi mô tả và so sánh chúng chính xác — trong 20 phút, "
                "tối thiểu 150 từ, không ý kiến, không suy đoán.",
    "structure": STRUCTURE,
    "rules_vi": RULES_VI,
    "type_tips": TYPE_TIPS,
    "language": LANGUAGE,
    "traps_vi": TRAPS_VI,
    "types": TYPES,
}


def prompt_knowledge(chart_type: str) -> str:
    """Compact English digest of the method, injected into LLM prompts."""
    tips = TYPE_TIPS.get(chart_type, [])
    return (
        "IELTS Writing Task 1 method (Simon / band 9):\n"
        "- 4 paragraphs: introduction (paraphrase the question), overview (2 sentences, NO figures, "
        "the big picture: overall trend, highest/lowest, biggest difference), then 2 detail paragraphs "
        "carrying the figures.\n"
        "- Never describe each line/bar/row separately: the examiner rewards COMPARISON.\n"
        "- Select key features only (first point, last point, peaks, lows, biggest change); ignore "
        "middle-of-the-road numbers.\n"
        "- No opinions, no speculation about causes, no Task-2-style conclusion.\n"
        "- 150+ words, 20 minutes. Past simple for past years; present simple if no time is shown; "
        "present simple + passive for processes.\n"
        + ("Type-specific (" + chart_type + "): " + " ".join(tips) if tips else "")
    )


# ----------------------------------------------------------------------- bank
# Every item: a real Task 1 question, its original image, and a band-9 model answer.

BANK: list[dict[str, Any]] = [
    {
        "id": "internet-users",
        "type": "line",
        "title": "Internet users as percentage of population",
        "question": "The line graph below shows the percentage of the population in three countries "
                    "who used the Internet between 1999 and 2009. Summarise the information by "
                    "selecting and reporting the main features, and make comparisons where relevant.",
        "image": "internet-users.png",
        "focus_vi": "Bài mẫu chuẩn nhất để học cấu trúc 4 đoạn: overview không số, detail mở bằng năm đầu.",
        "model": (
            "The line graph compares the percentage of people in three countries who used the Internet "
            "between 1999 and 2009.\n\n"
            "It is clear that the proportion of the population who used the Internet increased in each "
            "country over the period shown. Overall, a much larger percentage of Canadians and Americans "
            "had access to the Internet in comparison with Mexicans, and Canada experienced the fastest "
            "growth in Internet usage.\n\n"
            "In 1999, the proportion of people using the Internet in the USA was about 20%. The figures "
            "for Canada and Mexico were lower, at about 10% and 5% respectively. In 2005, Internet usage "
            "in both the USA and Canada rose to around 70% of the population, while the figure for Mexico "
            "reached just over 25%.\n\n"
            "By 2009, the percentage of Internet users was highest in Canada. Almost 100% of Canadians "
            "used the Internet, compared to about 80% of Americans and only 40% of Mexicans."
        ),
    },
    {
        "id": "uk-migration",
        "type": "line",
        "title": "International migration in the UK",
        "question": "The chart below gives information about UK immigration, emigration and net "
                    "migration between 1999 and 2008. Summarise the information by selecting and "
                    "reporting the main features, and make comparisons where relevant.",
        "image": "uk-migration.png",
        "focus_vi": "Đề lai (đường + cột) và có khái niệm 'net' — luyện cách xử lý 3 dữ liệu liên quan nhau.",
        "model": (
            "The chart gives information about UK immigration, emigration and net migration between "
            "1999 and 2008.\n\n"
            "Both immigration and emigration rates rose over the period shown, but the figures for "
            "immigration were significantly higher. Net migration peaked in 2004 and 2007.\n\n"
            "In 1999, over 450,000 people came to live in the UK, while the number of people who "
            "emigrated stood at just under 300,000. The figure for net migration was around 160,000, "
            "and it remained at a similar level until 2003. From 1999 to 2004, the immigration rate "
            "rose by nearly 150,000 people, but there was a much smaller rise in emigration. Net "
            "migration peaked at almost 250,000 people in 2004.\n\n"
            "After 2004, the rate of immigration remained high, but the number of people emigrating "
            "fluctuated. Emigration fell suddenly in 2007, before peaking at about 420,000 people in "
            "2008. As a result, the net migration figure rose to around 240,000 in 2007, but fell back "
            "to around 160,000 in 2008."
        ),
    },
    {
        "id": "acid-rain",
        "type": "line",
        "title": "UK acid rain emissions",
        "question": "The graph below shows UK acid rain emissions, measured in millions of tonnes, "
                    "from four different sectors between 1990 and 2007. Summarise the information by "
                    "selecting and reporting the main features, and make comparisons where relevant.",
        "image": "acid-rain.png",
        "focus_vi": "4 đường cùng giảm nhưng tốc độ khác nhau — luyện so sánh mức độ giảm.",
        "note_vi": "Trong PDF đây là bài điền từ; bản mẫu dưới đây đã điền đầy đủ đáp án.",
        "model": (
            "The line graph compares four sectors in terms of the amount of acid rain emissions that "
            "they produced over a period of 17 years in the UK.\n\n"
            "It is clear that the total amount of acid rain emissions in the UK fell considerably "
            "between 1990 and 2007. The most dramatic decrease was seen in the electricity, gas and "
            "water supply sector.\n\n"
            "In 1990, around 3.3 million tonnes of acid rain emissions came from the electricity, gas "
            "and water sector. The transport and communication sector was responsible for about 0.7 "
            "million tonnes of emissions, while the domestic sector produced around 0.6 million tonnes. "
            "Just over 2 million tonnes of acid rain gases came from other industries.\n\n"
            "Emissions from electricity, gas and water supply fell dramatically to only 0.5 million "
            "tonnes in 2007, a drop of almost 3 million tonnes. While acid rain gases from the domestic "
            "sector and other industries fell gradually, the transport sector saw a small increase in "
            "emissions, reaching a peak of 1 million tonnes in 2005."
        ),
    },
    {
        "id": "water-consumption",
        "type": "line",
        "title": "Global water use & consumption in two countries",
        "question": "The graph and table below give information about water use worldwide and water "
                    "consumption in two different countries. Summarise the information by selecting and "
                    "reporting the main features, and make comparisons where relevant.",
        "image": "water-consumption.png",
        "focus_vi": "Hai nguồn dữ liệu (đồ thị + bảng) trong một đề — overview phải bao cả hai.",
        "model": (
            "The charts compare the amount of water used for agriculture, industry and homes around the "
            "world, and water use in Brazil and the Democratic Republic of Congo.\n\n"
            "It is clear that global water needs rose significantly between 1900 and 2000, and that "
            "agriculture accounted for the largest proportion of water used. We can also see that water "
            "consumption was considerably higher in Brazil than in the Congo.\n\n"
            "In 1900, around 500km³ of water was used by the agriculture sector worldwide. The figures "
            "for industrial and domestic water consumption stood at around one fifth of that amount. By "
            "2000, global water use for agriculture had increased to around 3000km³, industrial water "
            "use had risen to just under half that amount, and domestic consumption had reached "
            "approximately 500km³.\n\n"
            "In the year 2000, the populations of Brazil and the Congo were 176 million and 5.2 million "
            "respectively. Water consumption per person in Brazil, at 359m³, was much higher than that "
            "in the Congo, at only 8m³, and this could be explained by the fact that Brazil had 265 "
            "times more irrigated land."
        ),
    },
    {
        "id": "car-ownership",
        "type": "line",
        "title": "Car ownership in Britain",
        "question": "The graph below gives information about car ownership in Britain from 1971 to "
                    "2007. Summarise the information by selecting and reporting the main features, and "
                    "make comparisons where relevant.",
        "image": "car-ownership.png",
        "focus_vi": "Bốn nhóm hộ gia đình, hai đường đổi ngôi nhau — luyện tả điểm giao và xu hướng ngược chiều.",
        "note_vi": "Trong PDF đây là bài điền từ; bản mẫu dưới đây đã điền đầy đủ đáp án.",
        "model": (
            "The graph shows changes in the number of cars per household in Great Britain over a period "
            "of 36 years.\n\n"
            "Overall, car ownership in Britain increased between 1971 and 2007. In particular, the "
            "number of households with two cars rose, while the number of households without a car "
            "fell.\n\n"
            "In 1971, almost half of all British households did not have regular use of a car. Around "
            "44% of households had one car, but only about 7% had two cars. It was uncommon for families "
            "to own three or more cars, with around 2% of households falling into this category.\n\n"
            "The one-car household was the most common type from the late 1970's onwards, although there "
            "was little change in the figures for this category. The biggest change was seen in the "
            "proportion of households without a car, which fell steadily over the 36-year period to "
            "around 25% in 2007. In contrast, the proportion of two-car families rose steadily, reaching "
            "about 26% in 2007, and the proportion of households with more than two cars rose by around 5%."
        ),
    },
    {
        "id": "marriages-divorces",
        "type": "bar",
        "title": "Marriages and divorces in the USA",
        "question": "The first chart below shows the number of marriages and divorces in the USA "
                    "between 1970 and 2000. The second chart shows the marital status of adult "
                    "Americans in 1970 and 2000. Summarise the information by selecting and reporting "
                    "the main features, and make comparisons where relevant.",
        "image": "marriages-divorces.png",
        "focus_vi": "Hai biểu đồ khác đơn vị (triệu người vs %) — overview phải nói được cả hai mà không lẫn.",
        "model": (
            "The first bar chart shows changes in the number of marriages and divorces in the USA, and "
            "the second chart shows figures for the marital status of American adults in 1970 and 2000.\n\n"
            "It is clear that there was a fall in the number of marriages in the USA between 1970 and "
            "2000. The majority of adult Americans were married in both years, but the proportion of "
            "single adults was higher in 2000.\n\n"
            "In 1970, there were 2.5 million marriages in the USA and 1 million divorces. The marriage "
            "rate remained stable in 1980, but fell to 2 million by the year 2000. In contrast, the "
            "divorce rate peaked in 1980, at nearly 1.5 million divorces, before falling back to 1 "
            "million at the end of the period.\n\n"
            "Around 70% of American adults were married in 1970, but this figure dropped to just under "
            "60% by 2000. At the same time, the proportion of unmarried people and divorcees rose by "
            "about 10% in total. The proportion of widowed Americans was slightly lower in 2000."
        ),
    },
    {
        "id": "participation",
        "type": "bar",
        "title": "Participation in education and science",
        "question": "The charts below show the levels of participation in education and science in "
                    "developing and industrialised countries in 1980 and 1990. Summarise the information "
                    "by selecting and reporting the main features, and make comparisons where relevant.",
        "image": "participation.png",
        "focus_vi": "BA biểu đồ cùng lúc — cách gom nhóm thông tin thay vì tả lần lượt từng cái.",
        "model": (
            "The three bar charts show average years of schooling, numbers of scientists and "
            "technicians, and research and development spending in developing and developed countries. "
            "Figures are given for 1980 and 1990.\n\n"
            "It is clear from the charts that the figures for developed countries are much higher than "
            "those for developing nations. Also, the charts show an overall increase in participation in "
            "education and science from 1980 to 1990.\n\n"
            "People in developing nations attended school for an average of around 3 years, with only a "
            "slight increase in years of schooling from 1980 to 1990. On the other hand, the figure for "
            "industrialised countries rose from nearly 9 years of schooling in 1980 to nearly 11 years "
            "in 1990.\n\n"
            "From 1980 to 1990, the number of scientists and technicians in industrialised countries "
            "almost doubled to about 70 per 1000 people. Spending on research and development also saw "
            "rapid growth in these countries, reaching $350 billion in 1990. By contrast, the number of "
            "science workers in developing countries remained below 20 per 1000 people, and research "
            "spending fell from about $50 billion to only $25 billion."
        ),
    },
    {
        "id": "consumer-goods",
        "type": "bar",
        "title": "Spending on consumer goods in four countries",
        "question": "The bar chart below shows the amount of money spent on six consumer goods in four "
                    "European countries. Summarise the information by selecting and reporting the main "
                    "features, and make comparisons where relevant.",
        "image": "consumer-goods.png",
        "focus_vi": "Không có mốc thời gian → hiện tại/quá khứ đơn thuần so sánh, và phải chọn số 'biết nói' trong rừng cột.",
        "model": (
            "The bar chart compares consumer spending on six different items in Germany, Italy, France "
            "and Britain.\n\n"
            "It is clear that British people spent significantly more money than people in the other "
            "three countries on all six goods. Of the six items, consumers spent the most money on "
            "photographic film.\n\n"
            "People in Britain spent just over £170,000 on photographic film, which is the highest "
            "figure shown on the chart. By contrast, Germans were the lowest overall spenders, with "
            "roughly the same figures (just under £150,000) for each of the six products.\n\n"
            "The figures for spending on toys were the same in both France and Italy, at nearly "
            "£160,000. However, while French people spent more than Italians on photographic film and "
            "CDs, Italians paid out more for personal stereos, tennis racquets and perfumes. The amount "
            "spent by French people on tennis racquets, around £145,000, is the lowest figure shown on "
            "the chart."
        ),
    },
    {
        "id": "house-prices",
        "type": "bar",
        "title": "Average house prices in five cities",
        "question": "The chart below shows information about changes in average house prices in five "
                    "different cities between 1990 and 2002 compared with the average house prices in "
                    "1989. Summarise the information by selecting and reporting the main features, and "
                    "make comparisons where relevant.",
        "image": "house-prices.png",
        "focus_vi": "Số âm/dương so với một mốc gốc — bẫy hiểu sai 'phần trăm thay đổi so với 1989'.",
        "model": (
            "The bar chart compares the cost of an average house in five major cities over a period of "
            "13 years from 1989.\n\n"
            "We can see that house prices fell overall between 1990 and 1995, but most of the cities saw "
            "rising prices between 1996 and 2002. London experienced by far the greatest changes in "
            "house prices over the 13-year period.\n\n"
            "Over the 5 years after 1989, the cost of average homes in Tokyo and London dropped by "
            "around 7%, while New York house prices went down by 5%. By contrast, prices rose by "
            "approximately 2% in both Madrid and Frankfurt.\n\n"
            "Between 1996 and 2002, London house prices jumped to around 12% above the 1989 average. "
            "Homebuyers in New York also had to pay significantly more, with prices rising to 5% above "
            "the 1989 average, but homes in Tokyo remained cheaper than they were in 1989. The cost of "
            "an average home in Madrid rose by a further 2%, while prices in Frankfurt remained stable."
        ),
    },
    {
        "id": "rail-networks",
        "type": "table",
        "title": "Underground railway systems in six cities",
        "question": "The table below gives information about the underground railway systems in six "
                    "cities. Summarise the information by selecting and reporting the main features, and "
                    "make comparisons where relevant.",
        "image": "rail-networks.png",
        "focus_vi": "Bảng kinh điển: gom 6 thành phố thành 2 nhóm (cũ/mới) thay vì tả từng dòng.",
        "model": (
            "The table shows data about the underground rail networks in six major cities.\n\n"
            "The table compares the six networks in terms of their age, size and the number of people "
            "who use them each year. It is clear that the three oldest underground systems are larger "
            "and serve significantly more passengers than the newer systems.\n\n"
            "The London underground is the oldest system, having opened in 1863. It is also the largest "
            "system, with 394 kilometres of route. The second largest system, in Paris, is only about "
            "half the size of the London underground, with 199 kilometres of route. However, it serves "
            "more people per year. While only third in terms of size, the Tokyo system is easily the "
            "most used, with 1927 million passengers per year.\n\n"
            "Of the three newer networks, the Washington DC underground is the most extensive, with 126 "
            "kilometres of route, compared to only 11 kilometres and 28 kilometres for the Kyoto and Los "
            "Angeles systems. The Los Angeles network is the newest, having opened in 2001, while the "
            "Kyoto network is the smallest and serves only 45 million passengers per year."
        ),
    },
    {
        "id": "poverty-australia",
        "type": "table",
        "title": "Families living in poverty in Australia",
        "question": "The table below shows the proportion of different categories of families living in "
                    "poverty in Australia in 1999. Summarise the information by selecting and reporting "
                    "the main features, and make comparisons where relevant.",
        "image": "poverty-australia.png",
        "focus_vi": "Bảng không có thời gian → thì quá khứ đơn theo năm 1999, và tìm quy luật (độc thân vs cặp đôi).",
        "model": (
            "The table gives information about poverty rates among six types of household in Australia "
            "in the year 1999.\n\n"
            "It is noticeable that levels of poverty were higher for single people than for couples, and "
            "people with children were more likely to be poor than those without. Poverty rates were "
            "considerably lower among elderly people.\n\n"
            "Overall, 11% of Australians, or 1,837,000 people, were living in poverty in 1999. Aged "
            "people were the least likely to be poor, with poverty levels of 6% and 4% for single aged "
            "people and aged couples respectively.\n\n"
            "Just over one fifth of single parents were living in poverty, whereas only 12% of parents "
            "living with a partner were classed as poor. The same pattern can be seen for people with no "
            "children: while 19% of single people in this group were living below the poverty line, the "
            "figure for couples was much lower, at only 7%."
        ),
    },
    {
        "id": "daily-activities",
        "type": "table",
        "title": "Daily activities of UK males and females",
        "question": "The table below shows the average hours and minutes spent by UK males and females "
                    "on different daily activities. Summarise the information by selecting and reporting "
                    "the main features, and make comparisons where relevant.",
        "image": "daily-activities.png",
        "focus_vi": "Bảng rất nhiều dòng — bài mẫu chỉ chọn 4-5 dòng biết nói (sleep, leisure, work, housework, childcare).",
        "note_vi": "Trong PDF đây là bài điền từ; bản mẫu dưới đây đã điền đầy đủ đáp án.",
        "model": (
            "The table compares the average amount of time per day that men and women in the UK spend "
            "doing different activities.\n\n"
            "It is clear that people in the UK spend more time sleeping than doing any other daily "
            "activity. Also, there are significant differences between the time spent by men and women "
            "on employment/study and housework.\n\n"
            "On average, men and women in the UK sleep for about 8 hours per day. Leisure takes up the "
            "second largest proportion of their time. Men spend 5 hours and 25 minutes doing various "
            "leisure activities, such as watching TV or doing sport, while women have 4 hours and 53 "
            "minutes of leisure time.\n\n"
            "It is noticeable that men work or study for an average of 79 minutes more than women every "
            "day. By contrast, women spend 79 minutes more than men doing housework, and they spend over "
            "twice as much time looking after children."
        ),
    },
    {
        "id": "consumer-expenditure",
        "type": "table",
        "title": "Consumer expenditure in five countries",
        "question": "The table below gives information on consumer spending on different items in five "
                    "different countries in 2002. Summarise the information by selecting and reporting "
                    "the main features, and make comparisons where relevant.",
        "image": "consumer-expenditure.png",
        "focus_vi": "Chia 2 đoạn detail theo 'các số cao nhất' rồi 'các số thấp nhất' — đúng công thức bảng của Simon.",
        "model": (
            "The table shows percentages of consumer expenditure for three categories of products and "
            "services in five countries in 2002.\n\n"
            "It is clear that the largest proportion of consumer spending in each country went on food, "
            "drinks and tobacco. On the other hand, the leisure/education category has the lowest "
            "percentages in the table.\n\n"
            "Out of the five countries, consumer spending on food, drinks and tobacco was noticeably "
            "higher in Turkey, at 32.14%, and Ireland, at nearly 29%. The proportion of spending on "
            "leisure and education was also highest in Turkey, at 4.35%, while expenditure on clothing "
            "and footwear was significantly higher in Italy, at 9%, than in any of the other countries.\n\n"
            "It can be seen that Sweden had the lowest percentages of national consumer expenditure for "
            "food/drinks/tobacco and for clothing/footwear, at nearly 16% and just over 5% respectively. "
            "Spain had slightly higher figures for these categories, but the lowest figure for "
            "leisure/education, at only 1.98%."
        ),
    },
    {
        "id": "electricity-fuel",
        "type": "pie",
        "title": "Electricity production by fuel source",
        "question": "The pie charts below show units of electricity production by fuel source in "
                    "Australia and France in 1980 and 2000. Summarise the information by selecting and "
                    "reporting the main features, and make comparisons where relevant.",
        "image": "electricity-fuel.png",
        "focus_vi": "Bốn cái bánh và TỔNG khác nhau — bẫy 'tỉ trọng giảm nhưng lượng tuyệt đối vẫn tăng'.",
        "model": (
            "The pie charts compare the amount of electricity produced using five different sources of "
            "fuel in two countries over two separate years.\n\n"
            "Total electricity production increased dramatically from 1980 to 2000 in both Australia and "
            "France. While the totals for both countries were similar, there were big differences in the "
            "fuel sources used.\n\n"
            "Coal was used to produce 50 of the total 100 units of electricity in Australia in 1980, "
            "rising to 130 out of 170 units in 2000. By contrast, nuclear power became the most "
            "important fuel source in France in 2000, producing almost 75% of the country's "
            "electricity.\n\n"
            "Australia depended on hydro power for just under 25% of its electricity in both years, but "
            "the amount of electricity produced using this type of power fell from 5 to only 2 units in "
            "France. Oil, on the other hand, remained a relatively important fuel source in France, but "
            "its use declined in Australia. Both countries relied on natural gas for electricity "
            "production significantly more in 1980 than in 2000."
        ),
    },
    {
        "id": "diet",
        "type": "pie",
        "title": "Composition of three diets",
        "question": "The pie charts below show the average composition of three different diets: an "
                    "average diet, a healthy diet, and a healthy diet for sport. Summarise the "
                    "information by selecting and reporting the main features, and make comparisons "
                    "where relevant.",
        "image": "diet.png",
        "focus_vi": "Ngôn ngữ tỉ trọng: make up, constitute, one fifth, the figure drops to…",
        "note_vi": "Trong PDF đây là bài điền từ; bản mẫu dưới đây đã điền đầy đủ đáp án.",
        "model": (
            "The pie charts compare the proportion of carbohydrates, protein and fat in three different "
            "diets, namely an average diet, a healthy diet, and a healthy diet for sport.\n\n"
            "It is noticeable that sportspeople require a diet comprising a significantly higher "
            "proportion of carbohydrates than an average diet or a healthy diet. The average diet "
            "contains the lowest percentage of carbohydrates but the highest proportion of protein.\n\n"
            "Carbohydrates make up 60% of the healthy diet for sport. This is 10% higher than the "
            "proportion of carbohydrates in a normal healthy diet, and 20% more than the proportion in "
            "an average diet. On the other hand, people who eat an average diet consume a greater "
            "relative amount of protein (40%) than those who eat a healthy diet (30%) and sportspeople "
            "(25%).\n\n"
            "The third compound shown in the charts is fat. Fat constitutes exactly one fifth of both "
            "the average diet and the healthy diet, but the figure drops to only 15% for the healthy "
            "sports diet."
        ),
    },
    {
        "id": "chorleywood",
        "type": "map",
        "title": "The village of Chorleywood",
        "question": "The map below shows the growth of a village called Chorleywood between 1868 and "
                    "1994. Summarise the information by selecting and reporting the main features, and "
                    "make comparisons where relevant.",
        "image": "chorleywood.png",
        "focus_vi": "Bản đồ phát triển theo thời gian — overview tìm ra 'quy luật': làng mọc theo hạ tầng giao thông.",
        "model": (
            "The map shows the growth of a village called Chorleywood between 1868 and 1994.\n\n"
            "It is clear that the village grew as the transport infrastructure was improved. Four "
            "periods of development are shown on the map, and each of the populated areas is near to the "
            "main roads, the railway or the motorway.\n\n"
            "From 1868 to 1883, Chorleywood covered a small area next to one of the main roads. "
            "Chorleywood Park and Golf Course is now located next to this original village area. The "
            "village grew along the main road to the south between 1883 and 1922, and in 1909 a railway "
            "line was built crossing this area from west to east. Chorleywood station is in this part of "
            "the village.\n\n"
            "The expansion of Chorleywood continued to the east and west alongside the railway line "
            "until 1970. At that time, a motorway was built to the east of the village, and from 1970 to "
            "1994, further development of the village took place around motorway intersections with the "
            "railway and one of the main roads."
        ),
    },
    {
        "id": "gallery",
        "type": "map",
        "title": "Art gallery redevelopment",
        "question": "The plans below show the layout of an art gallery at present, and how it will look "
                    "after redevelopment. Summarise the information by selecting and reporting the main "
                    "features, and make comparisons where relevant.",
        "image": "gallery.png",
        "focus_vi": "Bản đồ TƯƠNG LAI → thì tương lai (will be moved, will occupy). Rất hay bị dùng nhầm quá khứ.",
        "model": (
            "The first picture shows the layout of an art gallery, and the second shows some proposed "
            "changes to the gallery space.\n\n"
            "It is clear that significant changes will be made in terms of the use of floor space in the "
            "gallery. There will be a completely new entrance and more space for exhibitions.\n\n"
            "At present, visitors enter the gallery through doors which lead into a lobby. However, the "
            "plan is to move the entrance to the Parkinson Court side of the building, and visitors will "
            "walk straight into the exhibition area. In place of the lobby and office areas, which are "
            "shown on the existing plan, the new gallery plan shows an education area and a small "
            "storage area.\n\n"
            "The permanent exhibition space in the redeveloped gallery will be about twice as large as "
            "it is now because it will occupy the area that is now used for temporary exhibitions. There "
            "will also be a new room for special exhibitions. This room is shown in red on the existing "
            "plan and is not currently part of the gallery."
        ),
    },
    {
        "id": "house-design",
        "type": "map",
        "title": "House designs for different climates",
        "question": "The diagrams below show how house designs differ according to climate. Summarise "
                    "the information by selecting and reporting the main features, and make comparisons "
                    "where relevant.",
        "image": "house-design.png",
        "focus_vi": "Sơ đồ SO SÁNH (không phải quy trình, không theo thời gian) — tổ chức bài theo từng đặc điểm: mái, cửa sổ, vật liệu.",
        "model": (
            "The diagrams show how house designs differ according to climate.\n\n"
            "The most noticeable difference between houses designed for cool and warm climates is in the "
            "shape of the roof. The designs also differ with regard to the windows and the use of "
            "insulation.\n\n"
            "We can see that the cool climate house has a high-angled roof, which allows sunlight to "
            "enter through the window. By contrast, the roof of the warm climate house has a peak in the "
            "middle and roof overhangs to shade the windows. Insulation and thermal building materials "
            "are used in cool climates to reduce heat loss, whereas insulation and reflective materials "
            "are used to keep the heat out in warm climates.\n\n"
            "Finally, the cool climate house has one window which faces the direction of the sun, while "
            "the warm climate house has windows on two sides which are shaded from the sun. By opening "
            "the two windows at night, the house designed for warm climates can be ventilated."
        ),
    },
    {
        "id": "garlsdon",
        "type": "map",
        "title": "Two proposed supermarket sites in Garlsdon",
        "question": "The map below is of the town of Garlsdon. A new supermarket (S) is planned for the "
                    "town. The map shows two possible sites for the supermarket. Summarise the "
                    "information by selecting and reporting the main features, and make comparisons "
                    "where relevant.",
        "image": "garlsdon.png",
        "focus_vi": "Bản đồ so sánh 2 PHƯƠNG ÁN — tổ chức theo tiêu chí (vị trí, đường bộ, đường sắt), tuyệt đối không chọn phương án nào.",
        "model": (
            "The map shows two potential locations (S1 and S2) for a new supermarket in a town called "
            "Garlsdon.\n\n"
            "The main difference between the two sites is that S1 is outside the town, whereas S2 is in "
            "the town centre. The sites can also be compared in terms of access by road or rail, and "
            "their positions relative to three smaller towns.\n\n"
            "Looking at the information in more detail, S1 is in the countryside to the north west of "
            "Garlsdon, but it is close to the residential area of the town. S2 is also close to the "
            "housing area, which surrounds the town centre.\n\n"
            "There are main roads from Hindon, Bransdon and Cransdon to Garlsdon town centre, but this "
            "is a no traffic zone, so there would be no access to S2 by car. By contrast, S1 lies on the "
            "main road to Hindon, but it would be more difficult to reach from Bransdon and Cransdon. "
            "Both supermarket sites are close to the railway that runs through Garlsdon from Hindon to "
            "Cransdon."
        ),
    },
    {
        "id": "weather-forecast",
        "type": "process",
        "title": "How the Australian Bureau of Meteorology forecasts weather",
        "question": "The diagram below shows how the Australian Bureau of Meteorology collects "
                    "up-to-the-minute information on the weather in order to produce reliable forecasts. "
                    "Summarise the information by selecting and reporting the main features, and make "
                    "comparisons where relevant.",
        "image": "weather-forecast.png",
        "focus_vi": "Quy trình có NHÁNH (3 cách thu thập, 3 cách phân tích) — luyện firstly/secondly/finally.",
        "model": (
            "The figure illustrates the process used by the Australian Bureau of Meteorology to forecast "
            "the weather.\n\n"
            "There are four stages in the process, beginning with the collection of information about "
            "the weather. This information is then analysed, prepared for presentation, and finally "
            "broadcast to the public.\n\n"
            "Looking at the first and second stages of the process, there are three ways of collecting "
            "weather data and three ways of analysing it. Firstly, incoming information can be received "
            "by satellite and presented for analysis as a satellite photo. The same data can also be "
            "passed to a radar station and presented on a radar screen or synoptic chart. Secondly, "
            "incoming information may be collected directly by radar and analysed on a radar screen or "
            "synoptic chart. Finally, drifting buoys also receive data which can be shown on a synoptic "
            "chart.\n\n"
            "At the third stage of the process, the weather broadcast is prepared on computers. Finally, "
            "it is delivered to the public on television, on the radio, or as a recorded telephone "
            "announcement."
        ),
    },
    {
        "id": "brick-manufacturing",
        "type": "process",
        "title": "Brick manufacturing",
        "question": "The diagram below shows the process by which bricks are manufactured for the "
                    "building industry. Summarise the information by selecting and reporting the main "
                    "features, and make comparisons where relevant.",
        "image": "brick-manufacturing.png",
        "focus_vi": "Quy trình tuyến tính điển hình — bị động + hiện tại đơn, và phải nhắc ĐỦ mọi giai đoạn.",
        "note_vi": "PDF gốc chỉ đưa 2 đoạn thân bài; phần mở bài và overview ở đây được viết thêm đúng theo "
                   "phương pháp Simon để bạn có bài hoàn chỉnh làm mẫu.",
        "model": (
            "The diagram illustrates the various stages in the manufacture of bricks for the building "
            "industry.\n\n"
            "There are seven stages in the process, from the digging of clay to the delivery of the "
            "finished bricks. It is clear that the process is linear, and that the clay must be shaped, "
            "dried, fired and cooled before the bricks are ready to leave the factory.\n\n"
            "At the beginning of the process, clay is dug from the ground. The clay is put through a "
            "metal grid, and it passes onto a roller where it is mixed with sand and water. After that, "
            "the clay can be shaped into bricks in two ways: either it is put in a mould, or a wire "
            "cutter is used.\n\n"
            "At the fourth stage in the process, the clay bricks are placed in a drying oven for one to "
            "two days. Next, the bricks are heated in a kiln at a moderate temperature (200 - 900 "
            "degrees Celsius) and then at a high temperature (up to 1300 degrees), before spending two "
            "to three days in a cooling chamber. Finally, the finished bricks are packaged and delivered."
        ),
    },
    {
        "id": "water-cycle",
        "type": "process",
        "title": "The water cycle",
        "question": "The diagram below shows the water cycle, which is the continuous movement of water "
                    "on, above and below the surface of the Earth. Summarise the information by "
                    "selecting and reporting the main features, and make comparisons where relevant.",
        "image": "water-cycle.png",
        "focus_vi": "Quy trình TUẦN HOÀN — overview phải nói rõ nó quay lại điểm xuất phát.",
        "model": (
            "The picture illustrates the way in which water passes from ocean to air to land during the "
            "natural process known as the water cycle.\n\n"
            "Three main stages are shown on the diagram. Ocean water evaporates, falls as rain, and "
            "eventually runs back into the oceans again.\n\n"
            "Beginning at the evaporation stage, we can see that 80% of water vapour in the air comes "
            "from the oceans. Heat from the sun causes water to evaporate, and water vapour condenses to "
            "form clouds. At the second stage, labelled 'precipitation' on the diagram, water falls as "
            "rain or snow.\n\n"
            "At the third stage in the cycle, rainwater may take various paths. Some of it may fall into "
            "lakes or return to the oceans via 'surface runoff'. Otherwise, rainwater may filter through "
            "the ground, reaching the impervious layer of the earth. Salt water intrusion is shown to "
            "take place just before groundwater passes into the oceans to complete the cycle."
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
            "image": f"/static/task1/{it['image']}",
            "focus_vi": it.get("focus_vi", ""),
            "note_vi": it.get("note_vi", ""),
            "model_words": len(it["model"].split()),
        }
        for it in BANK
    ]


def model_answer(item_id: str) -> dict[str, Any] | None:
    it = BANK_BY_ID.get(item_id)
    if not it:
        return None
    return {"id": it["id"], "model": it["model"], "words": len(it["model"].split())}
