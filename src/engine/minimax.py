import chess
import time
from src.engine.nnue_evaluation import HybridEvaluation

class ChessEngine:
    def __init__(self, depth, use_opening_book=True):
        # Xử lý depth nếu là string (từ UI)
        if isinstance(depth, str):
            depth_map = {"Easy": 2, "Medium": 3, "Hard": 4, "Expert": 5}
            depth = depth_map.get(depth, 3)
        self.depth = int(depth)
        self.difficulty = self._depth_to_difficulty(self.depth)
        self.evaluator = HybridEvaluation(nnue_weight=0.7)
        self.nodes_searched = 0
        self.use_opening_book = use_opening_book
        self.opening_book = None

    def _depth_to_difficulty(self, depth):
        if depth <= 2: return "Easy"
        elif depth <= 3: return "Medium"
        elif depth <= 4: return "Hard"
        else: return "Expert"

    def set_difficulty(self, depth):
        self.depth = max(1, min(int(depth), 5))
        self.difficulty = self._depth_to_difficulty(self.depth)

    def order_moves(self, board, moves):
        move_scores = []
        for move in moves:
            score = 0
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                if victim:
                    attacker = board.piece_at(move.from_square)
                    if attacker:
                        score = 10 * victim.piece_type - attacker.piece_type
            if move.promotion:
                score += 800
            move_scores.append((move, score))
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def minimax(self, board, depth, alpha, beta, maximizing):
        self.nodes_searched += 1
        if board.is_game_over():
            if board.is_checkmate():
                return -10000 if maximizing else 10000
            return 0
        if depth == 0:
            return self.evaluator.evaluate(board)

        moves = self.order_moves(board, list(board.legal_moves))
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                board.push(move)
                eval = self.minimax(board, depth-1, alpha, beta, False)
                board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                board.push(move)
                eval = self.minimax(board, depth-1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_best_move(self, board, time_limit=5.0):
        self.nodes_searched = 0
        start_time = time.time()
        best_move = None
        best_score = float('-inf')

        for current_depth in range(1, self.depth + 1):
            if time.time() - start_time > time_limit:
                break
            current_best_move = None
            current_best_score = float('-inf')
            alpha = float('-inf')
            beta = float('inf')
            moves = self.order_moves(board, list(board.legal_moves))
            for move in moves:
                board.push(move)
                score = self.minimax(board, current_depth-1, alpha, beta, False)
                board.pop()
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move
                alpha = max(alpha, score)
            if current_best_move:
                best_move = current_best_move
                best_score = current_best_score
        return best_move

    def best_move(self, board, time_limit=2.0):
        """Giao diện tương thích với UI cũ (trả về tuple)"""
        move = self.get_best_move(board, time_limit)
        score = 0
        if move:
            board.push(move)
            score = self.evaluator.evaluate(board)
            board.pop()
        info = {"nodes": self.nodes_searched, "depth": self.depth}
        return move, score, info