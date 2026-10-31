# fatigue_manager.py (bộ não xử lý)
#    - Chức năng: Quản lý bộ nhớ trạng thái và tính toán điểm số buồn ngủ (0-100).
#    - Ý nghĩa: Đóng vai trò là "Bộ não". File này nhận số liệu từ `utils.py`, đối 
#      chiếu với luật lệ ở `config.py` để theo dõi hành vi theo thời gian (ví dụ: đếm
#      số lần ngáp, đo thời gian nhắm mắt liên tục). Từ đó chốt điểm số và xuất ra 
#      trạng thái cuối cùng (Normal, Tired, Warning, Danger).

import time
from config import Config
from canhbao import WarningLogger


# 2. quản lý trạng thái 
class FatigueManager:
    def __init__(self, warning_logger=None):
        self.score = 0
        self.violation_reason = "" # biến lưu trữ lý do vi phạm
        
        # mắt
        self.eye_closed_time = 0 # lưu lại thời gian tài xế nhắm mắt 
        self.is_eye_closed = False # đánh dấu trạng thái mắt: True là cả 2 mắt đang nhắm
        self.slow_blink_count = 0 # đếm số lần chớp mắt chậm liên tiếp 
        self.is_sleeping = False # cờ đánh dấu đang ngủ gật (nhắm mắt >= 1.5s)
        self.sleep_warning_logged = False # cờ ghi log cho sự kiện ngủ gật
        
        # miệng
        self.yawn_start_time = 0 # lưu lại thời gian khi tài xế há miệng to
        self.yawn_candidate_start = 0 # mốc thời gian bắt đầu vượt ngưỡng để lọc nhiễu
        self.is_yawning = False # đánh dấu đang trong một đợt ngáp hợp lệ (đã đủ 3s)
        self.yawn_alert_triggered = False # cờ chống lặp cảnh báo ngáp bất tận
        self.yawn_warning_logged = False # cờ đảm bảo chỉ ghi 1 lần cảnh báo vàng cho mỗi đợt ngáp
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
        self.head_drop_warning_logged = False # cờ ghi log cho sự kiện gục đầu nhắm mắt

        # Quản lý file cảnh báo
        if warning_logger is not None:
            self.warning_logger = warning_logger
        else:
            self.warning_logger = WarningLogger(
                log_file=Config.WARNING_LOG_FILE,
                text_log_file=Config.WARNING_TEXT_LOG_FILE
            )

        self.is_yellow_red_alert = False # cờ đánh dấu trạng thái Cảnh Báo Đỏ do tích lũy 5 cảnh báo vàng
        self.yellow_red_alert_start_time = 0.0 # mốc thời gian kích hoạt Cảnh Báo Đỏ (5 vàng -> đỏ)
        self.slow_blink_until = 0.0 # mốc thời gian giữ hiển thị cảnh báo vàng chớp mắt chậm

        # cơ chế giảm điểm (decay) thời gian thực
        now = time.time()
        self.last_safe_time = now
        self.last_decay_time = now

    @property
    def is_active_hazard(self):
        """Trả về True nếu ngay tại thời điểm này tài xế đang ngủ gật hoặc đang gục đầu nhắm mắt."""
        return self.is_sleeping or self.is_active_head_drop

    def _check_and_trigger_yellow_to_red(self, current_time):
        """
        QUY TẮC:
        1. 5 cảnh báo vàng trong 10p tương đương cảnh báo đỏ và phát âm thanh.
        2. Sau khi đạt 5 mức cảnh báo vàng thì sẽ reset biến đếm đó về 0.
        """
        count = self.warning_logger.count_yellow_warnings_in_window(
            window_seconds=Config.YELLOW_WARNING_WINDOW,
            current_time=current_time
        )
        if count >= Config.YELLOW_TO_RED_COUNT:
            self.is_yellow_red_alert = True
            self.yellow_red_alert_start_time = current_time
            self.score = 100
            self.violation_reason = f"CANH BAO DO (DAT {count} LAN VANG/10P)"

            # Ghi nhận cảnh báo đỏ vào file cảnh báo
            self.warning_logger.log_warning(
                warning_type="RED",
                score=100,
                reason=self.violation_reason,
                timestamp=current_time
            )
            print(f"🚨 [CẢNH BÁO ĐỎ] Đã đạt {count} mức cảnh báo vàng! Kích hoạt CẢNH BÁO ĐỎ và phát âm thanh.")

            # Sau khi đạt 5 cảnh báo vàng: RESET BIẾN ĐẾM ĐÓ VỀ 0
            self.warning_logger.reset_yellow_counter(current_time)

    @property
    def is_driver_alert(self):
        """
        Trả về True nếu tài xế đang hoàn toàn tỉnh táo:
        - Mắt mở bình thường (không nhắm, không ngủ gật)
        - Miệng bình thường (không ngáp, không đang há miệng ngáp)
        - Đầu ở tư thế bình thường (không cúi, không gục đầu)
        - Không đang trong đợt cảnh báo đỏ do tích lũy 5 cảnh báo vàng
        """
        return (
            not self.is_eye_closed and
            not self.is_sleeping and
            not self.is_yawning and
            self.yawn_candidate_start == 0 and
            not self.is_head_dropped and
            not self.is_active_head_drop and
            not self.is_yellow_red_alert
        )

    def _reset_score_if_alert(self):
        """QUY TẮC: Mỗi lần tỉnh táo thì sẽ lập tức trở về 0đ."""
        if self.is_driver_alert:
            self.score = 0

    def update_eyes(self, ear_data, current_time=None):
        """
        Nhận ear_data: tuple (ear_left, ear_right, ear_avg) hoặc float đơn lẻ.
        Hiển thị thời gian nhắm mắt từng 0.1s (VD: NHAM MAT (0.5s), NHAM MAT (1.2s)...).
        Đúng 1.5s kích hoạt ngay NGU GAT (1.5s) và hú còi.
        Khi mở mắt tỉnh táo: lập tức trở về 0đ.
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

                    if not self.sleep_warning_logged:
                        self.sleep_warning_logged = True
                        self.warning_logger.log_warning(
                            warning_type="RED",
                            score=100,
                            reason=self.violation_reason,
                            timestamp=current_time
                        )
                        print(f"🚨 [CẢNH BÁO ĐỎ] Phát hiện NGỦ GẬT ({duration:.1f}s)! Điểm: 100")
                    
        # trường hợp 2: có ít nhất một bên mắt mở (hoặc cả 2 mắt mở bình thường)
        else:
            if self.is_eye_closed:
                blink_duration = current_time - self.eye_closed_time
                self.is_eye_closed = False
                self.eye_closed_time = 0
                self.sleep_warning_logged = False
                
                # NẾU VỪA MỞ MẮT SAU KHI BỊ BÁO ĐỘNG NGỦ GẬT HOẶC GỤC ĐẦU NHẮM MẮT:
                if self.is_sleeping or self.is_active_head_drop:
                    self.is_sleeping = False
                    self.is_active_head_drop = False
                    self.is_yellow_red_alert = False
                    self.violation_reason = "DA MO MAT"
                    # Mở mắt tỉnh táo -> lập tức trở về 0đ
                    if not self.is_yawning:
                        self.score = 0
                    self._reset_score_if_alert()
                else:
                    self._evaluate_blink_speed(blink_duration, current_time)
            else:
                # Cả hai mắt đang mở bình thường
                if current_time >= self.slow_blink_until:
                    if self.violation_reason.startswith("CHOP MAT CHAM"):
                        self.violation_reason = ""
                    self._reset_score_if_alert()

    def _evaluate_blink_speed(self, duration, current_time=None):
        if current_time is None:
            current_time = time.time()

        # Chớp mắt bình thường: tài xế tỉnh táo -> lập tức trở về 0đ!
        if Config.NORMAL_BLINK_MIN_TIME <= duration <= Config.NORMAL_BLINK_MAX_TIME:
            self.slow_blink_count = 0
            self.slow_blink_until = 0.0
            self.violation_reason = ""
            self._reset_score_if_alert()
        elif Config.SLOW_BLINK_TIME <= duration < Config.MICROSLEEP_TIME:
            # QUY TẮC: Chớp mắt chậm tính là 60 điểm, tương đương Cảnh Báo Vàng!
            blink_score = getattr(Config, 'SCORE_SLOW_BLINK', 60)
            self.score = max(self.score, blink_score)
            self.slow_blink_count += 1
            self.slow_blink_until = current_time + 2.0 # Giữ trạng thái cảnh báo vàng trong 2 giây nếu không có vi phạm mới
            self.violation_reason = f"CHOP MAT CHAM ({duration:.2f}s)"

            # Ghi nhận cảnh báo vàng vào file cảnh báo
            self.warning_logger.log_warning(
                warning_type="YELLOW",
                score=self.score,
                reason=self.violation_reason,
                timestamp=current_time
            )
            print(f"⚠️ [Cảnh Báo Vàng] Đã ghi nhận CHỚP MẮT CHẬM ({duration:.2f}s) vào file cảnh báo. Điểm: {self.score}")

            # Kiểm tra: nếu đạt đủ 5 cảnh báo vàng -> kích hoạt Cảnh Báo Đỏ và reset biến đếm
            self._check_and_trigger_yellow_to_red(current_time)

    def update_mouth(self, mar, current_time=None):
        """
        Cơ chế ngáp: CHỈ CÒN NGÁP SÂU, KHÔNG CÒN NGÁP NHẸ (Đồng bộ theo Config).
        1. Khi ngáp ở mức MAR >= ngưỡng trong Config (ví dụ 0.70) trên thời gian Config (3s):
           xác nhận NGAP SAU và bị tính điểm (60đ - Cảnh báo vàng).
           Trong lúc há miệng chưa đủ thời gian: hiển thị DANG NGAP ({elapsed:.1f}s), chưa bị tính điểm phạt.
        2. Mỗi lần ngậm miệng tỉnh táo: lập tức trở về 0đ.
        3. Ghi nhận sự kiện cảnh báo vàng vào file cảnh báo để theo dõi giới hạn 10 phút.
        """
        if current_time is None:
            current_time = time.time()
        
        self.confirmed_yawns = [t for t in self.confirmed_yawns if (current_time - t) <= Config.YAWN_COUNT_WINDOW]

        # Đồng bộ các ngưỡng từ Config
        yawn_mar_threshold = getattr(Config, 'MAR_LIGHT_YAWN', getattr(Config, 'MAR_DEEP_YAWN', 0.70))
        yawn_time_threshold = getattr(Config, 'YAWN_CONFIRM_TIME', getattr(Config, 'DEEP_YAWN_TIME', 3.00))
        yawn_score_value = getattr(Config, 'SCORE_YAWN', getattr(Config, 'SCORE_LIGHT_YAWN', getattr(Config, 'SCORE_DEEP_YAWN', 60)))

        # Kiểm tra miệng mở ở mức ngáp sâu (MAR >= ngưỡng Config)
        if mar >= yawn_mar_threshold:
            if self.yawn_candidate_start == 0:
                self.yawn_candidate_start = current_time
            elapsed = current_time - self.yawn_candidate_start
            
            if elapsed < yawn_time_threshold:
                # Há miệng dưới thời gian quy định (ví dụ 3 giây): hiển thị tiến trình, CHƯA BỊ TÍNH ĐIỂM
                self.violation_reason = f"DANG NGAP ({elapsed:.1f}s)"
            else:
                # Ngáp sâu vượt ngưỡng thời gian: BỊ TÍNH ĐIỂM (NGÁP SÂU)
                self.is_yawning = True
                self.score = max(self.score, yawn_score_value)
                self.violation_reason = f"NGAP SAU ({elapsed:.1f}s)"

                # Ghi nhận cảnh báo vàng vào file cảnh báo (chỉ ghi 1 lần cho đợt ngáp này)
                if not self.yawn_warning_logged:
                    self.yawn_warning_logged = True
                    self.confirmed_yawns.append(current_time)
                    self.warning_logger.log_warning(
                        warning_type="YELLOW",
                        score=self.score,
                        reason=f"NGAP SAU ({elapsed:.1f}s)",
                        timestamp=current_time
                    )
                    print(f"⚠️ [Cảnh Báo Vàng] Đã ghi nhận NGÁP SÂU >= {yawn_mar_threshold} trên {yawn_time_threshold}s vào file cảnh báo. Điểm: {self.score}")

                    # Kiểm tra: nếu đạt đủ 5 cảnh báo vàng -> kích hoạt Cảnh Báo Đỏ và reset biến đếm
                    self._check_and_trigger_yellow_to_red(current_time)

        # Tài xế đã ngậm miệng lại (MAR < ngưỡng Config)
        else:
            was_yawning_event = self.is_yawning or (self.yawn_candidate_start > 0)
            self.is_yawning = False
            self.yawn_candidate_start = 0
            self.yawn_warning_logged = False
            self.is_yellow_red_alert = False

            if was_yawning_event:
                # TÀI XẾ ĐÃ NGẬM MIỆNG TỈNH TÁO: Lập tức trở về 0đ!
                self.violation_reason = ""
                self._reset_score_if_alert()
            elif self.violation_reason.startswith("DANG NGAP"):
                self.violation_reason = ""
                self._reset_score_if_alert()

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

            if was_head_dropped:
                # Ngẩng đầu tỉnh táo: lập tức trở về 0đ
                self.head_drop_warning_logged = False
                self.violation_reason = ""
                if not self.is_sleeping and not self.is_yawning and not self.is_yellow_red_alert and current_time >= self.slow_blink_until:
                    self.score = 0
                self._reset_score_if_alert()

    def update_head_open_eyes(self, current_time=None):
        if current_time is None:
            current_time = time.time()

        if self.head_open_start_time is None:
            self.head_open_start_time = current_time

        self.head_closed_start_time = None

        self.is_head_open_eyes = True
        self.is_head_closed_eyes = False
        self.is_active_head_drop = False
        self.head_drop_warning_logged = False

        elapsed = current_time - self.head_open_start_time
        self.violation_reason = f"CUI DAU - MAT MO ({elapsed:.1f}s)"

        if not self.is_sleeping and not self.is_yawning and not self.is_yellow_red_alert and current_time >= self.slow_blink_until:
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

        # QUY TẮC: Gục đầu nhắm mắt cùng lúc thì cảnh báo đỏ (score = 100, status = Danger, hú còi)
        if elapsed >= Config.HEAD_EYES_CLOSED_TIME:
            self.is_active_head_drop = True
            self.score = 100
            self.violation_reason = f"GUC DAU (NHAM MAT) ({elapsed:.1f}s)"

            if not self.head_drop_warning_logged:
                self.head_drop_warning_logged = True
                self.warning_logger.log_warning(
                    warning_type="RED",
                    score=100,
                    reason=self.violation_reason,
                    timestamp=current_time
                )
                print(f"🚨 [CẢNH BÁO ĐỎ] Phát hiện GỤC ĐẦU NHẮM MẮT CÙNG LÚC ({elapsed:.1f}s)! Điểm: 100")
        else:
            self.is_active_head_drop = False
            if not self.is_sleeping:
                self.violation_reason = f"CUI DAU - NHAM MAT ({elapsed:.1f}s)"

    def on_face_lost(self, current_time=None):
        """Xử lý khi mất dấu khuôn mặt: ngắt ngay các bộ đếm nhắm mắt/ngáp/gục đầu."""
        self.eye_closed_time = 0
        self.is_eye_closed = False
        self.yawn_candidate_start = 0
        self.is_yawning = False
        self.yawn_warning_logged = False
        self.sleep_warning_logged = False
        self.head_drop_warning_logged = False
        self.is_yellow_red_alert = False
        self.yellow_red_alert_start_time = 0.0
        self.slow_blink_until = 0.0

        self.head_drop_start_time = 0
        self.head_open_start_time = None
        self.head_closed_start_time = None

        self.is_head_dropped = False
        self.is_head_open_eyes = False
        self.is_head_closed_eyes = False
        self.is_active_head_drop = False

    def apply_decay(self, current_time=None):
        """Mỗi lần tỉnh táo thì sẽ lập tức trở về 0đ."""
        if current_time is None:
            current_time = time.time()

        if self.is_driver_alert and current_time >= self.slow_blink_until:
            self.score = 0
            if self.violation_reason.startswith("DA ") or self.violation_reason.startswith("CHOP MAT CHAM"):
                self.violation_reason = ""

    def get_status(self, current_time=None):
        """
        Xác định trạng thái và cấp độ cảnh báo:
        QUY TẮC CỐT LÕI:
        1. CẢNH BÁO VÀNG KHÔNG CẦN PHÁT ÂM THANH (should_alert = False).
        2. CHỈ CẢNH BÁO ĐỎ MỚI PHÁT ÂM THANH (should_alert = True khi status == 'Danger').
        3. Sau khi đạt 5 mức cảnh báo vàng thì kích hoạt Cảnh Báo Đỏ và reset biến đếm.
        4. Mỗi lần tỉnh táo: điểm lập tức trở về 0đ.
        """
        if current_time is None:
            current_time = time.time()

        # Tự động giải tỏa Cảnh Báo Đỏ sau khi còi hú đủ thời gian (ALERT_MAX_DURATION) và tài xế đã tỉnh táo
        if self.is_yellow_red_alert:
            alert_max_dur = getattr(Config, 'ALERT_MAX_DURATION', 3.0)
            if (current_time - self.yellow_red_alert_start_time) >= alert_max_dur:
                if not self.is_active_hazard and not self.is_yawning:
                    self.is_yellow_red_alert = False
                    self.score = 0
                    self.violation_reason = ""

        # Đảm bảo điểm số luôn trong khoảng 0-100
        self.score = max(Config.SCORE_MIN, min(Config.SCORE_MAX, self.score))

        # Kiểm tra trạng thái Cảnh Báo Đỏ (Danger):
        # 1. Đang ngủ gật (nhắm mắt >= 1.5s) hoặc gục đầu nhắm mắt (>= 2.0s)
        # 2. Đang trong đợt Cảnh Báo Đỏ do đạt 5 cảnh báo vàng (is_yellow_red_alert)
        # 3. Điểm số vượt ngưỡng nguy hiểm (score >= WARNING_LEVEL_3, tức >= 85)
        is_danger_alert = (
            self.is_active_hazard or
            self.is_yellow_red_alert or
            self.score >= Config.WARNING_LEVEL_3
        )

        if is_danger_alert:
            # CHỈ CẢNH BÁO ĐỎ MỚI PHÁT ÂM THANH:
            status = "Danger"
            color = (0, 0, 255) # Đỏ
            should_alert = True
            return status, color, should_alert, self.violation_reason

        # QUY TẮC: CẢNH BÁO VÀNG (hoặc Normal/Tired) TUYỆT ĐỐI KHÔNG PHÁT ÂM THANH:
        should_alert = False

        if self.score < Config.WARNING_LEVEL_1:
            return "Normal", (0, 255, 0), should_alert, self.violation_reason
        elif self.score < Config.WARNING_LEVEL_2:
            return "Tired", (0, 255, 255), should_alert, self.violation_reason
        else:
            # Mức điểm từ WARNING_LEVEL_2 (60đ) đến dưới WARNING_LEVEL_3 (85đ): Cảnh Báo Vàng
            # Ví dụ: ngáp sâu trên 3s = 60đ, chớp mắt chậm = 60đ
            # Màu Vàng: (0, 255, 255) trong OpenCV BGR
            # KHÔNG PHÁT ÂM THANH: should_alert = False
            return "Warning", (0, 255, 255), should_alert, self.violation_reason

    def reset(self):
        """Reset trạng thái và điểm về 0 khi kết thúc hoàn toàn phiên vi phạm."""
        self.score = 0
        self.violation_reason = ""
        self.is_yellow_red_alert = False
        self.yellow_red_alert_start_time = 0.0
        self.slow_blink_until = 0.0

        self.eye_closed_time = 0
        self.is_eye_closed = False
        self.slow_blink_count = 0
        self.is_sleeping = False
        
        self.yawn_start_time = 0
        self.yawn_candidate_start = 0
        self.is_yawning = False
        self.yawn_alert_triggered = False
        self.yawn_warning_logged = False
        self.confirmed_yawns = []
        self.last_yawn_time = 0
        
        self.head_drop_start_time = 0
        self.head_closed_start_time = None
        self.is_head_dropped = False
        self.is_active_head_drop = False
        self.sleep_warning_logged = False
        self.head_drop_warning_logged = False