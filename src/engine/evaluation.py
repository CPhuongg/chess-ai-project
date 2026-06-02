"""
evaluation.py  –  Static board evaluation (material + PST + mobility).
Positive  → White is better.
Negative  → Black is better.
"""

import chess
from src.engine.constants import (
    PIECE_VALUES, PST, KING_MID_TABLE, KING_END_TABLE,
    ENDGAME_THRESHOLD, CHECKMATE_SCORE, STALEMATE_SCORE,
)


def _mirror(sq: int) -> int:
    return (7 - sq // 8) * 8 + sq % 8


def _is_endgame(board: chess.Board) -> bool:
    total = 0
    for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
        total += (len(board.pieces(pt, chess.WHITE))
                + len(board.pieces(pt, chess.BLACK))) * PIECE_VALUES[pt]
    return total <= ENDGAME_THRESHOLD


def evaluate(board: chess.Board) -> int:
    """Return centipawn score from White's POV. Handles terminal states."""
    if board.is_checkmate():
        return -CHECKMATE_SCORE if board.turn == chess.WHITE else CHECKMATE_SCORE
    if board.is_stalemate() or board.is_insufficient_material():
        return STALEMATE_SCORE
    if board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return STALEMATE_SCORE

    endgame = _is_endgame(board)
    score   = 0

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None:
            continue
        sign     = 1 if piece.color == chess.WHITE else -1
        score   += sign * PIECE_VALUES[piece.piece_type]
        tsq      = sq if piece.color == chess.WHITE else _mirror(sq)
        if piece.piece_type == chess.KING:
            table = KING_END_TABLE if endgame else KING_MID_TABLE
        else:
            table = PST[piece.piece_type]
        score += sign * table[tsq]

    # Đã đóng băng khối lệnh tính Mobility để tối ưu tốc độ duyệt (nodes/sec)
    # mobility = board.legal_moves.count()
    # score   += mobility if board.turn == chess.WHITE else -mobility
    
    return score