"""
board_manager.py  –  Game state, move history, Fischer clock, PGN I/O.
"""

import chess
import chess.pgn
import datetime
import time
from typing import Optional


class FischerClock:
    """
    Two-player Fischer (increment) clock.
    base_sec=0 → unlimited.
    """

    def __init__(self, base_sec: float, increment_sec: float):
        self.base      = base_sec
        self.increment = increment_sec
        self.unlimited = (base_sec == 0)
        self.remaining = {chess.WHITE: float(base_sec),
                          chess.BLACK: float(base_sec)}
        self._active: Optional[chess.Color] = None
        self._tick: float = 0.0

    def start(self, color: chess.Color):
        self._active = color
        self._tick   = time.perf_counter()

    def stop(self):
        """Stop clock and add increment to the side that just moved."""
        if self._active is None or self.unlimited:
            return
        elapsed = time.perf_counter() - self._tick
        self.remaining[self._active] -= elapsed
        self.remaining[self._active] += self.increment
        self.remaining[self._active] = max(0.0, self.remaining[self._active])
        self._active = None

    def elapsed_current(self) -> float:
        """Seconds already consumed by the currently active side (live)."""
        if self._active is None or self.unlimited:
            return 0.0
        return time.perf_counter() - self._tick

    def time_left(self, color: chess.Color) -> float:
        if self.unlimited:
            return float("inf")
        base = self.remaining[color]
        if color == self._active:
            base -= self.elapsed_current()
        return max(0.0, base)

    def is_flagged(self, color: chess.Color) -> bool:
        return (not self.unlimited) and self.time_left(color) <= 0

    def fmt(self, color: chess.Color) -> str:
        t = self.time_left(color)
        if t == float("inf"):
            return "--:--"
        m, s = divmod(int(t), 60)
        return f"{m:02d}:{s:02d}"


class BoardManager:
    """
    Central game state.  UI calls this; never touches python-chess directly.
    """

    def __init__(self, base_sec: float = 0, increment_sec: float = 0):
        self.board           = chess.Board()
        self.move_history: list[chess.Move] = []
        self.captured_pieces = {"w": [], "b": []}
        self._last_move: Optional[chess.Move] = None
        self.clock           = FischerClock(base_sec, increment_sec)

        self.white_name  = "Player"
        self.black_name  = "AI"
        self.event_name  = "Local Game"
        self.start_time  = datetime.datetime.now()

        # Start clock for White
        if not self.clock.unlimited:
            self.clock.start(chess.WHITE)

    # ── Move handling ──────────────────────────────────────
    def push_move(self, move: chess.Move) -> bool:
        if move not in self.board.legal_moves:
            return False
        self.clock.stop()
        cap = self.board.piece_at(move.to_square)
        if cap:
            self.captured_pieces["b" if cap.color == chess.BLACK else "w"].append(cap.piece_type)
        elif self.board.is_en_passant(move):
            side = "b" if self.board.turn == chess.WHITE else "w"
            self.captured_pieces[side].append(chess.PAWN)

        self.board.push(move)
        self.move_history.append(move)
        self._last_move = move

        if not self.board.is_game_over() and not self.clock.unlimited:
            self.clock.start(self.board.turn)
        return True

    def push_uci(self, uci: str) -> bool:
        try:
            return self.push_move(chess.Move.from_uci(uci))
        except ValueError:
            return False

    def undo_move(self) -> bool:
        if not self.move_history:
            return False
        self.clock.stop()
        self.move_history.pop()
        self.board.pop()
        self._last_move = self.move_history[-1] if self.move_history else None
        self._rebuild_captured()
        if not self.clock.unlimited and not self.board.is_game_over():
            self.clock.start(self.board.turn)
        return True

    def _rebuild_captured(self):
        tmp = chess.Board()
        self.captured_pieces = {"w": [], "b": []}
        for m in self.move_history:
            cap = tmp.piece_at(m.to_square)
            if cap:
                self.captured_pieces["b" if cap.color == chess.BLACK else "w"].append(cap.piece_type)
            elif tmp.is_en_passant(m):
                side = "b" if tmp.turn == chess.WHITE else "w"
                self.captured_pieces[side].append(chess.PAWN)
            tmp.push(m)

    def reset(self, base_sec: float = 0, increment_sec: float = 0):
        self.__init__(base_sec, increment_sec)

    # ── Queries ────────────────────────────────────────────
    def legal_moves_from(self, sq: chess.Square) -> list[chess.Move]:
        return [m for m in self.board.legal_moves if m.from_square == sq]

    @property
    def last_move(self): return self._last_move
    @property
    def turn(self): return self.board.turn
    @property
    def is_game_over(self): return self.board.is_game_over()

    def game_over_reason(self) -> str:
        if self.board.is_checkmate():
            w = "White" if self.board.turn == chess.BLACK else "Black"
            return f"Checkmate – {w} wins"
        if self.board.is_stalemate():            return "Stalemate – Draw"
        if self.board.is_insufficient_material():return "Insufficient material – Draw"
        if self.board.is_seventyfive_moves():    return "75-move rule – Draw"
        if self.board.is_fivefold_repetition():  return "Fivefold repetition – Draw"
        if self.clock.is_flagged(chess.WHITE):   return "White ran out of time – Black wins"
        if self.clock.is_flagged(chess.BLACK):   return "Black ran out of time – White wins"
        return "Game over"

    def result_with_flag(self) -> str:
        if self.clock.is_flagged(chess.WHITE): return "0-1"
        if self.clock.is_flagged(chess.BLACK): return "1-0"
        return self.board.result()

    def is_in_check(self): return self.board.is_check()
    def king_square(self, c): return self.board.king(c)

    _PV = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3,
           chess.ROOK:5, chess.QUEEN:9, chess.KING:0}

    def material_balance(self) -> int:
        s = 0
        for sq in chess.SQUARES:
            p = self.board.piece_at(sq)
            if p:
                v = self._PV.get(p.piece_type, 0)
                s += v if p.color == chess.WHITE else -v
        return s

    # ── PGN ────────────────────────────────────────────────
    def export_pgn(self) -> str:
        game = chess.pgn.Game()
        game.headers.update({
            "Event":  self.event_name,
            "Date":   self.start_time.strftime("%Y.%m.%d"),
            "White":  self.white_name,
            "Black":  self.black_name,
            "Result": self.result_with_flag(),
        })
        node = game
        tmp  = chess.Board()
        for m in self.move_history:
            node = node.add_variation(m)
            tmp.push(m)
        return str(game)

    def save_pgn(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.export_pgn())

    def load_pgn(self, path: str) -> bool:
        try:
            with open(path, encoding="utf-8") as f:
                game = chess.pgn.read_game(f)
            if game is None:
                return False
            self.reset()
            for move in game.mainline_moves():
                self.board.push(move)
                self.move_history.append(move)
            self._last_move = self.move_history[-1] if self.move_history else None
            self.white_name = game.headers.get("White", "Player")
            self.black_name = game.headers.get("Black", "AI")
            return True
        except Exception:
            return False

    def move_history_san(self) -> list[str]:
        tmp, result = chess.Board(), []
        for m in self.move_history:
            result.append(tmp.san(m))
            tmp.push(m)
        return result