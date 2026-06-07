# Path: search/transposition_table.py
# Description:
# Implements a transposition table to cache evaluated positions.
# Uses Zobrist hashing as the position key with modulo indexing.
# Stores entry with: key, evaluation score, remaining depth, node type (exact/upper/lower bound), best move.
# Corrects mate scores during storage (adds ply searched) and retrieval (subtracts ply from root).
# Enables reusing search results across different branches and depths.
# Entry size is fixed at 64 bytes, table size configurable in MB.

from typing import Optional
import chess
import chess.polyglot
class TranspositionTable:
    lookup_failed = -1
    exact = 0
    lower_bound = 1
    upper_bound = 2

    def __init__(self, board: chess.Board, size_mb: int):
        self.board = board
        self.enabled = True

        # Determine table size based on desired size in MB
        tt_entry_size_bytes = 64  # Size of each entry (Entry structure) in bytes
        desired_table_size_in_bytes = size_mb * 1024 * 1024
        num_entries = desired_table_size_in_bytes // tt_entry_size_bytes

        self.count = num_entries
        self.entries = {}

    def clear(self):
        self.entries.clear()

    @property
    def index(self) -> int:
        zobrist_key = chess.polyglot.zobrist_hash(self.board)
        return zobrist_key % self.count

    def try_get_stored_move(self) -> Optional[chess.Move]:
        entry = self.entries.get(self.index)
        if entry:
            return entry.move
        return None

    def lookup_evaluation(self, depth: int, ply_from_root: int, alpha: int, beta: int) -> int:
        if not self.enabled:
            return self.lookup_failed

        entry = self.entries.get(self.index)
        if entry and entry.key == chess.polyglot.zobrist_hash(self.board):
            if entry.depth >= depth:
                corrected_score = self.correct_retrieved_mate_score(entry.value, ply_from_root)

                if entry.node_type == self.exact:
                    return corrected_score
                elif entry.node_type == self.upper_bound and corrected_score <= alpha:
                    return corrected_score
                elif entry.node_type == self.lower_bound and corrected_score >= beta:
                    return corrected_score
        return self.lookup_failed

    def store_evaluation(self,
        depth: int,
        num_ply_searched: int,
        score: int,
        eval_type: int,
        move: chess.Move
    ):
        if not self.enabled:
            return

        entry = Entry(
            chess.polyglot.zobrist_hash(self.board),
            self.correct_mate_score_for_storage(score, num_ply_searched),
            depth,
            eval_type,
            move
        )
        self.entries[self.index] = entry

    def correct_mate_score_for_storage(self, score: int, num_ply_searched: int) -> int:
        if self.is_mate_score(score):
            sign = 1 if score > 0 else -1
            return int((abs(score) + num_ply_searched) * sign)
        return score

    def correct_retrieved_mate_score(self, score: int, num_ply_searched: int) -> int:
        if self.is_mate_score(score):
            sign = 1 if score > 0 else -1
            return int((abs(score) - num_ply_searched) * sign)
        return score

    def is_mate_score(self, score: int) -> bool:
        return abs(score) >= 10000


class Entry:
    def __init__(self, key: int, value: int, depth: int, node_type: int, move: chess.Move):
        self.key = key
        self.value = value
        self.depth = depth
        self.node_type = node_type
        self.move = move

    @staticmethod
    def get_size() -> int:
        return 64  # Size of Entry in bytes
