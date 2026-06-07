### -Định nghĩa
+) Horizon problem: Trong trường hợp nếu đi thêm 1 bước nữa sẽ là nước đẹp (Ví dụ: chiếu hết), nhưng ở nước kết thúc tìm kiếm lại là một nước xấu. Nếu tiếp tục tăng độ sâu tìm kiếm vẫn gặp vấn đề tương tự ở mức depth+1.  
--> Thực hiện việc tìm kiếm những nước đi có tỷ lệ cao tạo đột biến khi depth = 0.  
+) Quiescence search: Khi depth = 0, thuật toán tìm kiếm chính sẽ dừng lại và chuyển sang vét các nước đi có tỷ lệ cao tạo đột biến.

### Các nước đi được kiểm tra gồm:  
    -) Các nước đi chiếu  
    -) Các nước ăn quân  
    -) Các nước phong cấp  

### Vấn đề:
-) Tìm kiếm quá sâu gây áp lực lên bộ nhớ và khả năng tính toán.  
-) Chưa tính đến các nước phòng thủ.  

### Tài liệu tham khảo:  
https://en.wikipedia.org/wiki/Quiescence_search  

---

## Advance Quiescence (Zzzzzz#Quiescence)  
Trong thuật toán Zzzzzz_quiescence, cho phép **QUIES_MAX** bước đầu được thực hiện ***như quiescence cơ bản*** (bất kỳ quân nào cũng có thể ăn quân khác và  chiếu tướng) nhưng những quân cờ đã di chuyển đó sẽ được đánh dấu (Trong code dùng 1 mảng 2 chiều để đánh dấu những vị trí các quân bị đánh dấu). Sau khi **zzzzzz_Quiescence** đạt đến depth = 0 sẽ gọi đến thuật toán **sub_zzzzzz_quiescence()** chỉ xét những nước ăn những quân đã được đánh dấu.   
Cách này giúp thuật toán quiescence luôn kết thúc với nhiều chuỗi trao đổi như "đổi hậu, thí hậu chiếu tướng,..." được đánh giá chính xác.  

Giá trị **QUIES_MAX** càng cao thì kết quả càng tốt, nhưng đồng thời cũng làm chậm chương trình, do đó cần cân bằng giữa độ chính xác và tốc độ. Trong **ZZZZZZ**, thuật toán quiescence hầu như không mất nhiều thời gian: thuật toán thường kết thúc ngay sau lần gọi **sub_zzzzzz_quiescence()** đầu tiên (depth = 0) , và chỉ khoảng 10% các lần gọi **sub_zzzzzz_quiescence()** được thực hiện sâu hơn. Các thử nghiệm áp dụng null-move trong quiescence search không đem lại hiệu quả đáng kể.  

### Tài liệu tham khảo:  
https://www.chessprogramming.org/Zzzzzz#Quiescence  