# EPux

EPux là web app local giúp bạn học từ vựng + luyện Writing cho IELTS, mọi tính năng thông minh chạy bằng LLM của bạn (cấu hình trong `.env`):

- **Tự động mở rộng vốn từ**: AI đề xuất chủ đề hay gặp trong IELTS, sinh thẻ từ vựng đầy đủ (nghĩa, IPA, ví dụ, collocations, band CEFR) và tránh trùng từ bạn đã có.
- **Ôn tập theo đường cong lãng quên**: thẻ mới ôn dày (10 phút → 1 giờ → 8 giờ), nhớ tốt thì giãn dần theo stability — hợp với người online thường xuyên.
- **Writing**: AI ra đề (diễn tả hoạt động thường ngày hoặc IELTS Task 2), chấm band theo 4 tiêu chí, chỉ từng lỗi, viết lại bản band cao hơn, gợi ý từ "nâng band" để thêm thẳng vào bộ học. Kèm thư viện **mẫu câu** theo chủ đề, có chấm câu bạn tự đặt.
- **Sưu tập thẻ bài**: mỗi từ là một card có độ hiếm **D → C → B → A → S → SS → SSS**. Hoàn thành thử thách mỗi ngày → nhận pack (Đồng/Bạc/Vàng) → mở pack để sở hữu thẻ. Nếu roll ra độ hiếm chưa có trong kho, AI sinh từ mới đúng độ khó đó — gacha cũng là học.
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
AZURE_OPENAI_API_VERSION=2024-02-15-preview
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
