### -Định nghĩa:
-) lưu trữ kết quả của các trạng thái cờ đã được phân tích trước đó vào một bảng băm để không phải đánh giá lại các trạng thái đã đánh giá.   
## Lợi ích:
-) Giảm số nhánh tìm kiếm.   
-) Tránh đánh giá lặp.   
--> Tiết kiệm thời gian một cách đáng kể.   
 
## Vấn đề:
-) Hàm băm tốt nhất cho cờ vua là zobrist cũng cần đến 64 bit(có sẵn trong thư viện chess).   
-)Kích thước bảng băm thực tế (Transposition Table) thường được đặt khoảng 10^8 mục(tài liệu 1) 1 mục dự kiến cần khoảng 16 byte -> 1,6 gb, tùy thuộc vào bộ nhớ có sẵn.   
-) Số lượng trạng thái quá lớn cần cài đặt xử lý dữ liệu bảng băm một cách khéo léo (*vấn đề chính*):   

+)Độ sâu 10: Giả sử trung bình mỗi vị trí có 35 nước đi hợp lệ.   
Số vị trí = 35^10 ≈ 2.76 * 10^15 trạng thái(cutoff và trùng nhiều claude tính hộ)   
Độ sâu 15: Số vị trí tiềm năng = 35^15 ≈ 2.01 * 10^23   
## Phương pháp(đề xuất):
-) chỉ lưu kết quả chính xác(các nhánh dừng với cut-off chỉ dùng killer search)   
-) Quản lý bộ nhớ:   
1. Thay thế luôn (Always Replace): chiến lược đơn giản nhất: Thay thế ngay lập tức bất kỳ mục cũ nào khi một mục mới được lưu.
2. Ưu tiên theo số lượng nút đã duyệt (Priority by Searched Nodes Count): sử dụng số lượng nút được duyệt để tạo ra một mục trong bảng băm làm tiêu chí ưu tiên. Mục nào được tạo ra nhờ việc duyệt nhiều nút hơn sẽ được ưu tiên giữ lại vì nó có thể chính xác hơn.(trùng với cái số 5)
3. Ưu tiên theo vị trí trong danh sách sắp xếp nước đi (Priority by Move Ordering Position) Chiến lược này dựa vào thứ tự sắp xếp nước đi (move ordering). Nếu một nước đi được đánh giá là tốt bởi thuật toán sắp xếp nước đi, việc lưu trữ nó trong bảng băm sẽ giúp tìm kiếm nhanh hơn sau này.
4. Ưu tiên theo độ sâu (Depth-Preferred) Đây là chiến lược ưu tiên hoàn toàn dựa trên độ sâu (depth). Một mục trong bảng băm chỉ bị ghi đè nếu mục mới có độ sâu lớn hơn mục cũ. Thích hợp khi muốn duy trì các kết quả tìm kiếm sâu hơn, chính xác hơn.
5. Hệ thống hai tầng (Two-tier System): Sử dụng hai bảng băm đặt cạnh nhau. Một bảng ưu tiên theo độ sâu (depth-preferred). Một bảng áp dụng chiến lược thay thế luôn (always-replace). Kết hợp hai cách lưu trữ giúp giảm thiểu việc mất mát thông tin quan trọng.
6. (cái này t chịu) Hệ thống nhiều tầng (Bucket Systems): Giống với hệ thống hai tầng nhưng có thể sử dụng bất kỳ số lượng tầng (buckets) nào. Số tầng thường được thiết kế dựa trên kích thước của một dòng bộ nhớ (cache line). Khi cần thay thế, mục có độ sâu thấp nhất trong bucket sẽ bị ghi đè.   
7. Lão hóa (Aging) Chiến lược này tính đến việc tìm kiếm các vị trí cờ khác nhau trong suốt quá trình chơi. Các chương trình hiện đại không xóa bảng băm sau mỗi lượt đi, mà tận dụng các mục cũ từ các lần tìm kiếm trước. Để tránh lưu trữ các mục cũ quá lâu, Aging được sử dụng:   
So sánh thời gian (halfmove clock) hiện tại với thời gian khi mục được lưu trữ. Nếu quá cũ, mục đó sẽ bị thay thế ngay cả khi độ sâu hoặc cờ (flag) của nó vẫn còn tốt.   

### Tài liệu tham khảo:  
https://www.chessprogramming.org/Transposition_Table    
https://en.wikipedia.org/wiki/Zobrist_hashing    

# Thông tin bổ sung:
Các chương trình cờ vua mạnh hiện nay:

Độ sâu cơ bản: 12-16 nước đi trong middlegame
Độ sâu phân tích nước đi quan trọng (selective search): 20-30+ ply
Phân tích quân ăn nhau (quiescence search): thêm 6-10 ply


Phân loại theo sức mạnh:

Beginner engines: 6-8 ply
Intermediate engines: 8-12 ply
Advanced engines: 12-18 ply
Đẳng cấp thế giới (Stockfish, Leela): 18-40+ ply tùy tình huống


Phụ thuộc vào giai đoạn ván đấu:

Opening (khai cuộc): 10-18 ply (thường dùng thêm opening book)
Middlegame (trung cuộc): 12-20 ply
Endgame (tàn cuộc): 15-35+ ply (ít quân hơn nên tìm sâu hơn)


Phụ thuộc vào phần cứng:

CPU thông thường: 12-18 ply