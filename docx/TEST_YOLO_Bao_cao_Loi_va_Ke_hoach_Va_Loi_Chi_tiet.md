
**DRIVELINKER MINI / TEST_YOLO**

BÁO CÁO LỖI NGHIỆP VỤ 
VÀ KẾ HOẠCH VÁ LỖI CHI TIẾT
**Module giám sát trạng thái tài xế bằng camera chính diện**

| THÔNG TIN | NỘI DUNG |
|---|---|
| Phạm vi | YOLOv8 + MediaPipe + FatigueManager + âm thanh + bằng chứng + kiểm thử |
| Nguồn đánh giá | test_yolo.zip (mã nguồn và tài nguyên trong tệp đính kèm) |
| Góc camera | Chính diện tài xế; chưa xét camera nghiêng, camera cabin nhiều góc |
| Ngày lập báo cáo | 17/10/2026 |
| Trạng thái | Prototype đã có; chưa được kiểm chứng end-to-end trên webcam trong môi trường đánh giá |

**MỤC TIÊU TÀI LIỆU**
Chỉ rõ cái đã có, cái đang sai và cái còn thiếu; sau đó chuyển từng vấn đề thành việc lập trình, kiểm thử và điều kiện hoàn thành có thể đối chiếu với source code.

> Chú ý: Tài liệu này là kế hoạch kỹ thuật/QA, không xác nhận hệ thống đã đủ điều kiện sử dụng cho mục đích an toàn giao thông thực tế.

# MỤC LỤC NỘI DUNG

**PHẦN I. HIỆN TRẠNG, LỖI SAI VÀ PHẦN CÒN THIẾU**
1. Phạm vi và phương pháp đánh giá
2. Những gì source code đã có
3. Danh sách lỗi và thiếu sót có mã theo dõi
4. Kết quả tái hiện lỗi bằng kiểm thử logic
5. Đánh giá dữ liệu AI, mức độ hoàn thành và rủi ro
**PHẦN II. KẾ HOẠCH VÁ LỖI VÀ HOÀN THIỆN**
6. Mô hình nghiệp vụ và kiến trúc đích
7. Kế hoạch sửa chi tiết theo từng module
8. Lộ trình triển khai và danh sách đầu ra
9. Bộ kiểm thử nghiệm thu và Definition of Done
10. Rủi ro triển khai và các quyết định phải thống nhất
**PHỤ LỤC A. 37 cấu hình đang không được sử dụng**
**PHỤ LỤC B. Cấu trúc thư mục đề xuất và mẫu sự kiện**
> Dùng Heading trong Word để xem Navigation Pane và tự tạo mục lục có số trang khi cần. Nội dung được bố cục thành hai phần chính đúng thứ tự yêu cầu.

# TÓM TẮT ĐIỀU HÀNH

Kết luận: TEST_YOLO đã có nguyên mẫu nhận diện khuôn mặt, EAR/MAR, ước lượng góc đầu, cơ chế tính điểm, cảnh báo âm thanh, ảnh bằng chứng và mô hình YOLOv8. Tuy nhiên, logic xác nhận sự kiện chưa an toàn, một số biến cấu hình chưa dùng, thiếu giám sát mất dữ liệu và chưa có kiểm thử thực tế đủ tin cậy.

| CHỈ DẤU | KẾT QUẢ XÁC MINH |
|---|---|
| Mã nguồn Python | 7 file, tổng 564 dòng; đã kiểm tra cú pháp |
| Config | 68 biến; 31 được tham chiếu, 37 chưa được tham chiếu từ các file Python còn lại |
| Tập dữ liệu | 237 ảnh train; 12 ảnh validation; 9 ảnh test |
| Mô hình | YOLOv8n; weights best.pt/last.pt tồn tại; Face Landmarker tồn tại |
| Kết quả train | mAP50(B) = 0,995 ở epoch cuối; không đủ chứng minh hiệu quả ngoài hiện trường |
| Rò rỉ đánh giá | 9 tên ảnh gốc xuất hiện trong hơn một tập train/valid/test |
| Mức triển khai | Ước lượng quản trị 46/100 theo rubric tính năng, KHÔNG phải accuracy AI |

Ưu tiên số 1: vá mất tín hiệu / mất khuôn mặt; xác nhận thời gian ngáp / nhắm mắt; sửa cách cộng điểm; bỏ cơ chế reset nguy hiểm không điều kiện sau 10 giây. Chỉ khi nhóm P0 đạt mới triển khai sâu thêm gaze, PERCLOS, head pose và tích hợp Backend.

# PHẦN I. HIỆN TRẠNG, LỖI SAI VÀ PHẦN CÒN THIẾU

## 1. Phạm vi và phương pháp đánh giá

- Đọc đầy đủ 7 file Python: main.py, config.py, fatigue_manager.py, utils.py, train.py, canhbao.py, create_sound.py; đối chiếu README, data.yaml, ảnh bằng chứng, cấu trúc dữ liệu và kết quả train.
- Đánh giá luồng thực tế theo camera chính diện: camera → xử lý YOLO → trích xuất landmarks → EAR/MAR/Pitch → tính điểm → cảnh báo → lưu bằng chứng.
- Kiểm tra cú pháp và tái hiện các quy tắc FatigueManager bằng đồng hồ mô phỏng; xem xét tĩnh code khởi động camera, audio, giải phóng tài nguyên và chuẩn bị triển khai.
- Không có webcam và bộ thư viện AI đầy đủ trong môi trường kiểm tra này, do đó không đưa ra kết luận về FPS thực, độ nhạy, độ đặc hiệu hoặc hiệu quả hoạt động liên tục.

## 2. Những gì source code đã có

| THÀNH PHẦN | HIỆN TRẠNG | NHẬN ĐỊNH |
|---|---|---|
| main.py | Camera OpenCV; YOLO; MediaPipe; overlay; cảnh báo; lưu ảnh | Có flow thực tế, nhưng nhiều lỗi điều phối và xử lý trạng thái |
| config.py | 68 ngưỡng, công tắc, tham số chất lượng | Thiết kế rộng; 37 biến chưa được sử dụng |
| fatigue_manager.py | Nhắm mắt; tốc độ chớp; ngáp; gục đầu; 4 mức trạng thái | Có state nhưng chưa nhất quán, dễ cảnh báo giả |
| utils.py | EAR hai mắt, MAR, pitch từ landmarks | EAR/MAR dùng được ở mức prototype; pitch chưa hiệu chuẩn |
| train.py và weights | Train YOLOv8n 50 epoch; best.pt/last.pt | Có training và checkpoint; cần benchmark khách quan |
| canhbao.py + create_sound.py | Sinh TTS và tạo beep WAV | 2 cách cùng ghi đè một tên file, định dạng TTS sai |
| bang_chung/ | 5 ảnh sự kiện từ chạy thử trước | Có chứng cứ mẫu, chưa có metadata/sổ sự kiện |
| README.md | Hướng dẫn cài và chạy | Một số tên tệp/đường dẫn/thông số lệch code |

## 3. Danh sách lỗi và thiếu sót có mã theo dõi

Quy ước: P0 = phải sửa trước khi demo đáng tin cậy; P1 = cần để hoàn thiện nghiệp vụ; P2 = cải thiện chất lượng/vận hành. Nhóm P0 có khả năng dẫn đến phát hiện nhầm, bỏ sót, lỗi vận hành hoặc chấm điểm sai.

| MÃ / ƯU TIÊN | LỖI / THIẾU | DẪN CHỨNG | HƯỚNG VÁ |
|---|---|---|---|
| I-01 P0 | Mất khuôn mặt nhưng bộ đếm nhắm mắt vẫn chạy | main.py: 98–125; fatigue_manager.py: 33–55 | Reset/pause đúng, tách NO_FACE khỏi EYES_CLOSED |
| I-02 P0 | Ngáp nhẹ cộng 40 điểm ngay ở frame đầu | fatigue_manager.py: 85–100; config.py: LIGHT_YAWN_MIN_TIME | Thêm candidate → confirm → end |
| I-03 P0 | 3 lần há miệng thoáng qua có thể báo ngáp liên tục | fatigue_manager.py: 66–104 | Sử dụng queue timestamps + gap/cooldown |
| I-04 P0 | Chớp mắt chậm 0,6s lên ngay 60 điểm | fatigue_manager.py: 57–64 | Đổi sang cộng 10 có giới hạn và chống cộng lặp |
| I-05 P1 | Không có suy giảm điểm khi tỉnh táo ổn định | config.py: SCORE_DECAY_*; fatigue_manager.py | Tích lũy thời gian hợp lệ, decay theo interval |
| I-06 P0 | Reset nguy hiểm sau 10s dù hành vi vẫn tiếp diễn | main.py: 128–161 | Tách âm thanh cooldown khỏi hành vi/risk |
| I-07 P1 | Lý do cảnh báo cũ không được quản lý theo sự kiện | fatigue_manager.py: violation_reason; reset() | Event riêng có reason/time/severity |
| I-08 P1 | Ngáp sâu có thể tính cả thời gian hạ xuống ngáp nhẹ | fatigue_manager.py: 75–104 | Bộ đếm deep_dwell độc lập, có hysteresis |
| I-09 P0 | Góc gục đầu thiếu tham chiếu hướng camera | utils.py: 38–48; fatigue_manager.py: 107–121 | SolvePnP/3D pose + baseline + test |
| I-10 P0 | Mất khuôn mặt chưa cảnh báo đúng ngưỡng 2s | main.py: 119–125; config.py: FACE_MISSING_TIME | State NO_FACE với timer, nhắc nhở riêng |
| I-11 P0 | Camera timeout dùng số frame lỗi, không dùng giây thực | main.py: 74–85 | monotonic_elapsed + camera error event |
| I-12 P0 | Khởi động camera lỗi không dừng sớm / không cleanup bảo đảm | main.py: 63–85, 170–180 | Context/try-finally; teardown mọi nhánh |
| I-13 P1 | Kết quả YOLO không được đưa vào quyết định nghiệp vụ | main.py: 88–98 | Quyết định vai trò YOLO: classifier phụ hoặc loại khỏi hot path |
| I-14 P1 | PERCLOS, gật gù, gaze, yaw/roll chưa có logic | config.py vs fatigue_manager.py/utils.py | Triển khai module mới và validity gate |
| I-15 P1 | Hai script âm thanh ghi chung .wav; TTS thực chất MP3 | canhbao.py: 1–11; create_sound.py: 1–22 | wav PCM beep riêng; mp3 TTS riêng |
| I-16 P1 | Thiếu cơ chế chất lượng landmarks / định danh đúng tài xế | main.py: FaceLandmarkerOptions num_faces=1 | ROI driver, validity flags, calibration |
| I-17 P1 | Có ảnh cùng gốc trong các split train/val/test | dataset train/valid/test | Re-split theo source/subject rồi đánh giá lại |
| I-18 P1 | Thiếu test tự động, lock deps và benchmark FPS | Toàn bộ project; README.md | pytest, requirements, smoke, replay benchmark |
| I-19 P1 | Ảnh bằng chứng chưa có hồ sơ sự kiện và bảo mật | main.py: 138–154; bang_chung/ | Event ID, metadata, retention, kiểm tra lưu |
| I-20 P2 | Vẽ lên frame trước khi MediaPipe nhận ảnh | main.py: 88–102 | Giữ inference_frame tách display_frame |
| I-21 P2 | README lệch tên và mô tả hành vi | README.md: 10–29, 69–95 | Cập nhật tài liệu chạy thật |
| I-22 P2 | Config cảnh báo/thời gian không khớp mô tả README | config.py: WARNING_LEVEL_*; README.md: 13 | Định nghĩa lại thống nhất cấp 0–3 |

## 4. Kết quả kiểm thử logic đã tái hiện

Các test sau dùng mô phỏng time.time của fatigue_manager.py, không chạy YOLO/camera. “Đạt theo luật đang viết” không có nghĩa ngưỡng là đúng về mặt lâm sàng hoặc áp dụng ngoài đời.

| MÃ TEST | TÌNH HUỐNG | KẾT QUẢ HIỆN TẠI | ĐÁNH GIÁ |
|---|---|---|---|
| UT-01 | Một frame MAR = 0,72 | Score +40 ngay | FAIL: chưa chờ 1,5s |
| UT-02 | 3 lần mở/đóng miệng trong 0,6s | Score 100, NGAP LIEN TUC | FAIL: báo giả |
| UT-03 | MAR = 0,88 kéo dài 3,1s | Score 100, NGAP SAU | PASS theo rule hiện tại |
| UT-04 | EAR nhắm 0,6s rồi mở | Score 60 | FAIL: config đề xuất +10 |
| UT-05 | Chớp bình thường 0,2s từ score 40 | Score 35 | PASS theo rule hiện tại |
| UT-06 | Pitch đầu vào 26° trong 2,1s | Score 100, GUC DAU | PASS rule; hình học chưa tin cậy |
| UT-07 | EAR nhắm + 10s không nhận mặt + nhận lại | Score 100, ngủ gật | FAIL: nối nhầm gap |
| UT-08 | Score 40, sau 300s không có update nguy cơ | Score 40 | FAIL: thiếu decay |

## 5. Dữ liệu AI, phạm vi hoàn thành và rủi ro

### 5.1. Dữ liệu huấn luyện và tính độc lập

Dataset công bố 3 class: Alert, Microsleep, Yawn. Source chứa 237 ảnh train, 12 ảnh valid và 9 ảnh test. Trong results.csv ở epoch 50: precision(B) ~0,900, recall(B) ~0,998, mAP50(B)=0,995 và mAP50-95(B) ~0,763. Đây là metric trên bộ dữ liệu có sẵn, không phải kiểm chứng hệ thống toàn diện trên tài xế thực tế.
Kiểm tra filename đã bỏ phần hậu tố Roboflow “.rf.<hash>” cho thấy 9 tên gốc xuất hiện ở hơn một split. Cần coi đây là dấu hiệu giao thoa dữ liệu; phải xác minh ảnh liên quan và split lại theo người/video/session, không được xem 0,995 là độ chính xác ngoài thực địa.

### 5.2. Ước lượng mức hoàn thiện

| HẠNG MỤC | TRỌNG SỐ | ĐIỂM HIỆN TẠI |
|---|---|---|
| Camera + giao diện | 10 | 8 |
| YOLO đã train | 10 | 6 |
| Mắt | 15 | 9 |
| Ngáp | 15 | 7 |
| Tư thế đầu | 10 | 3 |
| Hướng nhìn | 10 | 0 |
| Chấm điểm | 10 | 5 |
| Cảnh báo + bằng chứng | 10 | 7 |
| An toàn + xử lý lỗi | 5 | 1 |
| Test/đóng gói/tích hợp | 5 | 0 |
| TỔNG | 100 | 46 |

46/100 là rubric ước tính mức triển khai chức năng, không phải phần trăm code đã đúng, không phải tiến độ dự án Capstone 1 và không phải accuracy của YOLO. Tỷ lệ thực tế cần cập nhật sau khi nghiệm thu từng test case.

### 5.3. Giới hạn riêng của góc chính diện

- Có thể quan sát nhắm mắt, mức mở miệng, thay đổi tư thế đầu, ước lượng hướng mắt trong giới hạn ánh sáng, kính đeo, góc lệch và độ phân giải.
- Không khẳng định người dùng điện thoại hoặc thực sự thiếu tập trung chỉ từ hướng nhìn xuống; sự kiện phải có mức độ tin cậy và trường “nghi ngờ”.
- Chưa thể phân biệt chắc chắn ngủ gật và chủ động nhắm mắt; cần thời gian, chuỗi tín hiệu, bối cảnh và kiểm thử đối kháng bằng dữ liệu thật.

# PHẦN II. KẾ HOẠCH VÁ LỖI VÀ HOÀN THIỆN

## 6. Luồng nghiệp vụ và kiến trúc đích

Nguyên tắc kiến trúc: phát hiện hành vi (sự kiện) và mức độ rủi ro (risk score) là hai khái niệm khác nhau. Camera mất mặt là sự cố chất lượng dữ liệu, không phải bằng chứng người lái đang nhắm mắt. Âm thanh là hành động thông báo, không phải cơ chế xóa nguy cơ.

| GIAI ĐOẠN | INPUT → XỬ LÝ | OUTPUT BẮT BUỘC |
|---|---|---|
| 1. Frame acquisition | Camera + monotonic timestamp; kiểm tra frame đúng kích thước/đúng tín hiệu | FrameData(valid, time, frame_id) |
| 2. Face validation | ROI tài xế, landmarks hợp lệ, xử lý kính/che khuất | face_state: VALID / NO_FACE / INVALID |
| 3. Feature extraction | EAR, MAR, head pose, PERCLOS, gaze nếu đủ điều kiện | FeatureVector(value, quality, timestamp) |
| 4. Event detector | Máy trạng thái theo thời gian: candidate → confirmed → ended | BehaviorEvent có thời điểm, độ dài, reason, confidence |
| 5. Risk manager | Cộng/trừ điểm khi có event hợp lệ, time decay; giữ lỗi an toàn riêng | score 0..100, level, active_event, data_quality |
| 6. Alert manager | Chính sách âm thanh theo mức, chống lặp, không reset risk | AlertState với cooldown/time_last_played |
| 7. Evidence + logging | Lưu jpg khi sự kiện mới; id/JSONL; sai lưu phải báo | Sự kiện bền vững, tra cứu được |
| 8. Local UI / optional BE | Hiển thị trạng thái + lý do; gửi API theo queue nếu có mạng | Màn hình dễ đọc; sự kiện không mất do mất mạng |

### 6.1. Quy tắc trạng thái nền

- CAMERA_ERROR: không có frame hợp lệ sau khoảng timeout tính bằng monotonic; tạo sự kiện lỗi thiết bị, ngừng chấm điểm mệt mỏi từ dữ liệu cũ.
- NO_FACE: vẫn có frame nhưng khuôn mặt tài xế vắng/mất hợp lệ quá FACE_MISSING_TIME; không quy đổi thành ngủ gật, không tiếp tục đồng hồ blink/yawn.
- VALID_TRACKING: có khuôn mặt tài xế và feature hợp lệ; mới cho phép bộ phát hiện hành vi tích lũy thời gian.
- ALERTING: chỉ là trạng thái phát âm thanh; có thể tồn tại đồng thời với VALID_TRACKING. Khi alert kết thúc không reset bộ phân tích hành vi.
- WARMUP / RECALIBRATION: sau khi khởi động, đổi góc camera hoặc tái xuất hiện sau mất mặt, thu baseline rồi mới bật phán đoán góc/hướng nhìn.

### 6.2. Quy tắc cảnh báo được đề xuất

Giữ cấu hình mức Normal <30; Tired 30–59; Warning 60–84; Danger ≥85 làm baseline kiểm thử. Riêng sự kiện nguy cấp đã được xác nhận (ví dụ mắt nhắm kéo dài) được phép kích hoạt âm thanh ngay theo “rule override”, không buộc chờ score do ngáp cộng dồn. Mọi ngưỡng phải được đánh giá lại trên video thực nghiệm và phê duyệt trước khi coi là cố định.

## 7. Kế hoạch sửa chi tiết theo từng module

## M01 — Camera, vòng lặp và xử lý mất dữ liệu

**Ưu tiên: **P0  **| File liên quan: **main.py → camera_service.py, frame_processor.py**  | Ước tính: **2–3 ngày công
**Mục tiêu / lỗi cần xử lý: **Không phát hiện đúng timeout theo giây; thiếu teardown và gặp tình huống camera không mở.
1. Đưa CameraService.open/read/retry/close ra khỏi main; nếu không mở được camera thì tạo lỗi và kết thúc có kiểm soát.
2. Dùng time.monotonic() đo elapsed kể từ frame hợp lệ cuối; không nhân CAMERA_TIMEOUT với TARGET_FPS để đếm vòng fail.
3. Mỗi frame có frame_id, capture_time, valid; mọi read fail đổi state; retry có backoff ngắn không tạo vòng lặp CPU cao.
4. Tách inference_frame = frame.copy() và display_frame; dùng khung gốc cho MediaPipe/YOLO, overlay chỉ ở display.
5. Thay os._exit(0) bằng vòng chạy có cờ và khối try/finally đóng cap, face_landmarker, mixer và OpenCV windows.
**Tiêu chí nghiệm thu: **Không crash khi unplug/plug camera; sự kiện CAMERA_ERROR phát đúng thời gian thực; thoát qua Q/ESC/đóng cửa sổ đều giải phóng tài nguyên.
**Kiểm thử bắt buộc: **IT-CAM-01 không mở camera; IT-CAM-02 rút camera trong khi chạy; IT-CAM-03 đóng cửa sổ; IT-CAM-04 FPS thực thấp hơn TARGET_FPS.

## M02 — Theo dõi khuôn mặt và kiểm tra độ tin cậy

**Ưu tiên: **P0  **| File liên quan: **main.py → face_tracker.py, feature_validity.py**  | Ước tính: **2–3 ngày công
**Mục tiêu / lỗi cần xử lý: **Vắng mặt tài xế bị xem như dữ liệu trống, nhưng bộ đếm hành vi không được ngắt; chỉ num_faces=1 không bảo đảm là khuôn mặt tài xế.
1. Định nghĩa TrackingState: WARMUP, VALID_TRACKING, NO_FACE, INVALID_FACE, CAMERA_ERROR; phát state change.
2. Gán vùng ROI cố định/tùy chỉnh quanh ghế tài xế; nếu có nhiều mặt, chọn ứng viên trong ROI hoặc giữ track của tài xế đang theo dõi.
3. Khi landmark mất hoặc feature không hợp lệ, gọi on_tracking_lost(now) ở từng detector để đóng chuỗi candidate, không tăng dwell.
4. Đếm FACE_MISSING_TIME bằng monotonic; ngắt cảnh báo sai do gap, và tạo thông báo NO_FACE sau 2s.
5. Chỉ chấp nhận score khi feature.valid và chất lượng mẫu đủ; bỏ mẫu eye bị che khỏi PERCLOS denominator.
**Tiêu chí nghiệm thu: **Đứt nhận diện 10 giây rồi tìm lại không tạo sự kiện nhắm mắt 10 giây; NO_FACE và CAMERA_ERROR hiển thị khác nhau.
**Kiểm thử bắt buộc: **UT-FACE-01 gap mắt; IT-FACE-02 che mặt; IT-FACE-03 người thứ hai đi vào; IT-FACE-04 quay đầu quá lớn.
> Phụ thuộc: M01

## M03 — Mắt: EAR, chớp mắt chậm, microsleep, PERCLOS

**Ưu tiên: **P0 + P1  **| File liên quan: **utils.py, fatigue_manager.py → eye_detector.py, perclos_tracker.py**  | Ước tính: **3–4 ngày công
**Mục tiêu / lỗi cần xử lý: **Ngưỡng EAR cố định, slow blink tính sai, không có half-closed, PERCLOS và severe eye closed.
1. Tạo EyeDetector với các trạng thái OPEN, HALF_CLOSED, CLOSED, INVALID; EAR trung bình và tùy chọn từng mắt với reliability flag.
2. Hiệu chuẩn EAR mở bình thường tại đầu phiên; xác minh EAR_CLOSED / EAR_HALF_CLOSED với dữ liệu của từng người; áp dụng hysteresis/debounce.
3. Ghi thời điểm bắt đầu kết thúc một blink hợp lệ; 0,5–1,5s cộng SCORE_SLOW_BLINK=10 đúng một lần, không set score=60.
4. Theo dõi microsleep >=1,5s và sự kiện nghiêm trọng >=2,0s; nếu signal invalid thì hủy xác nhận liên tục hoặc tạm dừng theo quy tắc rõ ràng.
5. Tạo cửa sổ PERCLOS=60s; xác định mắt gần đóng dựa trên tỷ lệ đóng so với EAR baseline (PERCLOS_EYE_CLOSURE_RATIO=0,80), đo theo thời lượng, không chỉ đếm frame; denominator có quy tắc riêng và chỉ công bố kết quả khi valid_ratio >=0,8.
6. PERCLOS cảnh báo/nguy hiểm theo cấu hình, thêm thời điểm phát, không cộng điểm ở mỗi frame.
**Tiêu chí nghiệm thu: **Ngưỡng blink 0,6s tăng 10 điểm một lần; mất mặt không kích hoạt ngủ gật; PERCLOS không phát khi valid_ratio <0,8; thống kê so với nhãn video.
**Kiểm thử bắt buộc: **UT-EYE-01..07: 0,08s, 0,2s, 0,6s, 1,5s, 2,1s, gap, PERCLOS 24/25/40%.
> Phụ thuộc: M02

## M04 — Miệng: nhận diện đúng 1 lần ngáp và ngáp liên tục

**Ưu tiên: **P0  **| File liên quan: **fatigue_manager.py → yawn_detector.py**  | Ước tính: **2–3 ngày công
**Mục tiêu / lỗi cần xử lý: **Ngáp nhẹ cộng điểm từ 1 frame; 3 lần mở miệng nhanh làm score 100; deep dwell bị nối qua vùng MAR nhẹ.
1. Tách trạng thái IDLE → CANDIDATE → CONFIRMED → COOLDOWN; chỉ xác nhận light yawn khi MAR nằm trên ngưỡng đủ LIGHT_YAWN_MIN_TIME.
2. Deep yawn có đồng hồ deep_duration riêng; vượt MAR_DEEP_YAWN liên tục theo ngưỡng và xác nhận một lần trên mỗi event.
3. Đóng sự kiện khi MAR giảm dưới release threshold ổn định; gộp các đoạn gần nhau nếu gap <=YAWN_EVENT_GAP để tránh đếm trùng.
4. Giới hạn không cộng 2 lần cho cùng một event bằng event_id và YAWN_SCORE_COOLDOWN; xử lý ưu tiên deep so với light để không double count.
5. Dùng deque(timestamp) chỉ chứa sự kiện ngáp đã xác nhận trong YAWN_COUNT_WINDOW 120s; xóa item quá hạn theo rolling window.
**Tiêu chí nghiệm thu: **3 lần há miệng 0,1s không tạo cảnh báo; ngáp hợp lệ 1,5s được ghi một lần; 3 lần thật trong 120s tạo repeated_yawn đúng một event.
**Kiểm thử bắt buộc: **UT-YAWN-01 mở <1,5s; UT-YAWN-02 nói chuyện; UT-YAWN-03 deep >3s; UT-YAWN-04 gap 0,8/1,2s; UT-YAWN-05 lặp 120s.
> Phụ thuộc: M02

## M05 — Tư thế đầu 3 trục, cúi đầu và gật gù

**Ưu tiên: **P0 + P1  **| File liên quan: **utils.py, fatigue_manager.py → head_pose.py, head_event_detector.py**  | Ước tính: **3–5 ngày công
**Mục tiêu / lỗi cần xử lý: **Hiện dùng atan2(dz,dy) không đủ xác định pitch chuẩn camera; chưa có yaw, roll, head nod cycle.
1. Ước lượng yaw/pitch/roll từ landmark 2D/3D đã chọn bằng solvePnP hoặc phương pháp có kiểm chứng; ghi rõ quy ước dấu, camera flip.
2. Lấy baseline neutral pose theo phiên (có quality gate) và dùng delta so với baseline thay vì góc tuyệt đối.
3. Phát hiện head_drop khi delta pitch vượt HEAD_DROP_ANGLE đủ HEAD_DROP_TIME; thêm hysteresis, ngắt khi mất tracking.
4. Định nghĩa nod cycle downward → upward trong HEAD_NOD_MIN_TIME..MAX_TIME; đếm 3 chu kỳ trong 60s theo deque, không cộng mỗi frame.
5. Đánh giá roll HEAD_TILT_ANGLE / HEAD_TILT_TIME; yaw là tín hiệu mất tập trung kết hợp gaze chứ không mặc định là buồn ngủ.
**Tiêu chí nghiệm thu: **Pitch có dấu và độ lớn nhất quán trên bộ video gật/cúi thật; quay trái/phải không tạo nhầm cúi; event nod đếm đúng chu kỳ.
**Kiểm thử bắt buộc: **UT-POSE-01 baseline; UT-POSE-02 tilt; UT-POSE-03 3 nods/60s; IT-POSE-04 chuyển camera position.
> Phụ thuộc: M02; thiết kế baseline

## M06 — Gaze và phát hiện mất tập trung

**Ưu tiên: **P1  **| File liên quan: **config.py → gaze_detector.py, distraction_manager.py**  | Ước tính: **3–5 ngày công
**Mục tiêu / lỗi cần xử lý: **ENABLE_GAZE_DETECTION=True nhưng không tồn tại pipeline gaze.
1. Xác định điều kiện cần: khuôn mặt hợp lệ, mắt nhìn được, chất lượng iris/landmark đủ; nếu không thì UNKNOWN thay vì mất tập trung.
2. Xây vùng nhìn “forward/left/right/down” tương đối theo baseline chính diện, sử dụng hướng mắt + head yaw/pitch.
3. Dùng dwell GAZE_AWAY_TIME và GAZE_DOWN_TIME, chống jitter và bỏ sự kiện khi confidence thấp.
4. Chỉ gắn nhãn “nghi ngờ mất tập trung”, không suy ra “dùng điện thoại” khi chưa có detector/vật chứng.
5. Ghi distraction thành lớp sự kiện riêng có thể ảnh hưởng cảnh báo nhưng không nhập nhằng với điểm buồn ngủ.
**Tiêu chí nghiệm thu: **Nhìn xuống ngắn <2s không phát; nhìn xuống đủ ngưỡng phát một lần; mắt che/khuất không kết luận mất tập trung.
**Kiểm thử bắt buộc: **IT-GAZE-01 nhìn trái/phải; IT-GAZE-02 nhìn xuống; IT-GAZE-03 kính; IT-GAZE-04 nhìn gương 1s.
> Phụ thuộc: M02 + M05

## M07 — Risk score, decay, độ ưu tiên sự kiện

**Ưu tiên: **P0  **| File liên quan: **fatigue_manager.py → risk_manager.py, event_models.py**  | Ước tính: **2–3 ngày công
**Mục tiêu / lỗi cần xử lý: **Hiện logic update trực tiếp mỗi frame và có lệnh set score=100; không dùng SCORE_* và decay đầy đủ.
1. Tạo sự kiện immutable (id, type, start/end, confidence, source) từ detectors; RiskManager chỉ nhận event_confirmed, tránh điểm cộng hàng frame.
2. Lập bảng mapping điểm config cho từng loại; microsleep nguy cấp dùng safety_override có thời gian kết thúc riêng, thay vì score reset toàn bộ.
3. Áp dụng SCORE_DECAY_INTERVAL/SCORE_DECAY_AMOUNT khi dữ liệu hợp lệ và ổn định; không decay nếu camera/mặt mất hoặc vẫn có sự kiện nguy cấp.
4. Đảm bảo clamp điểm 0..100; lần sự kiện đã xử lý được đánh dấu idempotent; xử lý sự kiện đến trễ có kiểm soát.
5. Quản lý reason/current_events theo ưu tiên và thời gian; trạng thái status từ score và override, không phụ thuộc chuỗi violation_reason cũ.
**Tiêu chí nghiệm thu: **UT-04 chớp chậm cộng 10; 300s ổn định được decay theo cấu hình; sự kiện đang active vẫn giữ Danger; không double score một ID.
**Kiểm thử bắt buộc: **UT-RISK-01..08: additive/cap/floor/decay/idempotency/override/priority/missing-data.
> Phụ thuộc: M02–M05

## M08 — Cảnh báo âm thanh và chính sách nhắc lại

**Ưu tiên: **P0 + P1  **| File liên quan: **main.py, canhbao.py, create_sound.py → alert_manager.py, assets/audio/**  | Ước tính: **2–3 ngày công
**Mục tiêu / lỗi cần xử lý: **Báo động 10 giây rồi reset FatigueManager, khóa tiếp nhận hành vi khi còi đang phát.
1. Đưa cảnh báo sang AlertManager độc lập với nhận diện và risk; luôn tiếp tục xử lý dữ liệu khi đang phát âm thanh.
2. Khai báo cảnh báo theo level và loại sự kiện; riêng CAMERA_ERROR/NO_FACE dùng thông báo kỹ thuật khác ngủ gật.
3. WARNING_CONFIRM_TIME dùng cho cảnh báo thông thường; nguy cấp có thể vượt qua hold-time theo rule override.
4. WARNING_REPEAT_INTERVAL giới hạn nhắc âm thanh, không đóng hoặc xóa active incident; chỉ clear khi điều kiện thật sự hết.
5. Tách beep.wav tạo bằng wave và warning_vi.mp3 tạo bằng gTTS; giữ đúng đuôi/codec, xác thực tồn tại asset, fallback khi mixer lỗi.
**Tiêu chí nghiệm thu: **Âm thanh kết thúc không reset điểm; vẫn nhận hành vi trong lúc cảnh báo; các lỗi âm thanh không làm chương trình chính crash.
**Kiểm thử bắt buộc: **UT-ALERT-01 cooldown; UT-ALERT-02 sustained danger >10s; IT-ALERT-03 thiếu file; IT-ALERT-04 mất audio device.
> Phụ thuộc: M07

## M09 — Lưu bằng chứng, log và quyền riêng tư

**Ưu tiên: **P1  **| File liên quan: **main.py → evidence_store.py, event_logger.py**  | Ước tính: **2–3 ngày công
**Mục tiêu / lỗi cần xử lý: **Ảnh được lưu nhưng chưa có log sự kiện có cấu trúc, không kiểm tra kết quả ghi, tên có thể trùng trong cùng giây.
1. Đặt event_id UUID; file jpg theo event_id/time millis, ghi metadata JSONL hoặc SQLite gồm type/score/confidence/source/time/device/version.
2. Lưu ảnh đúng thời điểm event được xác nhận, có tùy chọn blur ngoài ROI, không lưu video thô nếu SAVE_RAW_VIDEO=False.
3. Kiểm tra cv2.imwrite trả True; nếu lỗi đĩa tạo error event riêng; không reset nguy cơ vì không thể lưu ảnh.
4. Có retention mặc định cần nhóm thống nhất; xóa theo lịch; hạn chế truy cập và không đẩy ảnh ra server nếu chưa có quyền.
5. Thiết kế evidence capture policy theo event_id để chống ảnh trùng trong cùng một event và hỗ trợ retry upload sau này.
**Tiêu chí nghiệm thu: **Mỗi event xác nhận có một hồ sơ truy xuất được; tên ảnh không trùng; lỗi hết dung lượng không làm chết camera loop.
**Kiểm thử bắt buộc: **UT-EVD-01 filename; UT-EVD-02 duplicate event; IT-EVD-03 disk full/permission; IT-EVD-04 privacy policy.
> Phụ thuộc: M07 + M08

## M10 — Quyết định vị trí của YOLO trong pipeline

**Ưu tiên: **P1  **| File liên quan: **main.py, train.py, config.py**  | Ước tính: **2–4 ngày công
**Mục tiêu / lỗi cần xử lý: **YOLO 3 class hiện chỉ dùng để vẽ, dù tiêu tốn tài nguyên GPU/CPU; dữ liệu YOLO và MediaPipe chưa fusion.
1. Thống nhất một trong hai chiến lược: (A) YOLO là nguồn chứng thực phụ event Yawn/Microsleep, có confidence + temporal agreement; (B) bỏ YOLO khỏi runtime để tối ưu, giữ model train làm nghiên cứu.
2. Nếu dùng A, chỉ nhận class Alert/Microsleep/Yawn với confidence threshold, điều kiện diện tích ROI và thời gian tồn tại; không cộng đôi cùng một sự kiện.
3. So sánh ablation: MediaPipe-only vs YOLO-only vs Fusion trên cùng tập test tách độc lập, lấy precision/recall/false alerts và FPS.
4. Cho phép cấu hình bật/tắt YOLO runtime; model không tải được phải có degraded mode rõ ràng hoặc dừng an toàn.
**Tiêu chí nghiệm thu: **Không còn “YOLO chỉ để trang trí” trừ khi được chủ động thiết kế display-only và nêu rõ; có benchmark tradeoff và quyết định lưu trong ADR.
**Kiểm thử bắt buộc: **BENCH-YOLO-01 latency; BENCH-YOLO-02 fusion error; BENCH-YOLO-03 missing weights.
> Phụ thuộc: M03, M04; có bộ test dữ liệu

## M11 — Dataset, huấn luyện và validation tin cậy

**Ưu tiên: **P1  **| File liên quan: **dataset, train.py → scripts/prepare_dataset.py, scripts/evaluate.py**  | Ước tính: **4–6 ngày công
**Mục tiêu / lỗi cần xử lý: **Ảnh ít, val/test nhỏ và có tên gốc trùng giữa các split; số mAP train hiện tại dễ bị hiểu nhầm.
1. Lập metadata bảng các ảnh: subject_id, session_id, source_video_id, class, lighting, camera_angle, glasses; rà 9 filename gốc trùng, kiểm tra cả near-duplicates.
2. Tách train/valid/test theo source/subject trước augmentation; khóa tập test và không tune ngưỡng trên test.
3. Bổ sung video camera chính diện trong các điều kiện khó: cười/nói/ngáp, kính, ánh sáng, nghiêng đầu, nhiều khuôn mặt, không thấy mặt.
4. Đánh giá ở event-level: TP, FP, FN, precision, recall, false-alert/hour, detection latency, uptime, FPS; báo khoảng tin cậy nếu đủ mẫu.
5. Lưu environment, seed, model hash, dataset version, confusion matrix và ngày đánh giá để so sánh trước/sau.
**Tiêu chí nghiệm thu: **Tập test độc lập, không có giao thoa người/video giữa split; báo cáo video replay ngoài train có bảng lỗi theo hành vi.
**Kiểm thử bắt buộc: **DATA-01 duplicate audit; DATA-02 held-out subjects; DATA-03 event-matching; DATA-04 failure categories.
> Phụ thuộc: Cần dữ liệu quay hợp lệ/đồng ý sử dụng

## M12 — Tối ưu hiệu năng, UI và đóng gói

**Ưu tiên: **P1 + P2  **| File liên quan: **main.py → ui_renderer.py; requirements.txt / pyproject.toml**  | Ước tính: **3–4 ngày công
**Mục tiêu / lỗi cần xử lý: **YOLO + MediaPipe chạy trên mỗi frame; không đo latency/FPS; thay đổi version dễ làm project không chạy.
1. Bổ sung FPS thực/latency p50,p95, queue backlog, %frame hợp lệ; phân biệt target FPS với measured FPS.
2. Benchmark độ phân giải 640×480 với bật/tắt YOLO; cân nhắc bỏ xử lý frame cũ, giảm tần suất YOLO, đảm bảo không phá thời gian event.
3. Giao diện hiển thị Normal/Tired/Warning/Danger, Tracking/No face/Camera error riêng, reason, confidence và FPS; tránh hiển thị thiếu tin cậy như kết luận chắc chắn.
4. Khóa phiên bản opencv-python, ultralytics, mediapipe, pygame, gTTS, numpy; thêm quickstart cho Windows, asset check trước start.
5. Thêm log runtime có rotation và fallback an toàn khi model/driver/mixer lỗi.
**Tiêu chí nghiệm thu: **Chạy start/stop lặp 20 lần không leak tài nguyên; benchmark trên máy demo đạt mục tiêu do nhóm phê duyệt (đề xuất tối thiểu 15 FPS đo thực khi bật pipeline cần thiết).
**Kiểm thử bắt buộc: **BENCH-PERF-01 p50/p95; IT-START-01 clean install; IT-START-02 model path; IT-STOP-01 20 restart.
> Phụ thuộc: Các module core ổn định

## M13 — Tự động kiểm thử và quản lý chất lượng

**Ưu tiên: **P0 + P1  **| File liên quan: **tests/; .github/workflows/ nếu dùng GitHub**  | Ước tính: **3–5 ngày công
**Mục tiêu / lỗi cần xử lý: **Chưa có test suite trong ZIP và chưa có công cụ bắt regression từ thay đổi ngưỡng.
1. Dùng pytest cho EyeDetector, YawnDetector, HeadEventDetector, RiskManager, AlertManager; inject clock monotonic giả thay monkeypatch time toàn cục.
2. Dựng replay runner nhận chuỗi (timestamp, features, valid_mask) trả event; tạo fixtures tình huống nhanh, thiếu mặt, boundary 1,5s/2s/3s/120s.
3. Tạo integration test với webcam giả/video lưu sẵn; assert event và reason chính xác mà không cần màn hình GUI.
4. Thêm kiểm tra `python -m compileall`, formatting/lint, unit tests vào CI; test không phụ thuộc mạng cho TTS/âm thanh.
5. Mỗi lỗi I-01..I-22 phải có linked test ID và bằng chứng PASS sau khi vá; test FAIL trước fix và PASS sau fix cho P0.
**Tiêu chí nghiệm thu: **Mọi bug P0 đều có regression test; bộ test chạy lại được bằng một lệnh; không biến mất hành vi đúng UT-03/UT-05 sau refactor.
**Kiểm thử bắt buộc: **CI-01 smoke; CI-02 regression; CI-03 replay; CI-04 result artifact.
> Phụ thuộc: Bắt đầu ngay, thực hiện song song các module

## M14 — Chuẩn bị tích hợp Backend DriveLinker (giai đoạn sau)

**Ưu tiên: **P2  **| File liên quan: **event_models.py → sync_queue.py, api_client.py**  | Ước tính: **3–5 ngày công
**Mục tiêu / lỗi cần xử lý: **Prototype chỉ lưu ảnh local, chưa tích hợp event API; đây là mở rộng scope, không phải bug P0 của module camera.
1. Chốt schema sự kiện có organization_id, device_id, driver_id (khi có xác thực), event_id, event_type, timestamp UTC, score, level, model/config_version, evidence_ref.
2. Không đưa mật khẩu/token vào log; token nằm trong secret store và áp dụng tenant isolation nếu hệ thống đa doanh nghiệp.
3. Tạo queue cục bộ có retry/backoff, idempotent event_id và khả năng offline để không mất sự kiện do mất mạng.
4. Định nghĩa POST sự kiện và upload bằng chứng sau khi backend có contract; phân quyền tổ chức, retention, khả năng audit; kiểm thử tải lại.
5. Tách hoàn toàn sự cố API khỏi cảnh báo tại xe: mất backend không được làm hỏng local AI safety loop.
**Tiêu chí nghiệm thu: **Mất mạng 5 phút vẫn ghi local và có thể đồng bộ lại không duplicate sau khi kết nối; không lộ dữ liệu giữa tenant.
**Kiểm thử bắt buộc: **IT-SYNC-01 offline/online; IT-SYNC-02 duplicate ID; SEC-SYNC-03 tenant/auth.
> Phụ thuộc: M09 + hợp đồng API Backend được thống nhất

## 8. Lộ trình triển khai và danh sách đầu ra

Ước lượng bên dưới là ngày công cho người đã biết Python/OpenCV, KHÔNG phải cam kết thời gian thực tế và có thể rút ngắn khi làm song song. Giai đoạn tích hợp BE làm sau khi đạt nghiệm thu camera chính diện.

| CHẶNG | TRỌNG TÂM | MÃ LỖI/ MODULE | SẢN PHẨM BÀN GIAO | CỬA KIỂM TRA |
|---|---|---|---|---|
| S0 – Baseline | Khóa ZIP, tạo branch, requirements, pytest skeleton | M13, I-18/I-21 | Issue board, môi trường chạy, test hiện trạng | Smoke + 8 tests logic tái hiện |
| S1 – Lõi an toàn | Camera/face validity/alert reset | M01,M02,M07,M08; I-01/I-06/I-10/I-11/I-12 | State machine, lỗi thiết bị và tài xế, alert manager | Mất face 10s ≠ mắt nhắm 10s; danger >10s không tự reset |
| S2 – Mắt & miệng | Đúng dwell, score, cooldown, PERCLOS | M03,M04; I-02/I-03/I-04/I-05/I-08 | Eye + Yawn detectors có unit tests | UT-EYE/UT-YAWN toàn bộ PASS |
| S3 – Đầu & gaze | Head pose baseline, nod, distraction | M05,M06; I-09/I-14/I-16 | Pose/Gaze modules + data validation | Test camera chính diện và khó nhất PASS |
| S4 – Dữ liệu & ổn định | YOLO role, benchmark, event logs, dataset split | M09,M10,M11,M12; I-13/I-15/I-17/I-19/I-20 | Benchmark report, test set độc lập, evidence store | Replay, false-alert/hour, FPS, restart |
| S5 – Demo & handover | Hồi quy, tài liệu, release tag | M13, I-21/I-22 | README mới, QA report, demo checklist | Toàn bộ P0 đóng; P1 có lý do rõ |
| S6 – BE (tuỳ phạm vi) | Contract và hàng đợi đồng bộ | M14 | API client + offline queue | Sự kiện không mất và không trùng |

### 8.1. Thứ tự commit/PR đề xuất (vá nhỏ, dễ review)

- PR-01: tests/baseline + dependency lock + compile + README chạy thử.
- PR-02: camera_service + monotonic time + try/finally + lỗi camera.
- PR-03: face_tracker validity + on_tracking_lost + no-face timeout.
- PR-04: eye_detector + slow blink score + microsleep + PERCLOS.
- PR-05: yawn_detector + min dwell + duplicate suppression + rolling window.
- PR-06: risk_manager event-based + decay + severity + no automatic reset.
- PR-07: alert_manager + âm thanh đúng format + retry/cooldown.
- PR-08: head_pose/head_nod + gaze + calibration.
- PR-09: evidence_store + JSONL + security + YOLO choice + benchmarks.
- PR-10: dataset split evaluation + full test run + release demo.

### 8.2. Bảng ưu tiên hành động ngay

| THỨ TỰ | VIỆC LÀM | VÌ SAO LÀM TRƯỚC |
|---|---|---|
| 01 | Thêm test I-01, I-02, I-03, I-04, I-06 | Khóa hành vi sai trước khi refactor |
| 02 | Sửa camera state / face validity / cleanup | Không cho dữ liệu cũ gây báo động giả |
| 03 | Sửa event mouth/eye và risk manager | Kết quả cảnh báo có căn cứ thời gian |
| 04 | Bỏ tự reset sau 10s, độc lập cảnh báo | Đảm bảo nguy hiểm liên tục không biến mất |
| 05 | Mở rộng head pose, PERCLOS, gaze | Hoàn thiện 4 nhóm nhận diện chính diện |
| 06 | Re-split dataset và benchmark | Chứng minh hiệu quả thay vì chỉ chạy được |

## 9. Bộ kiểm thử nghiệm thu và Definition of Done

### 9.1. Ma trận test theo nghiệp vụ

| ID | ĐẦU VÀO / KỊCH BẢN | KỲ VỌNG SAU VÁ |
|---|---|---|
| TC-01 | EAR dưới ngưỡng 0,08s | Bỏ nhiễu; không cộng điểm |
| TC-02 | Nhắm/mở 0,2s | 1 chớp thường; score giảm 5 nếu hợp lệ |
| TC-03 | Nhắm/mở 0,6s | 1 slow blink; score +10 đúng một lần |
| TC-04 | Mắt nhắm 1,5–2,1s, landmarks liên tục | Microsleep/severe đúng theo ngưỡng được duyệt |
| TC-05 | Nhắm 0,3s → mất mặt 10s → quay lại | Không được ghép thành 10,3s nhắm mắt |
| TC-06 | PERCLOS 24%, 25%, 40% với valid >=80% | Tách trạng thái đúng tại ranh giới |
| TC-07 | PERCLOS hợp lệ <80% thời lượng | Không phán đoán; thông báo dữ liệu không đủ |
| TC-08 | MAR 0,72 chỉ 0,1s | Không tạo yawn/không +40 |
| TC-09 | MAR 0,72 trong 1,5s | Xác nhận 1 light yawn, cộng 40 một lần |
| TC-10 | 3 lần há miệng 0,1s cách nhau ngắn | Không tạo repeated_yawn |
| TC-11 | 3 ngáp hợp lệ trong 120s | Đếm 3 event, chỉ cộng theo chính sách |
| TC-12 | MAR >0,85 liên tục >3s | Deep yawn đúng một lần; không cộng trùng light |
| TC-13 | Deep → light → deep đứt quãng | Không nối deep duration sai |
| TC-14 | Pitch cúi đủ 2s sau calibration | Head drop event đúng một lần |
| TC-15 | 3 chu kỳ gật 0,3–2s/60s | Head nod repeat event đúng |
| TC-16 | Head yaw >35° thoáng qua | Không tự động báo ngủ gật |
| TC-17 | Nhìn xuống >=2s + gaze hợp lệ | Distraction event; không khẳng định dùng điện thoại |
| TC-18 | Mắt bị che, không có gaze valid | UNKNOWN, không báo nhầm |
| TC-19 | Mất mặt >2s, vẫn có frame | NO_FACE riêng, không suy ra microsleep |
| TC-20 | cap.read() lỗi liên tục >3 giây thực | CAMERA_ERROR và an toàn khi dừng |
| TC-21 | Danger liên tục >10s khi âm thanh đã hết | Danger vẫn active / có nhắc lại phù hợp |
| TC-22 | Score 40, 300s trạng thái tỉnh táo, valid | Decays theo 10s / 3 điểm đến 0 (nếu không sự kiện mới) |
| TC-23 | Lặp lại cùng event_id nhiều lần | Điểm và evidence chỉ xử lý một lần |
| TC-24 | Disk full hoặc thư mục không ghi được | Lỗi lưu được log, camera tiếp tục/đóng an toàn |
| TC-25 | Không có asset âm thanh, sai model path | Lỗi dễ hiểu, fallback không crash thầm lặng |
| TC-26 | Chạy Q/ESC, mở/đóng GUI 20 vòng | Mọi resource release; không còn tiến trình treo |
| TC-27 | YOLO bật/tắt trên cùng tập video | Báo cáo latency + detection difference |
| TC-28 | Replay bộ video hold-out nhiều điều kiện | Báo precision/recall/false alerts/hour/latency/FPS |

### 9.2. Tiêu chí chấp nhận bản demo camera chính diện

- GATE A — Chức năng: mọi P0 I-01/I-02/I-03/I-04/I-06/I-09/I-10/I-11/I-12 đóng; TC-01..TC-05, TC-08..TC-13, TC-19..TC-23 đều PASS.
- GATE B — Tính an toàn: mất camera, mất mặt, mất âm thanh, lỗi ghi đĩa có biểu hiện riêng; không âm thầm kết luận ngủ gật từ dữ liệu không hợp lệ.
- GATE C — Đo lường: demo phải có video replay và báo tỷ lệ cảnh báo giả/giờ, phát hiện đúng, độ trễ và FPS trên máy thực tế. Các ngưỡng mục tiêu do nhóm duyệt trước khi test.
- GATE D — Tài liệu: README, dependencies, model path, sơ đồ nghiệp vụ, bảng ngưỡng và ví dụ log trùng khớp code; có ít nhất một báo cáo chạy test tự động.
- GATE E — Dữ liệu: dataset test độc lập theo nguồn/subject, không sử dụng ảnh augment cùng gốc để đánh giá tổng quát hóa.

### 9.3. Definition of Done cho từng vấn đề

- Có issue ID, mô tả lỗi và mức ưu tiên rõ ràng; có test FAIL trước khi sửa hoặc bằng chứng tái hiện.
- Có commit/PR liên kết issue, sửa tối thiểu và không làm hỏng các luồng khác.
- Có unit test, integration/replay test tương ứng với tình huống thực tế; CI chạy PASS.
- Có log/bằng chứng định lượng hoặc screenshot/video minh họa trước–sau trên máy demo.
- Cập nhật config/README khi thay threshold, tên file hoặc chính sách chấm điểm; reviewer xác nhận.
- Khi có thay đổi AI, lưu model hash/dataset version và báo lại metric trên cùng tập test đã khóa.

## 10. Rủi ro triển khai và các quyết định phải thống nhất

| QUYẾT ĐỊNH | KHUYẾN NGHỊ MẶC ĐỊNH | TÁC ĐỘNG |
|---|---|---|
| Mục tiêu demo | Ưu tiên mắt + ngáp + safety pipeline trước, tiếp đó pose và gaze | Giảm rủi ro demo fail |
| YOLO runtime | Bật/tắt cấu hình; không bắt buộc chạy nếu chưa chứng minh cải thiện | FPS/độ trễ rõ ràng |
| Ngưỡng EAR/MAR | Coi giá trị hiện có là thử nghiệm; baseline/calibration và dữ liệu mới quyết định | Giảm cảnh báo giả giữa cá nhân |
| Phát hiện mất mặt | NO_FACE, không tính là tài xế ngủ gật | Không nhầm chất lượng dữ liệu với hành vi |
| Thời gian/clock | monotonic cho đo khoảng thời gian, UTC ISO 8601 cho log | Không lỗi khi đồng hồ hệ thống nhảy |
| Nguy cơ và âm thanh | Alarm không reset risk; cooldown/nhắc lại độc lập | Không bỏ sót nguy cơ kéo dài |
| Quyền riêng tư | Chỉ lưu ảnh theo event, áp dụng retention, không mặc định lưu video | Giảm rò rỉ dữ liệu |
| Tích hợp DriveLinker BE | Đưa vào pha sau khi end-to-end tại xe PASS | Giảm scope creep |

Kết luận thực thi: không nên “vá” bằng cách tăng/giảm ngưỡng tùy cảm giác. Mỗi thay đổi nên đi theo chuỗi: test tái hiện → sửa state/event → replay → đo số liệu → nghiệm thu → cập nhật tài liệu.

# PHỤ LỤC A. CÁC CẤU HÌNH CHƯA ĐƯỢC THAM CHIẾU

Đối chiếu AST trong 7 file Python: 68 tên biến Config, trong đó 37 tên chưa xuất hiện dưới dạng Config.<tên> trong các file ngoài config.py. Danh sách là dấu hiệu chức năng chưa nối, không đồng nghĩa mọi biến đều bắt buộc sử dụng. Các biến sau cần được triển khai, xóa có chủ ý hoặc ghi “reserved” rõ lý do.

| NHÓM | BIẾN CHƯA DÙNG |
|---|---|
| Camera / face | FACE_MISSING_TIME |
| Eyes / PERCLOS | EAR_HALF_CLOSED, SEVERE_EYE_CLOSED_TIME, PERCLOS_WINDOW, PERCLOS_EYE_CLOSURE_RATIO, PERCLOS_WARNING, PERCLOS_DANGER, PERCLOS_MIN_VALID_RATIO |
| Yawn | LIGHT_YAWN_MIN_TIME, YAWN_EVENT_GAP, YAWN_SCORE_COOLDOWN |
| Head pose | HEAD_NOD_MIN_TIME, HEAD_NOD_MAX_TIME, HEAD_NOD_WINDOW, HEAD_NOD_REPEAT_WARNING, HEAD_TILT_ANGLE, HEAD_TILT_TIME |
| Gaze | GAZE_AWAY_TIME, GAZE_DOWN_TIME, HEAD_YAW_AWAY_ANGLE, DISTRACTION_REPEAT_WINDOW |
| Scoring | SCORE_DEEP_YAWN, SCORE_SLOW_BLINK, SCORE_REPEATED_YAWN, SCORE_HEAD_NOD, SCORE_HEAD_DROP, SCORE_DECAY_INTERVAL, SCORE_DECAY_AMOUNT |
| Alert | WARNING_CONFIRM_TIME, WARNING_REPEAT_INTERVAL |
| Safety | ALERT_ON_CAMERA_FAILURE, REQUIRE_VALID_FACE_FOR_SCORING, REQUIRE_VALID_EYES_FOR_PERCLOS, ENABLE_GAZE_DETECTION |
| Logging | ENABLE_LOGGING, LOG_EVENTS, SAVE_RAW_VIDEO |

# PHỤ LỤC B. CẤU TRÚC THƯ MỤC ĐỀ XUẤT

drivelinker_edge_ai/
  app/main.py                      # entrypoint, start/stop + wiring
  app/config.py                    # có schema, validation
  app/camera_service.py            # camera + timeout
  app/face_tracker.py              # ROI + validity
  app/features/eye.py              # EAR/PERCLOS
  app/features/mouth.py            # MAR/yawn
  app/features/head_pose.py        # pose/nods
  app/features/gaze.py             # hướng nhìn
  app/domain/events.py             # BehaviorEvent, states
  app/domain/risk_manager.py       # scoring + decay
  app/services/alert_manager.py    # âm thanh
  app/services/evidence_store.py   # ảnh + metadata
  app/services/event_logger.py     # log chuẩn
  app/services/sync_queue.py       # tuỳ chọn tích hợp BE
  app/ui_renderer.py               # giao diện
  assets/models/                  # best.pt, face_landmarker.task
  assets/audio/                   # beep.wav, warning_vi.mp3
  data/                           # sự kiện cục bộ (gitignore)
  scripts/                        # train, eval, dataset split
  tests/unit/  tests/integration/  tests/replay/
  requirements.txt / README.md / .gitignore

## Ví dụ schema sự kiện lưu cục bộ (gợi ý)

{
  "event_id": "uuid",
  "event_type": "MICROSLEEP_CONFIRMED",
  "detected_at_utc": "2026-10-17T14:30:00Z",
  "device_id": "demo_cam_01",
  "level": "DANGER",
  "score": 100,
  "duration_ms": 2100,
  "confidence": null,
  "data_quality": "VALID",
  "model_version": "to-be-versioned",
  "evidence_path": "data/evidence/<event_id>.jpg"
}
> Schema minh họa để thống nhất thiết kế; không phải endpoint API hay dữ liệu hiện đang tồn tại trong source.

# NGUỒN ĐỐI CHIẾU NỘI BỘ

- Code: main.py, config.py, fatigue_manager.py, utils.py, train.py, canhbao.py, create_sound.py trong test_yolo.zip.
- Đọc thêm: README.md; Drowsiness Detectin Using Yolov8.v1i.yolov8/data.yaml; runs/detect/train/results.csv; runs/detect/train/weights/best.pt và face_landmarker.task.
- Bằng chứng: năm ảnh trong bang_chung/; tám ca test logic được chạy với đồng hồ giả; kiểm tra 9 tên ảnh gốc xuất hiện ở từ hai split trở lên.
- Phạm vi chưa xác minh: webcam thật, microcontroller/edge device, tình huống đường thực, end-to-end Backend DriveLinker.