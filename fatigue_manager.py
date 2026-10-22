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
        self.is_eye_closed = False # đánh dấu trạng thái mắt: True là cả 2 mắt đang nhắm
        self.slow_blink_count = 0 # đếm số lần chớp mắt chậm liên tiếp 
        self.is_sleeping = False # cờ đánh dấu đang ngủ gật (nhắm mắt >= 1.5s)
        
        # miệng
        self.yawn_start_time = 0 # lưu lại thời gian khi tài xế há miệng to
        self.yawn_candidate_start = 0 # mốc thời gian bắt đầu vượt ngưỡng để lọc nhiễu
        self.is_yawning = False # đánh dấu đang trong một đợt ngáp hợp lệ (đã đủ 1.5s)
        self.yawn_alert_triggered = False # cờ chống lặp cảnh báo ngáp bất tận
        self.confirmed_yawns = [] # danh sách timestamps các lần ngáp đã xác nhận trong 120s
        self.last_yawn_time = 0 # lưu lại mốc thời gian ngáp cuối cùng 

       # đầu
        self.head_drop_start_time = 0
        self.head_open_start_time = None
        self.head_closed_start_time = None
        self.is_head_dropped = False
        self.is_head_open_eyes = False
        self.is_head_closed_eyes = False
        self.is_active_head_drop = False

        # cơ chế giảm điểm (decay) thời gian thực
        now = time.time()
        self.last_safe_time = now
        self.last_decay_time = now

    @property
    def is_active_hazard(self):
        """Trả về True nếu ngay tại thời điểm này tài xế đang ngủ gật hoặc đang gục đầu nhắm mắt."""
        return self.is_sleeping or self.is_active_head_drop

    def update_eyes(self, ear_data, current_time=None):
        """
        Nhận ear_data: tuple (ear_left, ear_right, ear_avg) hoặc float đơn lẻ.
        Hiển thị thời gian nhắm mắt từng 0.1s (VD: NHAM MAT (0.5s), NHAM MAT (1.2s)...).
        Đúng 1.5s kích hoạt ngay NGU GAT (1.5s) và hú còi.
        """
        if current_time is None:
            current_time = time.time()
        
        if isinstance(ear_data, (tuple, list)):
            ear_left, ear_right, ear_avg = ear_data[0], ear_data[1], ear_data[2]
        else:
            ear_left = ear_right = ear_avg = ear_data

        # QUY TẮC: CẢ HAI MẮT ĐỀU PHẢI NHẮM (< EAR_CLOSED)
        both_eyes_closed = (ear_left < Config.EAR_CLOSED) and (ear_right < Config.EAR_CLOSED)
        
        # trường hợp 1: cả hai mắt đang nhắm
        if both_eyes_closed:
            if not self.is_eye_closed:
                self.is_eye_closed = True
                self.eye_closed_time = current_time
                self.violation_reason = "NHAM MAT (0.0s)"
            else:
                duration = current_time - self.eye_closed_time
                # Hiển thị số giây nhắm mắt chạy liên tục theo thời gian thực
                if duration < Config.MICROSLEEP_TIME:
                    self.violation_reason = f"NHAM MAT ({duration:.1f}s)"
                else:
                    # Đúng 1.5s là kích hoạt báo động ngủ gật ngay lập tức
                    self.is_sleeping = True
                    self.score = 100
                    self.violation_reason = f"NGU GAT ({duration:.1f}s)"
                    
        # trường hợp 2: có ít nhất một bên mắt mở (hoặc cả 2 mắt mở bình thường)
        else:
            if self.is_eye_closed:
                blink_duration = current_time - self.eye_closed_time
                self.is_eye_closed = False
                
                # NẾU VỪA MỞ MẮT SAU KHI BỊ BÁO ĐỘNG NGỦ GẬT:
                if self.is_sleeping:
                    self.is_sleeping = False
                    self.score = Config.WARNING_LEVEL_1 # hạ ngay về 30 để còi tắt tức thì
                    self.violation_reason = "DA MO MAT"
                else:
                    self._evaluate_blink_speed(blink_duration)

    def _evaluate_blink_speed(self, duration):
        # Lọc và đánh giá tốc độ chớp mắt siêu nhạy
        if Config.NORMAL_BLINK_MIN_TIME <= duration <= Config.NORMAL_BLINK_MAX_TIME:
            # chớp mắt khỏe mạnh tự nhiên: trừ ngay 5 điểm hồi phục
            self.score = max(0, self.score - Config.SCORE_RECOVERY)
            self.slow_blink_count = 0
            if self.score <= Config.WARNING_LEVEL_1 and (self.violation_reason.startswith("DA ") or self.violation_reason.startswith("NHAM")):
                self.violation_reason = ""
        elif Config.SLOW_BLINK_TIME <= duration < Config.MICROSLEEP_TIME:
            # chớp mắt chậm mệt mỏi: cộng SCORE_SLOW_BLINK (20 điểm) và hiển thị thời lượng
            self.score = min(Config.SCORE_MAX, self.score + Config.SCORE_SLOW_BLINK)
            self.slow_blink_count += 1
            self.violation_reason = f"CHOP MAT CHAM ({duration:.2f}s)"

    def update_mouth(self, mar, current_time=None):
        """
        Nhận tỉ lệ mở miệng MAR:
        - Đang há miệng chưa đủ 1.5s: hiển thị DANG NGAP (x.xs) để người dùng thấy thời gian thực.
        - Đủ đúng 1.5s: Kích hoạt cảnh báo NGAP ngay lập tức!
        - Ngậm miệng lại: tắt cảnh báo tức thì.
        """
        if current_time is None:
            current_time = time.time()
        
        self.confirmed_yawns = [t for t in self.confirmed_yawns if (current_time - t) <= Config.YAWN_COUNT_WINDOW]

        # mức ngáp (sâu hoặc nhẹ)
        if mar > Config.MAR_DEEP_YAWN:
            if self.yawn_candidate_start == 0:
                self.yawn_candidate_start = current_time
            elapsed = current_time - self.yawn_candidate_start
            
            if elapsed < Config.LIGHT_YAWN_MIN_TIME:
                self.violation_reason = f"DANG NGAP ({elapsed:.1f}s)"
            else:
                # Đủ 1.5s là kích hoạt cảnh báo ngay!
                if not self.is_yawning:
                    self.is_yawning = True
                    self.yawn_alert_triggered = False
                    self.score = max(self.score, 60)
                    self.confirmed_yawns.append(current_time)
                
                if elapsed >= Config.DEEP_YAWN_TIME:
                    self.score = min(Config.SCORE_MAX, self.score + Config.SCORE_DEEP_YAWN)
                    self.violation_reason = f"NGAP SAU ({elapsed:.1f}s)"
                else:
                    self.violation_reason = f"NGAP ({elapsed:.1f}s)"

        elif mar > Config.MAR_LIGHT_YAWN:
            if self.yawn_candidate_start == 0:
                self.yawn_candidate_start = current_time
            elapsed = current_time - self.yawn_candidate_start

            if elapsed < Config.LIGHT_YAWN_MIN_TIME:
                self.violation_reason = f"DANG NGAP ({elapsed:.1f}s)"
            else:
                # Đủ đúng 1.5s là cảnh báo ngay lập tức!
                if not self.is_yawning:
                    self.is_yawning = True
                    self.yawn_alert_triggered = False
                    self.score = max(self.score, 60)
                    self.confirmed_yawns.append(current_time)
                    
                    if len(self.confirmed_yawns) >= Config.YAWN_REPEAT_WARNING:
                        self.score = 100
                        self.violation_reason = "NGAP LIEN TUC"
                    else:
                        self.violation_reason = f"NGAP ({elapsed:.1f}s)"
                else:
                    if len(self.confirmed_yawns) >= Config.YAWN_REPEAT_WARNING:
                        self.violation_reason = "NGAP LIEN TUC"
                    else:
                        self.violation_reason = f"NGAP ({elapsed:.1f}s)"

        # miệng đóng lại / nói chuyện bình thường
        else:
            if self.is_yawning:
                # TÀI XẾ ĐÃ NGẬM MIỆNG LẠI:
                self.is_yawning = False
                self.yawn_alert_triggered = True
                self.score = min(self.score, 30) # hạ điểm an toàn
                self.violation_reason = "DA HET NGAP"
            elif self.violation_reason.startswith("DANG NGAP"):
                self.violation_reason = ""
            self.yawn_candidate_start = 0
    def update_head(self, pitch_angle, current_time=None):
        if current_time is None:
            current_time = time.time()

        if pitch_angle > Config.HEAD_DROP_ANGLE:
            if not self.is_head_dropped:
                self.is_head_dropped = True
                self.head_drop_start_time = current_time

            if self.is_eye_closed:
                self.update_head_closed_eyes(current_time)
            else:
                self.update_head_open_eyes(current_time)
        else:
            was_head_dropped = (
                self.is_head_dropped or self.is_active_head_drop
            )

            self.head_drop_start_time = 0
            self.head_open_start_time = None
            self.head_closed_start_time = None

            self.is_head_dropped = False
            self.is_head_open_eyes = False
            self.is_head_closed_eyes = False
            self.is_active_head_drop = False

            if was_head_dropped and not self.is_sleeping:
                self.score = min(self.score, 25)
                self.violation_reason = "DA NGAN DAU"

    def update_head_open_eyes(self, current_time=None):
        if current_time is None:
            current_time = time.time()

        if self.head_open_start_time is None:
            self.head_open_start_time = current_time

        self.head_closed_start_time = None

        self.is_head_open_eyes = True
        self.is_head_closed_eyes = False
        self.is_active_head_drop = False

        elapsed = current_time - self.head_open_start_time

        self.violation_reason = (
            f"CUI DAU - MAT MO ({elapsed:.1f}s)"
        )

        if not self.is_sleeping:
            self.score = min(self.score, 30)

    def update_head_closed_eyes(self, current_time=None):
        if current_time is None:
            current_time = time.time()

        if self.head_closed_start_time is None:
            self.head_closed_start_time = current_time

        self.head_open_start_time = None

        self.is_head_open_eyes = False
        self.is_head_closed_eyes = True

        elapsed = current_time - self.head_closed_start_time

        if elapsed >= Config.HEAD_EYES_CLOSED_TIME:
            self.is_active_head_drop = True
            self.score = 100

            self.violation_reason = (
                f"GUC DAU (NHAM MAT) ({elapsed:.1f}s)"
            )
        else:
            self.is_active_head_drop = False

            if not self.is_sleeping:
                self.violation_reason = (
                    f"CUI DAU - NHAM MAT ({elapsed:.1f}s)"
                )

    def on_face_lost(self, current_time=None):
      """Xử lý khi mất dấu khuôn mặt."""
      self.head_drop_start_time = 0
      self.head_open_start_time = None
      self.head_closed_start_time = None

      self.is_head_dropped = False
      self.is_head_open_eyes = False
      self.is_head_closed_eyes = False
      self.is_active_head_drop = False

    def apply_decay(self, current_time=None):
         """Giảm dần điểm số theo thời gian thực."""
         if current_time is None:
            current_time = time.time()

         if (not self.is_eye_closed and not self.is_sleeping and
            not self.is_yawning and not self.is_active_head_drop
            and not self.is_head_dropped):

            elapsed = current_time - self.last_decay_time

            if elapsed >= Config.SCORE_DECAY_INTERVAL:
                steps = int(elapsed / Config.SCORE_DECAY_INTERVAL)

                self.score = max(
                    Config.SCORE_MIN,
                    self.score - steps * Config.SCORE_DECAY_AMOUNT
                )

                self.last_decay_time = current_time

                if (self.score <= Config.WARNING_LEVEL_1
                    and self.violation_reason.startswith("DA ")):
                    self.violation_reason = ""

    def get_status(self):
        # chốt điểm số trong khoảng 0-100
        self.score = max(Config.SCORE_MIN, min(Config.SCORE_MAX, self.score))
        
        # Xác định trạng thái cảnh báo
        should_alert = False
        if self.is_active_hazard:
            should_alert = True
        elif self.is_yawning and not self.yawn_alert_triggered:
            should_alert = True
        elif self.score >= Config.WARNING_LEVEL_3:
            should_alert = True

        # Đánh giá cấp độ cảnh báo
        if self.score < Config.WARNING_LEVEL_1:
            return "Normal", (0, 255, 0), should_alert, self.violation_reason
        elif self.score < Config.WARNING_LEVEL_2:
            return "Tired", (0, 255, 255), should_alert, self.violation_reason
        elif self.score < Config.WARNING_LEVEL_3:
            return "Warning", (0, 165, 255), should_alert, self.violation_reason
        else:
            return "Danger", (0, 0, 255), should_alert, self.violation_reason

    def reset(self):
        """Reset trạng thái và điểm về 0 khi kết thúc hoàn toàn phiên vi phạm."""
        self.score = 0
        self.violation_reason = ""

        self.eye_closed_time = 0
        self.is_eye_closed = False
        self.slow_blink_count = 0
        self.is_sleeping = False
        
        self.yawn_start_time = 0
        self.yawn_candidate_start = 0
        self.is_yawning = False
        self.yawn_alert_triggered = False
        self.confirmed_yawns = []
        self.last_yawn_time = 0
        
        self.head_drop_start_time = 0
        self.head_closed_start_time = None
        self.is_head_dropped = False
        self.is_active_head_drop = False