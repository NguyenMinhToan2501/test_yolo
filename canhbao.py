# canhbao.py - Quản lý dữ liệu và phát cảnh báo (Alert & Warning Management)
#    - Chức năng:
#      1. Ghi nhận và lưu trữ lịch sử các sự kiện cảnh báo (vàng, đỏ) vào file cảnh báo (JSON và TXT).
#      2. Phân tích dữ liệu cảnh báo theo thời gian (đếm số cảnh báo vàng trong 10 phút gần nhất).
#      3. Đưa ra quyết định nâng cấp cảnh báo: 5 cảnh báo vàng trong 10p tương đương cảnh báo đỏ và phát âm thanh.
#      4. Cung cấp chức năng tạo âm thanh cảnh báo bằng giọng nói AI (gTTS).

import json
import os
import time
from datetime import datetime


class WarningLogger:
    """Quản lý việc ghi nhật ký và đọc dữ liệu từ file cảnh báo."""

    def __init__(self, log_file="canh_bao_log.json", text_log_file="canh_bao_log.txt"):
        self.log_file = log_file
        self.text_log_file = text_log_file
        self.last_yellow_reset_time = 0.0

    def reset_yellow_counter(self, current_time=None):
        """
        QUY TẮC: Sau khi đạt 5 mức cảnh báo vàng thì sẽ reset biến đếm đó về 0.
        Đánh dấu các cảnh báo vàng cũ là đã tiêu thụ (consumed) và ghi log.
        """
        if current_time is None:
            current_time = time.time()
        self.last_yellow_reset_time = current_time

        history = self.get_all_warnings()
        updated = False
        for item in history:
            if item.get("type") == "YELLOW" and item.get("timestamp", 0) <= current_time:
                if not item.get("consumed", False):
                    item["consumed"] = True
                    updated = True

        if updated:
            try:
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[Cảnh Báo] Lỗi ghi file khi reset cảnh báo vàng: {e}")

        try:
            time_str = datetime.fromtimestamp(current_time).strftime("%d/%m/%Y %H:%M:%S")
            with open(self.text_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{time_str}] [HE THONG] Đạt 5 mức cảnh báo vàng -> Nâng cấp CẢNH BÁO ĐỎ và RESET biến đếm về 0.\n")
        except Exception:
            pass

        print(f"🔄 [Cảnh Báo] Đã reset biến đếm cảnh báo vàng về 0 tại mốc thời gian {current_time:.1f}.")

    def log_warning(self, warning_type, score, reason, timestamp=None):
        """
        Ghi nhận một sự kiện cảnh báo vào file cảnh báo (JSON và TXT).
        warning_type: "YELLOW" (cảnh báo vàng) hoặc "RED" (cảnh báo đỏ)
        score: Điểm buồn ngủ tại thời điểm cảnh báo
        reason: Lý do vi phạm (ví dụ: 'NGAP SAU (3.1s)', 'CHOP MAT CHAM', ...)
        """
        if timestamp is None:
            timestamp = time.time()

        time_str = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M:%S")
        entry = {
            "timestamp": round(timestamp, 3),
            "datetime": time_str,
            "type": warning_type.upper(),
            "score": score,
            "reason": reason,
            "consumed": False
        }

        # 1. Đọc dữ liệu cũ và ghi thêm vào file JSON
        history = self.get_all_warnings()
        history.append(entry)

        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Cảnh Báo] Lỗi khi ghi file cảnh báo JSON: {e}")

        # 2. Ghi nhật ký vào file TXT trực quan dễ xem
        try:
            type_label = "CANH BAO VANG" if warning_type.upper() == "YELLOW" else "CANH BAO DO"
            with open(self.text_log_file, "a", encoding="utf-8") as f:
                f.write(f"[{time_str}] [{type_label}] Diem: {score}/100 | Ly do: {reason}\n")
        except Exception as e:
            print(f"[Cảnh Báo] Lỗi khi ghi file cảnh báo TXT: {e}")

        return entry

    def get_all_warnings(self):
        """Đọc toàn bộ lịch sử từ file cảnh báo JSON."""
        if not os.path.exists(self.log_file):
            return []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except Exception:
            return []

    def get_recent_warnings(self, window_seconds=600.0, warning_type=None, current_time=None):
        """
        Lấy danh sách các cảnh báo trong khoảng thời gian window_seconds (mặc định 10 phút = 600s).
        Chỉ lấy các cảnh báo chưa bị tiêu thụ (consumed) và sau lần reset gần nhất.
        """
        if current_time is None:
            current_time = time.time()

        all_warnings = self.get_all_warnings()
        recent = []
        for item in all_warnings:
            t = item.get("timestamp", 0)
            is_consumed = item.get("consumed", False)
            if is_consumed or t <= self.last_yellow_reset_time:
                continue
            if (current_time - t) <= window_seconds:
                if warning_type is None or item.get("type") == warning_type.upper():
                    recent.append(item)
        return recent

    def count_yellow_warnings_in_window(self, window_seconds=600.0, current_time=None):
        """
        Đếm số lượng cảnh báo vàng xuất hiện trong khung thời gian (mặc định 10 phút = 600s).
        Chỉ đếm các cảnh báo vàng chưa bị tiêu thụ (chưa reset).
        """
        recent_yellow = self.get_recent_warnings(
            window_seconds=window_seconds,
            warning_type="YELLOW",
            current_time=current_time
        )
        return len(recent_yellow)

    def is_yellow_exceeded(self, max_allowed=5, window_seconds=600.0, current_time=None):
        """
        Kiểm tra nếu trong 10 phút đã có từ 5 cảnh báo vàng trở lên:
        Tương đương cảnh báo đỏ và cần phát âm thanh.
        """
        return self.count_yellow_warnings_in_window(window_seconds, current_time) >= max_allowed

    def clear_logs(self):
        """Xóa trắng file nhật ký cảnh báo (dùng khi kiểm thử hoặc reset dữ liệu)."""
        self.last_yellow_reset_time = 0.0
        if os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
            except Exception:
                pass
        if os.path.exists(self.text_log_file):
            try:
                os.remove(self.text_log_file)
            except Exception:
                pass


# Tạo instance mặc định
default_warning_logger = WarningLogger()


def log_warning(warning_type, score, reason, timestamp=None):
    """Hàm tiện ích ghi nhận cảnh báo vào file cảnh báo mặc định."""
    return default_warning_logger.log_warning(warning_type, score, reason, timestamp)


def count_recent_yellow_warnings(window_seconds=600.0, current_time=None):
    """Hàm tiện ích đếm số cảnh báo vàng trong 10 phút gần nhất từ file cảnh báo."""
    return default_warning_logger.count_yellow_warnings_in_window(window_seconds, current_time)


def is_yellow_exceeded(max_allowed=5, window_seconds=600.0, current_time=None):
    """Hàm tiện ích kiểm tra xem đã đủ 5 cảnh báo vàng trong 10p hay chưa."""
    return default_warning_logger.is_yellow_exceeded(max_allowed, window_seconds, current_time)


def generate_sound():
    """Tạo file âm thanh cảnh báo bằng gTTS nếu chạy trực tiếp script này."""
    try:
        # pyrefly: ignore[missing-import]
        from gtts import gTTS
        print("Đang tổng hợp giọng nói AI. Vui lòng chờ...")
        van_ban = "Cảnh báo! Phát hiện tài xế có dấu hiệu buồn ngủ. Yêu cầu tập trung lái xe ngay lập tức!"
        tts = gTTS(van_ban, lang='vi')
        tts.save("am_thanh_canh_bao.wav")
        print("Thành công! Đã tạo file am_thanh_canh_bao.wav")
    except Exception as e:
        print(f"Không thể tạo âm thanh gTTS: {e}")


if __name__ == "__main__":
    generate_sound()