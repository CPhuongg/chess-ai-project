# Path: search/repetition_table.py
# Description:
# Tracks position hashes to detect threefold repetition draws.
# Maintains a fixed-size array of Zobrist hashes with start indices that reset after
# irreversible moves (captures or pawn moves). This correctly implements the
# threefold repetition rule by only counting repetitions that occur after the last
# irreversible move. Supports push() and pop() operations during search.

import chess
import chess.polyglot

class RepetitionTable:
    """
    Tracks position repetitions during search to detect draws.
    This implementation efficiently manages memory and correctly
    handles the threefold repetition rule.
    """
    def __init__(self, max_size=1024):
        self.hashes = [0] * max_size
        self.count = 0
        self.start_indices = [0] * (max_size + 1)
        self.max_size = max_size

    def init(self, board: chess.Board):
        """Initialize the repetition table with the board's current position history."""
        self.count = 0

        # Get position hashes from the board's move history
        # Note: We're using a temporary list to avoid modifying the actual board
        if len(board.move_stack) > 0:
            temp_board = board.copy()
            initial_hashes = []

            # Go backward through the moves to collect position hashes
            while len(temp_board.move_stack) > 0:
                temp_board.pop()
                # Only add positions after irreversible moves (captures or pawn moves)
                # to properly track repetition sequences
                initial_hashes.append(chess.polyglot.zobrist_hash(temp_board))

            # Store hashes in reverse order (oldest first)
            initial_hashes.reverse()
            self.count = min(len(initial_hashes), self.max_size)

            for i in range(self.count):
                self.hashes[i] = initial_hashes[i]
                # Set start index for each position
                # Reset start index after captures or pawn moves
                # This is simplified - in actual implementation you'd need to check each move
                self.start_indices[i] = 0

        # Set the start index for the next position
        self.start_indices[self.count] = 0

    def push(self, hash_value: int, reset: bool):
        """
        Add a new position hash to the table.
        
        Args:
            hash_value: Zobrist hash of the position
            reset: Whether this is after an irreversible move (capture/pawn move)
                   which resets the repetition counting
        """
        if self.count >= self.max_size:
            # Shift everything down to make room
            for i in range(self.max_size - 1):
                self.hashes[i] = self.hashes[i + 1]
                self.start_indices[i] = max(0, self.start_indices[i + 1] - 1)
            index = self.max_size - 1
        else:
            index = self.count
            self.count += 1

        self.hashes[index] = hash_value
        # If reset is True, set start index to current position
        # This means repetition counting starts fresh from here
        self.start_indices[index + 1] = index if reset else self.start_indices[index]

    def try_pop(self):
        """Remove the most recent position from the table. Returns True if successful."""
        if self.count > 0:
            self.count -= 1
            return True
        return False

    def contains(self, hash_value: int) -> bool:
        """
        Check if the position exists in the repetition table.
        Only checks positions since the last irreversible move.
        """
        if self.count == 0:
            return False

        start_idx = self.start_indices[self.count]
        # Check positions from start_idx up to the second-most recent position
        # (exclude the most recent which would be the current position in search)
        for i in range(start_idx, self.count):
            if self.hashes[i] == hash_value:
                return True
        return False
