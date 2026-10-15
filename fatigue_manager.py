# fatigue_manager.py (bộ não xử lý)
#    - Chức năng: Quản lý bộ nhớ trạng thái và tính toán điểm số buồn ngủ (0-100).
#    - Ý nghĩa: Đóng vai trò là "Bộ não". File này nhận số liệu từ `utils.py`, đối 
#      chiếu với luật lệ ở `config.py` để theo dõi hành vi theo thời gian (ví dụ: đếm
#      số lần ngáp, đo thời gian nhắm mắt liên tục). Từ đó chốt điểm số và xuất ra 
#      trạng thái cuối cùng (Normal, Tired, Warning, Danger).

import time
from config import Config

# 2. quản lý trạng thái 
class FatigueManager:
    def __init__(self):
        self.score = 0
        self.violation_reason = "" # biến lưu trữ lý do vi phạm
        
        # mắt
        self.eye_closed_time = 0 # lưu lại thời gian tài xế nhắm mắt 
        self.is_eye_closed = False # đánh dấu trạng thái mắt. false là đang mở, true là nhắm
        self.slow_blink_count = 0 # đếm số lần chớp mắt chậm liên tiếp 
        
        # miệng
        self.yawn_start_time = 0 # lưu lại thời gian khi tài xế há miệng to
        self.is_yawning = False # đánh dấu trạng thái miệng, như cái mắt zị 
        self.light_yawn_count = 0 # bộ đếm số lần ngáp, nếu đạt mức 3 sẽ cảnh báo 
        self.last_yawn_time = 0 # lưu lại mốc thời gian ngáp ngắn cuối cùng 

        # đầu
        self.head_drop_start_time = 0 
        self.is_head_dropped = False

    def update_eyes(self, ear):
        current_time = time.time()
        
        # trường hợp 1: tài xế nhắm mắt 
        if ear < Config.EAR_CLOSED:
            if not self.is_eye_closed:
                self.is_eye_closed = True
                self.eye_closed_time = current_time # ghi nhớ thời gian bắt đầu nhắm 
            
            # mắt vẫn đang nhắm 
            else:
                # bắt sự kiện ngủ gật
                if (current_time - self.eye_closed_time) > Config.MICROSLEEP_TIME:
                    self.score = 100 # phạt 100 điểm để còi réo lên
                    # ghi nhận lý do 
                    if not self.violation_reason: self.violation_reason = "NGU GAT (NHAM MAT)"
                    
        # trường hơp 2: tài xế mở mắt 
        else:
            if self.is_eye_closed:
                # kết thúc 1 chu kỳ chớp mắt
                blink_duration = current_time - self.eye_closed_time
                self.is_eye_closed = False
                self._evaluate_blink_speed(blink_duration)

    def _evaluate_blink_speed(self, duration):
        # lọc nhiễu (<NORMAL_BLINK_MIN_TIME) và phân loại tốc độ chớp mắt
        if Config.NORMAL_BLINK_MIN_TIME <= duration <= Config.NORMAL_BLINK_MAX_TIME: # chớp mắt khỏe mạnh    
            self.score = max(0, self.score - Config.SCORE_RECOVERY) # hạ điểm 
            self.slow_blink_count = 0
        elif Config.SLOW_BLINK_TIME <= duration <= Config.MICROSLEEP_TIME: # chớp mắt mệt mỏi 
            self.score = max(self.score, Config.WARNING_LEVEL_2) # đẩy trạng thái tài xế lên mức điểm cảnh báo
            self.slow_blink_count += 1 # ghi nhận chớp mắt chậm

    def update_mouth(self, mar):
        current_time = time.time()
        
        # reset chuỗi ngáp ngắn nếu đã qua thời gian cooldown
        # nếu quá 2p tài xế ko ngáp, hệ thống sẽ xóa và đưa về 0 và tắt cảnh báo 
        if self.last_yawn_time and (current_time - self.last_yawn_time > Config.YAWN_COUNT_WINDOW):
            self.light_yawn_count = 0
            self.last_yawn_time = 0

        # mức 3: ngáp sâu
        if mar > Config.MAR_DEEP_YAWN:
            if not self.is_yawning:
                self.is_yawning = True
                self.yawn_start_time = current_time # ghi lại thời điểm ngáp 

            # nếu ngáp quá to liên tục quá 3s -> lên max điểm 
            elif (current_time - self.yawn_start_time) > Config.DEEP_YAWN_TIME:
                self.score = 100
                if not self.violation_reason: self.violation_reason = "NGAP SAU"
        # mức 2: ngáp nhẹ        
        elif mar > Config.MAR_LIGHT_YAWN:
            if not self.is_yawning:
                self.is_yawning = True
                self.yawn_start_time = current_time

                # phát hiện ngáp nhẹ -> lên 40 điểm 
                self.score = min(100, self.score + Config.SCORE_LIGHT_YAWN)
                self.light_yawn_count += 1
                self.last_yawn_time = current_time
                
                # nếu đủ số lần ngáp liên tiếp theo Config -> lên max điểm 
                if self.light_yawn_count >= Config.YAWN_REPEAT_WARNING:
                    self.score = 100
                    self.light_yawn_count = 0
                    if not self.violation_reason: self.violation_reason = "NGAP LIEN TUC"
        # mức 1: nói chuyện bth            
        else:
            # khẩu hình miệng dưới ngưỡng ngáp, đánh dấu là ko ngáp - ko cộng điểm 
            self.is_yawning = False

    # trạng thái gục đầu
    def update_head(self, pitch_angle):
        current_time = time.time()

        # nếu góc đầu cúi quá 25 độ 
        if pitch_angle > Config.HEAD_DROP_ANGLE:
            if not self.is_head_dropped:
                self.is_head_dropped = True  
                self.head_drop_start_time = current_time 
            else:
                # nếu giữ tư thế quá 2s -> cảnh báo nguy hiểm
                if (current_time - self.head_drop_start_time) > Config.HEAD_DROP_TIME:
                    self.score = 100
                    if not self.violation_reason: self.violation_reason = "GUC DAU"
        else:
            self.is_head_dropped = False


    def get_status(self):
        # chốt điểm số và tính trạng thái 
        self.score = max(Config.SCORE_MIN, min(Config.SCORE_MAX, self.score))
        
        # Đã cập nhật để trả về 4 biến, ngưỡng lấy từ Config
        if self.score < Config.WARNING_LEVEL_1:
            return "Normal", (0, 255, 0), False, ""
        elif self.score < Config.WARNING_LEVEL_2:
            return "Tired", (0, 255, 255), False, ""
        elif self.score < Config.WARNING_LEVEL_3:
            return "Warning", (0, 165, 255), False, ""
        else:
            return "Danger", (0, 0, 255), True, self.violation_reason

    def reset(self):
        # reset toàn bộ điểm số và trạng thái về 0 sau khi kêu còi 10s
        self.score = 0
        self.violation_reason = "" # reset lý do khi chụp ảnh bằng chứng 

        self.eye_closed_time = 0
        self.is_eye_closed = False
        self.slow_blink_count = 0
        
        self.yawn_start_time = 0
        self.is_yawning = False
        self.light_yawn_count = 0
        self.last_yawn_time = 0
        
        self.head_drop_start_time = 0
        self.is_head_dropped = False