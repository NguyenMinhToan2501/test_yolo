# BÁO CÁO KỸ THUẬT VÀ TỔNG HỢP HỆ THỐNG
## MODULE EDGE-AI NHẬN DIỆN VÀ CẢNH BÁO TÀI XẾ BUỒN NGỦ (DRIVELINKER MINI)

---

- **Dự án:** DriveLinker: Intelligent Rental Vehicle Management and Driver Monitoring System
- **Học phần:** Đồ án Capstone 1 (Capstone Project 1)
- **Sinh viên thực hiện (SVTH):** 
  - Nguyễn Phạm Thiên Ân
  - Nguyễn Nhật Long
  - Nguyễn Minh Toàn
- **Công nghệ cốt lõi:** Python, OpenCV, Ultralytics YOLOv8, Google MediaPipe Face Mesh (478 Landmarks), Pygame Audio Engine, Google Text-to-Speech (gTTS).
- **Trạng thái kiểm thử:** 15/15 bài kiểm thử tự động (Pytest) đạt tỉ lệ thành công 100%.

---

## MỤC LỤC
1. [GIỚI THIỆU TỔNG QUAN DỰ ÁN](#1-giới-thiệu-tổng-quan-dự-án)
2. [KIẾN TRÚC TOÀN DIỆN HỆ THỐNG (SYSTEM ARCHITECTURE)](#2-kiến-trúc-toàn-diện-hệ-thống-system-architecture)
3. [CHI TIẾT MÔ HÌNH HỌC SÂU (DEEP LEARNING MODELS)](#3-chi-tiết-mô-hình-học-sâu-deep-learning-models)
   - 3.1. Mô hình nhận diện đối tượng YOLOv8n (Custom Trained)
   - 3.2. Mô hình mốc khuôn mặt 3D Google MediaPipe Face Landmarker
4. [CÔNG THỨC TOÁN HỌC & CHỈ SỐ SINH TRẮC HỌC (BIOMETRIC METRICS)](#4-công-thức-toán-học--chỉ-số-sinh-trắc-học-biometric-metrics)
   - 4.1. Tỷ lệ mở mắt - Eye Aspect Ratio (EAR)
   - 4.2. Tỷ lệ há miệng - Mouth Aspect Ratio (MAR)
   - 4.3. Góc cúi đầu - Head Pitch Angle
5. [CƠ CHẾ ĐÁNH GIÁ HÀNH VI & MA TRẬN CẢNH BÁO (STATE MACHINE & ALERT MATRIX)](#5-cơ-chế-đánh-giá-hành-vi--ma-trận-cảnh-báo-state-machine--alert-matrix)
   - 5.1. Bảng quy tắc nhận diện hành vi vi phạm
   - 5.2. Hệ thống chấm điểm buồn ngủ (Drowsiness Score: 0 - 100)
   - 5.3. Quy tắc tích lũy: 5 Cảnh báo Vàng nâng cấp 1 Cảnh báo Đỏ (Phát giọng nói cảnh báo)
   - 5.4. Cơ chế giải tỏa báo động tức thì (Instant Recovery)
6. [HỆ THỐNG PHẢN HỒI, CHẤP PHÁP VÀ LƯU TRỮ BẰNG CHỨNG](#6-hệ-thống-phản-hồi-chấp-pháp-và-lưu-trữ-bằng-chứng)
   - 6.1. Cảnh báo âm thanh đa tầng (Multi-tier Audio Alerts & AI Voices)
   - 6.2. Chụp ảnh lưu bằng chứng vi phạm (Evidence Capture)
   - 6.3. Hệ thống lưu trữ nhật ký kép (JSON & TXT Logging)
7. [KẾT QUẢ THỰC NGHIỆM VÀ KIỂM THỬ HỆ THỐNG (TESTING & VALIDATION)](#7-kết-quả-thực-nghiệm-và-kiểm-thử-hệ-thống-testing--validation)
8. [ĐÁNH GIÁ ƯU ĐIỂM, HẠN CHẾ VÀ ĐỊNH HƯỚNG MỞ RỘNG (GÓC NGHIÊNG 45°)](#8-đánh-giá-ưu-điểm-hạn-chế-và-định-hướng-mở-rộng-góc-nghiêng-45)

---

## 1. GIỚI THIỆU TỔNG QUAN DỰ ÁN

Module **DriveLinker Mini** là thành phần biên (Edge-AI) cốt lõi trong giải pháp giám sát hành vi người lái xe thuộc đề tài Capstone **DriveLinker**. Mục tiêu chính của hệ thống là hoạt động theo thời gian thực (Real-time $\ge 30\text{ FPS}$) trên thiết bị gắn trên cabin ô tô, liên tục phân tích cử chỉ sinh trắc học của tài xế để:
- Phát hiện sớm các trạng thái mệt mỏi tiềm ẩn (ngáp sâu kéo dài $\ge 3\text{s}$, chớp mắt chậm lờ đờ $\ge 0.32\text{s}$).
- Cảnh báo khẩn cấp các tình huống nguy hiểm cao độ (ngủ gật $\ge 1.5\text{s}$, gục đầu nhắm mắt $\ge 0.7\text{s}$).
- Cảnh báo giọng nói nhắc nhở giữ tỉnh táo khi tài xế tích lũy 5 lần cảnh báo vàng trong vòng 10 phút: *"Cảnh báo! Tài xế có dấu hiệu buồn ngủ, vui lòng giữ tỉnh táo!"*.
- Cảnh báo người lái bằng giọng nói tiếng Việt khi khuôn mặt bị che khuất hoặc quay mặt khỏi góc quan sát của camera $\ge 2.0\text{s}$.
- Tự động chụp và lưu lại hình ảnh vi phạm cùng nhật ký làm dữ liệu chứng thực cho trung tâm điều hành.

```
+-----------------------------------------------------------------------------------------+
|                                    DRIVELINKER EDGE-AI                                  |
|                                                                                         |
|   [Camera Feed 30 FPS]                                                                  |
|            |                                                                            |
|            +---> [YOLOv8n Object Detector] ---> Bounding Box & Phân loại sơ bộ          |
|            |                                                                            |
|            +---> [MediaPipe 3D Mesh]       ---> 478 Facial Landmarks (x, y, z)          |
|                        |                                                                |
|                        v                                                                |
|             [utils.py Biometrics]          ---> EAR (Mắt), MAR (Miệng), Pitch (Góc đầu) |
|                        |                                                                |
|                        v                                                                |
|        [fatigue_manager.py Logic Engine]   ---> Điểm 0-100, Trạng thái (Vàng/Đỏ)       |
|                        |                                                                |
|       +----------------+----------------+----------------+                              |
|       |                                 |                |                              |
|       v                                 v                v                              |
| [Pygame Còi/Giọng nói AI]    [Ảnh bằng chứng .jpg]   [Log JSON/TXT]                     |
+-----------------------------------------------------------------------------------------+
```

---

## 2. KIẾN TRÚC TOÀN DIỆN HỆ THỐNG (SYSTEM ARCHITECTURE)

Hệ thống được thiết kế theo mô hình phân tầng mô-đun hóa cao (Modular Architecture), tách bạch rõ ràng giữa xử lý hình ảnh, tính toán số học, quản lý trạng thái và chấp pháp:

| Tên File | Vai Trò Kiến Trúc | Chức Năng Chi Tiết |
| :--- | :--- | :--- |
| [`config.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/config.py) | **Bảng điều khiển trung tâm (Configuration)** | Quản lý toàn bộ thông số: ngưỡng EAR mắt nhắm (0.25), MAR ngáp (0.70), góc gục đầu (15°), thời gian kích hoạt ngủ gật (1.5s), gục đầu nhắm mắt (0.7s), số cảnh báo vàng (5 lần/10p), file giọng nói cảnh báo (`canh_bao_buon_ngu.mp3`), độ phân giải camera, v.v. |
| [`utils.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/utils.py) | **Hộp công cụ sinh trắc học (Biometrics Toolkit)** | Tính toán thuần túy hình học không lưu trạng thái: khoảng cách Euclid, tính tỷ lệ mở mắt từng bên (EAR), độ há miệng (MAR), góc nghiêng chúi đầu (Pitch Angle). |
| [`fatigue_manager.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/fatigue_manager.py) | **Bộ não điều phối trạng thái (State Machine & Logic)** | Theo dõi chuỗi thời gian (Time-series), đo thời lượng nhắm mắt, lọc nhiễu ngáp, quản lý điểm số buồn ngủ (0 - 100), cờ cảnh báo đỏ do 5 vàng (`is_yellow_red_alert`), quyết định mức độ cảnh báo (Normal, Tired, Warning, Danger). |
| [`canhbao.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/canhbao.py) | **Trình ghi nhận & Phân tích nhật ký (Warning Logger)** | Quản lý cửa sổ trượt 10 phút (`600s`), đếm cảnh báo vàng, xử lý nâng cấp lên cảnh báo đỏ, ghi nhật ký đồng thời ra file JSON có cấu trúc và file TXT nhật trình trực quan. |
| [`tao_am_thanh_buon_ngu.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/tao_am_thanh_buon_ngu.py) | **Bộ tạo giọng nói tiếng Việt AI (Voice Generator)** | Sử dụng Google Text-to-Speech (gTTS) tổng hợp câu thoại cảnh báo buồn ngủ khi đạt 5 cảnh báo vàng: *"Cảnh báo! Tài xế có dấu hiệu buồn ngủ, vui lòng giữ tỉnh táo!"*. |
| [`main.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/main.py) | **Vòng lặp thực thi chính (Main Pipeline & UI)** | Khởi tạo Camera, nạp mô hình AI, điều phối luồng dữ liệu 30 FPS, hiển thị giao diện giám sát HUD (Heads-Up Display), kích hoạt âm thanh Pygame (còi hú hoặc giọng nói AI tương ứng) và lưu ảnh vi phạm. |
| [`tests/test_business_logic.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/tests/test_business_logic.py) | **Bộ kiểm chuẩn tự động (Regression Test Suite)** | 15 kịch bản kiểm thử tự động hóa toàn bộ logic nghiệp vụ khắt khe, bảo đảm hệ thống hoạt động ổn định và chính xác 100%. |

---

## 3. CHI TIẾT MÔ HÌNH HỌC SÂU (DEEP LEARNING MODELS)

Hệ thống triển khai kết hợp song song **Dual-AI Engine**:

### 3.1. Mô hình nhận diện đối tượng YOLOv8n (Custom Trained)
- **Kiến trúc:** YOLOv8 Nano (Ultralytics) - tối ưu cho các thiết bị nhúng và máy tính biên nhờ tốc độ suy luận cực nhanh.
- **Tập dữ liệu huấn luyện:** Dataset `Drowsiness Detectin Using Yolov8.v1i.yolov8` (Roboflow Universe - Giấy phép CC BY 4.0).
- **Cấu hình huấn luyện:** 50 Epochs, Kích thước ảnh đầu vào $640 \times 640$, Batch size 16.
- **Tập nhãn nhận diện (3 Classes):**
  1. `Alert`: Tài xế tỉnh táo, mắt mở bình thường.
  2. `Microsleep`: Trạng thái chợp mắt / nhắm mắt ngủ gật.
  3. `Yawn`: Trạng thái há miệng ngáp.
- **Chỉ số đánh giá định lượng (Validation Results tại Epoch 50):**
  - **Độ chính xác (Precision):** **$90.00\%$**
  - **Độ phủ (Recall):** **$99.76\%$**
  - **mAP@0.50:** **$99.50\%$**
  - **mAP@0.50:0.95:** **$76.35\%$**

### 3.2. Mô hình mốc khuôn mặt 3D Google MediaPipe Face Landmarker
- **File tài nguyên:** `face_landmarker.task`.
- **Khả năng:** Dự đoán thời gian thực **478 điểm mốc (landmarks)** chuẩn hóa trên khuôn mặt người trong không gian 3 chiều $(x, y, z)$.
- **Ưu điểm:** Khả năng nội suy tọa độ 3D sâu ($z$-axis) giúp đo đạc khoảng cách vật lý của mí mắt và khóe miệng với độ phân giải cao, không phụ thuộc vào ánh sáng hay kích thước khuôn mặt của từng tài xế.

---

## 4. CÔNG THỨC TOÁN HỌC & CHỈ SỐ SINH TRẮC HỌC (BIOMETRIC METRICS)

Toàn bộ các quyết định cảnh báo đều dựa trên các công thức sinh trắc học đã được chuẩn hóa trong khoa học giao thông:

### 4.1. Tỷ lệ mở mắt - Eye Aspect Ratio (EAR)
Hệ thống lấy 6 điểm mốc cho mỗi mắt từ MediaPipe Mesh:
- **Mắt trái:** Khóe mắt (33, 133); mí mắt trên (159, 158); mí mắt dưới (145, 153).
- **Mắt phải:** Khóe mắt (362, 263); mí mắt trên (386, 385); mí mắt dưới (374, 380).

Công thức tính tỷ lệ cho mắt trái:
$$\text{EAR}_{\text{left}} = \frac{\text{dist}(p_{159}, p_{145}) + \text{dist}(p_{158}, p_{153})}{2 \times \text{dist}(p_{33}, p_{133})}$$

Tương tự cho mắt phải:
$$\text{EAR}_{\text{right}} = \frac{\text{dist}(p_{386}, p_{374}) + \text{dist}(p_{385}, p_{380})}{2 \times \text{dist}(p_{362}, p_{263})}$$

$$\text{EAR}_{\text{avg}} = \frac{\text{EAR}_{\text{left}} + \text{EAR}_{\text{right}}}{2}$$

> **Quy tắc an toàn chống báo giả:** Mắt chỉ được xác nhận là đang nhắm khi **CẢ HAI MẮT** đồng thời có $\text{EAR} < \text{EAR\_CLOSED} = 0.25$. Nếu tài xế nháy 1 mắt (1 bên mở, 1 bên nhắm), hệ thống tuyệt đối không báo ngủ gật.

### 4.2. Tỷ lệ há miệng - Mouth Aspect Ratio (MAR)
Hệ thống sử dụng khoảng cách giữa hai khóe miệng (điểm 78 và 308) làm chuẩn chiều ngang, và khoảng cách giữa điểm giữa môi trên (điểm 13) và môi dưới (điểm 14) làm chiều dọc:
$$\text{MAR} = \frac{\text{dist}(p_{13}, p_{14})}{\text{dist}(p_{78}, p_{308})}$$

- Khi ngậm miệng: $\text{MAR} \approx 0.10 - 0.25$.
- Khi nói chuyện: $\text{MAR} \approx 0.30 - 0.55$.
- Khi ngáp sâu: $\text{MAR} \ge 0.70$.

### 4.3. Góc cúi đầu - Head Pitch Angle
Sử dụng điểm đỉnh trán ($p_{10}$) và điểm cằm ($p_{152}$) trong không gian tọa độ dọc ($y$) và chiều sâu ($z$):
$$\Delta y = p_{152}.y - p_{10}.y, \quad \Delta z = p_{152}.z - p_{10}.z$$
$$\text{Pitch Angle} = \text{degrees}\left(\text{atan2}(\Delta z, \Delta y)\right)$$

Khi đầu tài xế chúi về phía trước vượt quá $15.0^\circ$ (`HEAD_DROP_ANGLE = 15.0`), hệ thống nhận diện hành vi gục đầu.

---

## 5. CƠ CHẾ ĐÁNH GIÁ HÀNH VI & MA TRẬN CẢNH BÁO

### 5.1. Bảng quy tắc nhận diện hành vi vi phạm

| STT | Hành vi nhận diện | Điều kiện kỹ thuật kích hoạt | Điểm số | Trạng thái hiển thị | Phản ứng của hệ thống |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Chớp mắt sinh lý** | Mắt nhắm từ $0.08\text{s} \le t \le 0.30\text{s}$ | **0đ** | `Normal` | Đánh giá tỉnh táo bình thường; trừ điểm phạt về 0đ. |
| **2** | **Nháy 1 mắt (Anti-Winking)** | 1 mắt $\text{EAR} < 0.25$, mắt còn lại $\ge 0.25$ | **0đ** | `Normal` | Bỏ qua, chống báo nhầm ngủ gật khi tài xế nheo mắt/nháy mắt. |
| **3** | **Đang nhắm mắt (Real-time)** | Cả 2 mắt $\text{EAR} < 0.25$ dưới $1.5\text{s}$ | Tăng theo thời gian | `NHAM MAT (x.xs)` | Đếm giây liên tục từng $0.1\text{s}$ trên màn hình HUD. |
| **4** | **Chớp mắt chậm (Slow Blink)** | Mắt nhắm kéo dài $0.32\text{s} \le t < 1.50\text{s}$ | **60đ** | `CHOP MAT CHAM` (Warning) | **Cảnh báo Vàng**; giữ hiển thị 2s; ghi nhận log; **KHÔNG hú còi**. |
| **5** | **Ngủ gật (Microsleep)** | Cả 2 mắt nhắm liên tục $\ge 1.50\text{s}$ | **100đ** | `NGU GAT (x.xs)` (Danger) | **CẢNH BÁO ĐỎ**; **Hú còi khẩn cấp**; Chụp ảnh lưu `bang_chung/`; ghi log Đỏ. |
| **6** | **Đang há miệng (Lọc nhiễu)** | Miệng mở $\text{MAR} \ge 0.70$ dưới $3.0\text{s}$ | **0đ** | `DANG NGAP (x.xs)` | Chưa phạt điểm để tránh bắt nhầm khi nói chuyện hoặc hát. |
| **7** | **Ngáp sâu (Deep Yawn)** | Miệng mở $\text{MAR} \ge 0.70$ liên tục $\ge 3.0\text{s}$ | **60đ** | `NGAP SAU (x.xs)` (Warning) | **Cảnh báo Vàng**; ghi nhận log theo dõi; **KHÔNG hú còi**. |
| **8** | **Cúi đầu mắt mở** | Góc $\text{Pitch} > 15^\circ$ nhưng mắt vẫn mở | $\le 30\text{đ}$ | `CUI DAU - MAT MO` | Chỉ nhắc nhở trạng thái; **KHÔNG phát cảnh báo**. |
| **9** | **Gục đầu nhắm mắt** | Góc $\text{Pitch} > 15^\circ$ VÀ nhắm mắt $\ge \mathbf{0.70s}$ | **100đ** | `GUC DAU (NHAM MAT)` (Danger) | **CẢNH BÁO ĐỎ TỨC THÌ**; **Hú còi khẩn cấp**; Chụp ảnh lưu `bang_chung/`; ghi log Đỏ. |
| **10** | **Tích lũy mệt mỏi (5 Vàng)** | Đạt **5 lần Cảnh báo Vàng** trong 10 phút | **100đ** | `CANH BAO DO (5 VANG)` (Danger) | **NÂNG CẤP CẢNH BÁO ĐỎ**; **Đọc thông báo giọng nói AI: "Cảnh báo! Tài xế có dấu hiệu buồn ngủ, vui lòng giữ tỉnh táo!"**; Chụp ảnh; **Reset bộ đếm Vàng về 0**. |
| **11** | **Mất dấu khuôn mặt** | Không thấy khuôn mặt liên tục $\ge 2.0\text{s}$ | - | `KHONG THAY KHUON MAT!` | Phát cảnh báo giọng nói tiếng Việt tốc độ 1.5x lặp lại mỗi 4.5s; ngắt ngay bộ đếm nhắm mắt/ngáp. |
| **12** | **Lỗi Camera** | Mất tín hiệu hình ảnh $\ge 3.0\text{s}$ | - | Báo lỗi phần cứng | Dừng vòng lặp; giải phóng camera và tài nguyên hệ thống an toàn. |

### 5.2. Hệ thống chấm điểm buồn ngủ (Drowsiness Score)
Điểm số được tính toán động trong khoảng $[0, 100]$:
- **Mức 1 - Tỉnh táo (`Normal`):** $0 \le \text{Score} < 30$ (Hiển thị chữ màu Xanh lá).
- **Mức 2 - Mệt mỏi nhẹ (`Tired`):** $30 \le \text{Score} < 60$ (Hiển thị chữ màu Vàng nhạt).
- **Mức 3 - Cảnh báo Vàng (`Warning`):** $60 \le \text{Score} < 85$ (Hiển thị chữ màu Vàng đậm - **Tuyệt đối không hú còi**).
- **Mức 4 - Cảnh báo Đỏ / Nguy hiểm (`Danger`):** $\text{Score} \ge 85$ hoặc xuất hiện nguy cơ trực tiếp (Ngủ gật $\ge 1.5\text{s}$, Gục đầu nhắm mắt $\ge 0.7\text{s}$, Đạt 5 cảnh báo vàng) $\rightarrow$ **Kích hoạt âm thanh báo động**.

### 5.3. Quy tắc tích lũy: 5 Cảnh báo Vàng nâng cấp 1 Cảnh báo Đỏ
- Các hành vi như **Chớp mắt chậm** (`60đ`) và **Ngáp sâu $\ge 3\text{s}$** (`60đ`) là dấu hiệu của sự mệt mỏi tích lũy.
- Lớp `WarningLogger` trong [`canhbao.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/canhbao.py) duy trì một cửa sổ trượt $600\text{s}$ (10 phút).
- Khi phát hiện lần cảnh báo vàng thứ 5 trong vòng 10 phút:
  1. Kích hoạt chuyển đổi ngay lập tức sang **Cảnh báo Đỏ** (`Score = 100`, `State = Danger`, cờ `is_yellow_red_alert = True`).
  2. Hệ thống phát âm thanh giọng nói tiếng Việt: **"Cảnh báo! Tài xế có dấu hiệu buồn ngủ, vui lòng giữ tỉnh táo!"** (`canh_bao_buon_ngu.mp3`).
  3. Chụp ảnh lưu bằng chứng `CANH_BAO_DO_DAT_5_LAN_VANG`.
  4. Đánh dấu các bản ghi vàng trước đó là `consumed` và **Reset biến đếm cảnh báo vàng về 0**.

### 5.4. Cơ chế giải tỏa báo động tức thì (Instant Recovery)
- Hệ thống không gây phiền toái cho tài xế bằng việc kéo dài tiếng còi.
- Ngay khi tài xế có hành vi phục hồi: **Mở mắt**, **Ngậm miệng lại** hoặc **Ngẩng đầu lên**:
  - Còi báo động được tắt ngay lập tức (độ trễ đệm buffer $0.2\text{s}$ để chống chập chờn).
  - Điểm số lập tức được đưa thẳng về **$0\text{ điểm}$** (`Score = 0`).

---

## 6. HỆ THỐNG PHẢN HỒI, CHẤP PHÁP VÀ LƯU TRỮ BẰNG CHỨNG

### 6.1. Cảnh báo âm thanh đa tầng (Multi-tier Audio Alerts & AI Voices)
- Tích hợp qua thư viện `pygame.mixer` chạy nền đa luồng (Multi-threaded), không gây nghẽn tốc độ xử lý của camera:
  - **Cảnh báo Nguy cấp trực tiếp (Ngủ gật $\ge 1.5\text{s}$ hoặc Gục đầu nhắm mắt $\ge 0.7\text{s}$):** Phát liên tục tiếng còi báo động `am_thanh_canh_bao.wav` (`play(-1)`) cho đến khi tài xế tỉnh táo mở mắt/ngẩng đầu hoặc hết thời gian tối đa mỗi đợt ($3.0\text{s}$).
  - **Cảnh báo tích lũy 5 lần vàng:** Phát lời thoại giọng nói tiếng Việt rõ ràng, lịch sự: *"Cảnh báo! Tài xế có dấu hiệu buồn ngủ, vui lòng giữ tỉnh táo!"* (`canh_bao_buon_ngu.mp3`).
  - **Cảnh báo mất tập trung / mất mặt:** Phát lời thoại tiếng Việt tốc độ $1.5\times$: *"Camera không thấy khuôn mặt! Camera không thấy khuôn mặt!"* (`canh_bao_mat_mat.mp3`).

### 6.2. Chụp ảnh lưu bằng chứng vi phạm (Evidence Capture)
- Khi phát hiện vi phạm mức Đỏ, hệ thống tự động trích xuất khung hình từ `display_frame`.
- Vẽ đè thông tin giám sát pháp lý lên ảnh:
  - Dòng vi phạm: `VI PHAM: <Tên lỗi> - <Ngày giờ thực tế>`
  - Lưu tại thư mục: `bang_chung/{TEN_LOI}_{YYYYMMDD_HHMMSS}.jpg`
- **Bộ lọc chống lưu ảnh trùng lặp:** Giới hạn tối thiểu $10.0\text{s}$ giữa các lần chụp cho cùng một loại vi phạm để tối ưu hóa bộ nhớ đĩa cứng.

### 6.3. Hệ thống lưu trữ nhật ký kép (JSON & TXT Logging)
- **File JSON (`canh_bao_log.json`):** Lưu trữ dạng dữ liệu có cấu trúc phục vụ việc tích hợp API, đồng bộ hóa lên máy chủ đám mây Cloud của DriveLinker:
  ```json
  {
    "timestamp": 1730419520.123,
    "datetime": "31/10/2026 21:05:20",
    "type": "RED",
    "score": 100,
    "reason": "CANH BAO DO (DAT 5 LAN VANG/10P)",
    "consumed": false
  }
  ```
- **File văn bản nhật trình (`canh_bao_log.txt`):** Nhật trình trực quan cho người quản trị đọc trực tiếp:
  ```text
  [06/11/2026 21:05:20] [CANH BAO DO] Diem: 100/100 | Ly do: CANH BAO DO (DAT 5 LAN VANG/10P)
  [06/11/2026 21:05:20] [HE THONG] Đạt 5 mức cảnh báo vàng -> Nâng cấp CẢNH BÁO ĐỎ và RESET biến đếm về 0.
  ```

---

## 7. KẾT QUẢ THỰC NGHIỆM VÀ KIỂM THỬ HỆ THỐNG (TESTING & VALIDATION)

Bộ kiểm thử hồi quy tự động trong [`tests/test_business_logic.py`](file:///d:/To%C3%A0n/captone1/TEST_YOLO/tests/test_business_logic.py) đã thực hiện kiểm chứng toàn bộ 15 kịch bản then chốt:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.x, pytest-9.0.3, pluggy-1.6.0
rootdir: D:\Toàn\captone1\TEST_YOLO
collected 15 items

tests\test_business_logic.py ...............                             [100%]

============================= 15 passed in 0.14s ==============================
```

### Danh sách 15 ca kiểm thử đã được xác minh thành công 100%:
1. `test_yawn_filtered_when_under_3s`: Há miệng dưới 3 giây không bị tính điểm phạt, chỉ hiển thị `DANG NGAP`.
2. `test_deep_yawn_confirmed_at_3s_calculates_60_points`: Ngáp sâu đủ 3 giây được tính 60 điểm (Cảnh báo Vàng).
3. `test_yellow_warning_does_not_play_sound`: Cảnh báo Vàng tuyệt đối không phát âm thanh làm phiền tài xế.
4. `test_slow_blink_calculates_60_points_and_is_yellow_warning`: Chớp mắt chậm tính đúng 60 điểm và ghi nhận vào log.
5. `test_yawn_mouth_close_resets_immediately_to_zero`: Ngậm miệng lại sau khi ngáp ngay lập tức giải tỏa về 0 điểm.
6. `test_normal_blink_resets_to_zero_when_alert`: Chớp mắt bình thường lập tức trừ điểm về 0.
7. `test_opening_eyes_dismisses_emergency_and_resets_to_zero`: Mở mắt sau khi ngủ gật ngắt ngay báo động và reset về 0 điểm.
8. `test_head_up_resets_immediately_to_zero`: Ngẩng đầu dậy đưa điểm số về 0 điểm.
9. `test_score_resets_to_zero_when_awake_decay`: Cơ chế tự phục hồi đưa điểm về 0 khi tài xế tỉnh táo.
10. `test_winking_one_eye_does_not_trigger_microsleep`: Nháy 1 mắt (1 mở, 1 nhắm) không bị nhận nhầm thành ngủ gật.
11. `test_head_down_with_eyes_open_only_reason_no_alert`: Cúi đầu mà mắt vẫn mở thì chỉ hiện trạng thái, không cảnh báo nguy hiểm.
12. `test_head_down_with_eyes_closed_triggers_danger_alert`: Cúi đầu nhắm mắt đạt 0.7s kích hoạt ngay Cảnh báo Đỏ (100đ, hú còi).
13. `test_face_lost_does_not_accumulate_into_sleep`: Mất dấu mặt không bị tính dồn thành nhắm mắt ngủ gật.
14. `test_5_yellow_warnings_triggers_red_alert_and_resets_counter`: Đạt 5 lần Cảnh báo Vàng nâng cấp thành Cảnh báo Đỏ, kích hoạt cờ giọng nói và tự động reset biến đếm về 0.
15. `test_slow_blink_holds_warning_and_normal_blink_clears`: Chớp mắt chậm giữ hiển thị 2s, nếu chớp mắt bình thường sẽ xóa ngay lập tức.

---

## 8. ĐÁNH GIÁ ƯU ĐIỂM, HẠN CHẾ VÀ ĐỊNH HƯỚNG MỞ RỘNG (GÓC NGHIÊNG 45°)

### 8.1. Các ưu điểm nổi bật
- **Tốc độ xử lý cao:** Đạt 30 FPS ổn định trên phần cứng thông thường không cần GPU rời đắt tiền.
- **Tính thực tiễn cao:** Bắt được cả giai đoạn sớm thông qua cơ chế tích lũy 5 cảnh báo vàng (ngáp, chớp mắt chậm) và cảnh báo bằng giọng nói thông minh trước khi tài xế ngủ gật sâu.
- **Trải nghiệm lái xe thân thiện:** Tự động tắt còi ngay khi tài xế phản ứng mở mắt/ngậm miệng, không gây ức chế tâm lý khi lái xe.

### 8.2. Phân tích hiện trạng góc nhận diện & Giải pháp mở rộng góc nghiêng 45°
- **Hiện trạng:** Hệ thống đang hoạt động tối ưu nhất ở góc camera chính diện ($0^\circ - 15^\circ$). Khi tài xế quay mặt nghiêng $45^\circ$ (hoặc camera lắp lệch trên cột chữ A/taplo), độ chính xác bị suy giảm do:
  - Mắt phía xa bị sống mũi che khuất một phần.
  - Phép chiếu hình phẳng 2D làm co hẹp chiều ngang của mắt và miệng, khiến chỉ số EAR/MAR tính toán bị sai lệch.
- **Lộ trình nâng cấp mở rộng góc nghiêng 45° (Khuyến nghị cho giai đoạn Capstone 2):**
  1. **Chuyển đổi sang khoảng cách Euclid 3D:** Sử dụng đầy đủ tọa độ chiều sâu $z$ của MediaPipe $\sqrt{\Delta x^2 + \Delta y^2 + \Delta z^2}$ để bảo toàn kích thước vật lý của mắt và miệng khi xoay không gian.
  2. **Thuật toán thích ứng góc xoay ngang (Yaw-Aware Adaptive EAR):** Tính góc quay mặt ngang (Yaw). Khi phát hiện mặt nghiêng từ $20^\circ - 50^\circ$, hệ thống tự động ưu tiên lấy dữ liệu từ mắt nằm gần camera hơn (mắt nhìn rõ, không bị che) thay vì bắt buộc cả 2 mắt.
  3. **Ước lượng tư thế đầu bằng thuật toán PnP (`cv2.solvePnP`):** Tính toán chính xác ma trận quay 3D để tách bạch hoàn toàn giữa việc quay đầu nhìn gương chiếu hậu ($45^\circ$) với việc gục đầu ngủ gật.

