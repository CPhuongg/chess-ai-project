# Genetic Algorithm và Differential Evolution

## 1. Mã hóa và Biểu diễn
### Nguyên lý:
- GA dựa trên cơ chế tiến hóa tự nhiên: quần thể cá thể, chọn lọc tự nhiên, lai tạo (crossover) và đột biến (mutation). Mỗi cá thể có thể là một chuỗi biểu diễn chiến lược hoặc hàm đánh giá nước đi.
- DE là thuật toán tối ưu dựa trên các vector sai phân, liên tục cải tiến các cá thể thông qua sự kết hợp tuyến tính giữa các thành phần của quần thể.
### GA trong Cờ vua:
- **Mã hóa bộ trọng số đánh giá**: 
  ```
  [9, 5, 3, 3, 1, 0.5, 0.3, 0.4, 0.6, 0.2, 0.7]
  ```
  Trong đó: 9=hậu, 5=xe, 3=mã/tượng, 1=tốt, 0.5=kiểm soát trung tâm, 0.3=an toàn vua, v.v.

- **Mã hóa chiến lược**: 
  ```
  [1, 0, 1, 0, 1, 0, 1]
  ```
  Biểu thị: tấn công/phòng thủ, đổi quân/giữ quân, v.v.

### DE trong Cờ vua:
- **Vector tham số liên tục**: 
  ```
  [9.24, 3.15, 3.33, 5.11, 9.35, 0.47, 0.32, 0.41, 0.59, 0.23, 0.68]
  ```

## 2. Triển khai Cụ thể cho GA

1. **Mã hoá:** Định nghĩa bộ gene đại diện cho chiến lược hoặc tham số của hàm đánh giá.
2. **Hàm fitness:** Xây dựng hàm đánh giá hiệu quả của một cá thể dựa trên kết quả trận đấu hoặc mô phỏng.
3. **Chọn lọc:** Lựa chọn các cá thể có fitness cao để lai tạo.
4. **Lai tạo & Đột biến:** Tạo ra thế hệ mới bằng cách kết hợp các cá thể đã chọn, đồng thời thực hiện đột biến ngẫu nhiên để duy trì đa dạng.
5. **Lặp lại:** Lặp quá trình trên cho đến khi đạt được tiêu chí hội tụ (số thế hệ hoặc fitness tối ưu).

### Ưu điểm:
- Khả năng khám phá không gian giải pháp rộng.
- Dễ dàng kết hợp nhiều yếu tố đánh giá.
### Nhược điểm:
- Cần nhiều tài nguyên tính toán nếu quần thể lớn.
- Quá trình hội tụ có thể chậm nếu tham số không được chọn tối ưu.

## 3. Triển khai Cụ thể cho DE

1. **Khởi tạo quần thể:** Tạo ra các vector ứng với các tham số chiến lược hoặc hàm đánh giá.
2. **Phép trừ và cộng vector:** Với mỗi cá thể, chọn ngẫu nhiên 3 cá thể khác rồi tính vector sai phân và cộng vào cá thể hiện tại.
3. **Biến đổi:** Áp dụng phép lai tạo để tạo ra giải pháp thử nghiệm.
4. **Chọn lọc:** So sánh hàm mục tiêu của giải pháp thử với cá thể ban đầu và giữ lại giải pháp có giá trị cao hơn.
5. **Lặp lại:** Tiếp tục quá trình này cho đến khi đạt tiêu chí dừng (số vòng lặp hoặc đạt fitness tối ưu).

### Ưu điểm:
- Thích hợp với không gian liên tục, tìm kiếm nhanh nhạy.
- Cấu trúc đơn giản, ít tham số cần điều chỉnh.
### Nhược điểm:
- Ít phù hợp với bài toán có không gian giải pháp rời rạc nếu không có bước biến đổi thích hợp.
- Có thể gặp khó khăn trong việc tránh cực trị cục bộ nếu không thiết lập tốt.

## 4. Kết hợp Alpha-Beta, Static Evaluation với GA và DE trong engine cờ:

- **Alpha-Beta & Static Evaluation:** 

    Dùng thuật toán tìm kiếm Alpha-Beta với hàm đánh giá tĩnh dựa trên các đặc trưng (giá trị quân, an toàn vua, v.v.) có trọng số.

- **GA (Genetic Algorithm):**
    - Mã hóa mỗi bộ trọng số dưới dạng vector.
    - Chạy các trận mô phỏng, đánh giá hiệu năng qua hàm fitness.
    - Lựa chọn, lai tạo, và đột biến để xác định sơ bộ các trọng số tối ưu cho hàm đánh giá.
- **DE (Differential Evolution):**

    - Tinh chỉnh các trọng số từ GA bằng cách tự động điều chỉnh các tham số F và CR dựa trên lịch sử thành công.
    - Giúp cải thiện hội tụ và tránh rơi vào cực trị cục bộ.
- **Kết hợp & Ứng dụng:**

    - Phân chia trọng số theo giai đoạn trận đấu (mở đầu, giữa trận, cuối trận).
    - Sử dụng GA để khám phá không gian giải pháp, sau đó DE tinh chỉnh tham số liên tục qua các ván đấu mô phỏng hoặc self-play.
    - Kết quả là hàm đánh giá chính xác hơn, hỗ trợ Alpha-Beta loại bỏ các nhánh không khả thi nhanh chóng.

## 6. Kết luận

Giải thuật Di truyền và Tiến hóa Vi phân cung cấp phương pháp hiệu quả để tối ưu hóa các tham số trong engine cờ vua. GA phù hợp cho việc tìm kiếm ban đầu trên không gian rộng, trong khi DE phù hợp cho việc tinh chỉnh chính xác các tham số. Việc kết hợp cả hai phương pháp tạo ra cách tiếp cận mạnh mẽ để phát triển các hệ thống cờ vua hiệu quả.