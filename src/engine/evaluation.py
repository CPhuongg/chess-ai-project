# Ham luong gia ban co
import chess
from .constants import PIECE_VALUES, PST

def evaluate_board(board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if not piece:
            continue
            
        val = PIECE_VALUES[piece.piece_type]
        
        if piece.color == chess.WHITE:
            pst_val = PST[piece.piece_type][square]
            score += (val + pst_val)
        else:
            pst_val = PST[piece.piece_type][chess.square_mirror(square)]
            score -= (val + pst_val)
            
    return score
