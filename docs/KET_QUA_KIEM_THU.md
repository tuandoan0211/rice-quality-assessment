# Kết quả kiểm tra bản Jupyter Notebook

Ngày chạy kiểm tra 19 tháng 11 năm 2026. Bốn notebook được chạy lần lượt bằng **bốn kernel Python mới**, không chia sẻ biến và không import module `.py` của dự án. Thư mục làm việc kiểm tra khác thư mục mã nguồn; đầu vào được trỏ tới hai thư mục ảnh gốc.

| Notebook | Kết quả | Ô code | Hình đã tạo | Thời gian |
|---|---|---:|---:|---:|
| 01 dữ liệu và tiền xử lý | Đạt | 7 | 1 | 95,52 giây |
| 02 phân đoạn và tách hạt | Đạt | 9 | 2 | 65,79 giây |
| 03 trích xuất đặc trưng | Đạt | 9 | 1 | 55,88 giây |
| 04 phân loại và thống kê | Đạt | 15 | 2 | 18,99 giây |

Thời gian là số đo trên môi trường kiểm tra hiện tại, không phải cam kết hiệu năng.

## Dữ liệu và file bàn giao

- Đọc được 69 ảnh nguồn; phát hiện 2 ảnh trùng; xử lý 67 ảnh duy nhất.
- Chia tập sơ bộ: 58 ảnh calibration và 9 ảnh test.
- Tạo 14.415 dòng đặc trưng vùng sau khi không xử lý lặp ảnh trùng.
- Các bước sau đọc lại CSV, ảnh và bản đồ ID nén từ đĩa, không sử dụng biến của kernel trước.
- Đối chiếu hàm băm xác nhận toàn bộ ảnh nguồn không thay đổi sau khi chạy.
- Code notebook được kiểm tra cú pháp và các lệnh import, không dùng module triển khai cũ.

## Các kiểm tra hành vi trong notebook

- Notebook 01: danh sách ảnh duy nhất, tệp màu/xám tồn tại và resize giữ tỷ lệ.
- Notebook 02: hai vùng tiếp xúc trong ảnh giả lập được tách; ảnh rỗng không có vùng; tổng ID khớp bảng vùng.
- Notebook 03: thay đổi nền không làm đổi GLCM trong mask; mỗi vùng có đúng một dòng đặc trưng.
- Notebook 04: biên quy tắc Nguyên/Vỡ/Không xác định, hạt cắt biên, xung đột màu và tỷ lệ thống kê nhất quán.

Đã xem các hình tiền xử lý, mask/ROI, phân bố đặc trưng và biểu đồ/ảnh phân loại để kiểm tra khả năng đọc của đầu ra notebook.

## Bằng chứng

- Bốn notebook lưu các ô đã chạy cùng bảng/hình đầu ra thực tế.
- `outputs/notebook/validation.json`: kết quả chạy từng notebook bằng kernel riêng.
- `outputs/notebook/01_du_lieu/audit.json`: kiểm kê dữ liệu.
- `outputs/notebook/02_phan_doan/handoff.json`: kết quả và cấu hình phân đoạn.
- `outputs/notebook/03_dac_trung/handoff.json`: số dòng và dấu vết file đặc trưng.
- `outputs/notebook/04_phan_loai/`: kết quả phân loại, thống kê và hình minh họa.

## Giới hạn diễn giải

**Chưa có nhãn chuẩn từng hạt trên ảnh thật để công bố độ chính xác thực tế.** Các kiểm tra trên xác nhận chương trình chạy được và dữ liệu bàn giao nhất quán; không khẳng định đếm đúng mọi hạt hoặc phân loại đúng mọi trường hợp. Mặc định thiếu chuẩn chiều dài nên nhãn hình dạng ảnh thật là Không xác định. Các tỷ lệ màu vẫn phụ thuộc ngưỡng thử nghiệm và điều kiện chụp.

Kết quả 17 kiểm thử của bản module Python trước đây thuộc phiên bản cũ; không được coi là 17 kiểm thử mới cho bản notebook. Lịch sử phiên bản trước được giữ trong Git.
