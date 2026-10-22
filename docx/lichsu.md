# NHẬT KÝ CHI TIẾT CÁC CẢI TIẾN & VÁ LỖI HỆ THỐNG TEST_YOLO
*(Lưu trữ tại `docx/lichsu.md` - Cập nhật ngày 22/10/2026)*

Tài liệu này ghi lại toàn bộ quá trình khảo sát, tái cấu trúc logic, sửa lỗi hành vi thực tế, bổ sung tính năng âm thanh giọng nói và kiểm thử tự động hóa cho hệ thống phát hiện tài xế ngủ gật & mất tập trung (`test_yolo`).

---

## MỤC LỤC
1. [Bối Cảnh & Vấn Đề Ban Đầu](#1-bối-cảnh--vấn-đề-ban-đầu)
2. [Thiết Lập Môi Trường Thực Thi](#2-thiết-lập-môi-trường-thực-thi)
3. [Chi Tiết Các Thay Đổi & Vá Lỗi Nghiệp Vụ](#3-chi-tiết-các-thay-đổi--vá-lỗi-nghiệp-vụ)
   - [3.1. Sửa lỗi nháy 1 mắt (Winking False Positive)](#31-sửa-lỗi-nháy-1-mắt-winking-false-positive)
   - [3.2. Cảnh báo nhắm mắt chuẩn 1.5s & Bộ đếm thời gian thực](#32-cảnh-báo-nhắm-mắt-chuẩn-15s--bộ-đếm-thời-gian-thực)
   - [3.3. Phân biệt Cúi đầu mắt mở vs Gục đầu mắt nhắm](#33-phân-biệt-cúi-đầu-mắt-mở-vs-gục-đầu-mắt-nhắm)
   - [3.4. Khắc phục triệt để lỗi lặp ngáp vô tận (Infinite Yawn Loop)](#34-khắc-phục-triệt-để-lỗi-lặp-ngáp-vô-tận-infinite-yawn-loop)
   - [3.5. Cơ chế hồi điểm nhịp nhàng & Tăng tốc độ tụt điểm (Fast Decay)](#35-cơ-chế-hồi-điểm-nhịp-nhàng--tăng-tốc-độ-tụt-điểm-fast-decay)
   - [3.6. Cảnh báo mất khuôn mặt bằng giọng nói tiếng Việt tốc độ 1.5x](#36-cảnh-báo-mất-khuôn-mặt-bằng-giọng-nói-tiếng-việt-tốc-độ-15x)
   - [3.7. Khử nghẽn FPS & Chống spam lưu ảnh bằng chứng](#37-khử-nghẽn-fps--chống-spam-lưu-ảnh-bằng-chứng)
4. [Kiểm Thử Tự Động Hóa (Unit Test Suite)](#4-kiểm-thử-tự-động-hóa-unit-test-suite)
5. [Trạng Thái Mã Nguồn & Git](#5-trạng-thái-mã-nguồn--git)
6. [Bảng Tổng Hợp Tham Số Cấu Hình Hệ Thống](#6-bảng-tổng-hợp-tham-số-cấu-hình-hệ-thống)

---

## 1. Bối Cảnh & Vấn Đề Ban Đầu

Từ tài liệu báo cáo `docx/TEST_YOLO_Bao_cao_Loi_va_Ke_hoach_Va_Loi_Chi_tiet.md` và phản hồi thực tế từ tài xế khi test trên camera:
1. **Âm thanh cảnh báo kêu quá lâu:** Khi phát hiện nguy hiểm còi hú, nhưng khi tài xế đã mở mắt, ngẩng đầu hoặc ngậm miệng lại thì còi vẫn tiếp tục hú kéo dài, không phản hồi tức thì với trạng thái an toàn.
2. **Nháy 1 mắt bị báo nguy hiểm:** Khi tài xế nháy một bên mắt (hoặc bị nheo mắt do ánh sáng), hệ thống lấy trung bình cộng EAR của 2 mắt kéo chỉ số xuống `< 0.25`, kích hoạt phạt ngủ gật.
3. **Cúi đầu vẫn mở mắt bị hú còi oan:** Tài xế cúi nhẹ đầu nhìn bảng đồng hồ hoặc màn hình điều khiển nhưng mắt vẫn quan sát tốt thì hệ thống vẫn phát còi báo động khẩn cấp.
4. **Lỗi vòng lặp ngáp vô tận:** Khi ngáp sâu, điểm nhảy lên 100 và còi hú. Khi tài xế ngậm miệng lại, điểm không được hạ ngay lập tức mà vẫn giữ $\ge 85$, khiến `main.py` liên tục lặp lại việc hú còi và chụp ảnh bằng chứng lưu vào ổ cứng mỗi 2.5s.
5. **Điểm số không nhạy theo thời gian thực:** Điểm tăng thì nhanh nhưng tụt thì quá chậm (mỗi 3 giây mới giảm 1 điểm). Chớp mắt bình thường không làm điểm dao động nhịp nhàng.
6. **Mất mặt không có lời nhắc thoại:** Khi camera bị lệch hoặc tài xế quay hẳn đầu đi, cần có câu thoại nhắc nhở rõ ràng: *"Camera không thấy khuôn mặt! Camera không thấy khuôn mặt!"* với tốc độ nói nhanh 1.5x.

---

## 2. Thiết Lập Môi Trường Thực Thi

- **Cấu hình Python:** Thiết lập môi trường chạy với Python 3.14 (`C:\Python314\python.exe`).
- **Cài đặt thư viện bổ trợ:**
  - `pygame-ce` (2.5.8): Thư viện âm thanh tương thích hoàn toàn với Python 3.14.
  - `pytest` (9.1.1): Framework chạy kiểm thử tự động hóa logic nghiệp vụ.
  - `edge-tts` (7.3.1): Thư viện tạo giọng nói AI chất lượng cao (Microsoft Neural Voice).

---

## 3. Chi Tiết Các Thay Đổi & Vá Lỗi Nghiệp Vụ

### 3.1. Sửa lỗi nháy 1 mắt (Winking False Positive)
* **File thay đổi:** `utils.py`, `fatigue_manager.py`
* **Nguyên nhân gốc:** Hàm `calculate_ear` ban đầu chỉ trả về 1 giá trị duy nhất là trung bình cộng `(ear_left + ear_right) / 2`. Khi tài xế nháy 1 mắt (ví dụ mắt trái = 0.12, mắt phải = 0.32), trung bình là 0.22 `< 0.25`, dẫn đến bị tính là đang nhắm mắt ngủ gật.
* **Giải pháp thực hiện:**
  - Sửa `utils.calculate_ear` trả về bộ 3 giá trị: `(ear_left, ear_right, ear_avg)`.
  - Trong `fatigue_manager.py`, định nghĩa biến logic:
    ```python
    both_eyes_closed = (ear_left < self.ear_threshold) and (ear_right < self.ear_threshold)
    ```
  - Chỉ khi **cả hai mắt cùng nhắm** mới tính thời gian nhắm mắt. Nháy 1 mắt hoàn toàn không bị tính là ngủ gật.

### 3.2. Cảnh báo nhắm mắt chuẩn 1.5s & Bộ đếm thời gian thực
* **File thay đổi:** `config.py`, `fatigue_manager.py`, `main.py`
* **Yêu cầu:** Nhắm mắt liên tục 1.5s là báo động ngay. Trên màn hình phải hiển thị thời gian đã nhắm như lúc cúi đầu (ví dụ: `NHAM MAT (1.2s)`). Khi mở mắt phải tắt còi tức thì.
* **Giải pháp thực hiện:**
  - Trong `fatigue_manager.py`: Khi `both_eyes_closed` là `True`, tích lũy `closed_eye_time` theo thời gian thực `(current_time - eye_closed_start_time)`.
  - Trong lúc nhắm mắt từ 0.5s đến trước 1.5s: Cập nhật lý do hiển thị `f"NHAM MAT ({closed_eye_time:.1f}s)"` để tài xế hoặc người giám sát quan sát thấy đồng hồ đếm thời gian.
  - Khi `closed_eye_time >= 1.5s`: Ngay lập tức đặt điểm = 100, kích hoạt `is_microsleep = True`, lý do `f"NGU GAT ({closed_eye_time:.1f}s)"`.
  - Trong `main.py`: Các tình huống khẩn cấp (`NGU GAT`, `GUC DAU`) được phép bỏ qua độ trễ chờ `ALERT_COOLDOWN` để còi hú ngay lập tức tại mốc 1.5s.
  - Ngay khi mở mắt ra (`both_eyes_closed` là `False`): `closed_eye_time` được reset về 0, hệ thống chuyển lý do sang `MAT DA MO`, điểm số được hạ nhiệt và âm thanh còi báo dừng ngay.

### 3.3. Phân biệt Cúi đầu mắt mở vs Gục đầu mắt nhắm
* **File thay đổi:** `fatigue_manager.py`
* **Vấn đề thực tế:** Khi cúi đầu nhìn bảng điều khiển, mắt vẫn mở, camera chiếu góc nghiêng nên hình chiếu mắt có thể hẹp lại, gây hiểu nhầm là ngủ gật.
* **Giải pháp thực hiện:**
  - `fatigue_manager.update_head()` nhận thêm cờ trạng thái mắt `both_eyes_closed`.
  - **Trường hợp 1 (Cúi đầu nhưng mắt vẫn mở):**
    - Hệ thống chỉ cảnh báo nhắc nhở tư thế: `CUI DAU - MAT MO ({head_down_time:.1f}s)`.
    - Khống chế điểm mệt mỏi tối đa ở mức an toàn: `min(self.fatigue_score, 30)`.
    - **Không** bật còi báo động khẩn cấp (`is_head_down = False`, `should_alert = False`).
  - **Trường hợp 2 (Cúi đầu mà mắt nhắm hoặc không nhìn thấy mắt $\ge 2.0s$):**
    - Xác định tài xế đang gục đầu ngủ gật: `GUC DAU (NHAM MAT) ({head_down_time:.1f}s)`.
    - Đẩy điểm lên 100, kích hoạt còi báo động khẩn cấp để đánh thức tài xế.
  - Khi ngẩng đầu lên bình thường: Trạng thái gục đầu được hủy ngay lập tức, còi tắt ngay.

### 3.4. Khắc phục triệt để lỗi lặp ngáp vô tận (Infinite Yawn Loop)
* **File thay đổi:** `config.py`, `fatigue_manager.py`
* **Vấn đề thực tế:** Ngáp sâu $\ge 1.5s$ đẩy điểm lên 100. Khi tài xế đã ngậm miệng lại thì `is_yawning` chuyển thành `False`, nhưng điểm mệt mỏi vẫn còn kẹt ở mức 100. Do điều kiện cảnh báo trong `fatigue_manager.py` có kiểm tra `score >= 85`, vòng lặp trong `main.py` cứ sau mỗi chu kỳ lại tưởng là còn nguy hiểm nên hú còi và chụp ảnh liên tục.
* **Giải pháp thực hiện:**
  - Cập nhật `YAWN_ALERT_DURATION = 1.5s` (ngáp liên tục 1.5s là báo động).
  - Trong `fatigue_manager.update_mouth()`: Khi miệng đóng lại (`mar < threshold`), nếu trước đó vừa kết thúc một cơn ngáp thì lập tức:
    - Thiết lập lý do: `"DA HET NGAP"`.
    - Hạ điểm khẩn cấp về mức an toàn: `self.fatigue_score = min(self.fatigue_score, 30)`.
    - Tắt cờ cảnh báo `is_yawning = False`.
  - Kết quả: Ngay khi ngậm miệng, âm thanh còi dứt điểm ngay lập tức và không còn hiện tượng chụp ảnh spam.

### 3.5. Cơ chế hồi điểm nhịp nhàng & Tăng tốc độ tụt điểm (Fast Decay)
* **File thay đổi:** `config.py`, `fatigue_manager.py`
* **Tối ưu độ nhạy:**
  - **Chớp mắt sinh lý bình thường (< 0.30s):** Được cộng điểm phục hồi `-5 điểm` (`SCORE_RECOVERY = 5`). Khi chớp mắt bình thường, điểm số trên màn hình có bước nhảy dao động nhẹ nhàng, thể hiện hệ thống đang phản hồi real-time.
  - **Chớp mắt chậm / lờ đờ (> 0.32s):** Phạt `+20 điểm` mệt mỏi (`SCORE_SLOW_BLINK = 20`) và ghi nhận lý do `CHOP MAT CHAM`.
  - **Tốc độ tụt điểm (Decay):**
    - Trước đây: 3.0s mới giảm 1 điểm (quá chậm, tài xế tỉnh táo lại mà điểm vẫn cao).
    - Cải tiến: `SCORE_DECAY_INTERVAL = 0.5s`, `SCORE_DECAY_AMOUNT = 3` $\rightarrow$ Tốc độ giảm điểm đạt **6 điểm/giây**. Khi không còn hành vi nguy cơ, điểm số hạ nhiệt rất nhanh về 0.

### 3.6. Cảnh báo mất khuôn mặt bằng giọng nói tiếng Việt tốc độ 1.5x
* **File tạo mới:** `tao_am_thanh_mat_mat.py`, `canh_bao_mat_mat.mp3`
* **File tích hợp:** `main.py`
* **Chi tiết thực hiện:**
  - Tạo script sinh file âm thanh `tao_am_thanh_mat_mat.py` bằng Microsoft Edge TTS:
    - Giọng đọc: `vi-VN-HoaiMyNeural` (tiếng Việt chuẩn, rõ ràng, dứt khoát).
    - Nội dung: *"Camera không thấy khuôn mặt! Camera không thấy khuôn mặt!"*.
    - Tốc độ phát âm: `rate="+50%"` (chuẩn 1.5x giúp phát thông điệp nhanh, không bị rề rà).
  - Tích hợp phát âm thanh trong `main.py`:
    - Khi khuôn mặt bị che khuất hoặc quay đi vượt quá `FACE_MISSING_TIME` (1.5s): Phát file `canh_bao_mat_mat.mp3`.
    - Ngay khi khuôn mặt xuất hiện trở lại: Tự động ngắt kênh phát giọng nói (`mixer.stop()`).

### 3.7. Khử nghẽn FPS & Chống spam lưu ảnh bằng chứng
* **File thay đổi:** `main.py`
* **Chi tiết thực hiện:**
  - **Khử nghẽn FPS:** Xóa bỏ điều kiện kiểm tra `if not is_alerting:` trước đây. Luồng xử lý camera và MediaPipe/YOLO luôn chạy liên tục ở mức 30 FPS mượt mà ngay cả khi còi hoặc giọng nói đang phát.
  - **Chống spam ảnh:** Thêm bộ đệm thời gian chống trùng lặp `last_evidence_saved_time`. Cùng một hành vi vi phạm chỉ lưu ảnh bằng chứng tối đa 1 lần trong vòng 10 giây vào thư mục `bang_chung/`, tránh làm đầy bộ nhớ đĩa khi tài xế giữ nguyên trạng thái.
  - **Bổ sung Telemetry Overlay:** Hiển thị trực tiếp các thông số kỹ thuật góc trên màn hình:
    `EAR: 0.xx | MAR: 0.xx | Pitch: xx.x | Điểm: xx/100 | Lý do: ...`
  - **Dọn dẹp tài nguyên:** Bọc toàn bộ vòng lặp chính trong khối `try ... finally` để giải phóng camera (`cap.release()`), đóng cửa sổ OpenCV (`cv2.destroyAllWindows()`) và tắt âm thanh (`pygame.mixer.quit()`) an toàn khi thoát bằng phím `q`.

---

## 4. Kiểm Thử Tự Động Hóa (Unit Test Suite)

Toàn bộ logic nghiệp vụ đã được viết test case tự động tại file `tests/test_business_logic.py` sử dụng thư viện `pytest`.

### Danh sách 14 Test Cases:
1. `test_winking_single_eye_does_not_trigger_microsleep`: Kiểm tra nháy 1 mắt không kích hoạt ngủ gật.
2. `test_both_eyes_closed_triggers_microsleep_at_1_5s`: Kiểm tra nhắm cả 2 mắt đúng 1.5s sẽ kích hoạt báo động 100 điểm.
3. `test_opening_eyes_recovers_immediately`: Kiểm tra mở mắt ra thì timer nhắm mắt lập tức reset về 0 và chuyển sang trạng thái an toàn.
4. `test_head_down_with_eyes_open_does_not_alarm`: Cúi đầu nhưng mắt mở chỉ ghi nhận lý do, điểm $\le 30$, không hú còi.
5. `test_head_down_with_closed_eyes_alarms_at_2s`: Cúi đầu kết hợp nhắm mắt $\ge 2.0s$ kích hoạt còi báo động khẩn cấp (100 điểm).
6. `test_head_up_recovers_immediately`: Ngẩng đầu lên thì trạng thái gục đầu lập tức hủy.
7. `test_yawn_triggers_at_1_5s`: Ngáp duy trì $\ge 1.5s$ kích hoạt cảnh báo ngáp.
8. `test_mouth_close_breaks_yawn_loop_immediately`: Ngậm miệng lập tức hạ điểm về 30 và ngắt cảnh báo, ngăn chặn lỗi lặp còi vô tận.
9. `test_normal_blink_recovers_points`: Chớp mắt bình thường (< 0.30s) được trừ 5 điểm mệt mỏi.
10. `test_slow_blink_adds_fatigue_points`: Chớp mắt chậm (> 0.32s) bị phạt 20 điểm.
11. `test_score_fast_decay`: Tốc độ suy giảm điểm mệt mỏi đạt 6 điểm/giây khi trạng thái bình thường.
12. `test_closed_eye_timer_displayed_in_reason`: Lý do hiển thị đếm giây trực quan `NHAM MAT (x.xs)`.
13. `test_head_down_timer_displayed_in_reason`: Lý do hiển thị đếm giây trực quan `GUC DAU (x.xs)`.
14. `test_emergency_alerts_bypass_cooldown`: Cảnh báo nguy hiểm bỏ qua độ trễ cooldown để hú còi tức thì.

### Kết quả chạy kiểm thử thực tế:
```bash
py -3.14 -m pytest tests/test_business_logic.py
============================= 14 passed in 0.05s ==============================
```
**Tỷ lệ đạt: 14/14 test cases (100% Passed).**

---

## 5. Trạng Thái Mã Nguồn & Git

- **Nhánh hiện tại:** `main` (đồng bộ hoàn toàn với `origin/main`, không có xung đột merge).
- **Các file đã chỉnh sửa:**
  - `canhbao.py`: Bổ sung kiểm tra âm thanh an toàn.
  - `config.py`: Tinh chỉnh các tham số thời gian và độ nhạy.
  - `fatigue_manager.py`: Tái cấu trúc bộ não tính điểm và quản lý hành vi mệt mỏi.
  - `main.py`: Tích hợp camera, luồng xử lý mượt mà, telemetry và giọng nói.
  - `utils.py`: Hỗ trợ tính toán EAR độc lập 2 bên mắt.
- **Các file và thư mục mới:**
  - `tao_am_thanh_mat_mat.py`: Script tạo giọng nói cảnh báo.
  - `canh_bao_mat_mat.mp3`: File âm thanh giọng nói 1.5x.
  - `tests/test_business_logic.py`: Bộ kiểm thử 14 unit tests.
  - `docx/TEST_YOLO_Bao_cao_Loi_va_Ke_hoach_Va_Loi_Chi_tiet.md`: Báo cáo chi tiết lỗi và kế hoạch.
  - `docx/lichsu.md`: Tài liệu nhật ký này.

---

## 6. Bảng Tổng Hợp Tham Số Cấu Hình Hệ Thống

| Tham số | Giá trị mới | Ý nghĩa & Hành vi |
| :--- | :---: | :--- |
| `EAR_THRESHOLD` | `0.25` | Ngưỡng xác định mắt nhắm (áp dụng độc lập cho cả 2 mắt) |
| `EYE_CLOSED_TIME` | `1.5s` | Thời gian nhắm cả 2 mắt liên tục để kích hoạt báo động ngủ gật |
| `HEAD_DOWN_TIME` | `2.0s` | Thời gian cúi đầu liên tục (kèm nhắm mắt) để kích hoạt báo động gục đầu |
| `YAWN_ALERT_DURATION`| `1.5s` | Thời gian há miệng liên tục để kích hoạt cảnh báo ngáp |
| `SCORE_DECAY_INTERVAL`| `0.5s` | Chu kỳ giảm điểm mệt mỏi tự nhiên |
| `SCORE_DECAY_AMOUNT` | `3 điểm` | Điểm giảm mỗi chu kỳ $\rightarrow$ Tốc độ tụt điểm: **6 điểm/giây** |
| `SCORE_RECOVERY` | `5 điểm` | Điểm thưởng phục hồi khi tài xế chớp mắt bình thường |
| `SCORE_SLOW_BLINK` | `20 điểm` | Điểm phạt khi tài xế chớp mắt chậm, lờ đờ (> 0.32s) |
| `NORMAL_BLINK_MAX_TIME`| `0.30s` | Ngưỡng thời gian tối đa của một cái chớp mắt sinh lý bình thường |
| `SLOW_BLINK_TIME` | `0.32s` | Ngưỡng thời gian xác định chớp mắt chậm |
| `FACE_MISSING_TIME` | `1.5s` | Mất khuôn mặt quá 1.5s $\rightarrow$ Kích hoạt giọng nói cảnh báo 1.5x |
| `ALERT_COOLDOWN` | `1.0s` | Thời gian nghỉ giữa các lần cảnh báo thông thường (bị bypass khi khẩn cấp) |
