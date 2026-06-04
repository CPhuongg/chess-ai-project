import chess
import chess.pgn
import time
from datetime import datetime
from src.engine.minimax import ChessEngine
from src.engine.nnue_evaluation import HybridEvaluation

class ChessClock:
    def __init__(self, board_mgr):
        self.mgr = board_mgr
    def is_flagged(self, color):
        if color == chess.WHITE:
            return self.mgr.time_white <= 0
        else:
            return self.mgr.time_black <= 0
    def update(self, color, elapsed):
        # Không cần vì BoardManager tự cập nhật
        pass
    def fmt(self, color):
        """Trả về chuỗi thời gian định dạng MM:SS"""
        seconds = self.mgr.time_white if color == chess.WHITE else self.mgr.time_black
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    @property
    def difficulty(self):
        """Trả về độ khó dạng string dựa trên depth"""
        depth_map = {2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert"}
        return depth_map.get(self.depth, "Medium")
    
    @difficulty.setter
    def difficulty(self, value):
        """Cho phép gán độ khó bằng string"""
        depth_map = {"Easy": 2, "Medium": 3, "Hard": 4, "Expert": 5}
        self.depth = depth_map.get(value, 3)

class BoardManager:
    def __init__(self, base_time=600, increment=0):
        self.board = chess.Board()
        self.game_mode = "human_vs_ai"
        self.ai_color = chess.BLACK
        self.time_white = base_time
        self.time_black = base_time
        self.increment = increment
        self.last_move_time = time.time()
        self.game_active = True
        self.ai_engine = ChessEngine(depth=3)
        self.evaluator = HybridEvaluation(nnue_weight=0.7)
        self.move_history = []
        self._last_move = None   # Lưu nước đi cuối
        self.captured_pieces = {"w": [], "b": []}        
        # Đồng hồ cho UI
        self.clock = ChessClock(self)
        
    # Property để tương thích
    @property
    def is_game_over(self):
        return not self.game_active or self.board.is_game_over()
    
    @property
    def winner(self):
        return self._get_winner()
    
    @property
    def turn(self):
        return "white" if self.board.turn == chess.WHITE else "black"
    
    @property
    def board_fen(self):
        return self.board.fen()
    
    @property
    def last_move(self):
        return self._last_move
    
    def is_check(self):
        return self.board.is_check()
    
    def is_in_check(self):
        return self.board.is_check()
    
    def get_time(self, color):
        return self.time_white if color == chess.WHITE else self.time_black
    
    # Lịch sử nước đi dạng SAN cho UI
    def move_history_san(self):
        """Trả về danh sách các nước đi dưới dạng ký hiệu cờ vua (SAN)"""
        return [self.board.san(move) for move in self.board.move_stack]
    
    def reset_game(self, base_time=None, increment=None):
        self.board.reset()
        self.move_history.clear()
        self._last_move = None
        if base_time is not None:
            self.time_white = base_time
            self.time_black = base_time
        if increment is not None:
            self.increment = increment
        self.last_move_time = time.time()
        self.game_active = True
        
    def set_difficulty(self, depth):
        self.ai_engine.depth = max(1, min(int(depth), 5))
        
    def set_mode(self, mode, ai_color=chess.BLACK):
        self.game_mode = mode
        if mode == "human_vs_ai":
            self.ai_color = ai_color
        else:
            self.ai_color = None
            
    def make_move(self, move):
        if not self.game_active:
            return False, False, None, "Game ended"
        if move not in self.board.legal_moves:
            return False, False, None, "Invalid move"
        self._apply_move(move)
        if self.board.is_game_over() or not self.game_active:
            winner = self._get_winner()
            self.game_active = False
            return True, True, winner, None
        if self.game_mode == "human_vs_ai" and self.board.turn == self.ai_color:
            ai_move = self.get_ai_move()
            if ai_move:
                self._apply_move(ai_move)
        if self.board.is_game_over() or not self.game_active:
            winner = self._get_winner()
            self.game_active = False
            return True, True, winner, None
        return True, False, None, None
        
    def _apply_move(self, move):
        # Lưu thông tin bắt quân trước khi push
        captured_piece = None
        if self.board.is_capture(move):
            captured_piece = self.board.piece_at(move.to_square)
        
        self.move_history.append(self.board.copy())
        self.board.push(move)
        
        # Cập nhật captured pieces
        if captured_piece:
            color = "w" if captured_piece.color == chess.WHITE else "b"
            self.captured_pieces[color].append(captured_piece.piece_type)

        # Cập nhật thời gian
        now = time.time()
        elapsed = now - self.last_move_time
        if self.board.turn == chess.WHITE:  # vừa đi là đen
            self.time_black -= elapsed
            self.time_black += self.increment
        else:
            self.time_white -= elapsed
            self.time_white += self.increment
        self.last_move_time = now
        self.time_white = max(0, self.time_white)
        self.time_black = max(0, self.time_black)
        if self.time_white <= 0 or self.time_black <= 0:
            self.game_active = False
        
        # Lưu last_move
        self._last_move = move
            
    def get_ai_move(self):
        if self.board.is_game_over():
            return None
        time_left = self.time_white if self.board.turn == chess.WHITE else self.time_black
        think_time = min(max(0.5, time_left * 0.1), 5.0)
        return self.ai_engine.get_best_move(self.board, time_limit=think_time)
        
    def undo_move(self):
        if len(self.move_history) > 0:
            self.board = self.move_history.pop()
            self._last_move = None
            self.game_active = True
            return True
        return False
        
    def save_game(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"saved_game_{timestamp}.pgn"
        game = chess.pgn.Game()
        game.headers["Event"] = "Chess AI Game"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["White"] = "Human" if self.ai_color == chess.BLACK else "AI"
        game.headers["Black"] = "Human" if self.ai_color == chess.WHITE else "AI"
        game.headers["Result"] = self._get_result_string()
        node = game
        for move in self.board.move_stack:
            node = node.add_variation(move)
        with open(filename, "w") as f:
            f.write(str(game))
        return filename
        
    def load_game(self, filename):
        try:
            with open(filename, "r") as f:
                game = chess.pgn.read_game(f)
            if game is None:
                return False
            board = game.board()
            for move in game.mainline_moves():
                board.push(move)
            self.board = board
            self.move_history = []
            self._last_move = None
            self.game_active = not board.is_game_over()
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
            
    def get_status(self):
        return {
            "board_fen": self.board.fen(),
            "turn": "White" if self.board.turn == chess.WHITE else "Black",
            "white_time": self.time_white,
            "black_time": self.time_black,
            "game_over": self.is_game_over,
            "winner": self.winner,
            "is_check": self.board.is_check(),
            "captured_pieces": self.captured_pieces,
        }
    
    def result_with_flag(self):
        """Trả về kết quả trận đấu với lý do (dùng cho màn hình kết thúc)"""
        if not self.is_game_over:
            return "Game in progress"
        if self.time_white <= 0:
            return "Black wins (White timeout)"
        if self.time_black <= 0:
            return "White wins (Black timeout)"
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            return f"{winner} wins by checkmate"
        if self.board.is_stalemate():
            return "Draw by stalemate"
        if self.board.is_insufficient_material():
            return "Draw by insufficient material"
        if self.board.is_seventy_five_moves():
            return "Draw by 75-move rule"
        if self.board.is_fivefold_repetition():
            return "Draw by fivefold repetition"
        return "Game over"
    
    def game_over_reason(self):
        """Trả về lý do kết thúc trận đấu (dùng cho UI)"""
        if not self.is_game_over:
            return None
        if self.time_white <= 0:
            return "White ran out of time"
        if self.time_black <= 0:
            return "Black ran out of time"
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            return f"{winner} won by checkmate"
        if self.board.is_stalemate():
            return "Stalemate"
        if self.board.is_insufficient_material():
            return "Insufficient material"
        if self.board.is_seventy_five_moves():
            return "75-move rule"
        if self.board.is_fivefold_repetition():
            return "Fivefold repetition"
        return "Game over"
        
    def _get_winner(self):
        if not self.board.is_game_over():
            return None
        if self.board.is_checkmate():
            return "black" if self.board.turn == chess.WHITE else "white"
        return None
        
    def _get_result_string(self):
        winner = self._get_winner()
        if winner == "white":
            return "1-0"
        elif winner == "black":
            return "0-1"
        return "1/2-1/2"