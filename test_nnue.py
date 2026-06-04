import chess
from src.engine.nnue_evaluation import NNUEEvaluation, HybridEvaluation

# Test 1: NNUE evaluation
board = chess.Board()
nnue = NNUEEvaluation()
score = nnue.evaluate(board)
print(f"Initial board score: {score:.2f}")

# Test 2: Hybrid evaluation
hybrid = HybridEvaluation(nnue_weight=0.7)
score2 = hybrid.evaluate(board)
print(f"Hybrid score: {score2:.2f}")

# Test 3: So sánh với evaluation truyền thống
score3 = hybrid.evaluate_traditional(board)
print(f"Traditional score: {score3:.2f}")

# Test 4: Sau vài nước đi
board.push_san("e4")
board.push_san("e5")
board.push_san("Nf3")
board.push_san("Nc6")
print(f"\nAfter 2 moves (Italian Game):")
print(f"NNUE score: {nnue.evaluate(board):.2f}")
print(f"Hybrid score: {hybrid.evaluate(board):.2f}")