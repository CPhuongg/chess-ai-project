#killer movemove search

## Định nghĩa:
-) killer move là một nước đi đột phá của người chơi gây ra cắt tỉa ở phía người chơi đối diện.   
-) killer move search là phương pháp ghi lại những killer move và đưa lên đầu trong những lượt search tiếp theo với độ sâu tương tự hoặc độ sâu lớn hơn.   

## Lợi ích:
-) Đẩy một nước đi với tỉ lệ cao là đột biến dễ dàng đánh giá được trạng thái và tạo ra cắp số alpha beta tốt để thực hiện cắt tỉa nhanh chóng giảm thời gian tìm kiếm đáng kể.

### Triển khai cụ thể:
Tạo một list 2 chiều killer_moves để lưu các killermove kèm depth tạo ra chúng. Khi prunning lưu nước đi đó vào mảng đã tạo kèm depth.   
Ở những lượt search sau đó kiểm tra xem các nước đi trong killer_moves[depth] và killer_moves[depth+2] có thực hiện được không.   
sau khi search ở độ sâu depth xong thì clear killer_moves[depth-2](cần thử nghiệm với depth -4 để lấy con số tối ưu).   

## Vấn đề:
-)Tăng áp lực lên bộ nhớ(không phải vấn đề vì không quá nặng).   
-)Không quan tâm đến phản ứng của đối thủ. Nếu đối thủ đã phòng bị thì sẽ đặt một nước đi xấu lên đầu.   
-)Tính tái sử dụng thấp, khi trạng thái trong cây thay đổi có thể không áp dụng lại được các killer moves đã có.
