# Single Agent Architecture (Tóm tắt ngắn)

## 1) Single Agent là gì?
Một agent duy nhất nhận yêu cầu tự nhiên → chọn công cụ phù hợp → gọi công cụ với tham số cấu trúc → trả lời kết quả.

- Đơn giản, dễ triển khai (so với multi‑agent)
- Phù hợp MVP và quy trình nghiệp vụ tuyến tính

## 2) Luồng xử lý
1. User nhập câu hỏi trong UI (Streamlit)
2. Agent gửi messages + danh sách ToolSpec cho LLM (OpenAI)
3. LLM chọn tool và sinh arguments
4. Agent gọi handler thực thi (RAG/Weather/DB)
5. Agent trả kết quả (có thể qua LLM để diễn giải)

Sơ đồ ngắn: User → UI → Agent → LLM → Agent → Tool → Data → Agent → UI

## 3) Bộ công cụ (toolkit/)
- base.py: `ToolSpec`, `Tool`
- rag_tools.py: `rag_tool_factory` (BM25)
- external_tools.py: `weather_tool_factory` (Open‑Meteo + geocoding)
- db_tools.py: `query_db` và CRUD nhân viên (theo ID hoặc tên)

Nguyên tắc:
- Mỗi tool mô tả rõ ràng (tên, mô tả, schema tham số)
- Handler an toàn, mở/đóng kết nối DB cho mỗi yêu cầu (`check_same_thread=False` cho Streamlit)
- Lỗi trả về có cấu trúc: `{ success?, error?, message?, ... }`

## 4) Cách dùng trong dự án
- Giao diện: `app.py` (Streamlit), có các ví dụ câu hỏi và nút “📈 Show Flow”
- Agent: `agent.py` dùng OpenAI Function Calling, thực thi ngay (không xác nhận)
- DB: SQLite `data.db` (tự tạo khi cần)

Ví dụ truy vấn:
- “Thời tiết ở Đà Nẵng”
- “Hiển thị danh sách nhân viên”
- “Xóa nhân viên ID 4” hoặc “Xóa nhân viên Phạm Văn C”
- “Sửa nhân viên Lê Quốc An thành sinh năm 2002”

## 5) Khi nào nên dùng Single Agent
- Quy trình rõ ràng, một luồng chính, số công cụ ít
- Cần nhanh gọn, chi phí thấp, dễ vận hành/kiểm soát

## 6) Best practices ngắn
- Thiết kế ToolSpec + Pydantic rõ ràng (giúp LLM gọi đúng)
- Ghi chú hành vi trong mô tả tool (vd: “execute immediately, no confirmation”)
- Log vừa đủ để debug/audit; không log secrets/PII
- Dùng `.env` để quản lý API keys

## 7) Mở rộng (gợi ý)
- Backend riêng (FastAPI) + UI (Streamlit/React)
- RAG nâng cao: embedding + vector DB, reranking
- Observability: tracing tool calls, rate‑limit & retry
- Phân quyền tool (readonly vs write)
