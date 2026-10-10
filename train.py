# pyrefly: ignore [missing-import]
from ultralytics import YOLO

# Khởi tạo mô hình YOLOv8 nano
model = YOLO('yolov8n.pt')

# Bắt đầu train (trỏ file data.yaml tới thư mục dataset bạn vừa tải)
results = model.train(data='Drowsiness Detectin Using Yolov8.v1i.yolov8/data.yaml', epochs=50, imgsz=640)