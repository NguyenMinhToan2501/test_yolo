import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def tao_am_thanh():
    try:
        from gtts import gTTS
        text = "Cảnh báo! Tài xế có dấu hiệu buồn ngủ, vui lòng giữ tỉnh táo!"
        output_file = "canh_bao_buon_ngu.mp3"
        print(f"Đang tổng hợp giọng nói: '{text}'...")
        tts = gTTS(text, lang='vi')
        tts.save(output_file)
        print(f"✅ Thành công! Đã lưu file âm thanh: {output_file}")
    except Exception as e:
        print(f"❌ Lỗi tạo âm thanh: {e}")

if __name__ == "__main__":
    tao_am_thanh()

