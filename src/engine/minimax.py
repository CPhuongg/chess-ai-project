"""
minimax.py  –  Negamax + Alpha-Beta pruning + Quiescence search.
Supports per-difficulty depth and soft time limits.
"""

import chess
import time
from typing import Optional
from src.engine.evaluation import evaluate
from src.engine.constants import (
    INFINITY, CHECKMATE_SCORE, DEFAULT_DEPTH, QUIESCENCE_DEPTH,
    DIFFICULTY,
)

_PV = {chess.PAWN:100, chess.KNIGHT:320, chess.BISHOP:330,
       chess.ROOK:500, chess.QUEEN:900, chess.KING:20000}


def _mvv_lva(board: chess.Board, move: chess.Move) -> int:
    if not board.is_capture(move):
        return 0
    victim   = board.piece_at(move.to_square)
    attacker = board.piece_at(move.from_square)
    v = _PV.get(victim.piece_type,   0) if victim   else 0
    a = _PV.get(attacker.piece_type, 0) if attacker else 0
    return v * 10 - a


def _order(board: chess.Board, moves) -> list:
    def key(m):
        s = _mvv_lva(board, m)
        if m.promotion: s += _PV.get(m.promotion, 0)
        if board.gives_check(m): s += 60
        return s
    return sorted(moves, key=key, reverse=True)


def _quiescence(board, alpha, beta, depth):
    # Đã sửa: Quy điểm số về góc nhìn của phe đang đến lượt
    stand_pat = evaluate(board) * (1 if board.turn == chess.WHITE else -1)
    
    if depth == 0:         return stand_pat
    if stand_pat >= beta:  return beta
    if stand_pat > alpha:  alpha = stand_pat
    
    # Tối ưu: Dùng generate_legal_captures() để lấy danh sách nước bắt quân nhanh hơn
    captures = list(board.generate_legal_captures())
    for move in _order(board, captures):
        board.push(move)
        score = -_quiescence(board, -beta, -alpha, depth - 1)
        board.pop()
        if score >= beta:  return beta
        if score > alpha:  alpha = score
    return alpha


def _negamax(board, depth, alpha, beta, stats, deadline):
    stats["nodes"] += 1
    if board.is_game_over():
        score = evaluate(board)
        # Đã sửa: Trừ đi độ sâu (depth) vào điểm chiếu bí để bot chọn đường ngắn nhất
        if abs(score) >= CHECKMATE_SCORE:
            score = score + depth if score > 0 else score - depth
        return score * (1 if board.turn == chess.WHITE else -1)
        
    if depth == 0:
        return _quiescence(board, alpha, beta, QUIESCENCE_DEPTH)

    for move in _order(board, board.legal_moves):
        if deadline and time.perf_counter() > deadline:
            break
        board.push(move)
        score = -_negamax(board, depth - 1, -beta, -alpha, stats, deadline)
        board.pop()
        if score > alpha: alpha = score
        if alpha >= beta:
            stats["cutoffs"] += 1
            break
    return alpha


class ChessEngine:
    """
    Public engine API.

    Parameters
    ----------
    difficulty : "Easy" | "Medium" | "Hard" | "Expert"
    depth      : override depth (ignores difficulty)
    """

    def __init__(self, difficulty: str = "Medium", depth: int = None):
        cfg         = DIFFICULTY.get(difficulty, DIFFICULTY["Medium"])
        self.depth  = depth if depth is not None else cfg["depth"]
        self.tl     = cfg["time_limit"]
        self.difficulty = difficulty

    def best_move(
        self,
        board: chess.Board,
        time_limit: Optional[float] = None,
    ) -> tuple:
        """Return (move, white_score_cp, info_dict)."""
        if board.is_game_over():
            return None, evaluate(board), {}

        limit    = time_limit if time_limit is not None else self.tl
        deadline = time.perf_counter() + limit if limit else None
        stats    = {"nodes": 0, "cutoffs": 0}
        start    = time.perf_counter()

        best_move  = None
        best_score = -INFINITY
        alpha      = -INFINITY

        for move in _order(board, board.legal_moves):
            board.push(move)
            score = -_negamax(board, self.depth - 1, -INFINITY, -alpha, stats, deadline)
            board.pop()
            if score > best_score:
                best_score = score
                best_move  = move
            if score > alpha:
                alpha = score
            if deadline and time.perf_counter() > deadline:
                break

        elapsed     = time.perf_counter() - start
        white_score = best_score if board.turn == chess.WHITE else -best_score
        info = {
            "depth":     self.depth,
            "nodes":     stats["nodes"],
            "cutoffs":   stats["cutoffs"],
            "time_ms":   round(elapsed * 1000, 1),
            "score_cp":  white_score,
            "best_move": best_move.uci() if best_move else None,
            "difficulty":self.difficulty,
        }
        return best_move, white_score, info