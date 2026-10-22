# pyrefly: ignore[missing-import]
from gtts import gTTS

print("Đang tổng hợp giọng nói AI. Vui lòng chờ")
van_ban = "Cảnh báo! Phát hiện tài xế có dấu hiệu buồn ngủ. Yêu cầu tập trung lái xe ngay lập tức!"

# kéo API của google để đọc tiếng Việt
tts = gTTS(van_ban, lang='vi')

# lưu file âm thanh 
tts.save("am_thanh_canh_bao.wav")
print("Thành công! Đã tạo file am_thanh_canh_bao.wav")