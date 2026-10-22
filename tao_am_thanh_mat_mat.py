import sys
import asyncio
# pyrefly: ignore[missing-import]
import edge_tts

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def main():
    text = "Camera không thấy khuôn mặt! Camera không thấy khuôn mặt!"
    voice = "vi-VN-HoaiMyNeural" # Giọng tiếng Việt truyền cảm
    output = "canh_bao_mat_mat.mp3"
    rate = "+50%" # Tốc độ 1.5x theo yêu cầu
    
    print("Đang tạo âm thanh cảnh báo giọng nói (tốc độ 1.5x)...")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output)
    print(f"Thành công! Đã lưu file âm thanh giọng nói: {output}")

if __name__ == "__main__":
    asyncio.run(main())
