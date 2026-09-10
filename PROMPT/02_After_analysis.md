# LỆNH SAU KHI PHÂN TÍCH

Kế hoạch triển khai đã được xem xét và phê duyệt.

Tiến hành triển khai theo các quy tắc sau:

1. Tuân thủ kế hoạch đã phê duyệt:
- Chỉ thực hiện các thay đổi đã đề xuất. 
- Không thiết kế lại hoặc tái cấu trúc mã nguồn (refactor) nằm ngoài phạm vi kế hoạch.

2. Duy trì kiến ​​trúc Clean Architecture và các ranh giới DDD:
- Lớp Domain phải giữ được sự thuần khiết, không chứa các import liên quan đến framework, cơ sở dữ liệu hoặc HTTP. 
- Lớp Application điều phối các dịch vụ domain (domain services) và repository. 
- Lớp Execution quản lý trạng thái quy trình làm việc, thực thi chức năng và theo dõi (tracing). 
- Lớp Infrastructure triển khai các bộ chuyển đổi kỹ thuật (persistence, cache, upload). 
- Lớp Presentation (các route FastAPI / Streamlit) ủy quyền xử lý cho các dịch vụ application.

3. Tuân thủ các quy tắc kỹ thuật:
- Thực hiện thay đổi nhỏ nhất nhưng vẫn đảm bảo tính nhất quán. 
- Tận dụng lại các dịch vụ và chức năng hiện có khi có thể. 
- Duy trì khả năng tương thích ngược cho các endpoint và hợp đồng (contract) hiện tại. 
- Tuyệt đối không sử dụng `eval()`, `exec()`, tải YAML không an toàn, hoặc dữ liệu đầu ra từ LLM chưa qua kiểm chứng.

4. Xác minh từng bước:
- Chạy kiểm thử đơn vị (unit test) thường xuyên (`python -m pytest`). 
- Đảm bảo các bài kiểm thử hồi quy (regression test) luôn đạt kết quả thành công 100%. 
- Kiểm tra các tệp đã sửa đổi để tránh những thay đổi ngoài ý muốn hoặc lỗi về phong cách mã nguồn.

5. Chuẩn bị hoàn tất:
- Sau khi toàn bộ mã nguồn và các bài kiểm thử đã được xác minh, hãy thực hiện theo `PROMPT/03_End_Chat.md` để hoàn thiện tài liệu và bàn giao.