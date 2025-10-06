# Single Agent Demo

Demo kiến trúc Single Agent: chat UI (Streamlit), OpenAI Function Calling và bộ tool tách module (RAG, Weather, Database/Employees).

## Cấu trúc thư mục (rút gọn)

```
single_agent_demo/
├─ requirements.txt
├─ .env.example
├─ app.py                 # Giao diện Streamlit
├─ agent.py               # SingleAgent (planning/acting) + Registry
├─ toolkit/               # Bộ tool tách module
│  ├─ base.py             # ToolSpec, Tool
│  ├─ rag_tools.py        # rag_tool_factory (BM25)
│  ├─ external_tools.py   # weather_tool_factory (Open‑Meteo + geocoding)
│  └─ db_tools.py         # query_db + CRUD Employees (ID & tên)
├─ docs/
│  └─ SingleAgent_Architecture.md
└─ data.db                # SQLite (tự tạo khi chạy tool)
```

## Cài đặt

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Tạo file `.env` và cấu hình OpenAI (bắt buộc để agent hoạt động):
```bash
cp .env.example .env
# Mở .env và thêm:
# OPENAI_API_KEY=your_api_key_here
# OPENAI_MODEL=gpt-4o-mini   # hoặc model tương thích function calling
```

## Chạy ứng dụng

```bash
source venv/bin/activate
streamlit run app.py
```
Sau đó mở `http://localhost:8501`.

## Tính năng chính

- RAG (BM25): truy vấn tri thức nội bộ (minh họa corpus nhỏ)
- Weather: geocoding động + Open‑Meteo (current/hourly)
- Database/Employees (SQLite):
  - Thêm/list/xóa/sửa nhân viên theo ID
  - Tìm/xóa/sửa theo tên (partial, case‑insensitive)
  - Thực thi ngay, không yêu cầu xác nhận
- Modal “Project Flow”: nút “📈 Show Flow” hiển thị sơ đồ Graphviz luồng xử lý
- Không còn keyword routing; nếu thiếu API key → báo lỗi rõ ràng

## Ví dụ câu hỏi (copy & click)

- “Thời tiết ở Đà Nẵng”
- “Hiển thị danh sách nhân viên”
- “Thêm nhân viên Nguyễn Văn A sinh năm 1990”
- “Xóa nhân viên ID 4” hoặc “Xóa nhân viên Phạm Văn C”
- “Sửa nhân viên Lê Quốc An thành sinh năm 2002”
- “Single Agent hoạt động thế nào?”

## Ghi chú kỹ thuật

- Mỗi request DB mở/đóng kết nối riêng (`sqlite3.connect(..., check_same_thread=False)`) để an toàn với Streamlit
- ToolSpec/Tool (Pydantic schema) giúp LLM chọn tool và sinh tham số chính xác
- Mô tả tool nêu rõ “execute immediately, no confirmation” để tránh model hỏi lại

## Mở rộng gợi ý

- Backend tách riêng (FastAPI) + UI (Streamlit/React)
- RAG nâng cao: embedding + vector DB, reranking, citation
- Observability: logging/tracing tool calls, rate‑limit & retry
- Bảo mật: least privilege cho tool, không log secrets/PII, dùng `.env`
