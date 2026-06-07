# Path: search/move_ordering.py
# Description:
# Implements move ordering heuristics to improve alpha-beta pruning efficiency.
# Moves are scored using multiple techniques:
#   - Hash move (from transposition table) - highest priority
#   - Winning captures (MVV-LVA via capture material delta)
#   - Promotion moves (especially to queen)
#   - Killer moves (successful beta-cutoff moves at same depth)
#   - History heuristic (successful quiet moves from previous searches)
#   - Piece-square table delta (encourages moving pieces to better squares)
#   - Penalty for moving to squares attacked by opponent pawns or pieces
# Scores use large bias constants to ensure clear priority ordering.

import chess
from evaluation.piece_square_table import PieceSquareTable
from evaluation.evaluation import Evaluation

class MoveOrdering:
    max_move_count = 218
    square_controlled_by_opponent_pawn_penalty = 350
    captured_piece_value_multiplier = 100

    max_killer_move_ply = 32
    million = 1000000
    hash_move_score = 100 * million
    winning_capture_bias = 8 * million
    promote_bias = 6 * million
    killer_bias = 4 * million
    losing_capture_bias = 2 * million
    regular_bias = 0

    def __init__(self, transposition_table):
        self.move_scores = [0] * self.max_move_count
        self.transposition_table = transposition_table
        self.invalid_move = chess.Move.null()
        self.killer_moves = [Killers() for _ in range(self.max_killer_move_ply)]
        self.history = [[[0] * 64 for _ in range(64)] for _ in range(2)]

    def clear_history(self):
        self.history = [[[0] * 64 for _ in range(64)] for _ in range(2)]

    def clear_killers(self):
        self.killer_moves = [Killers() for _ in range(self.max_killer_move_ply)]

    def clear(self):
        self.clear_killers()
        self.clear_history()

    def order_moves(self, hash_move, board, moves, opp_attacks, opp_pawn_attacks, in_qsearch, ply):
        """
        Order moves based on heuristics to improve alpha-beta pruning efficiency
        
        Parameters:
        - hash_move: Move from transposition table to prioritize
        - board: Current chess board
        - moves: List of legal moves to order
        - opp_attacks: Bitboard of all squares attacked by opponent
        - opp_pawn_attacks: Bitboard of squares attacked by opponent pawns
        - in_qsearch: Whether we're in quiescence search
        - ply: Current ply (depth)
        """

        opp_attacks_set = chess.SquareSet(opp_attacks)
        opp_pawn_attacks_set = chess.SquareSet(opp_pawn_attacks)

        for i, move in enumerate(moves):
            if move == hash_move:
                self.move_scores[i] = self.hash_move_score
                continue

            score = 0
            start_square = move.from_square
            target_square = move.to_square

            move_piece = board.piece_at(start_square)
            if not move_piece:
                self.move_scores[i] = self.regular_bias
                continue

            move_piece_type = move_piece.piece_type
            captured_piece = board.piece_at(target_square)
            capture_piece_type = captured_piece.piece_type if captured_piece else None
            is_capture = capture_piece_type is not None

            flag = move.promotion if move.promotion else 0
            piece_value = self.get_piece_value(move_piece_type)

            if is_capture:
                # Order moves to try capturing the most valuable opponent piece with
                # least valuable of own pieces first
                capture_material_delta = self.get_piece_value(capture_piece_type) - piece_value
                opponent_can_recapture = (
                    target_square in opp_attacks_set
                    or target_square in opp_pawn_attacks_set
                )
                if opponent_can_recapture:
                    score += (
                        (
                            self.winning_capture_bias if capture_material_delta >= 0 else
                            self.losing_capture_bias
                        )
                        + capture_material_delta
                    )
                else:
                    score += self.winning_capture_bias + capture_material_delta

            if move_piece_type == chess.PAWN:
                # Check for promotion to queen
                if flag == chess.QUEEN and not is_capture:
                    score += self.promote_bias
            elif move_piece_type == chess.KING:
                pass
            else:
                # Use piece-square tables to evaluate move quality
                try:
                    # Adapt how we access the piece-square table
                    to_score = PieceSquareTable.read(
                        PieceSquareTable.tables[move_piece_type-1],
                        target_square,
                        board.turn == chess.WHITE
                    )
                    from_score = PieceSquareTable.read(
                        PieceSquareTable.tables[move_piece_type-1],
                        start_square,
                        board.turn == chess.WHITE
                    )
                    score += to_score - from_score
                except (IndexError, TypeError):
                    # Fall back if tables aren't properly initialized
                    pass

                # Penalize moves to squares attacked by opponent
                if target_square in opp_pawn_attacks_set:
                    score -= 50
                elif target_square in opp_attacks_set:
                    score -= 25

            if not is_capture:
                is_killer = (
                    not in_qsearch and
                    ply < self.max_killer_move_ply and
                    self.killer_moves[ply].match(move)
                )
                score += self.killer_bias if is_killer else self.regular_bias
                score += self.history[int(board.turn)][start_square][target_square]

            self.move_scores[i] = score

        move_score_pairs = list(zip(moves, self.move_scores))

        # Sort by score in descending order
        sorted_pairs = sorted(move_score_pairs, key=lambda x: x[1], reverse=True)

        # Update the original lists
        for i, (move, score) in enumerate(sorted_pairs):
            moves[i] = move
            self.move_scores[i] = score

    def get_piece_value(self, piece_type):
        """Get the standard value of a piece type"""
        if piece_type is None:
            return 0

        piece_values = {
            chess.QUEEN: Evaluation.queen_value,
            chess.ROOK: Evaluation.rook_value,
            chess.KNIGHT: Evaluation.knight_value,
            chess.BISHOP: Evaluation.bishop_value,
            chess.PAWN: Evaluation.pawn_value,
        }
        return piece_values.get(piece_type, 0)

    def get_score(self, index):
        """Get a human-readable description of the move score"""
        score = self.move_scores[index]

        score_types = [
            self.hash_move_score,
            self.winning_capture_bias,
            self.losing_capture_bias,
            self.promote_bias,
            self.killer_bias,
            self.regular_bias
        ]
        type_names = [
            "Hash Move",
            "Good Capture",
            "Bad Capture",
            "Promote",
            "Killer Move",
            "Regular"
        ]
        closest = float('inf')
        type_name = ""

        for i, score_type in enumerate(score_types):
            delta = abs(score - score_type)
            if delta < closest:
                closest = delta
                type_name = type_names[i]

        return f"{score} ({type_name})"

class Killers:
    """Tracks killer moves for a particular ply"""
    def __init__(self):
        self.move_a = chess.Move.null()
        self.move_b = chess.Move.null()

    def add(self, move):
        """Add a killer move, shifting the previous one"""
        if move != self.move_a:
            self.move_b = self.move_a
            self.move_a = move

    def match(self, move):
        """Check if a move matches either of the stored killer moves"""
        return move == self.move_a or move == self.move_b
