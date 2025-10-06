# Single Agent Architecture

Single Agent là kiến trúc trong đó một LLM trung tâm có thể gọi nhiều tools như RAG, API, Database. Khi user đặt câu hỏi, Agent sẽ quyết định tool cần dùng, gọi tool, rồi tổng hợp kết quả.

## Các thành phần chính:

1. **Registry**: Quản lý danh sách các tools có sẵn
2. **Router**: Quyết định tool nào cần sử dụng dựa trên câu hỏi của user
3. **Tools**: Các công cụ chuyên biệt như RAG, Weather API, Database
4. **Agent**: Điều phối việc gọi tools và tổng hợp kết quả

## Ưu điểm:
- Modular: Dễ dàng thêm tools mới
- Flexible: Có thể sử dụng keyword routing hoặc LLM function calling
- Scalable: Có thể mở rộng cho nhiều use cases khác nhau
