# utils.py (tính toán)
#    - Chức năng: Chứa các hàm tính toán toán học độc lập (distance, EAR, MAR, Pitch).
#    - Ý nghĩa: Chịu trách nhiệm xử lý dữ liệu thô (tọa độ 3D từ MediaPipe) thành các 
#      chỉ số sinh lý học cụ thể (độ mở mắt, độ há miệng, góc chúi của đầu). File này
#      chỉ làm toán, không lưu trạng thái tài xế.

import math

# các hàm tiện ích 
def distance(p1, p2):
    # tính khoảng cách Eculid giữa 2 điểm p1, p2 trên mặt phẳng 2D (trục x, y)
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

# tính tỉ lệ mở của mắt 
def calculate_ear(landmarks):
    # tính toán cho mắt trái 
    left_h = distance(landmarks[33], landmarks[133]) # chiều ngang (đuôi đến khóe mắt)
    # chiều dọc mắt trái (lấy trung bình 2 đường dọc mí mắt)
    left_v = (distance(landmarks[159], landmarks[145]) + distance(landmarks[158], landmarks[153])) / 2.0
    # tính toán cho mắt phải 
    right_h = distance(landmarks[362], landmarks[263])# chiều ngang (đuôi đến khóe mắt)
    # chiều dọc mắt phải (tương tự như mắt trái)
    right_v = (distance(landmarks[386], landmarks[374]) + distance(landmarks[385], landmarks[380])) / 2.0
    
    # tính tỉ lệ dọc ngang cho từng mắt 
    ear_left = left_v / left_h if left_h > 0 else 0
    ear_right = right_v / right_h if right_h > 0 else 0

    # trả về tỉ lệ trung bình của cả 2 mắt 
    return (ear_left + ear_right) / 2.0

# tính tỉ lệ há miệng 
def calculate_mar(landmarks):
    mouth_h = distance(landmarks[78], landmarks[308]) # chiều ngang - lấy khoảng cách của 2 khóe miệng trái - phải 
    mouth_v = distance(landmarks[13], landmarks[14]) # chiều dọc - lấy khoảng cách giữa môi trên và môi dưới 
    return mouth_v / mouth_h if mouth_h > 0 else 0 # trả kết quả 

# hàm gục đầu
def calculate_head_pitch(landmarks):
    top_head = landmarks[10] # đỉnh trán
    chin = landmarks[152]    # cằm
    # tính chênh lệch tọa độ (y là chiều dọc, z là chiều sâu)
    dy = chin.y - top_head.y
    dz = chin.z - top_head.z
    
    # tính góc chúi đầu bằng hàm atan2
    pitch_angle = math.degrees(math.atan2(dz, dy))
    return pitch_angle