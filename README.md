# DriveLinker Mini - Hệ Thống AI Cảnh Báo Ngủ Gật (YOLOv8)

**Sinh viên thực hiện (SVTH):** Nguyễn Phạm Thiên Ân - Nguyễn Nhật Long - Nguyễn Minh Toàn

Dự án này là một nguyên mẫu thử nghiệm (Mini Project) mô phỏng module Edge-AI của hệ thống **DriveLinker: Intelligent Rental Vehicle Management and Driver Monitoring System**. 

Hệ thống sử dụng camera kết hợp với mô hình học sâu **YOLOv8** để theo dõi khuôn mặt, phân tích các dấu hiệu mệt mỏi của tài xế và đưa ra cảnh báo âm thanh trực tiếp tại xe (Level 1 Alert).

## 🌟 Cơ chế hoạt động & Logic thuật toán

- **Thuật toán "2 Chấm" (Xác định độ mở của mắt):** Ý tưởng cốt lõi của hệ thống dựa trên việc theo dõi khoảng cách mí mắt. AI sẽ xác định 1 chấm ở mí mắt trên và 1 chấm ở bọng mắt (mí dưới). Khi tài xế tỉnh táo, 2 chấm này giữ một khoảng cách nhất định. Khi 2 chấm này tiến lại gần sát nhau (khoảng cách tiến về 0) và giữ nguyên trạng thái trên 3 giây, hệ thống kết luận tài xế đang ngủ gật.
- **Hệ thống Điểm buồn ngủ (Drowsiness Score):** Thuật toán tính điểm động từ 0 đến 100 thay vì chỉ đánh giá Đúng/Sai. Điểm số bị trừ đi hoặc cộng dồn dựa trên trạng thái nhắm mắt hoặc ngáp.
- **Phân loại 4 trạng thái:** Cập nhật tình trạng tài xế qua các mức: Bình thường (0-30), Mệt mỏi (31-60), Cảnh báo (61-80), và Nguy hiểm (81-100).
- **Cảnh báo tức thời:** Tự động phát âm thanh báo động (Level 1 Audio Alert) khi điểm số chạm mức Nguy hiểm.

## 📂 Cấu trúc thư mục

```text
drivelinker_mini/
│
├── config.py                 # File cấu hình: Chứa các thông số, ngưỡng cảnh báo (EAR, MAR, góc gục đầu)
├── utils.py                  # Hộp công cụ: Chứa các hàm toán học tính toán tỷ lệ khuôn mặt
├── fatigue_manager.py        # Bộ não: Quản lý trạng thái, tính điểm và xác định lý do vi phạm
├── main.py                   # File chạy chính: Kết nối Camera, YOLO, MediaPipe và kết xuất UI
├── tao_am_thanh.py           # Script tự động tạo giọng nói cảnh báo bằng AI của Google
├── best.pt                   # File trọng số (weights) của YOLOv8 đã được huấn luyện
├── face_landmarker.task      # File mô hình MediaPipe dùng để lấy mốc khuôn mặt 3D
├── am_thanh_canh_bao.wav     # File âm thanh giọng nói cảnh báo (Được sinh tự động)
├── bang_chung/               # Thư mục lưu trữ hình ảnh vi phạm (Tự động tạo khi chạy)
└── README.md                 # Tài liệu hướng dẫn này

🚀 Hướng dẫn Cài đặt & Chạy dự án
Yêu cầu hệ thống (Prerequisites)
Python: Phiên bản từ 3.8 đến 3.11 (MediaPipe hoạt động ổn định nhất trên các phiên bản này).

Phần cứng: Máy tính có kết nối Webcam.

Bước 1: Chuẩn bị mã nguồn
Tải dự án về máy và mở terminal (Command Prompt / PowerShell / VS Code Terminal) tại thư mục drivelinker_mini.

Bước 2: Tạo môi trường ảo (Khuyến nghị)
Việc tạo môi trường ảo giúp các thư viện của dự án không bị xung đột với các phần mềm khác trên máy.

Trên Windows:

Bash
python -m venv venv
venv\Scripts\activate
Trên macOS/Linux:

Bash
python3 -m venv venv
source venv/bin/activate
Bước 3: Cài đặt các thư viện lõi (Core Dependencies)
Chạy lệnh sau để cài đặt các gói xử lý AI và hình ảnh:

Bash
pip install opencv-python ultralytics mediapipe pygame
Giải thích thư viện:

opencv-python: Xử lý hình ảnh, mở camera và kết xuất UI, lưu ảnh bằng chứng.

ultralytics: Framework chính thức để chạy mô hình YOLOv8.

mediapipe: Thư viện vẽ lưới khuôn mặt 3D và trích xuất tọa độ điểm chuẩn.

pygame: Phát âm thanh cảnh báo độc lập, không làm giật lag luồng xử lý camera.

Bước 4: Cấu hình Âm thanh cảnh báo (Giọng nói Google)
Hệ thống sử dụng giọng nói tiếng Việt của Google thay vì tiếng còi thông thường để tăng tính tương tác. Để sử dụng tính năng này, bạn cần cài thêm thư viện Text-to-Speech của Google.

Chạy lệnh cài đặt:

Bash
pip install gTTS
Mở file tao_am_thanh.py, bạn có thể tùy chỉnh lại nội dung câu nói ở biến van_ban theo ý muốn.

Chạy lệnh sau để hệ thống gọi API của Google và tải giọng nói về:

Bash
python tao_am_thanh.py
Sau khi chạy thành công, file am_thanh_canh_bao.wav sẽ xuất hiện trong thư mục.

Bước 5: Kiểm tra mô hình AI (Assets)
Đảm bảo bạn đã có đủ 2 file tài nguyên này nằm cùng thư mục với main.py:

best.pt: File mô hình của YOLOv8.

face_landmarker.task: File mô hình của MediaPipe.

Bước 6: Khởi chạy Hệ thống
Gõ lệnh sau vào Terminal để bắt đầu giám sát:

Bash
python main.py
Lưu ý: Ngay khi phát hiện điểm số vi phạm (Score = 100), hệ thống sẽ tự động tạo thư mục bang_chung/ và lưu lại hình ảnh khoảnh khắc vi phạm kèm theo thời gian và hành vi cụ thể (VD: NGAP_SAU_20261010_171411.jpg).

🛑 Phím tắt khi sử dụng
Khi camera đang bật, để tắt chương trình an toàn, hãy bấm phím q hoặc ESC trên bàn phím. Hệ thống sẽ tự động dọn dẹp bộ nhớ, ngắt camera và dừng âm thanh.
