"""
Bộ kiểm thử hồi quy (Regression & Business Logic Tests) cho TEST_YOLO
Bao gồm:
- Tái hiện và xử lý lỗi P0 (UT-01 .. UT-08)
- Xử lý nháy 1 mắt (không báo ngủ gật khi 1 mắt mở)
- Gục đầu mắt mở -> chỉ hiện reason, KHÔNG CẢNH BÁO
- Gục đầu mắt nhắm -> CẢNH BÁO NGUY HIỂM 100 điểm
- Nhắm mắt có đếm giây thời gian thực: NHAM MAT (x.xs)
- Cơ chế ngáp mới: chỉ còn ngáp sâu, MAR >= ngưỡng Config trên 3s tính 60đ (dưới 3s hiển thị DANG NGAP)
- Mỗi lần tỉnh táo (mở mắt, ngậm miệng, ngẩng đầu) lập tức trở về 0đ
- Cảnh báo vàng KHÔNG phát âm thanh (should_alert = False)
- Chỉ cảnh báo đỏ mới phát âm thanh (should_alert = True)
- Chớp mắt chậm tính là 60 điểm (tương đương cảnh báo vàng)
- Sau khi đạt 5 mức cảnh báo vàng thì kích hoạt Cảnh Báo Đỏ và reset biến đếm đó về 0
"""

# pyrefly: ignore[missing-import]
import pytest
from config import Config
from fatigue_manager import FatigueManager
from canhbao import WarningLogger


@pytest.fixture
def temp_warning_logger(tmp_path):
    """Tạo WarningLogger với file tạm để không làm bẩn dữ liệu thật."""
    log_json = str(tmp_path / "test_canh_bao_log.json")
    log_txt = str(tmp_path / "test_canh_bao_log.txt")
    return WarningLogger(log_file=log_json, text_log_file=log_txt)


def test_yawn_filtered_when_under_3s(temp_warning_logger):
    """YÊU CẦU: Há miệng MAR >= ngưỡng dưới 3s chưa bị tính điểm, hiển thị DANG NGAP."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    mar_val = getattr(Config, 'MAR_LIGHT_YAWN', 0.70) + 0.05
    fm.update_mouth(mar_val, current_time=t0)
    assert fm.score == 0
    assert fm.is_yawning is False

    # 1.5s: hiển thị DANG NGAP, chưa tính điểm (không còn ngáp nhẹ 1.5s)
    fm.update_mouth(mar_val, current_time=t0 + 1.5)
    assert fm.score == 0
    assert fm.is_yawning is False
    assert "DANG NGAP" in fm.violation_reason

    # 2.8s: vẫn đang trong tiến trình đếm
    fm.update_mouth(mar_val, current_time=t0 + 2.8)
    assert fm.score == 0
    assert fm.is_yawning is False

    # Ngậm miệng lại trước 3s -> tỉnh táo về 0đ
    fm.update_mouth(0.30, current_time=t0 + 2.9)
    assert fm.score == 0
    assert fm.is_yawning is False


def test_deep_yawn_confirmed_at_3s_calculates_60_points(temp_warning_logger):
    """YÊU CẦU: Ngáp ở mức >= ngưỡng Config (0.70) trên 3s thì bị tính 60đ."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    mar_val = getattr(Config, 'MAR_LIGHT_YAWN', 0.70) + 0.05
    fm.update_mouth(mar_val, current_time=t0)
    fm.update_mouth(mar_val, current_time=t0 + 1.5)
    assert fm.is_yawning is False
    assert "DANG NGAP" in fm.violation_reason

    # Đúng 3.0s: Xác nhận NGÁP SÂU, bị tính 60 điểm (Cảnh báo vàng)
    fm.update_mouth(mar_val, current_time=t0 + 3.1)
    assert fm.is_yawning is True
    assert fm.score == 60
    assert "NGAP SAU" in fm.violation_reason

    # Kiểm tra đã ghi vào file cảnh báo 1 sự kiện YELLOW
    assert temp_warning_logger.count_yellow_warnings_in_window(window_seconds=600.0, current_time=t0 + 3.1) == 1


def test_yellow_warning_does_not_play_sound(temp_warning_logger):
    """QUY TẮC MỚI: Cảnh báo vàng KHÔNG cần phát âm thanh (should_alert = False)."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    mar_val = getattr(Config, 'MAR_LIGHT_YAWN', 0.70) + 0.05
    fm.update_mouth(mar_val, current_time=t0)
    fm.update_mouth(mar_val, current_time=t0 + 3.1)

    assert fm.score == 60
    status, color, should_alert, reason = fm.get_status(current_time=t0 + 3.1)
    assert status == "Warning"  # Cảnh báo vàng
    assert color == (0, 255, 255)  # Màu vàng
    assert should_alert is False  # TUYỆT ĐỐI KHÔNG PHÁT ÂM THANH!


def test_slow_blink_calculates_60_points_and_is_yellow_warning(temp_warning_logger):
    """QUY TẮC MỚI: Khi chớp mắt chậm thì vẫn sẽ tính là 60 điểm, tương đương cảnh báo vàng."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    assert fm.is_eye_closed is True

    # Chớp mắt chậm 0.40s (> 0.32s) -> tính 60 điểm
    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 0.40)
    assert fm.score == 60
    assert "CHOP MAT CHAM" in fm.violation_reason

    # Cảnh báo vàng không phát âm thanh
    status, color, should_alert, reason = fm.get_status(current_time=t0 + 0.40)
    assert status == "Warning"
    assert should_alert is False

    # Đã được ghi nhận vào file cảnh báo là 1 cảnh báo vàng
    assert temp_warning_logger.count_yellow_warnings_in_window(window_seconds=600.0, current_time=t0 + 0.40) == 1


def test_yawn_mouth_close_resets_immediately_to_zero(temp_warning_logger):
    """YÊU CẦU: Mỗi lần tỉnh táo (ngậm miệng lại sau khi ngáp) thì lập tức trở về 0đ."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    mar_val = getattr(Config, 'MAR_LIGHT_YAWN', 0.70) + 0.05
    fm.update_mouth(mar_val, current_time=t0)
    fm.update_mouth(mar_val, current_time=t0 + 3.1)
    assert fm.score == 60
    assert fm.is_yawning is True

    # Ngậm miệng lại (MAR = 0.25) -> tỉnh táo: lập tức trở về 0đ!
    fm.update_mouth(0.25, current_time=t0 + 4.0)
    assert fm.is_yawning is False
    assert fm.score == 0
    assert fm.violation_reason == ""


def test_normal_blink_resets_to_zero_when_alert(temp_warning_logger):
    """YÊU CẦU: Chớp mắt sinh lý bình thường thể hiện tài xế tỉnh táo -> lập tức về 0đ."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    fm.score = 40  # Điểm số giả định trước đó
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 0.2)
    assert fm.score == 0


def test_opening_eyes_dismisses_emergency_and_resets_to_zero(temp_warning_logger):
    """YÊU CẦU: Ngủ gật nhưng khi MỞ MẮT RA còi tắt và điểm lập tức trở về 0đ."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0 + 1.6)

    assert fm.is_sleeping is True
    assert fm.is_active_hazard is True
    assert fm.score == 100

    # VỪA MỞ MẮT RA: Tài xế tỉnh táo -> lập tức trở về 0đ!
    fm.update_eyes((0.32, 0.32, 0.32), current_time=t0 + 1.8)

    assert fm.is_sleeping is False
    assert fm.is_active_hazard is False
    assert fm.score == 0
    assert "DA MO MAT" in fm.violation_reason


def test_head_up_resets_immediately_to_zero(temp_warning_logger):
    """YÊU CẦU: Ngẩng đầu lên tỉnh táo thì điểm lập tức về 0đ."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    # Mắt nhắm và cúi đầu 2.1s -> gục đầu 100đ
    fm.update_eyes((0.12, 0.12, 0.12), current_time=t0)
    fm.update_head(28.0, current_time=t0)
    fm.update_head(28.0, current_time=t0 + 2.1)
    assert fm.score == 100

    # Ngẩng đầu lên và mở mắt ra -> tỉnh táo -> lập tức về 0đ
    fm.update_eyes((0.35, 0.35, 0.35), current_time=t0 + 2.5)
    fm.update_head(5.0, current_time=t0 + 2.5)
    assert fm.score == 0


def test_score_resets_to_zero_when_awake_decay(temp_warning_logger):
    """YÊU CẦU: Khi tỉnh táo, cơ chế cập nhật lập tức đưa điểm về 0đ."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    fm.score = 40
    t0 = 100.0
    fm.apply_decay(current_time=t0 + 0.5)
    assert fm.score == 0


def test_winking_one_eye_does_not_trigger_microsleep(temp_warning_logger):
    """QUAN TRỌNG: Nháy 1 mắt (mắt trái nhắm, mắt phải mở to) không được báo ngủ gật!"""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    fm.update_eyes((0.10, 0.35, 0.225), current_time=t0)
    fm.update_eyes((0.10, 0.35, 0.225), current_time=t0 + 2.0)

    assert fm.is_sleeping is False
    assert fm.is_active_hazard is False
    assert fm.score < 100
    assert "NGU GAT" not in fm.violation_reason


def test_head_down_with_eyes_open_only_reason_no_alert(temp_warning_logger):
    """YÊU CẦU: Cúi đầu mà mắt vẫn mở thì CHỈ HIỆN REASON, KHÔNG CẢNH BÁO."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    fm.update_eyes((0.32, 0.32, 0.32), current_time=t0)
    fm.update_head(28.0, current_time=t0)
    fm.update_head(28.0, current_time=t0 + 2.1)

    assert "CUI DAU - MAT MO" in fm.violation_reason
    assert fm.is_active_head_drop is False
    status, color, should_alert, reason = fm.get_status()
    assert should_alert is False
    assert fm.score <= 30


def test_head_down_with_eyes_closed_triggers_danger_alert(temp_warning_logger):
    """YÊU CẦU: Gục đầu mà MẮT NHẮM thì MỚI CẢNH BÁO NGUY HIỂM 100 điểm (Cảnh báo đỏ)."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    fm.update_eyes((0.12, 0.12, 0.12), current_time=t0)
    fm.update_head(28.0, current_time=t0)
    fm.update_head(28.0, current_time=t0 + 2.1)

    assert fm.is_active_head_drop is True
    assert fm.score == 100
    assert "GUC DAU (NHAM MAT)" in fm.violation_reason
    status, color, should_alert, reason = fm.get_status()
    assert status == "Danger"
    assert color == (0, 0, 255)
    assert should_alert is True  # Chỉ Cảnh Báo Đỏ mới phát âm thanh!

    # Kiểm tra đã ghi nhận sự kiện CẢNH BÁO ĐỎ vào file cảnh báo
    all_warnings = temp_warning_logger.get_all_warnings()
    assert any(w.get("type") == "RED" and "GUC DAU" in w.get("reason", "") for w in all_warnings)


def test_face_lost_does_not_accumulate_into_sleep(temp_warning_logger):
    """UT-07: Mất mặt 10s không bị ghép nối thành nhắm mắt 10s."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    fm.on_face_lost(current_time=t0 + 0.3)
    assert fm.is_eye_closed is False

    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 10.3)
    assert fm.score == 0
    assert fm.is_sleeping is False
    assert fm.is_active_hazard is False


def test_5_yellow_warnings_triggers_red_alert_and_resets_counter(temp_warning_logger):
    """
    QUY TẮC:
    1. Trong 10p, 5 cảnh báo vàng sẽ tương đương cảnh báo đỏ và phát âm thanh.
    2. Sau khi đạt 5 mức cảnh báo vàng thì sẽ RESET biến đếm đó về 0.
    """
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 1000.0
    mar_val = getattr(Config, 'MAR_LIGHT_YAWN', 0.70) + 0.05

    # 4 lần cảnh báo vàng (ví dụ 4 lần ngáp sâu trên 3s, mỗi lần cách nhau 60s)
    for i in range(4):
        t_yawn = t0 + i * 60.0
        fm.update_mouth(mar_val, current_time=t_yawn)
        fm.update_mouth(mar_val, current_time=t_yawn + 3.1)
        assert fm.score == 60
        # Cảnh báo vàng: không phát âm thanh
        status, color, should_alert, reason = fm.get_status(current_time=t_yawn + 3.1)
        assert status == "Warning"
        assert should_alert is False

        # Ngậm miệng lại -> tỉnh táo về 0đ
        fm.update_mouth(0.25, current_time=t_yawn + 4.0)
        assert fm.score == 0

    # Kiểm tra biến đếm đang là 4 cảnh báo vàng
    assert temp_warning_logger.count_yellow_warnings_in_window(window_seconds=600.0, current_time=t0 + 250.0) == 4

    # Lần cảnh báo vàng thứ 5 (ngáp sâu thứ 5 tại t = t0 + 300s):
    t_5 = t0 + 300.0
    fm.update_mouth(mar_val, current_time=t_5)
    fm.update_mouth(mar_val, current_time=t_5 + 3.1)

    # ĐÁNH GIÁ 1: Đạt 5 cảnh báo vàng -> NÂNG CẤP THÀNH CẢNH BÁO ĐỎ VÀ PHÁT ÂM THANH!
    status, color, should_alert, reason = fm.get_status(current_time=t_5 + 3.1)
    assert status == "Danger"  # Cảnh báo Đỏ!
    assert color == (0, 0, 255)  # Màu Đỏ!
    assert should_alert is True  # Chỉ Cảnh Báo Đỏ mới phát âm thanh!
    assert "CANH BAO DO" in reason

    # ĐÁNH GIÁ 2: SAU KHI ĐẠT 5 CẢNH BÁO VÀNG -> BIẾN ĐẾM ĐÃ ĐƯỢC RESET VỀ 0!
    current_yellow_count = temp_warning_logger.count_yellow_warnings_in_window(window_seconds=600.0, current_time=t_5 + 3.1)
    assert current_yellow_count == 0  # Biến đếm đã reset về 0 hoàn hảo!


def test_slow_blink_holds_warning_and_normal_blink_clears(temp_warning_logger):
    """KIỂM TRA: Chớp mắt chậm giữ 60đ cảnh báo vàng trong 2s, chớp mắt bình thường lập tức giải tỏa về 0đ."""
    fm = FatigueManager(warning_logger=temp_warning_logger)
    t0 = 100.0
    # Chớp mắt chậm 0.40s
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 0.40)
    assert fm.score == 60
    assert "CHOP MAT CHAM" in fm.violation_reason

    # Khung hình kế tiếp (mắt mở bình thường sau 0.05s): Vẫn duy trì 60đ để hiển thị cho tài xế và camera
    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 0.45)
    fm.apply_decay(current_time=t0 + 0.45)
    assert fm.score == 60
    status, color, should_alert, reason = fm.get_status(current_time=t0 + 0.45)
    assert status == "Warning"
    assert should_alert is False

    # Tài xế chớp mắt bình thường (0.15s) -> tỉnh táo -> giải tỏa ngay về 0đ!
    t_normal = t0 + 0.60
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t_normal)
    fm.update_eyes((0.30, 0.30, 0.30), current_time=t_normal + 0.15)
    assert fm.score == 0
    assert fm.violation_reason == ""


