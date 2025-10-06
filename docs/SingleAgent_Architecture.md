# Kiến trúc Single Agent và tính ứng dụng

Tài liệu ngắn mô tả khái niệm, kiến trúc, luồng xử lý, công nghệ và ứng dụng thực tế của mô hình Single Agent, kèm cách áp dụng trong dự án demo này.

## 1) Single Agent là gì?
Single Agent là một tác nhân phần mềm duy nhất chịu trách nhiệm:
- Hiểu ý định người dùng (ngôn ngữ tự nhiên)
- Lập kế hoạch chọn công cụ phù hợp (tool selection)
- Gọi công cụ với tham số cấu trúc (function calling)
- Tổng hợp kết quả thành câu trả lời

So với multi‑agent, Single Agent gọn nhẹ, dễ triển khai, phù hợp MVP và nhiều quy trình nghiệp vụ tuyến tính.

## 2) Kiến trúc tổng quan
- UI: Web app (ví dụ Streamlit) để chat và hiển thị kết quả
- SingleAgent: Lõi điều phối (planning + acting)
- Tooling: Bộ công cụ domain (RAG, API ngoài như Weather, Database/Employee CRUD)
- Model: LLM hỗ trợ Function Calling (OpenAI)
- Data: SQLite/Vector store/HTTP APIs

Luồng logic: User → UI → SingleAgent → (chọn Tool) → Tool Handler → Data/API → Kết quả → SingleAgent → UI

## 3) Luồng xử lý
1. Người dùng nhập câu tự nhiên
2. Agent gửi messages + danh sách tool specs cho LLM
3. LLM chọn tool và tạo arguments
4. Agent gọi tool (thực thi thật)
5. (Tuỳ chọn) Gửi kết quả tool lại cho LLM để diễn giải
6. Trả câu trả lời cuối cùng

Mấu chốt: ToolSpec nêu rõ tên, mô tả, schema tham số (Pydantic) giúp LLM gọi đúng công cụ.

## 4) Công nghệ trong demo
- Streamlit: UI chat + ví dụ câu hỏi
- OpenAI Function Calling: lựa chọn và gọi tool tự động
- SQLite: Lưu trữ nhân viên/khách hàng (CRUD qua tool)
- Requests: Gọi Open‑Meteo (Weather)
- BM25Okapi: Tìm kiếm RAG cơ bản (keyword relevance)

Cấu trúc mã tool (đã tách module):
- `toolkit/base.py`: `Tool`, `ToolSpec`
- `toolkit/rag_tools.py`: `rag_tool_factory`
- `toolkit/external_tools.py`: `weather_tool_factory`
- `toolkit/db_tools.py`: `db_tool_factory`, CRUD nhân viên (theo ID và theo tên)

## 5) Ứng dụng thực tế
- Trợ lý nội bộ tra cứu tri thức (RAG) + báo cáo đơn giản
- CSKH: kiểm tra thông tin khách/đơn hàng, cập nhật trạng thái
- Vận hành: CRUD thực thể nghiệp vụ (nhân sự, hàng hóa, ticket)
- Tích hợp API ngoài: thời tiết, tỷ giá, lịch vận hành
- Orchestration: gọi nhiều tool nối tiếp (validate → thực thi → tổng hợp)

Khi nên dùng Single Agent:
- Phạm vi rõ, quy trình tuyến tính, số tool ít
- Cần triển khai nhanh, chi phí thấp, dễ vận hành
- Muốn kiểm soát hành vi và audit log tool calls

## 6) Best practices
- Thiết kế ToolSpec rõ ràng; validate đầu vào bằng Pydantic
- Mỗi handler mở/đóng kết nối DB riêng (SQLite + Streamlit dùng `check_same_thread=False`)
- Mô tả tool nêu rõ hành vi (ví dụ: “thực thi ngay, không xác nhận”) để giảm việc model hỏi lại
- Trả lỗi có cấu trúc `{ success, error, message, ... }`
- Log tối thiểu input/output của tool để debug/audit

## 7) Áp dụng trong dự án này
- Weather: Geocoding → Forecast (Open‑Meteo), trả `current`/`hourly`
- RAG: BM25 cho corpus nhỏ minh hoạ truy xuất tri thức
- Employees: CRUD SQLite, hỗ trợ theo ID và theo tên, thực thi ngay không xác nhận
- UI: Các “Example Questions” tạo message và tự động gọi agent

## 8) Mở rộng
- Bảo mật: phân quyền tool (readonly vs write), mask secrets
- Hiệu năng: cache kết quả, chuyển khỏi SQLite khi cần
- Kiến trúc: tách backend (FastAPI) + frontend (Streamlit/React)
- RAG nâng cao: embedding + vector DB, reranking, citation
- Quan sát: tracing tool calls, rate‑limit & retry policies

## 9) Bảo mật & tuân thủ
- Không log secrets/PII; dùng `.env`, không commit
- Principle of least privilege cho tool
- Ràng buộc SQL và schema để tránh lỗi dữ liệu

## 10) Checklist nhanh
- [ ] Xác định use cases và công cụ
- [ ] Định nghĩa ToolSpec + schema
- [ ] Viết handler an toàn, đóng tài nguyên
- [ ] Ghi rõ hành vi trong mô tả tool
- [ ] Test end‑to‑end: prompt → tool → kết quả → diễn giải
- [ ] Theo dõi, tinh chỉnh prompt/tool desc

Tài liệu đủ để bạn triển khai Single Agent thực dụng và mở rộng theo nhu cầu doanh nghiệp.
