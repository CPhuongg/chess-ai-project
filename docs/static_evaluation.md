# Static evaluation function
## Định nghĩa 
 - Hàm đánh giá tĩnh (Static Evaluation Function) là một hàm được sử dụng trong các thuật toán tìm kiếm( Minimax, alpha-beta pruning,..), đặc biệt là trong các trò chơi hoặc trí tuệ nhân tạo để đánh giá "giá trị" của một trạng thái nhật định mà không cần phải mở rộng tìm kiếm đến trạng thái tiếp theo. 

 - Nó nhận vào 1 trạng thái của trò chơi/bài toán
 - Trả về một giá trị số để đánh giá mức độ tốt/xấu của trạng thái đó

## Static eval func trong cờ vua
 ### Nguyên lý 
 - Hàm đánh giá tĩnh trong cờ vua phân tích trạng thái bàn cờ hiện tại và trả về một giá trị sô biểu thị mức thuận lợi của vị thế. 
    + giá trị dương: có lợi cho quân trắng
    + giá trị âm: có lợi cho quân đen
    + giá trị 0: vị thế cân bằng 
- công thức tổng quát:
 Eval(position) = t1 * evaluate_material + t2 *evaluate_king_safety + t3 * W_pawn_structure + t4 *  + W_mobility + t5 * W_center_control + t6 * W_piece_square + t7 * W_evaluation_pieces + t8 * W_tempo  
  ti (i = 1,8): hệ số tối ưu của từng hàm/yếu tố -> xác định 

 ### evaluate_material - đánh giá giá trị quân cờ 
 - Dựa trên nguyên tắc rằng mỗi quân cờ có một giá trị vật chất cụ thể thể hiện sức mạnh của nó tương đối trên toàn bàn cờ.
 - Cung cấp nền tảng đánh giá cơ bản dựa trên sự cân bằng về vật chất giữa hai bên -> xác định liệu một bên có lợi thế về vật chất không.
   Cách xây dựng
 - sử dụng 1 hàm ánh xạ từng loại quân cờ đến giá trị số của nó
 - duyệt qua toàn bộ bàn cờ -> xác định quân cờ
 - cộng giá trị quân cờ nếu là quân trắng và ngược lại

 ### evaluate_king_safety
 - Mục tiêu cuối cùng trong cờ vua là **tấn công và chiếu hết vua đối phương**. Vì vậy, an toàn của vua là yếu tố quan trọng hàng đầu, đặc biệt trong giai đoạn trung và tàn cuộc. Vua được bảo vệ tốt sẽ ít bị tấn công hơn.

  Cách xây dựng
- Xác định vị trí của vua trắng và vua đen
- kiểm tra các ô phía trước vua (dựa theo màu)
- Cộng điểm nếu có tốt bảo vệ trước vua trắng và ngược lại

 ### evaluate_pawn_structure
- Cấu trúc quân tốt là xương sống của vị thế, ảnh hưởng đến tính linh hoạt và tiềm năng tấn công/phòng thủ lâu dài.
- **Tốt đôi (doubled penalty)** thường bị coi là bất lợi vì chúng không thể bảo vệ lẫn nhau 
-**tốt cô lập (isolated penalty)** dễ bị tấn công và khó được bảo vệ

  Cách xây dựng
- xác định vị trí của tất cả các quân tốt (trắng và đen)
- xác định cột có nhiều hơn 1 tốt và duyệt từng cột một 
- áp dụng hình phạt trừ điểm khi phát hiện tốt đôi và tốt cô lập với quân trắng và ngược lại

 ### evaluate_ mobility

 ### evaluate_center_control
 - Kiểm soát trung tâm bàn cờ là một chiến lược phổ biến trong cờ vua. Việc kiểm soát khu vực này giúp người chơi vừa phòng thủ lãnh thổ của mình, vừa tấn công lãnh thổ đối thủ dễ dàng hơn.
  Cách xây dựng
- xác định các ô trung tâm (D4, D5,E4,E5)
- cộng điểm cho mỗi ô trung tâm có quân trắng và ngược lại với quân đen.

 ### evaluate_piece_square
- Mỗi loại quân cờ có những vị trí tốt và kém trên bàn cờ, ảnh hưởng đến hiệu quả hoạt động của chúng. Ví dụ, đẩy tốt và trung tâm trong khai cuộc là một chiến lược tốt. 
- thúc đẩy AI đặt quân vào vị trí chiến lược và khuyến khích phát triển quân cờ theo nguyên tắc cờ vua tốt.
  Cách xây dựng
- Xác định bảng giá trị vị trí cho từng loại quân cờ
- mỗi ô trên bàn cờ có một giá trị cụ thể cho từng loại quân 
- cộng/trừ giá trị tương ứng tuỳ thuộc vào màu quân và vị trí

 ### evaluate_tactical_positions
- đánh giá các vị trí chiến thuật đặc biệt giúp AI phát hiện và tận dụng các cơ hội chiến thuật tinh tế hơn:
  + Xe ở trên cột mở có hiệu quả cao hơn rất nhiều so với xe bị chặn
  + Mã bị vị trí outpost(được bảo vệ bởi tốt, không bị đe doạ ) khá mạnh
  + Tượng trên đường chéo dài có thể ảnh hưởng nhiều tới bàn cờ
  + hậu di chuyển quá sớm thường là bất lợi về mặt phát triển.
   
  Cách xây dựng
- Xác định và đánh giá các tình huống chiến thuật cụ thể 

 ### evaluate_tempo
- Tempo trong cờ vua là số nước đi cần để đạt được một mục tiêu. Nếu một người chơi mất nhiều nước đi hơn cần thiết để thực hiện một ý tưởng, họ bị mất tempo. 
. Mất tempo nghĩa là mất lợi thế về thời gian.
- Khuyến khích AI hoàn thành mục tiêu với ít nước đi nhất có thể.
  Cách xây dựng
- đếm số nước đi đã thực hiện(board.move_stack)
- áp dụng 1 hệ số tempo_weight
- thêm điểm âm khi số nước tăng để khuyến khích giải quyết nhanh.

## tài liệu tham khảo
https://arxiv.org/pdf/2007.02130
https://byvn.net/nNvJ
https://byvn.net/AtEV
https://www.graham-kendall.com/papers/kw2001a.pdf
https://byvn.net/4CgQ
https://www.chessprogramming.org/Evaluation
https://chessify.me/blog/chess-engine-evaluation
