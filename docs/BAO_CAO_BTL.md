# Báo cáo hệ thống đánh giá chất lượng gạo bằng xử lý ảnh

## 1 Mục tiêu và phạm vi

Đề tài xây dựng chương trình nhận ảnh nhiều hạt gạo, tách từng vùng hạt, đo đặc trưng và phân loại bằng các quy tắc if/else. Mục tiêu của bản triển khai là cung cấp một quy trình chạy được và có thể giải thích, kiểm tra từng bước trên dữ liệu của nhóm. Không sử dụng học máy.

Hình dạng và màu sắc là hai trục đánh giá độc lập. Một hạt có thể vừa vỡ vừa vàng; vì vậy không gộp ngay thành một nhãn “Tốt/Kém/Tệ”. Kết cấu GLCM là đặc trưng bổ trợ để khảo sát, chưa có ngưỡng phân loại bất thường vì chưa có dữ liệu đối chiếu phù hợp.

Hệ thống đánh giá dấu hiệu quan sát được trên ảnh. Không kết luận hạt lép, độ ẩm, chất lượng dinh dưỡng hay an toàn thực phẩm từ ảnh chụp từ trên xuống. Không tự gán cấp chất lượng thương mại cho cả mẻ gạo.

## 2 Tiêu chí và định nghĩa nhãn

| Trục | Nhãn | Quy tắc thử nghiệm |
|---|---|---|
| Hình dạng | Nguyên | Chiều dài / chiều dài hạt nguyên chuẩn ≥ 0,80 |
| Hình dạng | Vỡ | Chiều dài / chiều dài hạt nguyên chuẩn < 0,70 |
| Hình dạng | Không xác định | Thiếu chuẩn, hạt cắt biên, đặc trưng lỗi hoặc tỷ lệ từ 0,70 đến dưới 0,80 |
| Màu sắc | Vàng | Tỷ lệ pixel vàng ≥ 0,25 và chưa đồng thời đạt ngưỡng sẫm |
| Màu sắc | Sẫm | Tỷ lệ pixel sẫm ≥ 0,30 và chưa đồng thời đạt ngưỡng vàng |
| Màu sắc | Bình thường | Hai tỷ lệ pixel vàng/sẫm đều ≤ 0,10 |
| Màu sắc | Không xác định | Giá trị chuyển tiếp, thiếu đặc trưng hoặc đồng thời đạt ngưỡng vàng và sẫm |

Các con số trên là **cấu hình khởi đầu để thử code**, không được diễn giải thành tiêu chuẩn đã được công nhận. Chiều dài chuẩn phải lấy từ hạt nguyên đã xác nhận, cùng giống và tỷ lệ chụp. `length_ratio` khác `aspect_ratio`: đại lượng thứ nhất so với chiều dài tham chiếu, đại lượng thứ hai là dài/rộng của chính hạt đó.

Kết luận tổng hợp “Có dấu hiệu lỗi” xuất hiện khi hạt vỡ hoặc có màu vàng/sẫm; “Đạt tiêu chí ảnh đã chọn” chỉ xuất hiện khi nguyên và màu bình thường. Các trường hợp còn lại là “Cần kiểm tra”. Đây là kết luận theo cấu hình của bài tập.

## 3 Dữ liệu và chuẩn bị

Dữ liệu hiện có gồm 38 ảnh trong `raw_dataset` và 31 ảnh trong `batch_dataset`. Trong nhóm tham chiếu có Tot 20, Vo 4, Kem 8, Te 4 và Tap_chat 2. Các ảnh chứa nhiều đối tượng; một số ảnh mẻ gạo có đồng xu làm tham chiếu.

Kiểm kê đọc ảnh xác nhận 69 tệp hợp lệ, trong đó 2 bản trùng nội dung pixel. Hai cặp trùng là ảnh batch số 12/13 và 14/15. Không xóa tệp gốc; manifest đánh dấu bản trùng và loại khỏi danh sách sử dụng chính. Còn 67 ảnh duy nhất.

Mỗi dòng manifest có đường dẫn tương đối, nhãn thư mục nguồn, SHA-256 tệp và nội dung pixel, kích thước, trạng thái đọc, ảnh trùng, tập dữ liệu, đường dẫn hai nhánh tiền xử lý và tỷ lệ resize. Nhãn hình dạng/màu từng hạt để trống, trạng thái chưa kiểm chứng. Không suy ra mọi hạt trong Tot đều nguyên và bình thường, hoặc mọi hạt trong Kem/Te đều vàng/sẫm.

Chia tập sơ bộ theo ảnh tạo 58 ảnh calibration và 9 ảnh test. Cùng một nội dung pixel luôn thuộc cùng tập. Việc này chỉ ngăn trùng chính xác; ảnh gần giống hoặc cùng phiên chụp vẫn cần nhóm thủ công để tránh rò rỉ. Không dùng ảnh test để đặt ngưỡng rồi báo kết quả test như một đánh giá độc lập.

## 4 Tiền xử lý ảnh

Ảnh được đọc qua `imdecode` từ byte tệp để hỗ trợ đường dẫn tiếng Việt trên Windows. Resize giữ tỷ lệ, cạnh dài tối đa mặc định 1600 px, không phóng to ảnh nhỏ. Với tỷ lệ s = min(1, 1600 / max(H,W)), kích thước mới là round(Ws), round(Hs). Lưu riêng scale_x và scale_y thực tế để bù sai số làm tròn khi đo hình học.

Nhánh màu chỉ resize, không cân bằng histogram và không làm mờ màu trước khi đo RGB/HSV. Nhánh phân đoạn gồm chuyển xám, Gaussian 3×3 và tùy chọn tương phản. Có ba lựa chọn: giữ nguyên, `equalizeHist` và CLAHE. Mặc định giữ nguyên; người dùng so sánh kết quả trước khi chọn.

Notebook ban đầu ép mọi ảnh thành 800×800 và luôn equalizeHist. Phần tiền xử lý hiện tại trong `preprocessing.py` sửa hai điểm này để tránh làm méo đặc trưng dài/rộng và khuếch đại nền/nhiễu không cần thiết. Dự án hiện chạy bằng các module Python, không phụ thuộc notebook.

## 5 Phân đoạn và tách hạt

Luồng mặc định: ảnh xám → Otsu → xác định cực tính → Opening → Closing → lấp lỗ kín → Connected Components → Watershed khi phù hợp → ROI và mask từng vùng.

Otsu chọn ngưỡng từ phân bố mức xám. Với lựa chọn tự động, chương trình xem tỷ lệ pixel sáng trên biên ảnh để quyết định đảo mask, giả định biên chủ yếu là nền. Có thể chỉ định hạt sáng/nền tối hoặc hạt tối/nền sáng. Khi giả định không đúng, người dùng cần kiểm tra và đổi cực tính.

Opening và Closing dùng nhân ellipse 3×3, mỗi thao tác một lần theo mặc định. Vùng có diện tích dưới 12 px trên ảnh xử lý bị loại như nhiễu; đây là tham số phụ thuộc độ phân giải, cần giảm nếu ảnh có hạt rất nhỏ. Lấp lỗ chỉ xử lý vùng kín bên trong mask.

Đối với vùng có độ đặc dưới 0,97, chương trình thử tách bằng distance transform và Watershed. Bản đồ khoảng cách được làm mượt, lấy cực đại có độ nổi bật tối thiểu và lọc các điểm mầm quá gần nhau. Nếu không có ít nhất hai điểm mầm hợp lệ, giữ nguyên vùng. Nếu một phần sau tách nhỏ hơn diện tích tối thiểu, hủy phép tách đó. Biên Watershed được gán về vùng mầm gần nhất để tránh làm mất pixel trong mask.

Mỗi vùng có ID, bounding box, centroid, contour, mask ROI, cờ cắt biên và cờ đã tách. ID là định danh của lần phân đoạn hiện tại, không bền vững sau khi đổi cấu hình. Watershed là một phép tách theo hình học, không đảm bảo phục hồi được hạt che khuất/chồng lên nhau.

Hạt tối có thể bị bỏ sót nếu Otsu chọn ngưỡng thiên về hạt sáng. Ứng dụng cho phép dùng ngưỡng thủ công khi cần; kết quả và cấu hình ghi rõ phương pháp đã dùng. Luôn kiểm tra mask trước khi phân tích các nhãn màu.

## 6 Đặc trưng

### 6.1 Hình dạng

Contour được quy về tọa độ ảnh gốc trước khi đo. Diện tích A dùng `contourArea`, chu vi P dùng `arcLength`. Chiều dài L và chiều rộng W là hai cạnh của `minAreaRect`, với L ≥ W. Lưu cả diện tích contour và diện tích đếm pixel để nhận biết khác biệt do raster hóa.

Các đại lượng dẫn xuất: Aspect Ratio = L/W; Circularity = 4πA/P²; Solidity = A/A_hull. Diện tích có đơn vị px²; chiều dài/rộng/chu vi có đơn vị px tại ảnh gốc. Không đổi sang mm khi chưa có hiệu chuẩn vật lý đáng tin cậy. Đồng xu không được tự động dùng làm chuẩn vì chưa biết kích thước thực và điều kiện phối cảnh.

### 6.2 Màu sắc

Chỉ lấy pixel nằm trong mask. Để giảm ảnh hưởng viền nền do Gaussian/resize, mask đo màu được co vào một pixel bằng nhân ellipse 3×3 nếu phần còn lại có ít nhất 3 pixel và chiếm tối thiểu 50% mask; hạt quá nhỏ dùng mask ban đầu. Lưu số pixel đo màu trong `color_pixel_count`. Tính RGB trung bình, HSV trung bình và tỷ lệ pixel theo điều kiện màu trên cùng mask đo màu này. Trong OpenCV, H thuộc 0–179, S/V thuộc 0–255. H trung bình là thống kê mô tả số học, không dùng để quyết định nhãn; với màu gần vòng quấn H cần cân nhắc thống kê góc.

Pixel vàng mặc định có 10 ≤ H ≤ 40, S ≥ 55 và V ≥ 65. Pixel sẫm có V ≤ 85. Tỷ lệ bằng số pixel thỏa điều kiện chia tổng pixel trong mask. Các ngưỡng phụ thuộc camera, giống gạo, cân bằng trắng và ánh sáng; ảnh gạo ngả vàng tự nhiên không thể mặc nhiên coi là lỗi chất lượng.

### 6.3 Kết cấu

Ảnh xám được lượng tử hóa về 32 mức. GLCM sử dụng khoảng cách một pixel theo bốn hướng: ngang, dọc và hai đường chéo. Chỉ đếm cặp có cả hai đầu nằm trong mask; đối xứng hóa và chuẩn hóa ma trận. Nhờ vậy nền của ROI không tạo đặc trưng kết cấu giả.

Xuất Contrast, Homogeneity, Energy và Correlation, lấy trung bình trên các hướng hợp lệ. Nếu không có cặp pixel hợp lệ, để giá trị thiếu và lưu số cặp bằng 0; không thay bằng số giả. GLCM chưa tham gia quyết định phân loại trong bản này.

## 7 Phân loại và thống kê

Hai hàm `classify_shape` và `classify_color` trả nhãn cùng lý do. Ngưỡng có vùng chuyển tiếp để giữ “Không xác định” thay vì ép mọi trường hợp vào một lớp. Khi thiếu tham chiếu, toàn bộ nhãn hình dạng là Không xác định; màu vẫn được đánh giá riêng.

Bộ lọc vật lớn gần tròn là tùy chọn: diện tích pixel lớn hơn 5 lần trung vị các vùng trong ảnh, Aspect Ratio < 1,4 và Circularity > 0,70. Vùng thỏa điều kiện bị loại khỏi mẫu số hạt. Đây chỉ là quy tắc giảm việc đếm đồng xu; không phải bộ phân loại tạp chất hoàn chỉnh, và có thể không phù hợp khi vật lạ có hình dạng khác hoặc ảnh chỉ có một vật.

Thống kê gồm số vùng phát hiện, số hạt ứng viên, vùng bị loại, số hạt chưa xác định ở ít nhất một trục, diện tích/dài trung bình, HSV trung bình và số hạt cắt biên. Với từng trục, số lượng nhóm chia tổng số hạt ứng viên nhân 100. Các nhóm trong mỗi trục cộng thành 100%; không cộng tỷ lệ hình dạng với tỷ lệ màu. Ảnh không có hạt xuất số đếm bằng 0, tỷ lệ bằng 0 và trung bình để trống.

## 8 Ứng dụng và kết quả xuất

Ứng dụng có tải ảnh, chọn ảnh có sẵn, điều chỉnh phân đoạn và quy tắc. Bốn tab trình bày các bước xử lý, bảng phân loại/biểu đồ, gán nhãn đối chiếu và hướng dẫn. Có thể tải CSV, ảnh kết quả trong ZIP và cấu hình JSON. Giao diện gán nhãn cho phép thêm/xóa dòng và sửa hộp bao; phải tải CSV để lưu trước khi đổi ảnh/cấu hình.

CLI dùng chung module với giao diện Streamlit. Mỗi kết quả có ảnh các bước, mask nhị phân, bản đồ instance dạng NPY, contour/ID/nhãn, ROI màu và mask riêng, features.csv, classification.csv, statistics.csv, summary.json và biểu đồ. CSV có BOM UTF-8 để Excel đọc tiếng Việt thuận tiện.

## 9 Hiệu chỉnh và đánh giá

Sau khi gán nhãn thủ công, `calibrate.py` khớp hộp bao với đặc trưng bằng IoU, lấy trung vị chiều dài của ít nhất 5 hạt nguyên không cắt biên làm chuẩn. Công cụ báo min/trung vị/max của đặc trưng theo nhãn để nhóm phân tích phạm vi giá trị. Các ngưỡng if/else vẫn cần lựa chọn dựa trên dữ liệu calibration và tiêu chí thống nhất; công cụ không tự gắn cờ đã hiệu chỉnh.

`evaluate.py` yêu cầu nhãn kiểm chứng có tên người gán nhãn, hộp bao hợp lệ và hai nhãn hợp lệ. Khớp một-một bằng Hungarian, ưu tiên số cặp có IoU hộp bao ≥ 0,5 rồi tối ưu IoU. Báo độ chính xác và ma trận nhầm lẫn riêng cho hình dạng/màu trên những hạt đã khớp. Độ chính xác này không bao gồm hạt bị bỏ sót.

Khi xác nhận gán nhãn hết ảnh bằng `--complete-image`, báo thêm precision/recall phát hiện, số hạt thiếu/thừa và sai số đếm tuyệt đối. Không có xác nhận gán hết ảnh thì không báo các chỉ số đó. IoU được dùng ở đây là IoU hộp bao, không phải IoU mask. Muốn đánh giá đường biên chính xác hơn cần bổ sung mask chuẩn từng hạt.

Kiểm thử tự động bao gồm giữ tỷ lệ và màu, quy đổi đơn vị sau resize, hình dạng/màu độc lập, nền sáng, hạt tiếp xúc, hạt dài đơn lẻ, cắt biên, ảnh rỗng, ảnh lỗi, đường dẫn tiếng Việt, GLCM loại nền, ngăn ảnh trùng chia sang hai tập và yêu cầu nhãn đối chiếu. Kết quả kiểm thử phần mềm không thay thế độ chính xác thực tế.

Thư mục `dataset/synthetic_demo` có một ảnh tổng hợp năm hạt và mask/nhãn sinh từ công thức vẽ. Ảnh này dùng để minh họa nguyên, vỡ, vàng, sẫm và vỡ đồng thời vàng. Có ghi rõ nguồn nhãn là bộ sinh tổng hợp. Mọi kết quả trên ảnh này chỉ chứng minh hành vi trên dữ liệu tổng hợp.

Dữ liệu ảnh thật hiện chưa có nhãn chuẩn từng hạt được kiểm chứng, nên báo cáo không đưa ra accuracy/F1/recall thực tế hay tuyên bố đếm đúng mọi hạt. Nhật ký `outputs/verification` chỉ xác nhận ảnh chạy được, đặc trưng hữu hạn và số liệu xuất nhất quán. Muốn kết luận hiệu quả phải gán nhãn độc lập, hiệu chỉnh và đánh giá theo quy trình trên.

## 10 Kịch bản demo và bảo vệ

1. Mở manifest và ứng dụng, trình bày nguồn ảnh, hai ảnh trùng và hai nhánh màu/xám. So sánh none/equalize/CLAHE trong giao diện và giải thích vì sao giữ tỷ lệ.
2. Mở ứng dụng, chọn ảnh nhiều hạt. Giải thích Otsu, cực tính mask và tác dụng của hình thái học. Bật/tắt Watershed để xem khác biệt ở vùng tiếp xúc.
3. Chọn một ID, đối chiếu ROI và vector đặc trưng. Nêu rõ pixel ảnh gốc khác mm và length_ratio khác aspect_ratio.
4. Phân tích ảnh tổng hợp bằng config kèm theo để minh họa hạt vừa vỡ vừa vàng. Không dùng kết quả tổng hợp làm số liệu chính xác ảnh thật.
5. Giải thích nhãn Không xác định khi thiếu chuẩn hoặc ở vùng chuyển tiếp. Trình bày bảng thống kê hai trục, ảnh đánh số và xuất CSV.
6. Mở bảng nhãn thủ công, giải thích calibration/test và cách dùng công cụ đánh giá. Nêu các giới hạn ảnh chồng lấp, hạt tối, ánh sáng và vật lạ.

Nếu được hỏi “vì sao không dùng ML”, câu trả lời là phạm vi đề tài yêu cầu quy tắc từ đặc trưng đo được; hệ thống dùng các phép xử lý ảnh và if/else có thể giải thích từng bước. Nếu được hỏi “độ chính xác bao nhiêu”, chỉ sử dụng số liệu đo trên dữ liệu kiểm chứng; hiện chưa đủ nhãn ảnh thật để công bố con số đó.

## 11 Đối chiếu phân công

| Thành viên | Phần đã triển khai | Tệp kiểm tra |
|---|---|---|
| 1 | Kiểm kê, phát hiện trùng/lỗi, manifest, chia tập sơ bộ và hai nhánh tiền xử lý | dataset_tools.py, preprocessing.py |
| 2 | Otsu, hình thái học, distance transform, Watershed, Connected Components, ROI, bbox, centroid và ID | segmentation.py |
| 3 | Shape, RGB/HSV, tỷ lệ pixel đổi màu, GLCM có mask và vector đặc trưng | feature_extraction.py |
| 4 | if/else hai trục, trạng thái chưa xác định, thống kê/biểu đồ, khảo sát ngưỡng và đánh giá | classification.py, rice_statistics.py, calibrate.py, evaluate.py |
| Cả nhóm | Tích hợp CLI/Streamlit, xuất CSV/ảnh và kiểm thử | pipeline.py, app.py, main.py, tests/ |

Phần cần dữ liệu kiểm chứng bổ sung là nhãn thủ công từng hạt, nhóm phiên chụp và ngưỡng chất lượng được nhóm/giảng viên thống nhất. Công cụ để thực hiện và đối chiếu đã có trong dự án.

## 12 Tài liệu tham khảo

- OpenCV, [Image Segmentation with Watershed Algorithm](https://docs.opencv.org/4.x/d3/db4/tutorial_py_watershed.html): nguyên lý marker, Otsu, distance transform và Watershed.
- OpenCV, [Histogram Equalization](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html): cân bằng histogram và CLAHE.
- scikit-image, [graycomatrix và graycoprops](https://scikit-image.org/docs/stable/api/skimage.feature.html#skimage.feature.graycomatrix): định nghĩa GLCM và các đặc trưng kết cấu.
- Tài liệu phân công `PhanCongViecLam-1.docx` và nội dung các giai đoạn do người dùng cung cấp: phạm vi bốn thành viên và yêu cầu không dùng ML.

Các thuật toán trong dự án được cài đặt theo phạm vi bài tập; các tài liệu trên không chứng nhận ngưỡng chất lượng gạo đang sử dụng.
