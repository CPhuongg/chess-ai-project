# 1.1 Heuristic Null Move chuẩn

### -Định nghĩa
+) Null move: thực hiện 1 bước đi rỗng, để đối thủ di chuyển 2 lần với giả định việc đó sẽ cho đối thủ 1 nước đi tốt.   
--> Tạo một trạng thái có vẻ tồi để thực hiện pruning.  
+) Zugzwang: các nước đi mà mọi hành động đều làm trạng thái người chơi tồi đi --> khác giả thuyết của Null move.

Có một lớp các trạng thái cờ vua mà việc áp dụng heuristic null-move có thể dẫn đến các sai lầm chiến thuật nghiêm trọng. Trong các vị trí zugzwang (tiếng Đức có nghĩa là "bị ép phải đi"), người chơi có quyền đi nước đi chỉ có các lựa chọn tồi, và do đó sẽ thực sự tốt hơn nếu họ được phép từ bỏ quyền đi nước. Trong những vị trí này, heuristic null-move có thể gây ra một cutoff mà một tìm kiếm đầy đủ sẽ không phát hiện được, khiến chương trình giả định rằng vị trí là rất tốt cho một bên trong khi thực tế lại rất xấu cho họ.

Để tránh sử dụng heuristic null-move trong các vị trí zugzwang, hầu hết các chương trình chơi cờ sử dụng heuristic null-move đều đặt ra các hạn chế trong việc sử dụng nó. Những hạn chế này thường bao gồm việc không sử dụng heuristic null-move nếu:

- Bên có quyền đi đang bị chiếu
- Bên có quyền đi chỉ còn vua và quân tốt
- Bên có quyền đi chỉ còn một số ít quân
- Nước đi trước trong tìm kiếm cũng là một nước null-move

### -Vấn đề:
Các trạng thái Zugzwang có thể gây nhầm lẫn trong tính toán tạo thành nước đi tốt nhất lỗi  
-> Tính toán thất bại

### -Tài liệu tham khảo:
https://en.wikipedia.org/wiki/Null-move_heuristic  
https://en.wikipedia.org/wiki/Zugzwang


# 1.2 Verified Null-Move Pruning (trong mã hóa)
+) Giảm độ sâu 3 sau null-move;  
+) Xác nhận cắt tỉa nếu nhánh sử dụng Null-move  
+) ...  
### -Tài liệu tham khảo:
https://ui.adsabs.harvard.edu/abs/2008arXiv0808.1125D/abstract
