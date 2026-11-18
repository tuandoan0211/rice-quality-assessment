# Kết quả kiểm tra BTL

Các số liệu ảnh nguồn dưới đây ghi nhận ở lượt kiểm tra ngày 18 tháng 11 năm 2026. Hai notebook chính đã được loại bỏ theo yêu cầu; dự án hiện chạy bằng ứng dụng Streamlit hoặc CLI.

| Nội dung | Kết quả đã ghi nhận |
|---|---|
| Kiểm thử hành vi phần mềm | 17 đạt, 0 thất bại, 0 lỗi |
| Chạy toàn bộ ảnh nguồn | 69/69 thành công |
| Tổng dòng đặc trưng vùng trong 69 ảnh | 14.857 dòng, gồm cả vùng bị loại và ảnh nguồn trùng |
| Kiểm tra nhất quán thống kê | Số vùng bằng hạt ứng viên cộng vùng bị loại; tỷ lệ mỗi trục cộng 100% khi có hạt |
| Kiểm thử Streamlit | Khởi tạo, nhập chuẩn chiều dài, bật ngưỡng thủ công và báo ngưỡng không hợp lệ |
| Demo tổng hợp trong ứng dụng | 5 hạt, 0 vùng bị loại, 0 hạt chưa xác định |
| Kiểm tra giao diện trực tiếp trên trình duyệt | Chưa hoàn tất do công cụ Windows không xác định được URL hiện tại |

`scripts/check_project.py` hiện kiểm tra các module qua bộ kiểm thử và ứng dụng bằng Streamlit AppTest, gồm demo tổng hợp; không còn đọc hoặc tạo notebook. Xem `outputs/verification/project_checks.json` và `unit_tests.txt` để biết kết quả lần chạy gần nhất.

## Dữ liệu thật

69 ảnh đọc được, 2 ảnh trùng nội dung và 67 ảnh duy nhất. Chia tập sơ bộ gồm 58 ảnh calibration và 9 ảnh test; cần rà soát ảnh cùng phiên chụp trước khi đánh giá độc lập.

Đặc trưng và dự đoán tổng hợp nằm trong `outputs/verification/all_features.csv` và `all_classification.csv`. Mỗi dòng có `image_path` để truy nguyên. Mẫu hộp bao để gán nhãn nằm trong `all_grain_labels_template.csv`.

Thời gian cộng dồn xử lý và kiểm tra ảnh trong lượt rà soát đã ghi nhận là khoảng 149,2 giây, chưa bao gồm toàn bộ thời gian xuất ảnh mẫu. Đây là số đo trong môi trường khi đó, không phải cam kết hiệu năng.

**Chưa có nhãn chuẩn từng hạt trên ảnh thật, nên chưa đo độ chính xác phân loại, precision/recall phát hiện hay độ chính xác đếm trên dữ liệu thật.** Chạy thành công không chứng minh phát hiện đúng mọi hạt. Ngưỡng mặc định chưa được xác nhận thực nghiệm; nhãn hình dạng để Không xác định khi chưa nhập chuẩn chiều dài.

## Dữ liệu tổng hợp

Ảnh demo có năm đối tượng với mask và nhãn biết trước từ công thức vẽ. Cấu hình riêng dùng chiều dài chuẩn 70 px và ngưỡng phân đoạn 30. Trên ảnh này, cả năm đối tượng được khớp và các nhãn hình dạng/màu đều đúng. Kết quả chỉ kiểm tra chức năng trên ảnh tổng hợp đã biết, không đại diện độ chính xác trên ảnh thật.

## Bằng chứng tái lập

- `outputs/verification/unit_tests.txt`: tên và kết quả từng kiểm thử.
- `outputs/verification/project_checks.json`: kết quả kiểm tra ứng dụng bằng Streamlit AppTest.
- `outputs/verification/all_images.csv`: từng ảnh, số vùng, số hạt ứng viên, thời gian và lỗi nếu có.
- `outputs/verification/report.json`: tổng kết lượt rà soát toàn bộ ảnh.
- `dataset/audit.json`: kiểm kê nguồn ảnh.
- `dataset/synthetic_demo/evaluation.json`: đối chiếu nhãn tổng hợp.
- `requirements-tested.txt`: phiên bản thư viện đã dùng.

Đọc README.md để chạy lại, gán nhãn, hiệu chỉnh và đánh giá; đọc BAO_CAO_BTL.md để xem thuật toán và kịch bản bảo vệ. Các ảnh đầu ra demo lặp lại đã được dọn; các bảng và nhật ký kiểm thử ở `outputs/verification/` được giữ lại. Có thể xuất lại ảnh mẫu bằng `python scripts/verify_dataset.py --export-examples`.
