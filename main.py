#  main.py
#    - Chức năng: Điểm neo điều phối toàn bộ vòng lặp của hệ thống.
#    - Ý nghĩa: Khởi tạo Camera, nạp mô hình AI (YOLOv8, MediaPipe), hệ thống âm 
#      thanh (Pygame). Nó liên tục đọc khung hình, luân chuyển dữ liệu qua lại giữa 
#      các file trên và vẽ kết quả (Render UI) lên màn hình giám sát.

# pyrefly: ignore[missing-import]
import cv2
import time
import os
# pyrefly: ignore[missing-import]
from ultralytics import YOLO
# pyrefly: ignore[missing-import]
import mediapipe as mp
# pyrefly: ignore[missing-import]
from mediapipe.tasks import python
# pyrefly: ignore[missing-import]
from mediapipe.tasks.python import vision

# Import các thành phần từ các file đã chia nhỏ
from config import Config
from fatigue_manager import FatigueManager
from utils import calculate_ear, calculate_mar, calculate_head_pitch

# thiết lập thư mục lưu bằng chứng 
EVIDENCE_DIR = "bang_chung"
if not os.path.exists(EVIDENCE_DIR): # kiểm tra xem ổ cứng đã có thư mục này chưa 
    os.makedirs(EVIDENCE_DIR) # nếu chưa sẽ tạo để tránh lỗi khi lưu 
    print(f"Đã tạo thư mục lưu ảnh: {EVIDENCE_DIR}")

# 3. main
if __name__ == "__main__":
    # khởi tạo âm thanh
    try:
        # pyrefly: ignore[missing-import]
        import pygame
        pygame.mixer.init()
        alert_sound = pygame.mixer.Sound('am_thanh_canh_bao.wav')
        
        # Nạp âm thanh cảnh báo mất khuôn mặt (lời thoại tiếng Việt tốc độ 1.5x)
        try:
            face_missing_sound = pygame.mixer.Sound('canh_bao_mat_mat.mp3')
        except Exception:
            face_missing_sound = None
        HAS_PYGAME = True
    except (ImportError, FileNotFoundError):
        print("Cảnh báo: Không tìm thấy pygame hoặc file âm thanh.")
        HAS_PYGAME = False
        alert_sound = None
        face_missing_sound = None

    # khởi tạo mô hình AI
    model = YOLO('runs/detect/train/weights/best.pt')
    
    base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=1,
        min_face_detection_confidence=Config.MIN_FACE_CONFIDENCE,
        min_face_presence_confidence=Config.MIN_FACE_CONFIDENCE,
        min_tracking_confidence=Config.MIN_LANDMARK_CONFIDENCE
    )
    face_landmarker = vision.FaceLandmarker.create_from_options(options)
    
    # khởi tạo bộ quản lý logic
    fatigue_manager = FatigueManager()
    is_alerting = False
    alert_start_time = 0
    alert_reason_type = "" # 'EMERGENCY', 'YAWN', 'GENERAL'
    last_alert_stop_time = 0
    last_evidence_time = 0
    last_evidence_reason = ""
    last_face_seen_time = time.time()
    is_face_missing_alerting = False
    last_face_missing_sound_time = 0

    print("Đang khởi động camera...Vui lòng chờ")
    cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, Config.TARGET_FPS)

    if not cap.isOpened():
        print("Không tìm thấy camera")
        
    # tạo cửa sổ hiển thị trước để tránh lỗi getWindowProperty
    cv2.namedWindow("DriveLinker Edge AI", cv2.WINDOW_NORMAL)

    # warmup: bỏ qua các frame rỗng đầu tiên khi camera chưa kịp khởi động
    print("Đang làm nóng camera...")
    for _ in range(10):
        cap.read()

    last_valid_frame_monotonic = time.monotonic()

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            current_loop_time = time.time()
            now_mono = time.monotonic()

            if not ret:
                # Bug I-11: Đo timeout camera bằng thời gian thực tế time.monotonic()
                if now_mono - last_valid_frame_monotonic >= Config.CAMERA_TIMEOUT:
                    print(f"❌ Camera mất tín hiệu quá {Config.CAMERA_TIMEOUT}s, dừng chương trình.")
                    break
                continue
            last_valid_frame_monotonic = now_mono

            # Bug I-20: Tách riêng display_frame để vẽ UI, giữ frame gốc cho MediaPipe/YOLO
            display_frame = frame.copy()

            # 1. pipeline yolo
            results = model(frame, verbose=False)
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = model.names[int(box.cls[0])]
                    # vẽ khung nhận diện lên màn hình hiển thị
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(display_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # 2. pipeline mediaPipe và xử lý logic
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            results_mp = face_landmarker.detect(mp_image)
            
            if results_mp.face_landmarks:
                landmarks = results_mp.face_landmarks[0]
                last_face_seen_time = current_loop_time

                # Nếu trước đó đang cảnh báo mất mặt -> dừng ngay giọng nói khi thấy lại mặt
                if is_face_missing_alerting:
                    if HAS_PYGAME and face_missing_sound:
                        face_missing_sound.stop()
                    is_face_missing_alerting = False

                # QUAN TRỌNG: KHÔNG ĐÓNG BĂNG XỬ LÝ KHI ĐANG CẢNH BÁO
                # Luôn cập nhật trạng thái mắt, miệng, đầu để phản hồi ngay khi tài xế mở mắt / hết ngáp
                if Config.ENABLE_EYE_DETECTION:
                    ear = calculate_ear(landmarks)
                    fatigue_manager.update_eyes(ear, current_loop_time)

                if Config.ENABLE_YAWN_DETECTION:
                    mar = calculate_mar(landmarks)
                    fatigue_manager.update_mouth(mar, current_loop_time)

                if Config.ENABLE_HEAD_DETECTION:
                    pitch_val = calculate_head_pitch(landmarks)
                    fatigue_manager.update_head(pitch_val, current_loop_time)

                # Giảm dần điểm khi lái xe an toàn tỉnh táo ổn định
                fatigue_manager.apply_decay(current_loop_time)

            else:
                # Bug I-01: Mất dấu khuôn mặt -> ngắt ngay các bộ đếm nhắm mắt/ngáp
                fatigue_manager.on_face_lost(current_loop_time)
                missing_duration = current_loop_time - last_face_seen_time
                if Config.ALERT_ON_FACE_MISSING:
                    if missing_duration >= Config.FACE_MISSING_TIME:
                        cv2.putText(display_frame, f"KHONG THAY KHUON MAT! ({missing_duration:.1f}s)", (20, 160),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
                        
                        # Phát cảnh báo giọng nói (tốc độ 1.5x): "Camera không thấy khuôn mặt! Camera không thấy khuôn mặt!"
                        if HAS_PYGAME and face_missing_sound:
                            if not is_face_missing_alerting or (current_loop_time - last_face_missing_sound_time >= 4.5):
                                face_missing_sound.play()
                                is_face_missing_alerting = True
                                last_face_missing_sound_time = current_loop_time
                                print("📢 CẢNH BÁO GIỌNG NÓI (1.5x): Camera không thấy khuôn mặt!")

            # 3. Lấy kết quả và quản lý cảnh báo nhạy bén (Responsive Alerting)
            status, color, should_alert, violation_reason = fatigue_manager.get_status()

            if is_alerting:
                alert_elapsed = current_loop_time - alert_start_time

                # --- ĐIỀU KIỆN 1: TỰ ĐỘNG TẮT CÒI NGAY KHI GIẢI TỎA NGUY HIỂM ---
                dismiss_alert = False
                
                # Nếu là cảnh báo ngáp: tài xế đã ngậm miệng lại hoặc còi đã kêu đủ 1.5s
                if alert_reason_type == "YAWN":
                    if (not fatigue_manager.is_yawning) or (alert_elapsed >= Config.YAWN_ALERT_DURATION):
                        dismiss_alert = True
                
                # Nếu là cảnh báo nguy cấp (ngủ gật / gục đầu): TÀI XẾ ĐÃ MỞ MẮT HOẶC NGẨNG ĐẦU LÊN
                elif alert_reason_type == "EMERGENCY":
                    if not fatigue_manager.is_active_hazard:
                        dismiss_alert = True
                
                # Trường hợp thông thường nếu không còn ở mức Danger
                elif not should_alert:
                    dismiss_alert = True

                # Hết thời gian cảnh báo tối đa mỗi đợt (ALERT_MAX_DURATION = 3s thay vì 10s)
                if alert_elapsed >= Config.ALERT_MAX_DURATION:
                    dismiss_alert = True

                if dismiss_alert:
                    if HAS_PYGAME and alert_sound:
                        alert_sound.stop()
                    is_alerting = False
                    last_alert_stop_time = current_loop_time
                    print("✅ Cảnh báo âm thanh đã dừng (Tài xế đã mở mắt / ngậm miệng / ngẩng đầu).")

            else:
                # --- ĐIỀU KIỆN 2: BẮT ĐẦU CẢNH BÁO MỚI ---
                # Nguy cấp (ngủ gật >= 1.5s hoặc gục đầu >= 2s): BÁO ĐỘNG NGAY LẬP TỨC KHÔNG CẦN CHỜ COOLDOWN
                can_alert = fatigue_manager.is_active_hazard or (current_loop_time - last_alert_stop_time >= Config.ALERT_COOLDOWN)
                if should_alert and can_alert:
                    is_alerting = True
                    alert_start_time = current_loop_time

                    if fatigue_manager.is_active_hazard:
                        alert_reason_type = "EMERGENCY"
                        # Ngủ gật/gục đầu: kêu lặp để cảnh báo tức thì
                        if HAS_PYGAME and alert_sound:
                            alert_sound.play(-1)
                    elif fatigue_manager.is_yawning:
                        alert_reason_type = "YAWN"
                        # Ngáp: chỉ phát tiếng ngắn nhắc nhở (1 lần, hoặc tối đa 1.5s)
                        if HAS_PYGAME and alert_sound:
                            alert_sound.play(0)
                    else:
                        alert_reason_type = "GENERAL"
                        if HAS_PYGAME and alert_sound:
                            alert_sound.play(0)

                    # === chụp ảnh bằng chứng (chống chụp lặp cho cùng một lỗi trong 10s) ===
                    reason_text = violation_reason if violation_reason else "BUON NGU"
                    if (reason_text != last_evidence_reason) or (current_loop_time - last_evidence_time >= 10.0):
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        display_time = time.strftime("%d/%m/%Y %H:%M:%S")
                        evidence_frame = display_frame.copy()
                        alert_text = f"VI PHAM: {reason_text} - {display_time}"
                        
                        cv2.putText(evidence_frame, alert_text, (10, 30), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        safe_reason_name = reason_text.replace(" ", "_")
                        img_path = os.path.join(EVIDENCE_DIR, f"{safe_reason_name}_{timestamp}.jpg")
                        cv2.imwrite(img_path, evidence_frame)
                        last_evidence_reason = reason_text
                        last_evidence_time = current_loop_time
                        print(f"📸 ĐÃ CHỤP ẢNH BẰNG CHỨNG [{reason_text}]: {img_path}")

            # 4. Vẽ thông số điểm và trạng thái lên display_frame
            cv2.putText(display_frame, f"Score: {fatigue_manager.score}/100", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(display_frame, f"State: {status}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            
            if violation_reason:
                cv2.putText(display_frame, f"Reason: {violation_reason}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Hiển thị số liệu cảm biến thời gian thực (EAR, MAR, Pitch)
            ear_show = ear[2] if 'ear' in locals() and isinstance(ear, (tuple, list)) else (ear if 'ear' in locals() else 0.0)
            mar_show = mar if 'mar' in locals() else 0.0
            pitch_show = pitch_val if 'pitch_val' in locals() else 0.0
            cv2.putText(display_frame, f"EAR: {ear_show:.2f} | MAR: {mar_show:.2f} | Pitch: {pitch_show:.1f} deg", 
                        (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)

            current_time_str = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
            cv2.putText(display_frame, current_time_str, (20, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            
            cv2.imshow("DriveLinker Edge AI", display_frame)

            # tắt hệ thống dứt điểm qua Q/ESC hoặc bấm nút X trên cửa sổ
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q') or key == 27 or cv2.getWindowProperty("DriveLinker Edge AI", cv2.WND_PROP_VISIBLE) == 0:
                break

    finally:
        # Bug I-12: Khối finally bảo đảm giải phóng mọi tài nguyên khi thoát
        print("Đang giải phóng tài nguyên...")
        if HAS_PYGAME:
            try:
                if alert_sound: alert_sound.stop()
                if face_missing_sound: face_missing_sound.stop()
                pygame.mixer.quit()
            except Exception:
                pass
        cap.release()
        cv2.destroyAllWindows()
        print("Đã đóng camera và dọn dẹp hệ thống an toàn.")