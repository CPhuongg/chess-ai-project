# Path: test.py
# Description:
# Quick test script for the ChessBot engine.
# Initializes a ChessBot instance and prints the best move at depth 3.
# Useful for verifying engine functionality and integration.

from bot import ChessBot

chess_bot = ChessBot()

print(chess_bot.get_best_move(depth=3))
