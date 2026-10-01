# pyrefly: ignore [missing-import]
import cv2
import time
import os
import math
# pyrefly: ignore [missing-import]
from ultralytics import YOLO
# pyrefly: ignore [missing-import]
import mediapipe as mp
# pyrefly: ignore [missing-import]
from mediapipe.tasks import python
# pyrefly: ignore [missing-import]
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)

def distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def calculate_ear(landmarks):
    left_h = distance(landmarks[33], landmarks[133])
    left_v1 = distance(landmarks[159], landmarks[145])
    left_v2 = distance(landmarks[158], landmarks[153])
    ear_left = (left_v1 + left_v2) / (2.0 * left_h) if left_h > 0 else 0
    
    right_h = distance(landmarks[362], landmarks[263])
    right_v1 = distance(landmarks[386], landmarks[374])
    right_v2 = distance(landmarks[385], landmarks[380])
    ear_right = (right_v1 + right_v2) / (2.0 * right_h) if right_h > 0 else 0
    
    return (ear_left + ear_right) / 2.0

def calculate_mar(landmarks):
    mouth_h = distance(landmarks[78], landmarks[308])
    mouth_v = distance(landmarks[13], landmarks[14])
    mar = mouth_v / mouth_h if mouth_h > 0 else 0
    return mar
import platform
import os

# Sử dụng winsound (có sẵn trên Windows) thay cho pygame để tránh lỗi cài đặt
if platform.system() == 'Windows':
    import winsound
    HAS_WINSOUND = True
    if not os.path.exists('am_thanh_canh_bao.wav'):
        print("Cảnh báo: Không tìm thấy file am_thanh_canh_bao.wav. Chế độ âm thanh sẽ bị vô hiệu hóa.")
        HAS_WINSOUND = False
else:
    print("Cảnh báo: Hệ điều hành không phải Windows. Chế độ âm thanh winsound bị vô hiệu hóa.")
    HAS_WINSOUND = False

# Tải mô hình YOLO đã huấn luyện
if not os.path.exists('runs/detect/train/weights/best.pt'):
    print("Lỗi: Không tìm thấy file best.pt. Vui lòng chạy file train.py để huấn luyện mô hình trước.")
    exit(1)

model = YOLO('runs/detect/train/weights/best.pt')

# Mở webcam
cap = cv2.VideoCapture(0)

# Các biến theo dõi logic của hệ thống DriveLinker
eyes_closed_start_time = None
drowsiness_score = 0
is_level_1_alert_active = False

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # 1. Đưa hình ảnh qua mô hình YOLO để nhận diện
    results = model(frame, verbose=False)
    
    is_eye_closed_yolo = False
    is_yawning_yolo = False

    # Quét kết quả trả về từ YOLO
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            
            # Vẽ khung nhận diện lên màn hình
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            if label.lower() in ['closed_eye', 'microsleep']:
                is_eye_closed_yolo = True
            if label.lower() == 'yawn':
                is_yawning_yolo = True

    # Validate bằng MediaPipe 3D Face Mesh để chống nhận diện sai (False Positives)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    results_mp = face_landmarker.detect(mp_image)
    ear = 1.0
    mar = 0.0
    
    if results_mp.face_landmarks:
        for face_landmarks in results_mp.face_landmarks:
            ear = calculate_ear(face_landmarks)
            mar = calculate_mar(face_landmarks)
            break
        
        # Ngưỡng EAR (mắt nhắm) và MAR (miệng ngáp)
        is_eye_closed = (ear < 0.25)
        is_yawning = (mar > 0.4)
    else:
        # Nếu MediaPipe không thấy mặt, dùng tạm kết quả của YOLO
        is_eye_closed = is_eye_closed_yolo
        is_yawning = is_yawning_yolo

    # 2. Logic đánh giá Dấu hiệu mệt mỏi theo tài liệu
    if is_eye_closed:
        if eyes_closed_start_time is None:
            eyes_closed_start_time = time.time()
        else:
            # Phát hiện nhắm mắt kéo dài
            closed_duration = time.time() - eyes_closed_start_time
            if closed_duration >= 3.0: # Ngưỡng >= 3 giây theo tài liệu
                drowsiness_score = 100 
    else:
        eyes_closed_start_time = None
        drowsiness_score -= 2 # Trừ điểm từ từ nếu tỉnh táo

    if is_yawning:
        drowsiness_score += 15 # Cộng điểm nếu ngáp

    # Giữ điểm số trong khoảng 0 - 100
    drowsiness_score = max(0, min(100, drowsiness_score))

    # 3. Phân loại trạng thái và Cảnh báo Level 1 theo tài liệu
    status = "Normal"
    color = (0, 255, 0)

    if 0 <= drowsiness_score <= 30:
        status = "Normal"
        color = (0, 255, 0)
    elif 31 <= drowsiness_score <= 60:
        status = "Tired"
        color = (0, 255, 255)
    elif 61 <= drowsiness_score <= 80:
        status = "Warning"
        color = (0, 165, 255)
    elif 81 <= drowsiness_score <= 100:
        status = "Danger"
        color = (0, 0, 255)

    # Kích hoạt âm thanh tại xe nếu ở mức Danger
    if status == "Danger":
        if not is_level_1_alert_active:
            if HAS_WINSOUND:
                winsound.PlaySound('am_thanh_canh_bao.wav', winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            is_level_1_alert_active = True
    else:
        if is_level_1_alert_active:
            if HAS_WINSOUND:
                winsound.PlaySound(None, winsound.SND_PURGE)
            is_level_1_alert_active = False

    # Hiển thị thông số lên UI
    cv2.putText(frame, f"Score: {drowsiness_score}/100", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.putText(frame, f"State: {status}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("DriveLinker Edge AI - YOLOv8", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if HAS_WINSOUND:
    winsound.PlaySound(None, winsound.SND_PURGE)