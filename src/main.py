# File khoi chay chinh
from board.board_manager import BoardManager
import chess

def main():
    print("CHESS AI")
    print("Ban cam quan trang. Nhap nuoc di theo dinh dang UCI (VD: e2e4, g1f3).")
    print("Go 'quit' de thoat game.")
    
    game = BoardManager()
    
    while not game.is_game_over():
        game.print_board()
        
        # Lượt của người chơi (Trắng)
        if game.board.turn == chess.WHITE:
            user_input = input("Toi luot ban (Trang): ").strip().lower()
            
            if user_input == 'quit':
                print("Da thoat game.")
                break
                
            # Nếu người dùng nhập sai, bắt nhập lại
            if not game.play_human_move(user_input):
                continue 
        
        # Lượt của AI (Đen)
        else:
            game.play_ai_move(depth=3)

if __name__ == "__main__":
    main()