"""
benchmark.py — Đánh giá ChessBot vs Stockfish ở nhiều mức ELO
=============================================================
Chạy từ thư mục gốc của project:
    python benchmark.py

Yêu cầu:
    pip install python-chess
    Stockfish đã cài và có trong PATH, hoặc set STOCKFISH_PATH bên dưới.

Kết quả xuất ra terminal + file results/benchmark_YYYYMMDD_HHMMSS.txt
"""

import chess
import chess.engine
import sys
import os
import time
import datetime
import statistics
from dataclasses import dataclass, field
from typing import Optional

# ── Cấu hình ──────────────────────────────────────────────────────────────

# Đường dẫn Stockfish — để None để tự tìm trong PATH
STOCKFISH_PATH: Optional[str] = r"C:\stockfish\stockfish.exe"

# Các mức ELO Stockfish sẽ được giới hạn
# Stockfish bản mới giới hạn tối thiểu 1320
ELO_LEVELS = [1320, 1400, 1500, 1600, 1800]

# Số ván mỗi mức ELO (nên chẵn để bot đi cả Trắng lẫn Đen)
GAMES_PER_LEVEL = 10

# Time control (giây): bullet = 1.0, blitz = 3.0, rapid = 10.0
BOT_TIME_PER_MOVE  = 1.0   # giây bot được suy nghĩ mỗi nước
SF_TIME_PER_MOVE   = 0.1   # Stockfish chỉ cần rất ít thời gian ở ELO thấp

# Độ sâu tìm kiếm của bot (Easy=2, Medium=4, Hard=6)
BOT_DEPTH = 4

# Giới hạn số nước tối đa 1 ván (tránh loop vô tận)
MAX_MOVES = 200

# Thư mục lưu kết quả
OUTPUT_DIR = "results"

# ── Import ChessBot từ project ─────────────────────────────────────────────
# Nếu cấu trúc project khác, điều chỉnh import này
try:
    from bot import ChessBot
except ImportError:
    print("[LỖI] Không import được 'bot.ChessBot'.")
    print("       Hãy chạy script này từ thư mục gốc của project,")
    print("       hoặc điều chỉnh dòng 'from bot import ChessBot'.")
    sys.exit(1)


# ── Data classes ───────────────────────────────────────────────────────────

@dataclass
class GameResult:
    elo: int
    game_num: int
    bot_color: str        # "white" hoặc "black"
    result: str           # "win", "loss", "draw"
    termination: str      # "checkmate", "stalemate", "50move", "repetition", "max_moves"
    num_moves: int
    acpl: float           # Average Centipawn Loss của bot trong ván này
    duration_s: float

@dataclass
class LevelSummary:
    elo: int
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_acpl: float = 0.0
    game_count: int = 0
    acpl_samples: list = field(default_factory=list)

    @property
    def score(self):
        """Điểm theo hệ thống cờ: thắng=1, hòa=0.5, thua=0"""
        return self.wins + self.draws * 0.5

    @property
    def score_pct(self):
        if self.game_count == 0:
            return 0.0
        return self.score / self.game_count * 100

    @property
    def avg_acpl(self):
        if not self.acpl_samples:
            return 0.0
        return statistics.mean(self.acpl_samples)


# ── Tìm Stockfish ──────────────────────────────────────────────────────────

def find_stockfish() -> str:
    if STOCKFISH_PATH and os.path.exists(STOCKFISH_PATH):
        return STOCKFISH_PATH

    candidates = ["stockfish", "stockfish.exe",
                  r"C:\stockfish\stockfish.exe",
                  "/usr/bin/stockfish", "/usr/local/bin/stockfish",
                  "/opt/homebrew/bin/stockfish"]
    for c in candidates:
        if os.path.exists(c):
            return c
        # Thử tìm trong PATH
        import shutil
        found = shutil.which(c)
        if found:
            return found

    print("[LỖI] Không tìm thấy Stockfish.")
    print("       Cài đặt: https://stockfishchess.org/download/")
    print("       Hoặc set biến STOCKFISH_PATH trong script này.")
    sys.exit(1)


# ── Tính ACPL ──────────────────────────────────────────────────────────────

def compute_acpl(analysis_log: list[tuple[int, int]], bot_color: chess.Color) -> float:
    """
    analysis_log: list of (score_before, score_after) từ góc nhìn Trắng (centipawn).
    Tính trung bình centipawn loss cho bot.
    """
    losses = []
    for score_before, score_after in analysis_log:
        if bot_color == chess.WHITE:
            # Bot là Trắng: muốn score tăng, loss = score_before - score_after
            loss = score_before - score_after
        else:
            # Bot là Đen: muốn score giảm (âm = lợi Đen), loss = score_after - score_before
            loss = score_after - score_before
        losses.append(max(0, loss))   # chỉ tính khi đi tệ hơn (loss >= 0)

    return statistics.mean(losses) if losses else 0.0


# ── Chạy 1 ván ─────────────────────────────────────────────────────────────

def play_one_game(
    bot: ChessBot,
    engine: chess.engine.SimpleEngine,
    elo: int,
    game_num: int,
    bot_is_white: bool,
    analyzer: chess.engine.SimpleEngine,
) -> GameResult:

    # Dùng chung board của bot để searcher tự động thấy vị trí hiện tại
    bot.notify_new_game()
    board = bot.board
    board.reset()

    bot_color  = chess.WHITE if bot_is_white else chess.BLACK
    bot_color_str = "white" if bot_is_white else "black"
    analysis_log = []
    num_moves = 0
    start = time.time()

    while not board.is_game_over() and num_moves < MAX_MOVES:

        # ── Lấy eval TRƯỚC khi đi ──────────────────────────────────────
        score_before = None
        if board.turn == bot_color:
            try:
                info = analyzer.analyse(board, chess.engine.Limit(depth=12))
                pov = info["score"].white()
                score_before = pov.score(mate_score=10000) if pov is not None else None
            except Exception:
                pass

        # ── Đi nước ────────────────────────────────────────────────────
        if board.turn == bot_color:
            # Bot của nhóm đi
            try:
                move_uci = bot.get_best_move(depth=BOT_DEPTH, time_ms=int(BOT_TIME_PER_MOVE * 1000))
                move = chess.Move.from_uci(move_uci)
                if move not in board.legal_moves:
                    # Nếu bot trả về nước không hợp lệ → thua ngay
                    return GameResult(elo, game_num, bot_color_str, "loss",
                                      "illegal_move", num_moves, 0.0, time.time() - start)
            except Exception as e:
                print(f"    [!] Bot lỗi ở nước {num_moves}: {e}")
                return GameResult(elo, game_num, bot_color_str, "loss",
                                  "bot_error", num_moves, 0.0, time.time() - start)
        else:
            # Stockfish đi
            result = engine.play(board, chess.engine.Limit(time=SF_TIME_PER_MOVE))
            move = result.move

        board.push(move)
        num_moves += 1

        # ── Lấy eval SAU khi đi (chỉ khi bot vừa đi) ──────────────────
        if score_before is not None:
            try:
                info = analyzer.analyse(board, chess.engine.Limit(depth=12))
                pov = info["score"].white()
                score_after = pov.score(mate_score=10000) if pov is not None else score_before
                analysis_log.append((score_before, score_after))
            except Exception:
                pass

    # ── Xác định kết quả ───────────────────────────────────────────────
    duration = time.time() - start

    if num_moves >= MAX_MOVES:
        outcome_str = "draw"
        termination = "max_moves"
    else:
        outcome = board.outcome()
        termination = outcome.termination.name.lower() if outcome else "unknown"

        if outcome is None or outcome.winner is None:
            outcome_str = "draw"
        elif outcome.winner == bot_color:
            outcome_str = "win"
        else:
            outcome_str = "loss"

    acpl = compute_acpl(analysis_log, bot_color)

    return GameResult(elo, game_num, bot_color_str, outcome_str,
                      termination, num_moves, acpl, duration)


# ── In kết quả 1 ván ───────────────────────────────────────────────────────

def print_game_result(r: GameResult):
    icon = {"win": "✓", "loss": "✗", "draw": "═"}.get(r.result, "?")
    color_icon = "♔" if r.bot_color == "white" else "♚"
    print(f"    [{icon}] Ván {r.game_num:>2} {color_icon}  "
          f"{r.result.upper():<5}  "
          f"{r.num_moves:>3} nước  "
          f"ACPL: {r.acpl:>5.1f}  "
          f"({r.termination})  "
          f"{r.duration_s:.1f}s")


# ── In bảng tổng kết ───────────────────────────────────────────────────────

def print_summary(summaries: list[LevelSummary]):
    print()
    print("═" * 66)
    print(f"  {'ELO':>5}  {'W':>4} {'D':>4} {'L':>4}  {'Score%':>7}  {'ACPL':>6}  {'Nhận xét'}")
    print("─" * 66)

    for s in summaries:
        remark = ""
        if s.score_pct >= 55:
            remark = "✓ Mạnh hơn"
        elif s.score_pct >= 45:
            remark = "≈ Ngang bằng"
        else:
            remark = "✗ Yếu hơn"

        print(f"  {s.elo:>5}  "
              f"{s.wins:>4} {s.draws:>4} {s.losses:>4}  "
              f"{s.score_pct:>6.1f}%  "
              f"{s.avg_acpl:>6.1f}  "
              f"{remark}")

    print("═" * 66)

    # Ước tính ELO
    best_level = None
    for s in summaries:
        if s.score_pct >= 50:
            best_level = s
    if best_level:
        print(f"\n  → Ước tính ELO bot: ~{best_level.elo} – {best_level.elo + 200}")
    else:
        lowest = summaries[0]
        print(f"\n  → Bot chưa đạt 50% ở ELO {lowest.elo}. ELO thực có thể < {lowest.elo}.")
    print()


# ── Lưu kết quả ra file ────────────────────────────────────────────────────

def save_results(summaries: list[LevelSummary], all_results: list[GameResult]):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(OUTPUT_DIR, f"benchmark_{ts}.txt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Chess Bot Benchmark — {ts}\n")
        f.write(f"Time control: bot={BOT_TIME_PER_MOVE}s/move, SF={SF_TIME_PER_MOVE}s/move\n")
        f.write(f"Games per level: {GAMES_PER_LEVEL}\n\n")

        f.write(f"{'ELO':>5}  {'W':>4} {'D':>4} {'L':>4}  {'Score%':>7}  {'ACPL':>6}\n")
        f.write("-" * 45 + "\n")
        for s in summaries:
            f.write(f"{s.elo:>5}  {s.wins:>4} {s.draws:>4} {s.losses:>4}  "
                    f"{s.score_pct:>6.1f}%  {s.avg_acpl:>6.1f}\n")

        f.write("\n\nChi tiết từng ván:\n")
        for r in all_results:
            f.write(f"ELO {r.elo:>4} | Ván {r.game_num:>2} | "
                    f"{r.bot_color:<5} | {r.result:<5} | "
                    f"{r.num_moves:>3} nước | ACPL {r.acpl:>5.1f} | {r.termination}\n")

    print(f"  Kết quả đã lưu: {path}")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║      CHESS BOT BENCHMARK vs STOCKFISH        ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    sf_path = find_stockfish()
    print(f"  Stockfish: {sf_path}")

    # Khởi tạo bot
    _book_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "komodo.bin")
    try:
        bot = ChessBot(opening_book_path=_book_path if os.path.exists(_book_path) else None)
    except Exception as e:
        print(f"[LỖI] Không khởi tạo được ChessBot: {e}")
        sys.exit(1)

    # Kiểm tra method tên gì — thử get_best_move, nếu không có thì báo lỗi
    move_method = None
    for name in ["get_best_move", "find_best_move", "search", "get_move"]:
        if hasattr(bot, name):
            move_method = name
            break
    if move_method is None:
        print("[LỖI] Không tìm thấy method trả về nước đi trong ChessBot.")
        print("       Các tên thử: get_best_move, find_best_move, search, get_move")
        print("       Hãy chỉnh dòng 'bot.get_best_move(board)' trong play_one_game().")
        sys.exit(1)

    # Monkey-patch nếu tên method khác
    if move_method != "get_best_move":
        print(f"  [!] Dùng method '{move_method}' thay vì 'get_best_move'")
        bot.get_best_move = getattr(bot, move_method)

    print(f"  ChessBot: OK (method: {move_method})")
    print(f"  ELO levels: {ELO_LEVELS}")
    print(f"  Ván/level: {GAMES_PER_LEVEL}  |  Time bot: {BOT_TIME_PER_MOVE}s/move")
    print()

    all_results: list[GameResult] = []
    summaries: list[LevelSummary] = []

    # Mở engine Stockfish (dùng chung cho cả chơi và phân tích)
    with chess.engine.SimpleEngine.popen_uci(sf_path) as engine, \
         chess.engine.SimpleEngine.popen_uci(sf_path) as analyzer:

        analyzer.configure({"Threads": 1, "Hash": 32})

        for elo in ELO_LEVELS:
            summary = LevelSummary(elo=elo)
            summaries.append(summary)

            print(f"  ┌─ ELO {elo} {'─' * 40}")

            # Set ELO một lần cho cả level, không gọi lại mỗi ván
            engine.configure({
                "UCI_LimitStrength": True,
                "UCI_Elo": elo,
            })

            for g in range(1, GAMES_PER_LEVEL + 1):
                # Đổi màu xen kẽ
                bot_is_white = (g % 2 == 1)

                r = play_one_game(bot, engine, elo, g, bot_is_white, analyzer)
                all_results.append(r)

                if r.result == "win":
                    summary.wins += 1
                elif r.result == "draw":
                    summary.draws += 1
                else:
                    summary.losses += 1
                summary.game_count += 1
                summary.acpl_samples.append(r.acpl)

                print_game_result(r)

            print(f"  └─ Tổng: {summary.wins}W {summary.draws}D {summary.losses}L  "
                  f"Score: {summary.score_pct:.1f}%  ACPL TB: {summary.avg_acpl:.1f}")
            print()

    print_summary(summaries)
    save_results(summaries, all_results)


if __name__ == "__main__":
    main()