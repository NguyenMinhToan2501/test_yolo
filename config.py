# config.py (Bảng Điều Khiển / Configuration)
#    - Chức năng: Lưu trữ toàn bộ các hằng số, ngưỡng (threshold), và quy tắc chấm điểm.
#    - Ý nghĩa: Hoạt động như một "Bảng điều khiển". Khi cần tinh chỉnh độ nhạy của 
#      hệ thống (như ngáp to/nhỏ, nhắm mắt bao lâu, góc gục đầu), lập trình viên chỉ 
#      cần sửa tại đây mà không cần can thiệp vào logic code cốt lõi.

# 1. cấu hình 
class Config:
    EAR_CLOSED = 0.25  # ngưỡng nhắm mắt
    
    # khu vực điều chỉnh thông số
    MAR_LIGHT_YAWN = 0.70  # ngưỡng miệng khi nói chuyện bình thường - ko cộng điểm 
    MAR_DEEP_YAWN = 0.85   # ngưỡng miệng khi ngáp sâu
    
    # điều chỉnh thông số gật đầu
    HEAD_DROP_ANGLE = 25.0 # góc gục đầu (độ)
    HEAD_DROP_TIME = 2.0   # thời gian gục đầu (2 giây sẽ gục đầu và hệ thống sẽ cảnh báo)

    MICROSLEEP_TIME = 1.5      # giây
    DEEP_YAWN_TIME = 3.0       # giây
    YAWN_COOLDOWN = 120.0      # giây (2 phút) thời gian reset cơ chế 100đ xuống 0đ
    
    SCORE_RECOVERY = 3         # điểm trừ mỗi lần chớp mắt khi tỉnh táo
    SCORE_LIGHT_YAWN = 40      # điểm cộng mỗi lần ngáp ngắn