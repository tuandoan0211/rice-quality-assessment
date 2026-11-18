# BTL đánh giá chất lượng gạo bằng xử lý ảnh

Hệ thống Python hoàn chỉnh cho bốn phần phân công: dữ liệu và tiền xử lý, phân đoạn, trích xuất đặc trưng, phân loại if/else và thống kê. Có ứng dụng Streamlit, CLI, công cụ hiệu chỉnh và đánh giá. Không dùng mô hình học máy.

## Chạy ngay trên máy này

Mở **`run_app.bat`** trong thư mục dự án. Hoặc chạy trong PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m streamlit run app.py
```

Trình duyệt mở tại `http://localhost:8501`. Chọn ảnh có sẵn hoặc tải ảnh; xem mask trước khi đọc kết quả. Mặc định **chưa có chiều dài hạt nguyên chuẩn**, nên hình dạng là “Không xác định”. Nhập chiều dài tham chiếu ở độ phân giải ảnh gốc, cùng giống và tỷ lệ chụp để dùng nhãn Nguyên/Vỡ.

Để xem đủ nhãn ngay, chọn `dataset/synthetic_demo/scene.png` trong danh sách ảnh có sẵn. Ứng dụng điền tham chiếu 70 px và ngưỡng phân đoạn 30 cho riêng ảnh tổng hợp này.

Khi cài trên máy khác, chạy `setup.bat`, rồi `run_app.bat`. Cần Python 3.11 trở lên và Internet khi cài thư viện. Chạy trực tiếp bằng các tệp Python, không cần Jupyter hoặc notebook.

## Chạy bằng dòng lệnh

Các lệnh dưới đây dùng Python của môi trường dự án; có thể thay `python` bằng `& .\.venv\Scripts\python.exe` trong PowerShell.

```powershell
# Kiểm kê, phát hiện trùng, chia tập theo ảnh và xuất hai nhánh tiền xử lý
python main.py prepare

# Phân tích một ảnh thật, xuất cả ROI và mask từng hạt
python main.py analyze "batch_dataset/picCacloaigao (1).jpg" --output outputs/demo

# Phân tích cả thư mục, không xuất các ảnh ROI nhỏ
python main.py analyze batch_dataset --output outputs/batch --no-rois

# Demo ảnh TỔNG HỢP có hình dạng/màu sắc biết trước
python scripts/create_synthetic_demo.py
python main.py analyze dataset/synthetic_demo/scene.png --config dataset/synthetic_demo/config.json --output outputs/demo_synthetic

# Kiểm thử và rà soát dữ liệu thật
python -m unittest discover -s tests -v
python scripts/verify_dataset.py
```

`--reference-length` đặt chiều dài chuẩn (px ảnh gốc) cho ảnh có cùng tỷ lệ chụp. Không dùng chung một giá trị cho các ảnh chụp ở khoảng cách khác nhau. Có thể tải cấu hình JSON từ ứng dụng rồi truyền qua `--config`.

## Tệp và thư mục chính

| Tệp | Trách nhiệm |
|---|---|
| `preprocessing.py`, `dataset_tools.py` | Thành viên 1, dữ liệu và tiền xử lý |
| `segmentation.py` | Thành viên 2, Otsu, hình thái học, Connected Components, Watershed, ROI |
| `feature_extraction.py` | Thành viên 3, hình dạng, RGB/HSV, GLCM |
| `classification.py`, `rice_statistics.py` | Thành viên 4, quy tắc và thống kê |
| `pipeline.py` | Ghép module, vẽ kết quả và xuất tệp |
| `app.py`, `main.py` | Ứng dụng và dòng lệnh |
| `calibrate.py`, `evaluate.py` | Khảo sát nhãn chuẩn, chiều dài tham chiếu và đối chiếu dự đoán |
| `docs/BAO_CAO_BTL.md` | Báo cáo kỹ thuật và kịch bản demo/bảo vệ |
| `dataset/manifest.csv`, `dataset/audit.json` | Danh mục ảnh, kiểm kê lỗi/trùng và nhãn nguồn |
| `outputs/verification/` | Nhật ký chạy toàn bộ ảnh thật |

Module thống kê tên `rice_statistics.py` để tránh che khuất thư viện chuẩn Python `statistics`, vốn có thể được các thư viện khác sử dụng.

Các thư mục kết quả demo lặp lại, `dataset/processed/` và bộ nhớ đệm Python đã được dọn. Ứng dụng đọc trực tiếp ảnh nguồn nên vẫn chạy bình thường. `python main.py prepare` sẽ tạo lại hai nhánh ảnh tiền xử lý nếu cần; trước khi tạo lại, các cột `color_path` và `gray_path` trong manifest để trống. Lệnh rà soát mặc định chỉ lưu bảng kiểm tra; thêm `--export-examples` vào `python scripts/verify_dataset.py` nếu cần xuất cả ảnh mẫu và ROI.

## Dữ liệu đã kiểm kê

69 tệp ảnh nguồn đọc được; 2 ảnh trùng nội dung; còn 67 ảnh duy nhất. Manifest chia thử nghiệm thành 58 ảnh calibration và 9 ảnh test theo băm nội dung ảnh. Đây là **chia tập sơ bộ**; cần kiểm tra và gom các ảnh cùng phiên chụp trước khi coi test là độc lập.

Nhóm thư mục: Tot 20, Vo 4, Kem 8, Te 4, Tap_chat 2 và batch 31. Nhãn thư mục không tự động trở thành nhãn hình dạng/màu sắc từng hạt. Dữ liệu nguồn được giữ nguyên.

## Gán nhãn và hiệu chỉnh

1. Phân tích một ảnh thuộc tập calibration. Vào tab **Gán nhãn đối chiếu** hoặc sửa `grain_labels_template.csv` trong thư mục kết quả.
2. Kiểm tra từng hộp bao/ID; thêm hạt thiếu, xóa vật không phải hạt, sửa hộp bao bị gộp. Điền hai nhãn, tên người kiểm tra và `verified=True`. CSV dùng hộp bao ở tọa độ ảnh gốc.
3. Để tạo tham chiếu, cần ít nhất 5 hạt nguyên đã xác nhận trong cùng ảnh và tỷ lệ chụp:

```powershell
python calibrate.py --labels labels_calibration.csv --features outputs/demo/features.csv --capture-group "gao_A_camera_co_dinh" --output outputs/calibration
```

4. Xem `ranges.json`, điều chỉnh ngưỡng hình dạng/màu trong `rules.json` theo dữ liệu calibration và tiêu chí nhóm thống nhất. Công cụ chỉ đề xuất chiều dài chuẩn, không tự tuyên bố các ngưỡng đã được kiểm chứng.
5. Cố định cấu hình, chạy ảnh test có nhãn thủ công. Mỗi lần đối chiếu một ảnh:

```powershell
python main.py analyze "anh_test.png" --config outputs/calibration/rules.json --output outputs/test_image
python evaluate.py --labels labels_test.csv --predictions outputs/test_image/classification.csv --complete-image --output outputs/test_evaluation.json
```

Chỉ dùng `--complete-image` nếu đã gán nhãn **tất cả** hạt của ảnh, gồm cả hạt thuật toán bỏ sót. Khi chưa gán hết ảnh, bỏ cờ này; chương trình chỉ báo độ chính xác phân loại trên các hạt khớp hộp bao, không báo precision/recall phát hiện.

Mỗi ảnh đầu ra có `features.csv`, `classification.csv`, `statistics.csv`, `summary.json`, ảnh gốc đã resize, ảnh xám, khử nhiễu, tăng tương phản, mask, ảnh đánh số, biểu đồ, `instance_labels.npy` và ROI. Mẫu nhãn thủ công đã tồn tại sẽ không bị ghi đè; nếu đổi ảnh/cấu hình, hãy xuất sang thư mục mới để tránh dùng ID cũ.

## Phạm vi kết quả

Ngưỡng mặc định là giá trị thử nghiệm, không phải tiêu chuẩn chất lượng thương mại. Chưa có nhãn chuẩn từng hạt trên ảnh thật, nên **chưa có số liệu độ chính xác thực tế**. Các kiểm thử ảnh tổng hợp chỉ xác nhận hành vi phần mềm. Đồng xu/vật lớn gần tròn được loại bằng quy tắc hình học tùy chọn; đây chưa phải bộ nhận dạng mọi loại tạp chất.

Nếu Otsu bỏ sót hạt tối, thử ngưỡng thủ công và kiểm tra mask. Hạt chồng lấp, bóng đổ, giống gạo khác nhau và ảnh khác tỷ lệ chụp vẫn có thể gây sai số. Xem báo cáo để biết công thức, cách đặt ngưỡng và giới hạn.
