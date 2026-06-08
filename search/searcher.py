# Path: search/searcher.py
# Description:
# Core search engine implementing iterative deepening alpha-beta search.
# Key features:
#   - Iterative deepening from depth 1 to max depth (default 10)
#   - Negamax framework with alpha-beta pruning
#   - Quiescence search to avoid horizon effect (only captures)
#   - Transposition table integration for position reuse
#   - Move ordering via MoveOrdering class
#   - Check and pawn push extensions (up to max_extensions=16)
#   - Late move reduction (LMR) for non-captures after first 3 moves
#   - Opening book integration for early game
#   - Repetition and fifty-move rule detection for draws
#   - Mate score detection and reporting
#   - Search cancellation support for time management

import time
from math import ceil
import chess
from search.move_ordering import MoveOrdering
from search.repetition_table import RepetitionTable
from search.transposition_table import TranspositionTable
from search.opening_book import OpeningBook
from evaluation.evaluation import Evaluation
class Searcher:
    # Constants
    transposition_table_size_mb = 64
    max_extensions = 16

    immediate_mate_score = 100000
    positive_infinity = 9999999
    negative_infinity = -positive_infinity
    minimize_start_time=[0, 722.73, 8822.65, 12089.35, 21323.83, 47866.55, 101753.56]

    def __init__(self, board: chess.Board, opening_book_path=None):
        self.board = board
        self.current_depth = 0
        self.best_move = chess.Move.null()
        self.best_eval = 0
        self.is_playing_white = False
        self.best_move_this_iteration = chess.Move.null()
        self.best_eval_this_iteration = 0
        self.has_searched_at_least_one_move = False
        self.search_cancelled = False
        self.debug_info = ""
        self.search_iteration_timer = time.time()
        self.search_total_timer = time.time()
        self.cancel_time = 0  # Thời điểm nhận tín hiệu hủy tìm kiếm
        self.start_depth = 1
        self.max_depth = 4

        # References and initialization
        self.evaluation = Evaluation()
        self.opening_book = OpeningBook(opening_book_path) if opening_book_path else None
        self.transposition_table = TranspositionTable(board, self.transposition_table_size_mb)
        self.move_orderer = MoveOrdering(self.transposition_table)
        self.repetition_table = RepetitionTable()

        # Run a depth 1 search for JIT warm-up
        self.search(1, 0, self.negative_infinity, self.positive_infinity)

    def start_search(self, on_search_complete=None):
        # Initialize search
        self.best_eval_this_iteration = self.best_eval = 0
        self.best_move_this_iteration = self.best_move = chess.Move.null()

        self.is_playing_white = self.board.turn == chess.WHITE

        self.move_orderer.clear_history()
        self.repetition_table.init(self.board)

        # Initialize debug info
        self.current_depth = 0
        self.debug_info = "Starting search with FEN " + self.board.fen()
        self.search_cancelled = False
        self.cancel_time = 0
        self.search_iteration_timer = time.time()
        self.search_total_timer = time.time()

        print('initialized')
        if self.opening_book:
            book_move = self.opening_book.get_weighted_book_move(self.board)
            if book_move:
                print(f'Book move found: {book_move.uci()}')
                self.best_move = book_move

                # ✅ GỌI CALLBACK ở đây
                if on_search_complete:
                    on_search_complete(self.best_move)
                return
        # Search
        self.run_iterative_deepening_search()
        search_end_time = time.time()
        print(f'SEARCH_END_TIME: {search_end_time:.6f}')
        
        # Nếu tìm kiếm bị hủy, hiện thông tin về độ trễ
        if self.cancel_time > 0:
            delay = search_end_time - self.cancel_time
            print(f'CANCEL_TO_END_DELAY: {delay:.6f} seconds')
            
        print('finished search')
        # Finish up
        print(self.best_move)
        if self.best_move.null():
            # In the unlikely event no best move is found, take any legal move
            moves = list(self.board.legal_moves)
            if moves:
                self.best_move = moves[0]

        if on_search_complete:
            on_search_complete(self.best_move)

        self.search_cancelled = False

    def run_iterative_deepening_search(self):
        for search_depth in range(self.start_depth, self.max_depth + 1):
            print(f"Starting depth {search_depth}")
            self.has_searched_at_least_one_move = False
            self.debug_info += f"\nStarting Iteration: {search_depth}"
            self.search_iteration_timer = time.time()

            self.search(search_depth, 0, self.negative_infinity, self.positive_infinity)

            if self.search_cancelled:
                if self.has_searched_at_least_one_move:
                    self.best_move = self.best_move_this_iteration
                    self.best_eval = self.best_eval_this_iteration
                    self.debug_info += f"\nUsing partial search result: {self.format_move(self.best_move)} Eval: {self.best_eval}"

                self.debug_info += "\nSearch aborted"
                print(f"Search aborted at depth {search_depth}")
                break
            else:
                self.current_depth = search_depth
                self.best_move = self.best_move_this_iteration
                self.best_eval = self.best_eval_this_iteration

                iter_time = time.time() - self.search_iteration_timer
                self.debug_info += f"\nIteration result: {self.format_move(self.best_move)} Eval: {self.best_eval} (Time: {iter_time:.2f}s)"
                if self.is_mate_score(self.best_eval):
                    self.debug_info += f" Mate in ply: {self.num_ply_to_mate_from_score(self.best_eval)}"
                print(f"\nIteration result: {self.format_move(self.best_move)} Eval: {self.best_eval} (Time: {iter_time:.2f}s)")
                self.best_eval_this_iteration = -float('inf')
                self.best_move_this_iteration = chess.Move.null()

                # Exit search if found a mate within search depth
                if (self.is_mate_score(self.best_eval) and
                    self.num_ply_to_mate_from_score(self.best_eval) <= search_depth
                ):
                    self.debug_info += "\nExiting search due to mate found within search depth"
                    break

    def end_search(self):
        """Được gọi để hủy tìm kiếm"""
        # Ghi lại thời điểm nhận tín hiệu hủy
        self.cancel_time = time.time()
        print(f"CANCEL_SIGNAL_RECEIVED: {self.cancel_time:.6f}")
        self.search_cancelled = True

    def search(self,
               ply_remaining,
               ply_from_root,
               alpha,
               beta,
               num_extensions=0,
               prev_move=None,
               prev_was_capture=False
    ):
        # Kiểm tra cancel ngay lập tức
        if self.search_cancelled:
            return 0

        if ply_from_root > 0:
            # Detect draw by three-fold repetition or fifty move rule
            if (
                self.board.is_fifty_moves() or
                self.repetition_table.contains(chess.polyglot.zobrist_hash(self.board))
            ):
                return 0

            # Skip positions where we already know a shorter mating sequence
            alpha = max(alpha, -self.immediate_mate_score + ply_from_root)
            beta = min(beta, self.immediate_mate_score - ply_from_root)
            if alpha >= beta:
                return alpha

        # Check transposition table
        tt_val = self.transposition_table.lookup_evaluation(
            ply_remaining,
            ply_from_root,
            alpha,
            beta
        )
        if tt_val != TranspositionTable.lookup_failed:
            if ply_from_root == 0:
                self.best_move_this_iteration = self.transposition_table.try_get_stored_move()
                entry = self.transposition_table.entries.get(self.transposition_table.index)
                if entry:
                    self.best_eval_this_iteration = entry.value
                else:
                    self.best_eval_this_iteration = 0
            return tt_val

        # If at max depth, perform quiescence search
        if ply_remaining == 0:
            eval_score = self.quiescence_search(alpha, beta)
            return eval_score

        # Generate and order moves
        legal_moves = list(self.board.legal_moves)
        prev_best_move = (
            self.best_move
            if ply_from_root == 0 else
            self.transposition_table.try_get_stored_move()
        )

        # Order moves
        opponent_attack_map, opponent_pawn_attack_map = self.get_opponent_attack_maps()
        self.move_orderer.order_moves(
            prev_best_move,
            self.board, legal_moves,
            opponent_attack_map,
            opponent_pawn_attack_map,
            False,
            ply_from_root
        )

        # Check for checkmate or stalemate
        if not legal_moves:
            if self.board.is_check():
                # Checkmate
                mate_score = self.immediate_mate_score - ply_from_root
                return -mate_score
            else:
                # Stalemate
                return 0

        if ply_from_root > 0 and prev_move:
            # Update repetition table
            was_pawn_move = (
                self.board.piece_at(prev_move.to_square) and
                self.board.piece_at(prev_move.to_square).piece_type == chess.PAWN
            )
            self.repetition_table.push(
                chess.polyglot.zobrist_hash(self.board),
                prev_was_capture or was_pawn_move
            )

        evaluation_bound = TranspositionTable.upper_bound
        best_move_in_this_position = chess.Move.null()

        for i, move in enumerate(legal_moves):
            # Kiểm tra cancel trước mỗi nước đi ở cấp độ gốc
            if ply_from_root == 0 and self.search_cancelled:
                break
                
            # Get move information
            captured_piece = self.board.piece_at(move.to_square)
            is_capture = captured_piece is not None

            # Make the move
            self.board.push(move)

            # Check for extensions
            extension = 0
            if num_extensions < self.max_extensions:
                moved_piece = self.board.piece_at(move.to_square)
                if moved_piece:
                    target_rank = chess.square_rank(move.to_square)
                    if self.board.is_check():
                        extension = 1
                    elif (moved_piece.piece_type == chess.PAWN and
                          target_rank in [1, 6]
                    ):
                        extension = 1

            # Decide whether to do a full search or reduced depth search
            needs_full_search = True
            eval_score = 0

            # Reduce depth for later moves in the move list
            if extension == 0 and ply_remaining >= 3 and i >= 3 and not is_capture:
                reduce_depth = 1
                eval_score = -self.search(
                    ply_remaining - 1 - reduce_depth,
                    ply_from_root + 1,
                    -alpha - 1,
                    -alpha,
                    num_extensions,
                    move,
                    is_capture
                )
                needs_full_search = eval_score > alpha

            # Perform full-depth search if needed
            if needs_full_search:
                eval_score = -self.search(
                    ply_remaining - 1 + extension,
                    ply_from_root + 1,
                    -beta,
                    -alpha,
                    num_extensions + extension,
                    move,
                    is_capture
                )

            # Unmake move
            self.board.pop()

            if self.search_cancelled:
                return 0

            # Beta cutoff (move was too good)
            if eval_score >= beta:
                # Store in transposition table
                self.transposition_table.store_evaluation(
                    ply_remaining,
                    ply_from_root,
                    beta,
                    TranspositionTable.lower_bound,
                    move
                )

                # Update killer moves and history heuristic
                if not is_capture:
                    if ply_from_root < MoveOrdering.max_killer_move_ply:
                        self.move_orderer.killer_moves[ply_from_root].add(move)
                    history_score = ply_remaining * ply_remaining
                    color_index = int(self.board.turn)
                    self.move_orderer.history[color_index][move.from_square][move.to_square] += history_score

                if ply_from_root > 0:
                    self.repetition_table.try_pop()

                return beta

            # Found a new best move in this position
            if eval_score > alpha:
                evaluation_bound = TranspositionTable.exact
                best_move_in_this_position = move
                alpha = eval_score

                if ply_from_root == 0:
                    self.best_move_this_iteration = move
                    self.best_eval_this_iteration = eval_score
                    self.has_searched_at_least_one_move = True
                    
                    # Ghi log khi tìm thấy nước đi mới ở root
                    if self.best_move_this_iteration != chess.Move.null():
                        print(f"Found new best move: {self.format_move(move)} Eval: {eval_score}")

        if ply_from_root > 0:
            self.repetition_table.try_pop()

        # Store position in transposition table
        self.transposition_table.store_evaluation(
            ply_remaining,
            ply_from_root,
            alpha,
            evaluation_bound,
            best_move_in_this_position
        )

        return alpha

    def quiescence_search(self, alpha, beta):
        # Thêm kiểm tra hủy
        if self.search_cancelled:
            return 0

        # Stand-pat evaluation
        eval_score = self.evaluation.evaluate(self.board)

        if eval_score >= beta:
            return beta

        if eval_score > alpha:
            alpha = eval_score

        # Generate capture moves only
        moves = [move for move in self.board.legal_moves if self.board.is_capture(move)]

        # Order captures
        moves.sort(key=lambda move: self.score_capture(move), reverse=True)

        for move in moves:
            self.board.push(move)
            eval_score = -self.quiescence_search(-beta, -alpha)
            self.board.pop()

            # Kiểm tra hủy sau mỗi nước đi
            if self.search_cancelled:
                return 0

            if eval_score >= beta:
                return beta

            if eval_score > alpha:
                alpha = eval_score

        return alpha

    def update_start_depth(self, search_time):
        for depth, threshold in enumerate(Searcher.minimize_start_time):
            if search_time > threshold * 1.5:
                self.start_depth = depth
            else:
                break
        self.start_depth = max(1, min(self.start_depth, self.max_depth))
        print(f"start search at depth {self.start_depth}")

    def get_opponent_attack_maps(self):
        """Build attack maps used by move ordering to avoid unsafe target squares."""
        opponent = not self.board.turn
        attacks = chess.SquareSet()
        pawn_attacks = chess.SquareSet()

        for square in chess.SQUARES:
            if self.board.is_attacked_by(opponent, square):
                attacks.add(square)

        for pawn_square in self.board.pieces(chess.PAWN, opponent):
            pawn_attacks |= self.board.attacks(pawn_square)

        return attacks, pawn_attacks

    def score_capture(self, move):
        """Score a capture move for move ordering in quiescence search"""
        victim_value = self.get_piece_value(self.board.piece_at(move.to_square))
        aggressor_value = self.get_piece_value(self.board.piece_at(move.from_square))
        return victim_value - aggressor_value/10  # MVV-LVA

    def get_piece_value(self, piece):
        """Get the value of a piece for move ordering"""
        if piece is None:
            return 0

        values = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 320,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 10000
        }
        return values.get(piece.piece_type, 0)

    def format_move(self, move):
        """Format a move for display"""
        if move.null():
            return "null"
        return move.uci()

    @staticmethod
    def is_mate_score(score):
        """Check if a score indicates a mate"""
        if score == -float('inf'):
            return False
        return abs(score) > Searcher.immediate_mate_score - 1000

    @staticmethod
    def num_ply_to_mate_from_score(score):
        """Calculate the number of ply to mate from a mate score"""
        return Searcher.immediate_mate_score - abs(score)

    def announce_mate(self):
        """Announce mate if found"""
        if self.is_mate_score(self.best_eval_this_iteration):
            num_ply_to_mate = self.num_ply_to_mate_from_score(self.best_eval_this_iteration)
            num_moves_to_mate = ceil(num_ply_to_mate / 2)
            side_with_mate = "Black" if (self.best_eval_this_iteration * (1 if self.board.turn == chess.WHITE else -1) < 0) else "White"
            return f"{side_with_mate} can mate in {num_moves_to_mate} move{'s' if num_moves_to_mate > 1 else ''}"
        return "No mate found"

    def get_search_result(self):
        """Return the best move and evaluation"""
        return (self.best_move, self.best_eval)

    def clear_for_new_position(self):
        """Clear search data for a new position"""
        self.transposition_table.clear()
        self.move_orderer.clear_killers()

    def get_transposition_table(self):
        """Return the transposition table"""
        return self.transposition_table
