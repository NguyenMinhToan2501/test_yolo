#  main.py
#    - Chức năng: Điểm neo điều phối toàn bộ vòng lặp của hệ thống.
#    - Ý nghĩa: Khởi tạo Camera, nạp mô hình AI (YOLOv8, MediaPipe), hệ thống âm 
#      thanh (Pygame). Nó liên tục đọc khung hình, luân chuyển dữ liệu qua lại giữa 
#      các file trên và vẽ kết quả (Render UI) lên màn hình giám sát.

import cv2
import time
import os
from ultralytics import YOLO
import mediapipe as mp
from mediapipe.tasks import python
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
        import pygame
        pygame.mixer.init()
        alert_sound = pygame.mixer.Sound('am_thanh_canh_bao.wav')
        HAS_PYGAME = True
    except (ImportError, FileNotFoundError):
        print("Cảnh báo: Không tìm thấy pygame hoặc file âm thanh.")
        HAS_PYGAME = False
        alert_sound = None

    # khởi tạo mô hình AI
    model = YOLO('runs/detect/train/weights/best.pt')
    
    base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    face_landmarker = vision.FaceLandmarker.create_from_options(options)
    
    # khởi tạo bộ quản lý logic
    fatigue_manager = FatigueManager()
    is_alerting = False
    alert_start_time = 0

    print("Đang khởi động camera...Vui lòng chờ")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Không tìm thấy camera")
        
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # 1. pipeline yolo
        results = model(frame, verbose=False)
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = model.names[int(box.cls[0])]
                # vẽ khung nhận diện lên màn hình
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # 2. pipeline mediaPipe và xử lý logic
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        results_mp = face_landmarker.detect(mp_image)
        
        if results_mp.face_landmarks:
            landmarks = results_mp.face_landmarks[0]
            ear = calculate_ear(landmarks) 
            mar = calculate_mar(landmarks) 
            pitch_val = calculate_head_pitch(landmarks)  
            
            if not is_alerting:
                fatigue_manager.update_eyes(ear) 
                fatigue_manager.update_mouth(mar) 
                fatigue_manager.update_head(pitch_val) 

        # 3. lấy kết quả và render UI
        status, color, should_alert, violation_reason = fatigue_manager.get_status()
        current_loop_time = time.time()

        # logic báo động 10 giây, chụp ảnh và reset
        if should_alert:
            if not is_alerting:
                if HAS_PYGAME and alert_sound: alert_sound.play(-1)
                is_alerting = True
                alert_start_time = current_loop_time
                
                # === chụp ảnh bằng chứng ===
                timestamp = time.strftime("%Y%m%d_%H%M%S") # dùng làm tên file
                display_time = time.strftime("%d/%m/%Y %H:%M:%S") # dùng để in lên ảnh
                
                # tạo bản sao của khung hình để in chữ lên
                evidence_frame = frame.copy()
                reason_text = violation_reason if violation_reason else "BUON NGU"
                alert_text = f"VI PHAM: {reason_text} - {display_time}"
                
                cv2.putText(evidence_frame, alert_text, (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # xử lý tên lỗi để làm tên file (đổi khoảng trắng thành dấu gạch dưới)
                safe_reason_name = reason_text.replace(" ", "_")
                # đổi định dạng tên file thành lỗi vi phạm_thời gian
                img_path = os.path.join(EVIDENCE_DIR, f"{safe_reason_name}_{timestamp}.jpg")
                
                cv2.imwrite(img_path, evidence_frame) # lưu bức ảnh đã chèn thời gian
                print(f"📸 ĐÃ CHỤP ẢNH BẰNG CHỨNG [{reason_text}]: {img_path}")
                # =========================================
            else:
                if current_loop_time - alert_start_time >= 10.0:
                    if HAS_PYGAME and alert_sound: alert_sound.stop()
                    is_alerting = False
                    fatigue_manager.reset()
                    status = "Normal"
                    color = (0, 255, 0)
        else:
            if is_alerting:
                if HAS_PYGAME and alert_sound: alert_sound.stop()
                is_alerting = False

        # vẽ thông số điểm và trạng thái
        cv2.putText(frame, f"Score: {fatigue_manager.score}/100", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(frame, f"State: {status}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # vẽ đồng hồ thời gian thực
        current_time_str = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        cv2.putText(frame, current_time_str, (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("DriveLinker Edge AI", frame)

        # tắt hệ thống dứt điểm 
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q') or key == 27 or cv2.getWindowProperty("DriveLinker Edge AI", cv2.WND_PROP_VISIBLE) < 1:
            cap.release()
            cv2.destroyAllWindows()
            os._exit(0)