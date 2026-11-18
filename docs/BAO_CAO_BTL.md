# Báo cáo đánh giá chất lượng gạo bằng Jupyter Notebook

## 1 Bài toán và phạm vi

Hệ thống nhận ảnh nhiều hạt gạo, tách vùng, đo đặc trưng và phân loại bằng if/else, không dùng học máy. Mỗi hạt có hai nhãn độc lập: hình dạng và màu sắc. Một hạt có thể vừa vỡ vừa vàng. GLCM được xuất để khảo sát kết cấu, chưa dùng để gán nhãn bất thường khi thiếu dữ liệu đối chiếu.

Phạm vi là các dấu hiệu quan sát được trên ảnh từ trên xuống. Không kết luận hạt lép, độ ẩm, dinh dưỡng, an toàn thực phẩm hoặc cấp chất lượng thương mại từ ảnh này.

## 2 Tổ chức bốn notebook

| Thành viên | Notebook | Sản phẩm bàn giao |
|---|---|---|
| 1 | 01_Du_Lieu_Va_Tien_Xu_Ly.ipynb | Danh mục, tập ảnh calibration/test, ảnh màu và xám |
| 2 | 02_Phan_Doan_Va_Tach_Hat.ipynb | Mask, ID, ROI, hộp bao, tâm và contour |
| 3 | 03_Trich_Xuat_Dac_Trung.ipynb | Bảng features.csv cho từng vùng |
| 4 | 04_Phan_Loai_Va_Thong_Ke.ipynb | Phân loại, thống kê, biểu đồ và đối chiếu nhãn |

Mỗi notebook chứa các hàm cần thiết ngay trong ô code. Các notebook không import module `.py` của dự án và không cần chia sẻ biến trong bộ nhớ. Các bước nhận dữ liệu qua file trong `outputs/notebook/` và kiểm tra file bàn giao trước khi chạy tiếp. Chạy lần lượt 01–04 bằng kernel riêng vẫn thực hiện được toàn bộ quy trình.

## 3 Dữ liệu và chuẩn bị

Đầu vào ban đầu chỉ gồm `raw_dataset/` và `batch_dataset/`. Có 38 ảnh trong nhóm raw: Tot 20, Vo 4, Kem 8, Te 4 và Tap_chat 2; cùng 31 ảnh batch. Kiểm kê phát hiện 2 bản trùng nội dung pixel, còn 67 ảnh duy nhất. Không xóa ảnh nguồn và không xử lý lặp ảnh trùng.

Nhãn thư mục là nhãn nguồn của cả ảnh, không phải nhãn kiểm chứng cho từng hạt. Không mặc nhiên coi mọi hạt trong Tot đều nguyên/bình thường hoặc mọi hạt trong Kem/Te đều vàng/sẫm.

Chia tập sơ bộ theo hàm băm nội dung ảnh tạo 58 ảnh calibration và 9 ảnh test. Cách này ngăn ảnh trùng chính xác nằm ở hai tập, nhưng chưa loại rò rỉ do ảnh gần giống hoặc cùng phiên chụp. Cần gom nhóm phiên chụp và gán nhãn thủ công trước đánh giá độc lập.

## 4 Tiền xử lý

Notebook 01 đọc ảnh bằng `imdecode` để hỗ trợ đường dẫn tiếng Việt trên Windows. Resize giữ tỷ lệ, cạnh dài tối đa mặc định 1600 px và không phóng to ảnh nhỏ. Lưu scale_x, scale_y thực tế để bù sai số làm tròn khi quy đổi tọa độ.

Nhánh màu chỉ resize, không cân bằng histogram. Nhánh phân đoạn chuyển xám, Gaussian 3×3 và lựa chọn `none`, `equalize` hoặc `clahe`. Mặc định không tăng tương phản. Notebook hiển thị các phương án để người dùng so sánh trước khi chọn.

Ảnh màu và xám được lưu riêng, cùng manifest chứa kích thước gốc, mã nội dung, tỷ lệ resize và đường dẫn tương đối. Notebook 02 chỉ cần file bàn giao này để bắt đầu.

## 5 Phân đoạn và tách hạt

Notebook 02 thực hiện Otsu, lựa chọn cực tính tiền cảnh, Opening/Closing bằng nhân ellipse 3×3, lấp lỗ kín và Connected Components. Diện tích vùng tối thiểu mặc định là 12 px tại ảnh đã resize, cần điều chỉnh nếu độ phân giải hoặc kích thước hạt thay đổi.

Chế độ tự động giả định biên ảnh chủ yếu là nền để xác định có cần đảo mask. Có thể chỉ định tiền cảnh sáng/tối. Hạt tối có thể bị Otsu bỏ sót; tùy chọn ngưỡng thủ công được cung cấp và ghi vào cấu hình.

Vùng có Solidity dưới 0,97 được thử tách bằng Watershed. Distance transform được làm mượt, cực đại có độ nổi bật đủ lớn được chọn làm mầm và loại những mầm quá gần nhau. Nếu thiếu hai mầm hợp lệ hoặc một phần sau tách quá nhỏ, giữ vùng ban đầu. Biên Watershed được gán về vùng hợp lệ gần nhất để tránh mất pixel mask.

Lưu ID, bounding box, centroid, cờ cắt biên và cờ đã tách. Bản đồ ID dùng `.npz` nén; 0 là nền. ROI/mask của mọi vùng khôi phục được từ bản đồ ID và bảng hộp bao; chỉ xuất một số ROI minh họa để tránh tạo hàng chục nghìn ảnh nhỏ. Watershed không đảm bảo phục hồi được hạt bị che khuất hoặc chồng lấp nặng.

## 6 Đặc trưng

Notebook 03 nhận ảnh màu và vùng phân đoạn từ file; ảnh xám cho GLCM được tạo từ nhánh màu chưa cân bằng histogram. Contour được quy về tọa độ ảnh gốc trước khi đo hình học.

| Nhóm | Đặc trưng | Cách tính |
|---|---|---|
| Hình dạng | Diện tích A, chu vi P | contourArea, arcLength |
| Hình dạng | Chiều dài L, rộng W | minAreaRect, L ≥ W |
| Hình dạng | Aspect Ratio | L/W |
| Hình dạng | Circularity | 4πA/P² |
| Hình dạng | Solidity | A/diện tích bao lồi |
| Màu | RGB/HSV trung bình | Pixel bên trong mask đo màu |
| Màu | Tỷ lệ pixel vàng/sẫm | Số pixel thỏa điều kiện / tổng pixel đo màu |
| Kết cấu | Contrast, Homogeneity, Energy, Correlation | GLCM 32 mức xám, khoảng cách 1 px, bốn hướng |

Đơn vị hình học là px hoặc px² tại ảnh gốc, không phải mm. Chiều dài chuẩn cần cùng giống và tỷ lệ chụp; không tự dùng đồng xu làm chuẩn khi chưa biết kích thước thực và phối cảnh.

Mask đo màu được co vào một pixel nếu phần còn lại có ít nhất 3 pixel và chiếm tối thiểu 50% vùng. Hạt quá nhỏ dùng mask ban đầu. Cách này giảm lẫn nền do blur/resize; số pixel được lưu ở `color_pixel_count`.

Trong OpenCV, H thuộc 0–179 và S/V thuộc 0–255. Pixel vàng mặc định có 10 ≤ H ≤ 40, S ≥ 55 và V ≥ 65; pixel sẫm có V ≤ 85. H trung bình là thống kê số học mô tả, không trực tiếp dùng để phân loại; cần thận trọng với tính vòng của H.

GLCM chỉ đếm cặp pixel có cả hai đầu trong mask, đối xứng hóa và chuẩn hóa rồi lấy trung bình đặc trưng qua các hướng hợp lệ. Thiếu cặp thì để trống đặc trưng kết cấu, không thay bằng số giả.

Bộ lọc vật lớn gần tròn loại các vùng có diện tích pixel hơn 5 lần trung vị trong ảnh, Aspect Ratio < 1,4 và Circularity > 0,70. Đây là bộ lọc hình học tùy chọn cho đồng xu/vật lớn, chưa phải bộ nhận dạng tạp chất hoàn chỉnh.

## 7 Quy tắc phân loại và thống kê

Notebook 04 sử dụng hai hàm riêng cho hình dạng và màu sắc. `length_ratio = chiều dài hạt / chiều dài hạt nguyên tham chiếu`, khác với Aspect Ratio là dài/rộng của chính hạt đó.

| Trục | Nhãn | Quy tắc thử nghiệm |
|---|---|---|
| Hình dạng | Nguyên | length_ratio ≥ 0,80 |
| Hình dạng | Vỡ | length_ratio < 0,70 |
| Hình dạng | Không xác định | Thiếu chuẩn, cắt biên, lỗi đặc trưng hoặc vùng chuyển tiếp |
| Màu | Vàng | Tỷ lệ vàng ≥ 0,25 và chưa đồng thời đạt ngưỡng sẫm |
| Màu | Sẫm | Tỷ lệ sẫm ≥ 0,30 và chưa đồng thời đạt ngưỡng vàng |
| Màu | Bình thường | Hai tỷ lệ vàng/sẫm đều ≤ 0,10 |
| Màu | Không xác định | Vùng chuyển tiếp, thiếu đặc trưng hoặc đồng thời đạt hai ngưỡng lỗi |

Những ngưỡng này là cấu hình thử nghiệm, chưa phải tiêu chuẩn chất lượng. Mặc định không có chuẩn chiều dài nên hình dạng của ảnh thật là Không xác định. Có thể đặt chuẩn riêng cho từng ảnh; không dùng tùy tiện một giá trị cho mọi khoảng cách chụp.

Kết luận tổng hợp là Có dấu hiệu lỗi nếu vỡ hoặc vàng/sẫm, Đạt tiêu chí ảnh đã chọn nếu nguyên và màu bình thường, còn lại Cần kiểm tra. Vùng bị loại không nằm trong mẫu số hạt ứng viên.

Thống kê số vùng, hạt ứng viên, vùng bị loại, hạt chưa xác định trên ít nhất một trục, diện tích/dài trung bình và HSV trung bình. Tỷ lệ tính riêng cho hình dạng và màu sắc, mỗi trục cộng 100% khi có hạt. Không cộng hai trục. Ảnh rỗng có số đếm/tỷ lệ bằng 0, các giá trị trung bình để trống.

## 8 Nhãn đối chiếu và hiệu chỉnh

Notebook 04 xuất mẫu nhãn trống với verified=False. Người gán nhãn phải kiểm tra hộp bao, thêm hạt thiếu, loại vật không phải hạt, điền hai nhãn và tên người kiểm tra. Các file nhãn đã tồn tại không bị tự ghi đè; đổi mask/ID nên dùng thư mục đầu ra mới.

Khi có ít nhất 5 hạt nguyên đã kiểm chứng trong cùng ảnh calibration, có thể lấy trung vị chiều dài các hạt khớp hộp bao làm chuẩn riêng cho ảnh đó. Việc này chỉ ước lượng chuẩn chiều dài, không tự chứng minh ngưỡng hình dạng/màu đã phù hợp. Không dùng ảnh test để đặt chuẩn trong chế độ hiệu chỉnh thủ công.

Đối chiếu nhãn bằng khớp một-một Hungarian, IoU hộp bao ≥ 0,5. Độ chính xác hình dạng/màu và ma trận nhầm lẫn chỉ tính trên các hạt khớp, không bao gồm hạt bỏ sót. Chỉ khi đã xác nhận gán nhãn hết ảnh mới báo precision/recall phát hiện và sai số đếm. Đây là IoU hộp bao, chưa phải đánh giá đường biên theo mask chuẩn.

## 9 Kiểm thử và giới hạn

Chuỗi notebook được kiểm tra bằng kernel mới cho từng bước, từ hai thư mục ảnh gốc. Kiểm tra giữ tỷ lệ, file bàn giao tồn tại, ảnh trùng, tách vùng tiếp xúc trong ảnh giả lập, ảnh rỗng, GLCM không tính nền, biên ngưỡng và tổng số liệu thống kê. Dữ liệu gốc được đối chiếu hàm băm để xác nhận không bị sửa.

Kết quả chạy thành công và số liệu nhất quán không chứng minh đếm/phân loại đúng mọi hạt trên ảnh thật. Chưa có bộ nhãn từng hạt được kiểm chứng đầy đủ, vì vậy không công bố độ chính xác thực tế. Các giới hạn chính là ánh sáng, bóng đổ, giống gạo, tỷ lệ chụp, hạt tối, chồng lấp và vật lạ.

## 10 Kịch bản bảo vệ

1. Thành viên 1 mở notebook 01, trình bày nguồn ảnh, ảnh trùng, manifest và so sánh tiền xử lý.
2. Thành viên 2 mở notebook 02, giải thích Otsu, cực tính, hình thái học, Watershed, ID và ROI/mask.
3. Thành viên 3 mở notebook 03, đối chiếu một vùng với vector đặc trưng, giải thích đơn vị và GLCM có mask.
4. Thành viên 4 mở notebook 04, giải thích hai nhãn độc lập, vùng chưa xác định, bảng thống kê và biểu đồ.
5. Trình bày file bàn giao giữa các notebook, cách hiệu chỉnh và đánh giá bằng nhãn thủ công. Khi được hỏi độ chính xác, phân biệt kết quả kiểm tra phần mềm với đánh giá trên nhãn chuẩn.

## 11 Tài liệu tham khảo

- OpenCV, [Image Segmentation with Watershed Algorithm](https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html).
- OpenCV, [Histogram Equalization](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html).
- scikit-image, [graycomatrix và graycoprops](https://scikit-image.org/docs/stable/api/skimage.feature.html#skimage.feature.graycomatrix).
- Tài liệu phân công và nội dung các giai đoạn do người dùng cung cấp.

Các nguồn thuật toán trên không chứng nhận ngưỡng chất lượng gạo đang sử dụng. Bản notebook được chuyển từ triển khai module Python trước đây; lịch sử bản trước nằm trong Git.
