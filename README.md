# EPux

EPux là web app local giúp bạn học từ vựng + luyện Writing cho IELTS, mọi tính năng thông minh chạy bằng LLM của bạn (cấu hình trong `.env`):

- **Tự động mở rộng vốn từ**: AI đề xuất chủ đề hay gặp trong IELTS, sinh thẻ từ vựng đầy đủ (nghĩa, IPA, ví dụ, collocations, ghi chú cách dùng, band CEFR) và tránh trùng từ bạn đã có. Mỗi lượt sinh trải đều các khía cạnh của chủ đề, trộn đủ loại từ (collocation, phrasal verb, idiom, danh/động/tính/trạng từ) — không dạy từ sáo rỗng kiểu "delve", "plethora".
- **Ôn tập theo đường cong lãng quên**: thẻ mới ôn dày (10 phút → 1 giờ → 8 giờ), nhớ tốt thì giãn dần theo stability — hợp với người online thường xuyên.
- **Writing**: AI ra đề (diễn tả hoạt động thường ngày hoặc IELTS Task 2, xoay vòng dạng đề + lĩnh vực) kèm dàn ý và cấu trúc mục tiêu để thử dùng trong bài. Chấm như giám khảo thật: band theo 4 tiêu chí với nhận xét có dẫn chứng, cách lên band từng tiêu chí, liệt kê hết lỗi (phân loại ngữ pháp/từ vựng/mạch lạc...), điểm mạnh cần giữ, bản viết lại band cao hơn + vì sao nó cao hơn, kế hoạch ưu tiên cho bài sau, và từ "nâng band" thay thế trực tiếp cách diễn đạt bạn đã dùng. Kèm thư viện **mẫu câu** theo chủ đề (đa dạng chức năng: tương phản, nhân quả, đảo ngữ...), có chấm câu bạn tự đặt kèm bản nâng cấp.
- **IELTS Writing Task 1**: tri thức đầy đủ theo phương pháp Simon (bộ khung 4 đoạn, luật bất di bất dịch, mẹo riêng cho từng dạng, ngôn ngữ mô tả số liệu, lỗi giết band) + **22 đề thật có hình gốc và bài mẫu band 9** (line, bar, table, pie, map, process), hoặc để **AI ra đề mới**: AI sinh số liệu, app tự vẽ biểu đồ SVG (line/bar/pie/table). Có đồng hồ 20 phút và đếm từ như thi thật. Chấm theo đúng chuẩn Task 1 — Task **Achievement**, đối chiếu từng con số bạn viết với dữ liệu thật, và soi 4 điểm sống còn: **có overview / số liệu chính xác / không ý kiến cá nhân / đủ 150 từ**.
- **IELTS Writing Task 2**: tri thức đầy đủ (bộ khung 4 đoạn có câu mẫu, 4 tiêu chí chấm và cách ăn điểm từng cái, mẹo riêng cho 6 dạng đề, bí quyết nghĩ ý theo góc nhìn, từ nối & referencing, lỗi giết band, kèm ảnh **band descriptors chính thức**) + **12 đề thật có bài mẫu band 9** (opinion, discussion, advantages, problem–solution), hoặc để **AI ra đề mới**. Có đồng hồ 40 phút và đếm từ. Chấm theo đúng chuẩn Task 2 — Task **Response**, và soi 4 điểm sống còn: **quan điểm rõ ràng / trả lời đủ mọi phần / ý liên quan & phát triển / đủ 250 từ**.
- **Sưu tập thẻ bài**: mỗi từ là một card có độ hiếm **D → C → B → A → S → SS → SSS**, với **chòm sao riêng** (sinh từ chính từ đó) và **thần hộ mệnh Hy Lạp** theo bậc (Sinh vật → Anh hùng → Bán thần → Olympian → Zeus/Poseidon/Hades → Titan → Nguyên thủy). Hoàn thành thử thách mỗi ngày → nhận pack (Đồng/Bạc/Vàng) → mở pack: có thể ra thẻ mới, **thẻ trùng** (gộp bản sao để nâng **1-5★**, 5★ = Thăng Hoa), hoặc AI rèn từ mới đúng độ hiếm đã roll — gacha cũng là học. Bấm vào thẻ để xem chi tiết: lore, sức mạnh, % trí nhớ theo đường cong lãng quên, nâng sao.
- **Quiz trắc nghiệm**, thống kê, streak, XP/level, nhắc học Windows.

Dữ liệu SQLite local (dữ liệu từ bản cũ được giữ nguyên và tự nâng cấp schema). Code bản TUI cũ nằm trong `legacy/`.

## Cài đặt

```powershell
git clone https://github.com/YOUR_USERNAME/epux.git
cd epux
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Cấu hình LLM (.env)

Tạo file `.env` ở thư mục dự án (xem `.env.example`):

```
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=...
```

Hoặc dùng bất kỳ API OpenAI-compatible: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`.

## Chạy

```powershell
epux            # chạy server + tự mở trình duyệt (http://127.0.0.1:8765)
epux serve --port 9000 --no-browser
epux paths      # xem đường dẫn config/database
```

## Nhắc học

```powershell
epux remind --once          # thử một thông báo
epux remind --daemon        # chạy nền: nhắc theo chu kỳ, càng nhiều thẻ đến hạn nhắc càng dày
epux remind --daemon --toast
```

Script tự chạy khi đăng nhập Windows (từ bản cũ) vẫn nằm trong `scripts/`.

## Vòng học mỗi ngày

1. Mở tab **Hôm nay** — xem thẻ đến hạn, thử thách, pack chưa mở.
2. **Ôn tập** hết thẻ đến hạn (phím Space lật thẻ, 1-4 chấm điểm).
3. Làm **Quiz** 10 câu, thêm từ mới (AI sinh theo chủ đề IELTS).
4. Viết một bài **Writing** để AI chấm.
5. Nhận pack từ thử thách → **mở pack** ở tab Bộ sưu tập. 🃏

## Ghi chú kỹ thuật

- Backend: FastAPI + SQLite (`epux/server.py`, `epux/db.py`).
- Lịch ôn: `epux/srs.py` — R(t) = 0.9^(t/S), learning steps 10m/1h/8h, stability nhân theo ease.
- Game: `epux/game.py` — tỉ lệ rơi rarity theo tier pack, thử thách tính từ log học trong ngày.
- LLM: `epux/llm.py` — mọi prompt trả JSON, hỗ trợ Azure OpenAI và OpenAI-compatible.
- Đổi thư mục dữ liệu: `$env:EPUX_HOME`, `$env:EPUX_CONFIG_HOME`.
