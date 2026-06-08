# Path: evaluation/evaluation.py
# Description:
# Main evaluation engine that computes a numeric score for a given chess board.
# Combines multiple evaluation components:
#   - Material balance (piece values)
#   - Piece-square table bonuses
#   - Pawn structure (passed pawns, isolated pawns)
#   - King safety (pawn shield)
#   - Mop-up evaluation (endgame king activity)
# Dynamically adjusts between opening and endgame using an endgame transition factor.
# Returns a score from the perspective of the side to move.

import chess
from evaluation.piece_square_table import PieceSquareTable
from evaluation.precomputed_evaluation_data import PrecomputedEvaluationData

class Evaluation:
    pawn_value = 100
    knight_value = 300
    bishop_value = 320
    rook_value = 500
    queen_value = 900

    passed_pawn_bonuses = [0, 120, 80, 50, 30, 15, 15]
    isolated_pawn_penalty_by_count = [0, -10, -25, -50, -75, -75, -75, -75, -75]
    king_pawn_shield_scores = [4, 7, 4, 3, 6, 3]

    endgame_material_start = rook_value * 2 + bishop_value + knight_value

    def __init__(self):
        self.white_eval = EvaluationData()
        self.black_eval = EvaluationData()

    def evaluate(self, board: chess.Board) -> int:
        white_eval = self.white_eval
        black_eval = self.black_eval

        white_material = self.get_material_info(chess.WHITE, board)
        black_material = self.get_material_info(chess.BLACK, board)

        # Score based on number (and type) of pieces on board
        white_eval.material_score = white_material.material_score
        black_eval.material_score = black_material.material_score

        # Score based on positions of pieces
        white_eval.piece_square_score = self.evaluate_piece_square_tables(
            True,
            black_material.endgame_t,
            board
        )
        black_eval.piece_square_score = self.evaluate_piece_square_tables(
            False,
            white_material.endgame_t,
            board
        )

        # Encourage using own king to push enemy king to edge of board in winning endgame
        white_eval.mop_up_score = self.mop_up_eval(
            True,
            white_material,
            black_material,
            board
        )
        black_eval.mop_up_score = self.mop_up_eval(
            False,
            black_material,
            white_material,
            board
        )

        white_eval.pawn_score = self.evaluate_pawns(chess.WHITE, board)
        black_eval.pawn_score = self.evaluate_pawns(chess.BLACK, board)

        white_eval.pawn_shield_score = self.king_pawn_shield(
            chess.WHITE,
            black_material,
            black_eval.piece_square_score,
            board
        )
        black_eval.pawn_shield_score = self.king_pawn_shield(
            chess.BLACK,
            white_material,
            white_eval.piece_square_score,
            board
        )

        white_eval.center_control_score = self.evaluate_center_control(chess.WHITE, board)
        black_eval.center_control_score = self.evaluate_center_control(chess.BLACK, board)

        perspective = 1 if board.turn == chess.WHITE else -1
        eval_score = white_eval.sum() - black_eval.sum()
        score = eval_score * perspective
        if board.is_check():
            score -= 45
        return score

    def evaluate_center_control(self, colour_index: int, board: chess.Board) -> int:
        """Reward occupying and attacking central squares."""
        center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
        extended_center = [
            chess.C3, chess.D3, chess.E3, chess.F3,
            chess.C4, chess.F4, chess.C5, chess.F5,
            chess.C6, chess.D6, chess.E6, chess.F6,
        ]
        score = 0

        for square in center_squares:
            piece = board.piece_at(square)
            if piece and piece.color == colour_index:
                score += 18
            score += 6 * len(board.attackers(colour_index, square))

        for square in extended_center:
            piece = board.piece_at(square)
            if piece and piece.color == colour_index:
                score += 5
            if board.is_attacked_by(colour_index, square):
                score += 2

        return score

    def king_pawn_shield(self, colour_index: int, enemy_material, enemy_piece_square_score: float, board: chess.Board) -> int:
        if enemy_material.endgame_t >= 1:
            return 0

        penalty = 0
        is_white = colour_index == chess.WHITE
        friendly_pawn = chess.PAWN
        king_square = board.king(colour_index)
        king_file = chess.square_file(king_square)

        if king_file <= 2 or king_file >= 5:
            squares = (
                PrecomputedEvaluationData.pawn_shield_squares_white[int(king_square)]
                if is_white else
                PrecomputedEvaluationData.pawn_shield_squares_black[int(king_square)]
            )

            for i in range(len(squares) // 2):
                shield_square_index = squares[i]
                piece = board.piece_at(shield_square_index)
                if piece is None or piece.piece_type != friendly_pawn or piece.color != colour_index:
                    penalty += self.king_pawn_shield_scores[i]

            penalty *= penalty
        else:
            enemy_development_score = max((enemy_piece_square_score + 10) / 130, 0, 1)
            uncastled_king_penalty = int(50 * enemy_development_score)
            # chưa sử dụng

        open_file_against_king_penalty = 0
        if (enemy_material.num_rooks > 1 or
            (enemy_material.num_rooks > 0 and enemy_material.num_queens > 0)
        ):
            clamped_king_file = max(1, min(6, king_file))
            my_pawns = enemy_material.enemy_pawns
            for attack_file in range(clamped_king_file, clamped_king_file + 2):
                file_mask = chess.BB_FILES[attack_file]  # Use python-chess's file mask
                is_king_file = attack_file == king_file
                if (enemy_material.pawns & file_mask) == 0:
                    open_file_against_king_penalty += 25 if is_king_file else 15
                    if (my_pawns & file_mask) == 0:
                        open_file_against_king_penalty += 15 if is_king_file else 10

        pawn_shield_weight = 1 - enemy_material.endgame_t
        if not any(board.pieces(chess.QUEEN, side) for side in [chess.WHITE, chess.BLACK]):
            pawn_shield_weight *= 0.6

        return int((-penalty - open_file_against_king_penalty) * pawn_shield_weight)

    def evaluate_pawns(self, colour_index: int, board: chess.Board) -> int:
        # Fixed implementation to avoid KeyError
        pawns = list(board.pieces(chess.PAWN, colour_index))
        opponent_pawns = list(board.pieces(chess.PAWN, chess.WHITE if colour_index == chess.BLACK else chess.BLACK))
        friendly_pawns = pawns  # For clarity

        masks = self.get_passed_pawn_masks(colour_index, board)
        bonus = 0
        num_isolated_pawns = 0

        for square in pawns:
            # Check if this is a passed pawn (no enemy pawns that can block it)
            if square in masks:
                passed_mask = masks[square]
                if not any(op_sq in passed_mask for op_sq in opponent_pawns):
                    rank = chess.square_rank(square)
                    num_squares_from_promotion = 7 - rank if colour_index == chess.WHITE else rank
                    bonus += self.passed_pawn_bonuses[min(6, num_squares_from_promotion)]

            # Check if this is an isolated pawn (no friendly pawns on adjacent files)
            square_file = chess.square_file(square)
            adjacent_files = self.get_adjacent_file_masks(square_file)
            if not any(fp_sq in adjacent_files for fp_sq in friendly_pawns):
                num_isolated_pawns += 1

        return bonus + self.isolated_pawn_penalty_by_count[min(8, num_isolated_pawns)]

    def mop_up_eval(self, is_white: bool, my_material, enemy_material, board: chess.Board) -> int:
        if (
            my_material.material_score > enemy_material.material_score
                                        + self.pawn_value * 2
            and enemy_material.endgame_t > 0
        ):
            mop_up_score = 0
            friendly_index = chess.WHITE if is_white else chess.BLACK
            opponent_index = chess.BLACK if is_white else chess.WHITE

            friendly_king_square = board.king(friendly_index)
            opponent_king_square = board.king(opponent_index)

            orthogonal_distance = chess.square_manhattan_distance(
                friendly_king_square,
                opponent_king_square
            )
            mop_up_score += (14 - orthogonal_distance) * 4

            center_squares = [
                chess.square(3, 3), chess.square(3, 4),
                chess.square(4, 3), chess.square(4, 4)]
            centre_distance = min(
                chess.square_manhattan_distance(opponent_king_square, center_square)
                for center_square in center_squares
            )
            mop_up_score += centre_distance * 10
            return int(mop_up_score * enemy_material.endgame_t)
        return 0

    def evaluate_piece_square_tables(self, is_white: bool, endgame_t: float, board: chess.Board) -> int:
        value = 0
        colour_index = chess.WHITE if is_white else chess.BLACK
        value += self.evaluate_piece_square_table(
            PieceSquareTable.rooks,
            list(board.pieces(chess.ROOK, colour_index)),
            is_white
        )
        value += self.evaluate_piece_square_table(
            PieceSquareTable.knights,
            list(board.pieces(chess.KNIGHT, colour_index)),
            is_white
        )
        value += self.evaluate_piece_square_table(
            PieceSquareTable.bishops,
            list(board.pieces(chess.BISHOP, colour_index)),
            is_white
        )
        value += self.evaluate_piece_square_table(
            PieceSquareTable.queens,
            list(board.pieces(chess.QUEEN, colour_index)),
            is_white
        )

        pawn_early = self.evaluate_piece_square_table(
            PieceSquareTable.pawns,
            list(board.pieces(chess.PAWN, colour_index)),
            is_white
        )
        pawn_late = self.evaluate_piece_square_table(
            PieceSquareTable.pawns_end,
            list(board.pieces(chess.PAWN, colour_index)),
            is_white
        )
        value += int(pawn_early * (1 - endgame_t))
        value += int(pawn_late * endgame_t)

        king_early_phase = PieceSquareTable.read(
            PieceSquareTable.king_start,
            board.king(colour_index),
            is_white
        )
        value += int(king_early_phase * (1 - endgame_t))
        king_late_phase = PieceSquareTable.read(
            PieceSquareTable.king_end,
            board.king(colour_index),
            is_white
        )
        value += int(king_late_phase * endgame_t)

        return value

    def evaluate_piece_square_table(self, table, piece_list, is_white):
        value = 0
        for square in piece_list:
            value += PieceSquareTable.read(table, square, is_white)
        return value

    def get_material_info(self, colour_index: int, board: chess.Board):
        # Implement a proper material info calculation
        opponent_index = chess.BLACK if colour_index == chess.WHITE else chess.WHITE
        material_info = MaterialInfo(
            num_pawns=len(board.pieces(chess.PAWN, colour_index)),
            num_knights=len(board.pieces(chess.KNIGHT, colour_index)),
            num_bishops=len(board.pieces(chess.BISHOP, colour_index)),
            num_queens=len(board.pieces(chess.QUEEN, colour_index)),
            num_rooks=len(board.pieces(chess.ROOK, colour_index)),
            my_pawns=board.pieces(chess.PAWN, colour_index),
            enemy_pawns=board.pieces(chess.PAWN, opponent_index)
        )

        # Calculate endgame transition value
        total_material = (material_info.num_rooks * self.rook_value +
                         material_info.num_knights * self.knight_value +
                         material_info.num_bishops * self.bishop_value +
                         material_info.num_queens * self.queen_value)

        # Normalize the endgame transition based on total material
        material_info.endgame_t = max(0, min(1, 1 - (total_material / self.endgame_material_start)))

        return material_info

    def get_passed_pawn_masks(self, colour_index: int, board: chess.Board):
        """Generate masks of squares that must be empty for a pawn to be 'passed'"""
        masks = {}
        is_white = colour_index == chess.WHITE

        # For each pawn, create a mask of squares in front of it
        for square in board.pieces(chess.PAWN, colour_index):
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            target_mask = set()

            # Direction of pawn movement depends on color
            direction = 1 if is_white else -1

            # Add squares directly in front of the pawn
            current_rank = rank + direction
            while 0 <= current_rank < 8:
                target_mask.add(chess.square(file, current_rank))
                current_rank += direction

            # Also add diagonal squares that could contain enemy pawns
            for adjacent_file in [file-1, file+1]:
                if 0 <= adjacent_file < 8:
                    current_rank = rank + direction
                    while 0 <= current_rank < 8:
                        target_mask.add(chess.square(adjacent_file, current_rank))
                        current_rank += direction

            masks[square] = target_mask

        return masks

    def get_adjacent_file_masks(self, file_index: int):
        """Generate a set of squares on adjacent files"""
        adjacent_files = set()

        # Add squares on file to the left (if it exists)
        if file_index > 0:
            for rank in range(8):
                adjacent_files.add(chess.square(file_index - 1, rank))

        # Add squares on file to the right (if it exists)
        if file_index < 7:
            for rank in range(8):
                adjacent_files.add(chess.square(file_index + 1, rank))

        return adjacent_files

class MaterialInfo:
    def __init__(self, num_pawns, num_knights, num_bishops, num_queens, num_rooks, my_pawns, enemy_pawns):
        self.num_pawns = num_pawns
        self.num_knights = num_knights
        self.num_bishops = num_bishops
        self.num_queens = num_queens
        self.num_rooks = num_rooks
        self.my_pawns = my_pawns
        self.enemy_pawns = enemy_pawns
        self.endgame_t = 0  # Will be set later
        self.pawns = my_pawns  # Add this field for compatibility
        
        # Calculate material score
        self.material_score = (self.num_pawns * Evaluation.pawn_value +
                               self.num_knights * Evaluation.knight_value +
                               self.num_bishops * Evaluation.bishop_value +
                               self.num_rooks * Evaluation.rook_value +
                               self.num_queens * Evaluation.queen_value)

class EvaluationData:
    def __init__(self):
        self.material_score = 0
        self.mop_up_score = 0
        self.piece_square_score = 0
        self.pawn_score = 0
        self.pawn_shield_score = 0
        self.center_control_score = 0

    def sum(self):
        return (self.material_score +
                self.mop_up_score +
                self.piece_square_score +
                self.pawn_score +
                self.pawn_shield_score +
                self.center_control_score
            )
