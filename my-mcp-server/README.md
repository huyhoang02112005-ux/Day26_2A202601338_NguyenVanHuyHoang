# My MCP Server — Log Analyzer Tools (v2.0.0)

Hệ thống MCP Server phục vụ tự động hóa việc tra cứu, lọc lỗi và phân tích log ứng dụng cho AI Agent (Claude Code / MCP Clients).

---

## 1. Use Case

- **Tên Use Case**: Tra cứu & Phân tích Log Hệ thống (Log Analyzer & Error Inspector).
- **Mô tả thủ công**: Hằng ngày dev phải mở file `.log` bằng text editor hoặc lệnh `grep` để lọc thủ công các dòng lỗi `ERROR`, `CRITICAL`, tìm nguyên nhân sự cố theo từ khóa (như `timeout`, `database`, `payment`).
- **Giải pháp MCP**: Xây dựng MCP Server cung cấp các công cụ cho phép AI Client tự động kết nối, khám phá, lọc log theo tham số và lập báo cáo tổng quan.

---

## 2. Danh sách MCP Tools & Resource

### 🛠️ Tools

| Tool Name | Version | Description | Input Parameters | Output |
|-----------|---------|-------------|------------------|--------|
| `search_logs` | `1.0.0` (Legacy) | Tra cứu log cơ bản | `keyword: str`, `log_level: str`, `limit: int` | `list[str]` (Mảng chuỗi log) |
| `search_logs_v2` | `2.0.0` (Recommended) | Tra cứu log nâng cao | `keyword: str`, `log_level: str`, `limit: int`, `case_sensitive: bool`, `include_line_numbers: bool` | JSON String chứa metadata & mảng log chi tiết |
| `get_error_summary` | `1.0.0` (Legacy) | Thống kê lỗi cơ bản | *(Không có)* | `dict` chứa đếm số log & top 5 lỗi |
| `get_error_summary_v2` | `2.0.0` (Recommended) | Thống kê log & tỉ lệ lỗi nâng cao | `top_n_errors: int` | JSON String chứa đếm chi tiết, tỉ lệ lỗi `%`, lỗi mới nhất |

### 📄 Resource

- **`server://info`**: Cung cấp metadata về thông tin phiên bản server (`2.0.0`), danh sách các tool đang hỗ trợ, các tool deprecated và khả năng bảo mật.

---

## 3. Cấu trúc Thư mục

```text
my-mcp-server/
├── server.py             # Mã nguồn chính MCP Server (STDIO & Streamable HTTP)
├── test_auth_http.py     # Script kiểm thử xác thực Authentication
├── test_tools.py         # Script test trực tiếp logic của các tools
├── requirements.txt      # Thư viện phụ thuộc
├── README.md             # Tài liệu dự án
└── data/
    └── app.log           # Dữ liệu log ứng dụng mô phỏng
```

---

## 4. Hướng dẫn Chạy & Đăng ký Server

### 4.1. Chạy ở chế độ STDIO (Mặc định cho Claude Code / local MCP client)

```bash
# 1. Kích hoạt môi trường ảo
source ../.venv/bin/activate

# 2. Khởi chạy Server ở chế độ stdio
python server.py
```

### 4.2. Đăng ký với Claude Code

Thực hiện lệnh sau trong Terminal (làm 1 lần):

```bash
claude mcp add log-analyzer -- python /đường/dẫn/đầy/đủ/đến/my-mcp-server/server.py
```

Sau khi đăng ký, trong Claude Code bạn có thể thực hiện lệnh tự nhiên:
> *"Tìm giúp tôi 5 lỗi ERROR gần nhất liên quan tới database trong log."*

---

## 5. Cấu hình Authentication (Streamable HTTP Transport)

Dự án hỗ trợ xác thực qua **Bearer Token** bằng `StaticTokenVerifier`:

### 5.1. Khởi chạy Server chế độ HTTP

```bash
TRANSPORT=streamable-http PORT=8085 python server.py
```

Server sẽ lắng nghe tại `http://localhost:8085/mcp`.

### 5.2. Danh sách Bearer Tokens hợp lệ

- `secret-token-123` (Admin Client)
- `dev-token-abc` (Developer Client)

### 5.3. Kiểm thử Authentication

Chạy script test auth:

```bash
python test_auth_http.py
```

- Request **không có Token** hoặc **Token sai**: Nhận phản hồi **401 Unauthorized** / **403 Forbidden**.
- Request chứa header `Authorization: Bearer secret-token-123`: Được xác thực thành công và phản hồi JSON-RPC 200 OK.

---

## 6. Chiến lược Versioning (Backward Compatibility)

Dự án áp dụng 3 chiến lược quản lý phiên bản:

1. **Giữ lại Tool V1**: `search_logs` và `get_error_summary` được giữ nguyên kiểu trả về cũ cho các Client legacy.
2. **Cung cấp Tool V2**: `search_logs_v2` và `get_error_summary_v2` trả về cấu trúc JSON chuẩn hóa kèm thông tin metadata (`timestamp`, `line_number`, `error_rate_percentage`).
3. **Thêm Optional Parameters**: Thêm `case_sensitive`, `include_line_numbers`, `top_n_errors` với giá trị mặc định để không gây ảnh hưởng tới các client hiện tại.
4. **Metadata Resource `server://info`**: Giúp MCP Client kiểm tra phiên bản và chủ động fallback giữa V2 và V1.
