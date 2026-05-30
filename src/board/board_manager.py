# Wrapper cho thu vie# Wrapper cho thu vien python-chess
import chess
from engine.minimax import minimax

class BoardManager:
    def __init__(self):
        self.board = chess.Board()

    def print_board(self):
        print("\n--- Ban co hien tai ---")
        print(self.board)
        print("-----------------------\n")

    def play_human_move(self, move_str):
        """Xử lý nước đi của người chơi (nhập từ bàn phím)"""
        try:
            # Chuyển chuỗi (vd: e2e4) thành đối tượng Move
            move = chess.Move.from_uci(move_str)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            else:
                print("Nuoc di khong hop le! Hay nhap lai.")
                return False
        except ValueError:
            print("Cu phap khong hop le! Hay nhap dang 'e2e4'.")
            return False

    def play_ai_move(self, depth=3):
        """Gọi AI suy nghĩ và đi quân"""
        print(f"AI dang suy nghi (Do sau {depth})...")
        # is_maximizing = False nếu AI cầm quân Đen
        is_maximizing = self.board.turn == chess.WHITE 
        
        score, best_move = minimax(self.board, depth, alpha=float('-inf'), beta=float('inf'), is_maximizing=is_maximizing)
        
        if best_move:
            self.board.push(best_move)
            print(f"AI Quyet dinh di: {best_move} (Diem danh gia: {score})")
        else:
            print("AI khong tim thay nuoc di (Co the da bi chieu het!)")

    def is_game_over(self):
        if self.board.is_checkmate():
            print("CHIEU HET! Tro choi ket thuc.")
            return True
        if self.board.is_stalemate():
            print("HOA! (Stalemate)")
            return True
        if self.board.is_insufficient_material():
            print("HOA! Khong di quan de chieu het.")
            return True
        return Falsen python-chess
