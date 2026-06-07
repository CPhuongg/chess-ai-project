# ỨNG DỤNG CỜ VUA - CHESS GAME APPLICATION

## GIỚI THIỆU ĐỀ TÀI

Ứng dụng cờ vua được phát triển bằng Python và PyQt5, cung cấp trải nghiệm chơi cờ vua hoàn chỉnh với AI thông minh. Ứng dụng hỗ trợ hai chế độ chơi chính: Người vs AI và AI vs AI, tích hợp hệ thống quản lý thời gian và các tính năng nâng cao.

### Tính năng chính:
- Chế độ Người vs AI với độ khó có thể điều chỉnh
- Chế độ AI vs AI để quan sát hai engine cờ vua thi đấu
- Hệ thống quản lý thời gian linh hoạt với tăng thời gian
- AI sử dụng thuật toán minimax với alpha-beta pruning
- Giao diện đồ họa hiện đại với hiệu ứng animation
- Lưu/tải game với metadata chi tiết
- Phân tích nước đi với độ sâu tìm kiếm khác nhau

## CÁCH CÀI ĐẶT

### Yêu cầu hệ thống:
- Python 3.7 trở lên
- Hệ điều hành: Windows, macOS, hoặc Linux

### Các bước cài đặt:

1. **Cài đặt Python:**
   - Tải Python từ https://python.org
   - Đảm bảo chọn "Add Python to PATH" khi cài đặt

2. **Tải source code:**
   ```
   git clone https://github.com/pathust/chess-bot
   ```

3. **Cài đặt các thư viện cần thiết:**
   ```
   pip install -r requirements.txt
   ```

4. **Chạy ứng dụng:**
   ```
   python main.py
   ```

## HƯỚNG DẪN SỬ DỤNG

### Bắt đầu game:
1. Chạy file `main.py`
2. Chọn chế độ chơi: "Human vs AI" hoặc "AI vs AI"
3. Thiết lập thời gian (tùy chọn)
4. Bắt đầu chơi!

### Điều khiển game:
- **Start/Pause**: Bắt đầu/tạm dừng game
- **Undo**: Hoàn tác nước đi
- **Save**: Lưu game hiện tại
- **Load**: Tải game đã lưu
- **Resign**: Đầu hàng
- **Reset**: Bắt đầu game mới

### Thiết lập thời gian:
- **Không giới hạn**: Chơi không áp lực thời gian
- **Có thời gian**: Thiết lập thời gian tùy chỉnh
- **Preset nhanh**: 1, 3, 5, 10, hoặc 15 phút
- **Tăng thời gian**: Thêm giây sau mỗi nước đi

## XỬ LÝ LỖI

Nếu gặp lỗi khi chạy:

1. **Lỗi module không tìm thấy:**
   ```
   pip install tên_module_bị_thiếu
   ```

2. **Lỗi Python không nhận diện:**
   - Kiểm tra Python đã được thêm vào PATH
   - Thử chạy: `python --version`

3. **Lỗi giao diện:**
   - Đảm bảo PyQt5 đã được cài đặt đúng
   - Thử cài lại: `pip uninstall PyQt5` sau đó `pip install PyQt5`

4. **Vấn đề với môi trường ảo:**
   - Đảm bảo đã kích hoạt môi trường ảo trước khi cài đặt packages
   - Nếu quên kích hoạt: `chess_env\Scripts\activate` (Windows) hoặc `source chess_env/bin/activate` (macOS/Linux)

## LIÊN HỆ VÀ HỖ TRỢ

Nếu có thắc mắc hoặc phát hiện lỗi, vui lòng tạo issue trong repository hoặc liên hệ trực tiếp với nhóm phát triển.