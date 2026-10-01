# DriveLinker Mini - Hệ Thống AI Cảnh Báo Ngủ Gật (YOLOv8)

Dự án này là một nguyên mẫu thử nghiệm (Mini Project) mô phỏng module Edge-AI của hệ thống **DriveLinker: Intelligent Rental Vehicle Management and Driver Monitoring System**. 

Hệ thống sử dụng camera kết hợp với mô hình học sâu **YOLOv8** để theo dõi khuôn mặt, phân tích các dấu hiệu mệt mỏi của tài xế và đưa ra cảnh báo âm thanh trực tiếp tại xe (Level 1 Alert)[cite: 1].

## 🌟 Cơ chế hoạt động & Logic thuật toán

- **Thuật toán "2 Chấm" (Xác định độ mở của mắt):** Ý tưởng cốt lõi của hệ thống dựa trên việc theo dõi khoảng cách mí mắt. AI sẽ xác định 1 chấm ở mí mắt trên và 1 chấm ở bọng mắt (mí dưới). Khi tài xế tỉnh táo, 2 chấm này giữ một khoảng cách nhất định. Khi 2 chấm này tiến lại gần sát nhau (khoảng cách tiến về 0) và giữ nguyên trạng thái trên 3 giây, hệ thống kết luận tài xế đang ngủ gật.
- **Hệ thống Điểm buồn ngủ (Drowsiness Score):** Thuật toán tính điểm động từ 0 đến 100 thay vì chỉ đánh giá Đúng/Sai[cite: 1]. Điểm số bị trừ đi hoặc cộng dồn dựa trên trạng thái nhắm mắt hoặc ngáp.
- **Phân loại 4 trạng thái:** Cập nhật tình trạng tài xế qua các mức: Bình thường (0-30), Mệt mỏi (31-60), Cảnh báo (61-80), và Nguy hiểm (81-100)[cite: 1].
- **Cảnh báo tức thời:** Tự động phát âm thanh báo động (Level 1 Audio Alert) khi điểm số chạm mức Nguy hiểm[cite: 1].

## 📂 Cấu trúc thư mục

```text
drivelinker_mini/
│
├── main.py                   # File code chính (chứa logic đo thời gian và tính điểm)
├── best.pt                   # File trọng số (weights) của YOLOv8 đã được huấn luyện
├── am_thanh_canh_bao.wav     # File âm thanh (.wav) dùng để phát báo động
└── README.md                 # Tài liệu hướng dẫn này