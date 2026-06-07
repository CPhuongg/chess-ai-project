# Path: search/opening_book.py
# Description:
# Implements Polyglot opening book reading and move selection.
# Loads a .bin Polyglot opening book from a given file path.
# Provides weighted random move selection: filters moves with weight >= 90% of max weight,
# then returns a randomly chosen move from that set to add variety.
# Includes debug method get_move_info() to print all book moves for a position.

import chess
import chess.polyglot
import os
import random
from random import choices

class OpeningBook:
    def __init__(self, path):
        self.path = path
        self.reader = None
        if os.path.exists(path):
            try:
                self.reader = chess.polyglot.open_reader(path)
            except Exception as e:
                print(f"Error opening book: {e}")
                self.reader = None

    def get_move_info(self, board):
        if not self.reader:
            return
        try:
            entries = list(self.reader.find_all(board))  # Lấy tất cả entries
            print(f"FEN: {board.fen()}")
            for entry in entries:
                move = entry.move
                weight = entry.weight
                learn = entry.learn
                print(f"Move: {move.uci()} | Weight: {weight} | Learn: {learn}")
            print("-" * 50)
        except Exception as e:
            print(f"Error getting move from book: {e}")

    def get_weighted_book_move(self, board):
        """Trả về một nước đi từ book với trọng số >= 90% trọng số lớn nhất, chọn ngẫu nhiên."""
        if not self.reader:
            return None
        try:
            entries = list(self.reader.find_all(board))
            if not entries:
                return None

            # Lấy tất cả các nước đi và trọng số tương ứng
            moves = [entry.move for entry in entries]
            weights = [entry.weight for entry in entries]

            # Xác định trọng số lớn nhất và ngưỡng 90%
            max_weight = max(weights)
            threshold = 0.9 * max_weight

            # Lọc những nước đi có trọng số >= 90% max_weight
            filtered_moves = [move for move, weight in zip(moves, weights) if weight >= threshold]

            # Trả về một nước đi ngẫu nhiên trong số đó
            return random.choice(filtered_moves) if filtered_moves else None

        except Exception as e:
            print(f"Error selecting book move: {e}")
            return None
