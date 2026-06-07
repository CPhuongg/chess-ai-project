# Áp dụng NNUE để tính scores cho hàm evaluation 
## Tập dữ liệu để train
- Lấy dữ liệu trên kaggle và lichess.
## Các bước train
- Step 1: Encoding fen dùng HalfKA hoặc HalfKP, ý tưởng chính là biểu diễn thế cờ của quân phòng thủ (HalfKP) và tấn công (HalfKA)  
*HalfKP (Half King-Piece Encoding): Dựa vào vị trí của quân vua để biểu diễn vị trí các quân cờ còn lại của quân phòng thủ.  
*HalfKA (Half King-Attacker Encoding): Vẫn dựa vào vị trí của quân vua để biểu diễn vị trí, mức độ nguy hiểm của quân cờ tấn công.  
Điều này giúp chúng ta đánh giá được toàn bộ thế cờ, giúp mô hình học được nhanh hơn và tiết kiệm không gian lưu trữ.
- Step 2: Build model, model sẽ giống với model neural network bình thuờng gồm có input layer (nhận vào các mã fen sau khi được encode ở bước 1), hidden layer (tùy vào kết quả để điều chỉnh số hidden layer cho hợp lý) và cuối cùng là output layer (dùng hàm ReLU activation) để trả về output là scores.
- Step 3: Train model: Dựa vào tập dữ liệu đã kiếm được để train, khoảng 1tr-2tr thế cờ, ta sẽ uớc lượng hàm loss bằng MSELoss(), dùng Adam kết hợp tuning để tìm learning rate hợp lí.

Code lần 1(Sử dụng model với 5 hidden layers): https://www.kaggle.com/code/sonspeed/train-your-own-stockfish-nnue-490aeb
Nhận xét: Model bị overfit, cần giảm lượng hidden layers và thêm một số cải tiến khác.