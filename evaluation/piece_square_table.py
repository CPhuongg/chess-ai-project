# Path: evaluation/piece_square_table.py
# Description:
# Defines positional piece-square tables for all chess piece types.
# These tables assign bonus or penalty points based on where a piece is placed on the board.
# Tables are used during evaluation to encourage pieces to move to better squares.
# Supports both opening/middlegame (pawns, king_start) and endgame (pawns_end, king_end) phases.
# Includes utility methods to read values with proper orientation for white or black pieces.

import chess

class PieceSquareTable:
    # Các bảng điểm cho từng quân cờ
    pawns = [
         0,   0,   0,   0,   0,   0,   0,   0,
        50,  50,  50,  50,  50,  50,  50,  50,
        10,  10,  20,  30,  30,  20,  10,  10,
         5,   5,  10,  25,  25,  10,   5,   5,
         0,   0,   0,  20,  20,   0,   0,   0,
         5,  -5, -10,   0,   0, -10,  -5,   5,
         5,  10,  10, -20, -20,  10,  10,   5,
         0,   0,   0,   0,   0,   0,   0,   0
    ]
    
    pawns_end = [
         0,   0,   0,   0,   0,   0,   0,   0,
        80,  80,  80,  80,  80,  80,  80,  80,
        50,  50,  50,  50,  50,  50,  50,  50,
        30,  30,  30,  30,  30,  30,  30,  30,
        20,  20,  20,  20,  20,  20,  20,  20,
        10,  10,  10,  10,  10,  10,  10,  10,
        10,  10,  10,  10,  10,  10,  10,  10,
         0,   0,   0,   0,   0,   0,   0,   0
    ]

    rooks = [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, 10, 10, 10, 10, 5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        0, 0, 0, 5, 5, 0, 0, 0
    ]

    knights = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ]

    bishops = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ]

    queens = [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ]

    king_start = [
        -80, -70, -70, -70, -70, -70, -70, -80,
        -60, -60, -60, -60, -60, -60, -60, -60,
        -40, -50, -50, -60, -60, -50, -50, -40,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, -5, -5, -5, -5, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20
    ]

    king_end = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -5, 0, 5, 5, 5, 5, 0, -5,
        -10, -5, 20, 30, 30, 20, -5, -10,
        -15, -10, 35, 45, 45, 35, -10, -15,
        -20, -15, 30, 40, 40, 30, -15, -20,
        -25, -20, 20, 25, 25, 20, -20, -25,
        -30, -25, 0, 0, 0, 0, -25, -30,
        -50, -30, -30, -30, -30, -30, -30, -50
    ]

    # Lưu trữ bảng điểm cho từng quân cờ
    tables = []

    @staticmethod
    def read(table, square: int, is_white: bool):
        if is_white:
            square = chess.square(chess.square_file(square), 7 - chess.square_rank(square))
        return table[square]

    @staticmethod
    def __init__():
        PieceSquareTable.tables = [None] * 6  # 6 quân cờ: Pawn, Rook, Knight, Bishop, Queen, King
        PieceSquareTable.tables[0] = PieceSquareTable.pawns  # Pawn
        PieceSquareTable.tables[1] = PieceSquareTable.rooks  # Rook
        PieceSquareTable.tables[2] = PieceSquareTable.knights  # Knight
        PieceSquareTable.tables[3] = PieceSquareTable.bishops  # Bishop
        PieceSquareTable.tables[4] = PieceSquareTable.queens  # Queen
        PieceSquareTable.tables[5] = PieceSquareTable.king_start  # King (start position)

    @staticmethod
    def get_flipped_table(table):
        """Lật bảng điểm cho quân cờ đối phương"""
        flipped_table = [0] * len(table)
        for i in range(len(table)):
            flipped_coord = chess.Square(63 - i)  # Đảo vị trí quân cờ
            flipped_table[flipped_coord] = table[i]
        return flipped_table

    @staticmethod
    def piece_square_value(piece, square):
        """Trả về giá trị của một quân cờ ở một ô cụ thể"""
        return PieceSquareTable.tables[piece][square]