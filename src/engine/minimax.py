# Thuat toan Minimax & Alpha-Beta
import chess
from .evaluation import evaluate_board

def minimax(board, depth, alpha, beta, is_maximizing):
    # Điều kiện dừng: Hết độ sâu hoặc kết thúc game
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    best_move = None

    if is_maximizing:
        max_eval = float('-inf')
        # Tối ưu: Sắp xếp nước đi (ăn quân lên trước) giúp Alpha-Beta nhanh hơn
        for move in board.legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Cắt tỉa Alpha
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in board.legal_moves:
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
                
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Cắt tỉa Beta
        return min_eval, best_move