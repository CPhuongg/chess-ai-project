# Path: evaluation/precomputed_evaluation_data.py
# Description:
# Precomputes and stores pawn shield squares around each king square.
# Pawn shields are defensive pawn structures that protect the king.
# Separate data for white and black to account for board symmetry.
# Used in king safety evaluation to penalize missing pawn cover.
# The initialize() method fills two lists of size 64 (one per square index).

import chess

class PrecomputedEvaluationData:
    pawn_shield_squares_white = []
    pawn_shield_squares_black = []

    @staticmethod
    def initialize():
        # Initialize the pawn shield squares for both white and black
        PrecomputedEvaluationData.pawn_shield_squares_white = [[] for _ in range(64)]
        PrecomputedEvaluationData.pawn_shield_squares_black = [[] for _ in range(64)]
        for square_index in range(64):
            PrecomputedEvaluationData.create_pawn_shield_square(square_index)

    @staticmethod
    def create_pawn_shield_square(square_index):
        shield_indices_white = []
        shield_indices_black = []
        file = square_index % 8
        rank = square_index // 8

        # Add shield squares for white
        for file_offset in range(-1, 2):
            PrecomputedEvaluationData.add_if_valid(file + file_offset, rank + 1, shield_indices_white)
            PrecomputedEvaluationData.add_if_valid(file + file_offset, rank - 1, shield_indices_black)

        # Add shield squares for black
        for file_offset in range(-1, 2):
            PrecomputedEvaluationData.add_if_valid(file + file_offset, rank + 2, shield_indices_white)
            PrecomputedEvaluationData.add_if_valid(file + file_offset, rank - 2, shield_indices_black)

        PrecomputedEvaluationData.pawn_shield_squares_white[square_index] = shield_indices_white
        PrecomputedEvaluationData.pawn_shield_squares_black[square_index] = shield_indices_black

    @staticmethod
    def add_if_valid(file, rank, list_):
        if 0 <= file < 8 and 0 <= rank < 8:
            list_.append(chess.square(file, rank))

# Initialize the PrecomputedEvaluationData
PrecomputedEvaluationData.initialize()

# Print pawn shield squares for a particular square (e.g., square 0)
print(PrecomputedEvaluationData.pawn_shield_squares_white[0])  # Shield squares for white at square 0
