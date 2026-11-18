# BTL đánh giá chất lượng gạo bằng Jupyter Notebook

Đây là nhánh **version2**, triển khai bằng Jupyter Notebook. Nhánh [main](https://github.com/tuandoan0211/rice-quality-assessment/tree/main) giữ bản Python và Streamlit trước đó để đối chiếu.

Dự án triển khai bằng **bốn notebook tương ứng bốn thành viên**. Mỗi notebook chứa trực tiếp các hàm xử lý và phần chạy minh họa; không import mã từ file `.py` của dự án. Hai thư mục ảnh gốc `raw_dataset/` và `batch_dataset/` là đầu vào ban đầu. Không dùng học máy.

## Cách mở và chạy

1. Mở thư mục dự án bằng VS Code có hỗ trợ Jupyter, hoặc chạy `mo_notebook.bat` để mở JupyterLab.
2. Chọn kernel Python của `.venv`. Nếu cài trên máy mới, chạy `setup.bat` trước.
3. Mở notebook 01, chọn **Restart Kernel → Run All** và đợi chạy xong.
4. Làm tương tự với 02, 03 và 04 theo đúng thứ tự. Mỗi notebook có thể dùng kernel riêng.

Cài bằng Terminal nếu cần:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m jupyterlab
```

Notebook mặc định tìm hai thư mục ảnh ở thư mục làm việc hiện tại. Nếu Jupyter mở từ nơi khác, sửa `PROJECT_ROOT` ở ô cấu hình đầu của từng notebook. Các notebook cùng dùng một `OUTPUT_ROOT` để nhận và xuất file bàn giao.

## Bốn notebook

| Notebook | Công việc | Đầu vào | Đầu ra bàn giao |
|---|---|---|---|
| `01_Du_Lieu_Va_Tien_Xu_Ly.ipynb` | Kiểm kê, phát hiện ảnh lỗi/trùng, chia tập sơ bộ, tiền xử lý và so sánh ảnh | Ảnh nguồn | `01_du_lieu/manifest.csv`, ảnh màu/xám, danh sách calibration/test |
| `02_Phan_Doan_Va_Tach_Hat.ipynb` | Otsu, hình thái học, Connected Components, distance transform, Watershed, ID và ROI | Kết quả 01 | `02_phan_doan/regions.csv`, `images.csv`, mask và bản đồ ID nén |
| `03_Trich_Xuat_Dac_Trung.ipynb` | Hình dạng, RGB/HSV, tỷ lệ pixel vàng/sẫm, GLCM có mask | Kết quả 01 và 02 | `03_dac_trung/features.csv` |
| `04_Phan_Loai_Va_Thong_Ke.ipynb` | Quy tắc if/else, hiệu chỉnh từ nhãn thủ công, thống kê, biểu đồ và đối chiếu | Kết quả 03 và file bàn giao trước | `04_phan_loai/` chứa phân loại, thống kê, hình minh họa và mẫu nhãn |

Tất cả đầu ra nằm trong **`outputs/notebook/`** và không cần có sẵn trước khi chạy notebook 01. Các file `handoff.json` lưu dấu vết phiên bản dữ liệu để phát hiện việc dùng lẫn kết quả cũ.

## Cấu trúc cần thiết

```text
rice-quality-assessment-main/
├── 01_Du_Lieu_Va_Tien_Xu_Ly.ipynb
├── 02_Phan_Doan_Va_Tach_Hat.ipynb
├── 03_Trich_Xuat_Dac_Trung.ipynb
├── 04_Phan_Loai_Va_Thong_Ke.ipynb
├── raw_dataset/
│   ├── Tot/
│   ├── Vo/
│   ├── Kem/
│   ├── Te/
│   └── Tap_chat/
├── batch_dataset/
├── docs/
├── outputs/                       Tự sinh khi chạy
├── .venv/                         Môi trường trên máy, không nộp kèm
├── requirements.txt
├── requirements-tested.txt
├── setup.bat
├── mo_notebook.bat
├── README.md
└── CAU_TRUC_THU_MUC_VA_CHUC_NANG.txt
```

## Những tham số cần chú ý

- Notebook 01: `MAX_SIDE`, `BLUR_KERNEL`, `CONTRAST`. Giữ tỷ lệ ảnh; nhánh màu không cân bằng histogram.
- Notebook 02: `MIN_AREA`, `FOREGROUND`, `USE_WATERSHED`, `THRESHOLD_OVERRIDE`. Xem mask trước khi đọc kết quả; hạt tối có thể cần thử ngưỡng thủ công.
- Notebook 03: ngưỡng pixel HSV, GLCM và bộ lọc vật lớn gần tròn. Bộ lọc này chưa nhận dạng được mọi loại tạp chất.
- Notebook 04: `REFERENCE_LENGTH_BY_IMAGE` và `RULES`. Chuẩn chiều dài phải cùng giống, tỷ lệ chụp và đơn vị pixel ảnh gốc. Mặc định chưa có chuẩn nên hình dạng là **Không xác định**.

Đổi dữ liệu hoặc tiền xử lý → chạy lại 01–04. Đổi phân đoạn → chạy lại 02–04. Đổi đặc trưng → chạy lại 03–04. Chỉ đổi quy tắc phân loại → chạy lại 04.

## Gán nhãn và đánh giá

Notebook 04 tạo `manual_labels_template.csv` với nhãn để trống và `verified=False`. Sao chép thành `manual_labels.csv`, kiểm tra/sửa hộp bao, thêm hạt thiếu, loại vật không phải hạt, điền hai nhãn và tên người gán nhãn. Không dùng dự đoán làm nhãn chuẩn.

Muốn đặt chuẩn từ nhãn, bật `USE_VERIFIED_CALIBRATION_LABELS` sau khi có ít nhất 5 hạt nguyên đã kiểm chứng trong cùng ảnh calibration. Notebook chỉ lấy chuẩn cho ảnh tương ứng, không áp dụng tùy tiện cho ảnh khác tỷ lệ chụp. Muốn báo precision/recall phát hiện và sai số đếm, chỉ thêm ảnh vào `COMPLETE_IMAGE_IDS` sau khi gán nhãn **tất cả** hạt của ảnh.

Các mẫu nhãn đã tồn tại không bị tự ghi đè. Nếu đã đổi mask/ID hoặc ảnh nguồn, dùng thư mục đầu ra mới để tránh nhãn cũ khớp sai đối tượng.

## Phạm vi kết quả

Dữ liệu nguồn ban đầu có 69 ảnh, 2 ảnh trùng nội dung và 67 ảnh duy nhất. Chia tập theo băm nội dung là sơ bộ; cần rà soát các ảnh cùng phiên chụp để đảm bảo độc lập.

Các ngưỡng mặc định là ngưỡng thử nghiệm. Chưa có bộ nhãn kiểm chứng đầy đủ trên ảnh thật để kết luận độ chính xác thực tế. Không suy ra nhãn từng hạt từ tên thư mục Tot/Kem/Te. Hệ thống không kết luận độ ẩm, hạt lép hay an toàn thực phẩm từ ảnh.

Xem `docs/BAO_CAO_BTL.md` để đọc thuật toán và `docs/KET_QUA_KIEM_THU.md` để đọc kết quả chạy kiểm tra. Bản notebook được chuyển từ triển khai module trước đây; lịch sử phiên bản Python vẫn có trong Git.
