"""
Bộ kiểm thử hồi quy (Regression & Business Logic Tests) cho TEST_YOLO
Bao gồm:
- Tái hiện và xử lý lỗi P0 (UT-01 .. UT-08)
- Xử lý nháy 1 mắt (không báo ngủ gật khi 1 mắt mở)
- Gục đầu mắt mở -> chỉ hiện reason, KHÔNG CẢNH BÁO
- Gục đầu mắt nhắm -> CẢNH BÁO NGUY HIỂM 100 điểm
- Nhắm mắt có đếm giây thời gian thực: NHAM MAT (x.xs)
- Ngáp đúng 1.5s là kích hoạt cảnh báo
- Chớp mắt chậm siêu nhạy (từ 0.32s, +20 điểm)
"""

# pyrefly: ignore[missing-import]
import pytest
from config import Config
from fatigue_manager import FatigueManager


def test_light_yawn_filtered_when_too_short():
    """UT-01: Há miệng nhanh 0.1s (nói chuyện/nhai) không được kích hoạt cảnh báo."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_mouth(0.75, current_time=t0)
    assert fm.score == 0
    assert fm.is_yawning is False

    fm.update_mouth(0.30, current_time=t0 + 0.5)
    assert fm.score == 0
    assert fm.is_yawning is False


def test_light_yawn_confirmed_and_alerts_at_1_5s():
    """YÊU CẦU: Ngáp đúng 1.5s là cảnh báo ngay lập tức."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_mouth(0.72, current_time=t0)
    # 1.0s: đang há miệng, chưa báo
    fm.update_mouth(0.72, current_time=t0 + 1.0)
    assert fm.is_yawning is False
    assert "DANG NGAP" in fm.violation_reason

    # Đúng 1.5s - 1.6s: Kích hoạt cảnh báo ngáp ngay!
    fm.update_mouth(0.72, current_time=t0 + 1.6)
    assert fm.is_yawning is True
    status, color, should_alert, reason = fm.get_status()
    assert should_alert is True
    assert "NGAP" in fm.violation_reason


def test_rapid_mouth_openings_not_counted_as_repeated_yawn():
    """UT-02: Há/ngậm miệng 3 lần nhanh trong 0.6s không được kích hoạt NGAP LIEN TUC."""
    fm = FatigueManager()
    t0 = 100.0
    for i in range(3):
        t = t0 + i * 0.2
        fm.update_mouth(0.75, current_time=t)
        fm.update_mouth(0.30, current_time=t + 0.1)

    assert fm.score == 0
    assert fm.violation_reason != "NGAP LIEN TUC"


def test_deep_yawn_confirmed():
    """UT-03: Ngáp sâu MAR > 0.85 kéo dài > 3s."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_mouth(0.90, current_time=t0)
    fm.update_mouth(0.90, current_time=t0 + 3.1)

    assert fm.is_yawning is True
    assert "NGAP SAU" in fm.violation_reason


def test_slow_blink_sensitive_adds_20_points():
    """UT-04: Chớp mắt chậm từ 0.32s trở lên đã kích hoạt siêu nhạy (+20 điểm)."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    assert fm.is_eye_closed is True

    # 0.40s mở mắt -> chớp mắt chậm siêu nhạy
    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 0.40)
    assert fm.score == Config.SCORE_SLOW_BLINK  # 20
    assert "CHOP MAT CHAM" in fm.violation_reason


def test_normal_blink_recovers_score():
    """UT-05: Chớp mắt bình thường 0.2s giúp giảm điểm hồi phục 5 điểm."""
    fm = FatigueManager()
    fm.score = 40
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 0.2)
    assert fm.score == 40 - Config.SCORE_RECOVERY


def test_closing_eyes_shows_realtime_countdown_timer():
    """YÊU CẦU: Nhắm mắt có đếm giây thời gian thực NHAM MAT (x.xs)."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_eyes((0.12, 0.12, 0.12), current_time=t0)
    assert fm.violation_reason == "NHAM MAT (0.0s)"

    # Nhắm 0.8s
    fm.update_eyes((0.12, 0.12, 0.12), current_time=t0 + 0.8)
    assert "NHAM MAT (0.8s)" in fm.violation_reason
    assert fm.is_sleeping is False

    # Đạt 1.6s -> Ngủ gật (100 điểm)
    fm.update_eyes((0.12, 0.12, 0.12), current_time=t0 + 1.6)
    assert "NGU GAT" in fm.violation_reason
    assert fm.is_sleeping is True
    assert fm.score == 100


def test_winking_one_eye_does_not_trigger_microsleep():
    """QUAN TRỌNG: Nhắm 1 mắt (mắt trái nhắm, mắt phải mở to) không được báo ngủ gật!"""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_eyes((0.10, 0.35, 0.225), current_time=t0)
    fm.update_eyes((0.10, 0.35, 0.225), current_time=t0 + 2.0)

    assert fm.is_sleeping is False
    assert fm.is_active_hazard is False
    assert fm.score < 100
    assert "NGU GAT" not in fm.violation_reason


def test_head_down_with_eyes_open_only_reason_no_alert():
    """YÊU CẦU: Cúi đầu mà mắt vẫn mở thì CHỈ HIỆN REASON, KHÔNG CẢNH BÁO."""
    fm = FatigueManager()
    t0 = 100.0
    # Mắt mở to
    fm.update_eyes((0.32, 0.32, 0.32), current_time=t0)
    # Cúi đầu kéo dài 2.1s
    fm.update_head(28.0, current_time=t0)
    fm.update_head(28.0, current_time=t0 + 2.1)

    # Hiển thị Reason rõ ràng
    assert "CUI DAU - MAT MO" in fm.violation_reason
    # NHƯNG TUYỆT ĐỐI KHÔNG CẢNH BÁO:
    assert fm.is_active_head_drop is False
    status, color, should_alert, reason = fm.get_status()
    assert should_alert is False
    assert fm.score <= 30


def test_head_down_with_eyes_closed_triggers_danger_alert():
    """YÊU CẦU: Gục đầu mà MẮT NHẮM thì MỚI CẢNH BÁO NGUY HIỂM 100 điểm."""
    fm = FatigueManager()
    t0 = 100.0
    # Mắt nhắm
    fm.update_eyes((0.12, 0.12, 0.12), current_time=t0)
    # Cúi đầu kéo dài 2.1s
    fm.update_head(28.0, current_time=t0)
    fm.update_head(28.0, current_time=t0 + 2.1)

    assert fm.is_active_head_drop is True
    assert fm.score == 100
    assert "GUC DAU (NHAM MAT)" in fm.violation_reason
    status, color, should_alert, reason = fm.get_status()
    assert should_alert is True


def test_face_lost_does_not_accumulate_into_sleep():
    """UT-07: Mất mặt 10s không bị ghép nối thành nhắm mắt 10s."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    fm.on_face_lost(current_time=t0 + 0.3)
    assert fm.is_eye_closed is False

    fm.update_eyes((0.30, 0.30, 0.30), current_time=t0 + 10.3)
    assert fm.score == 0
    assert fm.is_sleeping is False
    assert fm.is_active_hazard is False


def test_score_decay_fast_realtime_when_awake():
    """UT-08: Tỉnh táo 0.5s có decay mượt mà (giảm 3 điểm mỗi 0.5s)."""
    fm = FatigueManager()
    fm.score = 40
    t0 = 100.0
    fm.last_decay_time = t0

    fm.apply_decay(current_time=t0 + 0.6)
    assert fm.score == 40 - Config.SCORE_DECAY_AMOUNT  # 37


def test_opening_eyes_dismisses_emergency_immediately():
    """Kiểm thử tính nhạy: Ngủ gật nhưng khi MỞ MẮT RA còi phải tắt ngay."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0)
    fm.update_eyes((0.15, 0.15, 0.15), current_time=t0 + 1.6)

    assert fm.is_sleeping is True
    assert fm.is_active_hazard is True
    assert fm.score == 100

    # VỪA MỞ MẮT RA
    fm.update_eyes((0.32, 0.32, 0.32), current_time=t0 + 1.8)

    assert fm.is_sleeping is False
    assert fm.is_active_hazard is False
    assert fm.score <= Config.WARNING_LEVEL_1
    assert "DA MO MAT" in fm.violation_reason


def test_closing_mouth_prevents_yawn_alert_loop():
    """Chống lặp ngáp bất tận: Ngậm miệng lại thì is_yawning=False, score hạ an toàn."""
    fm = FatigueManager()
    t0 = 100.0
    fm.update_mouth(0.90, current_time=t0)
    fm.update_mouth(0.90, current_time=t0 + 3.1)
    status, color, should_alert, reason = fm.get_status()
    assert should_alert is True
    assert fm.is_yawning is True

    # Ngậm miệng lại (MAR = 0.25)
    fm.update_mouth(0.25, current_time=t0 + 4.0)
    assert fm.is_yawning is False
    status, color, should_alert, reason = fm.get_status()
    assert should_alert is False
    assert fm.score < Config.WARNING_LEVEL_3
