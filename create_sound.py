import wave
import math
import struct

sample_rate = 44100.0
duration = 0.5 # Độ dài nửa giây
frequency = 800.0 # Tần số 800Hz (Tiếng bíp lớn)

obj = wave.open('am_thanh_canh_bao.wav','w')
obj.setnchannels(1) # Âm thanh mono
obj.setsampwidth(2) # 16-bit
obj.setframerate(sample_rate)

# Tạo sóng âm thanh
for i in range(int(duration * sample_rate)):
    # Đóng gói dữ liệu thành nhị phân
    value = int(32767.0 * math.sin(2.0 * math.pi * frequency * (i / sample_rate)))
    data = struct.pack('<h', value)
    obj.writeframesraw(data)

obj.close()
print("Đã tạo thành công file am_thanh_canh_bao.wav!")
