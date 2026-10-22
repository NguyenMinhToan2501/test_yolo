# config.py (Bảng Điều Khiển / Configuration)
#    - Chức năng: Lưu trữ toàn bộ các hằng số, ngưỡng (threshold), và quy tắc chấm điểm.
#    - Ý nghĩa: Hoạt động như một "Bảng điều khiển". Khi cần tinh chỉnh độ nhạy của 
#      hệ thống (như ngáp to/nhỏ, nhắm mắt bao lâu, góc gục đầu), lập trình viên chỉ 
#      cần sửa tại đây mà không cần can thiệp vào logic code cốt lõi.

# 1. cấu hình 
class Config:

    # ==========================================================
    # 1. CAMERA & SYSTEM - CẤU HÌNH CAMERA VÀ HỆ THỐNG
    # ==========================================================

    CAMERA_INDEX = 0                 # Chọn camera số 0 (camera mặc định của máy tính)
    FRAME_WIDTH = 640                # Chiều rộng hình ảnh đầu vào: 640 pixel
    FRAME_HEIGHT = 480               # Chiều cao hình ảnh đầu vào: 480 pixel
    TARGET_FPS = 30                  # Mục tiêu xử lý 30 khung hình mỗi giây

    MIN_FACE_CONFIDENCE = 0.70       # Chỉ chấp nhận khuôn mặt có độ tin cậy từ 70% trở lên
    MIN_LANDMARK_CONFIDENCE = 0.70   # Ngưỡng tin cậy tối thiểu 70% nếu mô hình landmarks hỗ trợ
    FACE_MISSING_TIME = 2.0          # Không thấy khuôn mặt liên tục 2 giây thì báo mất khuôn mặt
    CAMERA_TIMEOUT = 3.0            # Camera không cung cấp hình ảnh hợp lệ trong 3 giây thì báo lỗi


    # ==========================================================
    # 2. EYE DETECTION - NHẬN DIỆN TRẠNG THÁI MẮT
    # ==========================================================

    EAR_CLOSED = 0.25                # EAR <= 0.25: xác định mắt đang nhắm
    EAR_HALF_CLOSED = 0.30           # 0.25 < EAR <= 0.30: mắt mở một phần, có thể đang lờ đờ

    NORMAL_BLINK_MIN_TIME = 0.08     # Thời gian chớp mắt tối thiểu 0.08 giây để lọc nhiễu
    NORMAL_BLINK_MAX_TIME = 0.30     # Chớp mắt kéo dài tối đa 0.30 giây được xem là bình thường
    SLOW_BLINK_TIME = 0.32           # Nhắm rồi mở mắt từ 0.32 giây: nhận diện chớp mắt chậm (siêu nhạy)

    MICROSLEEP_TIME = 1.50           # Mắt nhắm liên tục 1.5 giây: kích hoạt cảnh báo nghi ngờ ngủ gật
    SEVERE_EYE_CLOSED_TIME = 2.00    # Mắt nhắm liên tục 2 giây: kích hoạt cảnh báo nguy hiểm

    PERCLOS_WINDOW = 60.0            # Khoảng thời gian 60 giây dùng để tính tỷ lệ mắt gần đóng
    PERCLOS_EYE_CLOSURE_RATIO = 0.80 # Mí mắt đóng khoảng 80% so với trạng thái mở chuẩn
    PERCLOS_WARNING = 0.25           # PERCLOS >= 25%: cảnh báo dấu hiệu giảm tỉnh táo
    PERCLOS_DANGER = 0.40            # PERCLOS >= 40%: đánh giá nguy cơ buồn ngủ cao
    PERCLOS_MIN_VALID_RATIO = 0.80   # Chỉ tính PERCLOS khi ít nhất 80% thời gian có dữ liệu mắt hợp lệ


    # ==========================================================
    # 3. MOUTH DETECTION - NHẬN DIỆN MIỆNG VÀ NGÁP
    # ==========================================================

    MAR_LIGHT_YAWN = 0.70            # MAR >= 0.70: miệng mở lớn, bắt đầu theo dõi khả năng ngáp
    MAR_DEEP_YAWN = 0.85             # MAR >= 0.85: miệng mở rất lớn, là dấu hiệu ứng viên ngáp sâu

    LIGHT_YAWN_MIN_TIME = 1.50       # Miệng mở đủ lớn trong 1.5 giây: ứng viên ngáp nhẹ
    DEEP_YAWN_TIME = 3.00            # Hành vi ngáp kéo dài 3 giây: ứng viên ngáp sâu

    YAWN_COUNT_WINDOW = 120.0        # Theo dõi tổng số lần ngáp trong 120 giây gần nhất
    YAWN_REPEAT_WARNING = 3          # Ngáp ít nhất 3 lần trong 120 giây: cảnh báo ngáp liên tục

    YAWN_EVENT_GAP = 1.00            # Miệng đóng rồi mở lại trong <= 1 giây: có thể gộp thành cùng một lần ngáp
    YAWN_SCORE_COOLDOWN = 5.0        # Chờ ít nhất 5 giây trước khi cộng điểm cho một sự kiện ngáp mới


    # ==========================================================
    # 4. HEAD POSE - NHẬN DIỆN TƯ THẾ ĐẦU VÀ CỔ
    # ==========================================================

    HEAD_DROP_ANGLE = 15.0           # Đầu cúi xuống từ 15 độ so với tư thế đầu chuẩn
    HEAD_DROP_TIME = 2.0             # Đầu cúi liên tục 2 giây: ghi nhận một sự kiện gục đầu
    HEAD_EYES_CLOSED_TIME = MICROSLEEP_TIME
    HEAD_NOD_MIN_TIME = 0.30         # Thời gian tối thiểu của một chu kỳ gật đầu: 0.3 giây
    HEAD_NOD_MAX_TIME = 2.00         # Thời gian tối đa của một chu kỳ gật đầu: 2 giây

    HEAD_NOD_WINDOW = 60.0           # Theo dõi số lần gật đầu trong 60 giây gần nhất
    HEAD_NOD_REPEAT_WARNING = 3      # Gật đầu bất thường ít nhất 3 lần/60 giây: tăng mức cảnh báo

    HEAD_TILT_ANGLE = 30.0           # Đầu nghiêng trái hoặc phải từ 30 độ so với tư thế chuẩn
    HEAD_TILT_TIME = 3.0             # Đầu nghiêng liên tục 3 giây: ghi nhận hành vi nghiêng đầu kéo dài


    # ==========================================================
    # 5. GAZE DETECTION - PHÁT HIỆN HƯỚNG NHÌN
    # ==========================================================

    GAZE_AWAY_TIME = 2.0             # Nhìn ra khỏi vùng quan sát đường >= 2 giây: nghi ngờ mất tập trung
    GAZE_DOWN_TIME = 2.0             # Nhìn xuống liên tục >= 2 giây: ghi nhận hành vi nhìn xuống

    HEAD_YAW_AWAY_ANGLE = 35.0       # Đầu xoay ngang trái/phải từ 35 độ so với hướng chuẩn
    DISTRACTION_REPEAT_WINDOW = 60.0 # Theo dõi các hành vi mất tập trung lặp lại trong 60 giây


    # ==========================================================
    # 6. DROWSINESS SCORING - HỆ THỐNG CHẤM ĐIỂM BUỒN NGỦ
    # ==========================================================

    SCORE_MIN = 0                    # Điểm buồn ngủ thấp nhất là 0
    SCORE_MAX = 100                  # Điểm buồn ngủ cao nhất là 100

    SCORE_LIGHT_YAWN = 40            # Cộng 40 điểm khi xác nhận một lần ngáp nhẹ
    SCORE_DEEP_YAWN = 60             # Cộng 60 điểm khi xác nhận một lần ngáp sâu

    SCORE_SLOW_BLINK = 20            # Cộng 20 điểm cho một lần chớp mắt chậm bất thường (siêu nhạy)
    SCORE_REPEATED_YAWN = 15         # Cộng thêm 15 điểm khi đạt điều kiện ngáp lặp lại
    SCORE_HEAD_NOD = 20              # Cộng 20 điểm cho một chu kỳ gật đầu bất thường
    SCORE_HEAD_DROP = 45             # Cộng 45 điểm khi phát hiện một sự kiện gục đầu

    SCORE_DECAY_INTERVAL = 0.5       # Giảm điểm nhanh chóng mỗi 0.5 giây theo thời gian thực
    SCORE_DECAY_AMOUNT = 3           # Mỗi 0.5 giây giảm 3 điểm (tương đương 6 điểm/giây, điểm tụt nhanh)
    SCORE_RECOVERY = 5               # Trừ ngay 5 điểm cho mỗi lần chớp mắt bình thường (hồi phục nhạy)


    # ==========================================================
    # 7. WARNING LEVELS - PHÂN CẤP CẢNH BÁO
    # ==========================================================

    WARNING_LEVEL_1 = 30             # Điểm từ 30 đến dưới 60: cảnh báo mức 1
    WARNING_LEVEL_2 = 60             # Điểm từ 60 đến dưới 85: cảnh báo mức 2
    WARNING_LEVEL_3 = 85             # Điểm từ 85 trở lên: cảnh báo mức 3 (nguy hiểm)

    WARNING_CONFIRM_TIME = 1.0       # Điểm vượt ngưỡng liên tục 1 giây mới xác nhận cảnh báo thông thường
    WARNING_REPEAT_INTERVAL = 5.0    # Nếu nguy cơ vẫn tồn tại, nhắc lại cảnh báo sau 5 giây (thay vì 10s)
    ALERT_RESET_TIME = 3.0           # Thời gian báo động tối đa mỗi đợt giảm xuống 3 giây (thay vì 10s)
    ALERT_MAX_DURATION = 3.0         # Còi hú tối đa 3 giây cho mỗi đợt cảnh báo nếu nguy cơ chưa dứt
    ALERT_COOLDOWN = 1.0             # Khoảng nghỉ tối thiểu giữa các đợt cảnh báo
    ALERT_AUTO_DISMISS = True        # Tự động TẮT CÒI NGAY khi tài xế mở mắt, ngẩng đầu hoặc ngậm miệng
    YAWN_ALERT_DURATION = 1.5        # Thời gian cảnh báo ngáp chỉ 1.5 giây (nhắc nhở ngắn, không réo còi dai)
    DISMISS_BUFFER_TIME = 0.2        # Độ trễ tắt còi 0.2s sau khi mở mắt/ngậm miệng để chống chập chờn


    # ==========================================================
    # 8. SYSTEM SAFETY - KIỂM SOÁT ĐỘ TIN CẬY VÀ AN TOÀN
    # ==========================================================

    ALERT_ON_CAMERA_FAILURE = True   # Bật cảnh báo khi camera mất tín hiệu hoặc không hoạt động
    ALERT_ON_FACE_MISSING = True     # Bật cảnh báo khi không phát hiện khuôn mặt tài xế quá lâu

    REQUIRE_VALID_FACE_FOR_SCORING = True  # Chỉ chấm điểm hành vi khuôn mặt khi nhận diện đủ tin cậy
    REQUIRE_VALID_EYES_FOR_PERCLOS = True  # Không tính PERCLOS từ dữ liệu mắt bị che hoặc không hợp lệ

    ENABLE_EYE_DETECTION = True      # Bật module nhận diện mắt
    ENABLE_YAWN_DETECTION = True     # Bật module nhận diện ngáp
    ENABLE_HEAD_DETECTION = True     # Bật module nhận diện tư thế đầu
    ENABLE_GAZE_DETECTION = True     # Bật module phân tích hướng nhìn


    # ==========================================================
    # 9. LOGGING - GHI NHẬT KÝ HỆ THỐNG
    # ==========================================================

    ENABLE_LOGGING = True            # Bật chức năng ghi nhật ký hoạt động của AI
    LOG_EVENTS = True                # Lưu sự kiện: nhắm mắt, ngáp, gục đầu, cảnh báo...
    SAVE_RAW_VIDEO = False           # Mặc định không lưu video gốc để bảo vệ riêng tư
