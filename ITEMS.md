# Danh sách thiết bị bổ sung

## Checklist mua sắm bắt buộc
- [ ] Nguồn 5V-3A (official Raspberry Pi PSU) - cung cấp dòng ổn định khi cắm thêm camera, micro và loa.
- [ ] Thẻ nhớ microSD >= 32GB (Class 10) - cài đặt hệ điều hành, lưu mã nguồn và dữ liệu âm thanh/hình ảnh.
- [ ] Camera Raspberry Pi Module 3 hoặc webcam USB tương thích - cấp khung hình cho việc phát hiện cháy.
- [ ] Cáp ribbon CSI đúng độ (nếu dùng camera module) hoặc cáp USB dài chất lượng tốt cho webcam.
- [ ] Giá đỡ/khung cố định camera (tripod mini hoặc keo dính tường) - giúp hướng camera vào khu vực cần giám sát.
- [ ] Micro USB thu âm (plug-and-play) - thu lệnh giọng nói và chat voice tới Gemini.
- [ ] Loa mini chủ động (USB hoặc jack 3.5 mm) - phát cảnh báo và nhạc phát từ backend.
- [ ] Module rơ le 4 kênh 5V (loại opto cách ly) - điều khiển đèn/thiết bị theo trạng thái của LightingService.
- [ ] Dây jumper male-female và bộ chia GPIO - kết nối Pi với module rơ le an toàn.
- [ ] Đèn LED 5V + điện trở hạn dòng (ít nhất 2-4 bóng) - demo tính năng điều khiển IoT qua giao diện web/app.

## Checklist tùy chọn khuyến nghị
- [ ] Bộ mô phỏng tải/thiết bị điện thực - thay thế LED để điều khiển thiết bị 220VAC thực tế (đèn, quạt, ổ cắm).
- [ ] USB audio đồng bộ (nếu cần gộp micro + loa trên cùng một mô đun) - đơn giản hóa cấu hình ALSA.
- [ ] Vỏ Pi kèm quạt/tản nhiệt - giúp Pi chạy ổn định khi xử lý hình ảnh liên tục.

## Mô tả chi tiết và liên hệ mã nguồn

### Nguồn 5V-3A
- Vai trò: đảm bảo Pi nhận đủ dòng khi đồng thời chạy camera, micro và loa.
- Tích hợp: mọi dịch vụ (FastAPI, xử lý OpenCV, websocket) đều chạy trên Pi, cần nguồn ổn định để tránh reset.

### Thẻ nhớ microSD >= 32GB
- Vai trò: chứa Raspberry Pi OS, thư viện Python/Node, file âm thanh trong `backend/music`.
- Tích hợp: backend lưu thông tin tại `data/` (vd `fire_alert_audio.b64`), cần dung lượng đủ lớn.

### Camera Raspberry Pi Module 3 hoặc webcam USB
- Vai trò: cung cấp khung hình cho bộ lọc lửa trong `backend/app/utils/fire_detection.py`.
- Tích hợp: `fire_detection_service.py:85` nhận byte ảnh từ camera; frontend gọi `navigator.mediaDevices.getUserMedia` tại `frontend/src/hooks/useGeminiRealtime.ts:620` để stream video lên server.

### Cáp ribbon CSI hoặc cáp USB chất lượng
- Vai trò: nối vật lý camera với Pi, tránh nhiễu/rớt khung.
- Tích hợp: cần thiết để camera hoạt động ổn định, đặc biệt khi chạy liên tục để phát hiện lửa theo `settings.capture_interval_seconds`.

### Giá đỡ/khung cố định camera
- Vai trò: giữ góc quay ổn định, bao phủ được vùng cần giám sát.
- Tích hợp: đảm bảo feed ảnh gửi đến `FireDetectionService` không bị lệch góc hay rung lắc.

### Micro USB thu âm
- Vai trò: phục vụ ghi âm giọng nói streaming lên Gemini (tham chiếu `frontend/src/hooks/useGeminiRealtime.ts:873`).
- Tích hợp: tăng chất lượng input 16 kHz theo `frontend/src/constants/gemini.ts:1`.

### Loa mini chủ động
- Vai trò: phát thông báo cháy (`play_audio.py:49`) và âm thanh từ `NotificationVoiceService` (cảm biến `backend/app/services/notification_voice_service.py:19`).
- Tích hợp: cho phép nghe cảnh báo tại hiện trường, đồng thời phát nhạc từ `backend/music`.

### Module rơ le 4 kênh 5V
- Vai trò: chuyển tín hiệu logic từ GPIO Pi sang tín hiệu điều khiển bật/tắt thiết bị điện; map các trạng thái `LightingService.toggle_light` (`backend/app/services/smart_home_service.py:134`) sang thiết bị thực.
- Tích hợp: kết nối với GPIO để bật/tắt đèn theo các phòng mặc định trong `backend/app/core/config.py:113`; bắt buộc để demo tính năng điều khiển IoT.

### Dây jumper & bộ chia GPIO
- Vai trò: tạo liên kết an toàn từ pin 5V/GND và chân điều khiển GPIO tới module rơ le.
- Tích hợp: đảm bảo kết nối ổn định giữa Pi và rơ le; cần thiết để đồng bộ trạng thái thiết bị thật với lệnh từ API.

### Đèn LED 5V + điện trở hạn dòng
- Vai trò: thiết bị IoT cơ bản để demo tính năng điều khiển từ xa qua giao diện web/app; mỗi LED đại diện cho một đèn trong các phòng (phòng khách, phòng ngủ, bếp, sân).
- Tích hợp: kết nối vào các kênh rơ le, cho phép kiểm tra trực quan lệnh từ API `/smart-home/lights`; an toàn hơn thiết bị 220VAC khi thử nghiệm.

### Bộ mô phỏng tải/thiết bị điện thực (tùy chọn)
- Vai trò: nâng cấp từ LED sang thiết bị 220VAC thật (đèn, quạt, ổ cắm thông minh) sau khi đã test logic thành công.

### USB audio đồng bộ (tùy chọn)
- Vai trò: nếu muốn dùng một mô đun cho cả micro và loa, giảm xung đột driver ALSA.
- Tích hợp: giữ ổn định cho streaming audio hai chiều trên websocket `/ws/gemini`.

### Vỏ + quạt/tản nhiệt (tùy chọn)
- Vai trò: bảo vệ bo mạch, giảm nhiệt độ khi Pi xử lý camera liên tục bằng OpenCV.
- Tích hợp: giúp hệ thống hoạt động lâu dài khi dịch vụ `FireDetectionService` phải hoạt động liên tục.

## Hướng dẫn lắp ráp và cài đặt

1. Ghi ảnh hệ điều hành vào thẻ microSD, cắm vào Pi và khởi động lần đầu; cập nhật hệ điều hành và cài đặt phụ thuộc (Python, Node, OpenCV).
2. Kết nối nguồn 5V-3A cho Pi, đảm bảo đèn LED nguồn sáng ổn định trước khi cắm thiết bị ngoại vi.
3. Lắp camera:
   - Tắt nguồn Pi, cắm cáp CSI vào cổng camera (hỗ trợ bằng keo dán hoặc ốc kẹp để cố định).
   - Bật nguồn, chạy `sudo raspi-config` để bật camera nếu dùng Raspberry Pi OS (nếu dùng webcam USB thì kiểm tra bằng `lsusb`).
   - Test bằng `libcamera-jpeg -o test.jpg` hoặc `ffmpeg` để chắc chắn khung hình ổn định.
4. Cắm micro USB và loa:
   - Kiểm tra `arecord -l` và `aplay -l` để xác định thiết bị.
   - Đối với loa 3.5 mm, chọn đầu ra mặc định bằng `raspi-config` hoặc `pavucontrol`.
5. (Tùy chọn) Lắp module rơ le:
   - Kết nối 5V và GND từ Pi sang module; dùng dây jumper cho các chân điều khiển (ví dụ GPIO17/27/22/23).
   - Nối đèn LED thử nghiệm vào các kênh rơ le; không làm việc với điện áp 220VAC nếu chưa có kinh nghiệm và biện pháp cách ly.
6. Cài đặt mã nguồn:
   - Clone repo hoặc copy vào Pi, cài đặt `python -m venv .venv`, `pip install -r requirements.txt`, và `npm install` trong `frontend`.
   - Thiết lập biến môi trường trong `.env`, bổ sung API key nếu dùng Gemini.
7. Chạy thử nghiệm:
   - Mở `start.sh` hoặc chạy riêng backend/frontend, kiểm tra camera feed trên giao diện web/mobile.
   - Gửi lệnh bật/tắt đèn từ frontend; nếu dùng rơ le, quan sát đèn LED phản ứng.
   - Kích hoạt tính năng cảnh báo cháy bằng cách đưa nguồn ảnh có lửa, nghe thông báo từ loa.

> Luôn tắt nguồn và tháo rời dây nguồn trước khi điều chỉnh dây nối. Khi làm việc với điện áp cao, sử dụng hộp cách ly, cầu chì và tuân thủ quy định an toàn điện.
