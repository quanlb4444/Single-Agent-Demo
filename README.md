# Single Agent Demo

Một demo tối thiểu về Single Agent architecture với 3 tools: RAG, Weather API, và SQLite Database.

## Cấu trúc file

```
single_agent_demo/
├─ requirements.txt
├─ .env.example
├─ main.py          # điểm vào: chạy demo CLI
├─ app.py           # giao diện Streamlit
├─ run_streamlit.py # script chạy Streamlit
├─ agent.py         # agent + router + registry
├─ tools.py         # định nghĩa 3 tools: RAG, Weather API, SQLite DB
├─ corpus/
│  └─ knowledge.md  # dữ liệu RAG mẫu
└─ data.db          # SQLite mẫu (auto tạo nếu chưa có)
```

## Cài đặt

1. Tạo virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. (Tùy chọn) Cấu hình OpenAI API key:
```bash
cp .env.example .env
# Chỉnh sửa .env và thêm OPENAI_API_KEY nếu muốn dùng function calling
```

## Chạy demo

### CLI Version
```bash
python main.py
```

### Web Interface (Streamlit)
```bash
python run_streamlit.py
# Hoặc
streamlit run app.py
```

Sau khi chạy, mở browser tại: http://localhost:8501

## Ví dụ câu hỏi

- "Thời tiết hôm nay ở Đà Nẵng?" → Agent gọi get_weather
- "Cho tôi biết tổng số khách hàng trong DB." → Agent gọi query_db
- "Single Agent hoạt động thế nào?" → Agent gọi rag_search

## Kiểm thử

Chạy test structure:
```bash
python test_structure.py
```

## Tính năng

### 1. RAG Tool (BM25-based)
- Tìm kiếm trong corpus/knowledge.md
- Sử dụng BM25 ranking
- Không cần embedding model

### 2. Weather Tool
- Sử dụng Open-Meteo API (miễn phí)
- Hỗ trợ 3 thành phố Việt Nam: Đà Nẵng, Hà Nội, TP.HCM
- Trả về nhiệt độ theo giờ

### 3. Database Tool
- SQLite database với bảng customers
- Chỉ cho phép SELECT queries
- Tự động tạo dữ liệu mẫu (50 khách hàng)

### 4. Router
- **Với OpenAI API**: Sử dụng function calling
- **Không có API key**: Keyword-based routing đơn giản

## Mở rộng

Xem phần "Mở rộng sản xuất" trong tài liệu gốc để biết cách cải thiện:
- RAG với embedding + FAISS
- Observability với OpenTelemetry
- Policy enforcement
- Caching
- Async processing
- Evaluation framework
