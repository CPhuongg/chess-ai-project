"""
animation.py  –  Piece movement animations for the chess board.

Three effects:
  SlideAnimation  – piece glides from src square to dst square
  CaptureAnimation– captured piece shrinks & fades out
  DragState       – tracks a piece being dragged by the mouse
"""

import time
import math
import chess
import pygame
from typing import Optional

from src.engine.constants import (
    SQUARE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    BOARD_SIZE,
)


# ── helpers ───────────────────────────────────────────────
def _sq_center(sq: chess.Square, flipped: bool = False):
    """Pixel centre of a square."""
    f = chess.square_file(sq)
    r = chess.square_rank(sq)
    if flipped:
        f = 7 - f
        r = 7 - r
    x = BOARD_OFFSET_X + f * SQUARE_SIZE + SQUARE_SIZE // 2
    y = BOARD_OFFSET_Y + (7 - r) * SQUARE_SIZE + SQUARE_SIZE // 2
    return x, y


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def _ease_out_back(t: float, overshoot: float = 0.5) -> float:
    """Slight overshoot for a snappy landing feel."""
    c1 = overshoot
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


# ══════════════════════════════════════════════════════════
# SlideAnimation
# ══════════════════════════════════════════════════════════
class SlideAnimation:
    """
    Animates a piece sliding from `src_sq` to `dst_sq`.
    Duration scales with distance (min 120 ms, max 300 ms).
    """
    BASE_MS = 180      # base duration in ms
    MIN_MS  = 100
    MAX_MS  = 320

    def __init__(self, piece: chess.Piece,
                 src_sq: chess.Square, dst_sq: chess.Square,
                 flipped: bool = False):
        self.piece   = piece
        self.src_sq  = src_sq
        self.dst_sq  = dst_sq
        self.flipped = flipped

        sx, sy = _sq_center(src_sq, flipped)
        dx, dy = _sq_center(dst_sq, flipped)
        dist   = math.hypot(dx - sx, dy - sy)
        pixels_per_sq = SQUARE_SIZE * math.sqrt(2)
        factor = dist / pixels_per_sq

        self.duration = max(self.MIN_MS,
                            min(self.MAX_MS,
                                int(self.BASE_MS * (0.5 + 0.5 * factor))))
        self._start  = time.perf_counter()
        self.done    = False

    def current_pos(self) -> tuple[float, float]:
        """Return current (x, y) pixel position of the piece centre."""
        elapsed = (time.perf_counter() - self._start) * 1000
        t       = min(1.0, elapsed / self.duration)
        et      = _ease_out_back(t)

        if t >= 1.0:
            self.done = True

        sx, sy = _sq_center(self.src_sq, self.flipped)
        dx, dy = _sq_center(self.dst_sq, self.flipped)
        x = sx + (dx - sx) * et
        y = sy + (dy - sy) * et
        return x, y

    def draw(self, surf: pygame.Surface, renderer):
        if self.done:
            return
        cx, cy = self.current_pos()
        renderer._draw_piece_at_center(self.piece, cx, cy, alpha=255)


# ══════════════════════════════════════════════════════════
# CaptureAnimation
# ══════════════════════════════════════════════════════════
class CaptureAnimation:
    """
    The captured piece shrinks and fades out over ~180 ms,
    centred on dst_sq (where it was before being taken).
    """
    DURATION_MS = 180

    def __init__(self, piece: chess.Piece,
                 sq: chess.Square, flipped: bool = False):
        self.piece   = piece
        self.sq      = sq
        self.flipped = flipped
        self._start  = time.perf_counter()
        self.done    = False

    def draw(self, surf: pygame.Surface, renderer):
        elapsed = (time.perf_counter() - self._start) * 1000
        t       = min(1.0, elapsed / self.DURATION_MS)
        if t >= 1.0:
            self.done = True
            return
        scale = 1.0 - _ease_out_cubic(t)
        alpha = int(255 * (1.0 - t))
        cx, cy = _sq_center(self.sq, self.flipped)
        renderer._draw_piece_at_center(self.piece, cx, cy,
                                       alpha=alpha, scale=scale)


# ══════════════════════════════════════════════════════════
# DragState
# ══════════════════════════════════════════════════════════
class DragState:
    """Tracks a piece being dragged by the mouse."""

    def __init__(self):
        self.active   = False
        self.piece    : Optional[chess.Piece]  = None
        self.from_sq  : Optional[chess.Square] = None
        self.mouse_pos: tuple[int, int]        = (0, 0)
        # Subtle lift offset (piece rises slightly on pickup)
        self._lift    = 0.0
        self._lift_t  = 0.0

    def start(self, piece: chess.Piece, sq: chess.Square, pos: tuple):
        self.active    = True
        self.piece     = piece
        self.from_sq   = sq
        self.mouse_pos = pos
        self._lift_t   = time.perf_counter()
        self._lift     = 0.0

    def move(self, pos: tuple):
        self.mouse_pos = pos

    def stop(self):
        self.active  = False
        self.piece   = None
        self.from_sq = None

    @property
    def lift_offset(self) -> float:
        """Vertical lift in pixels (0→8 px over 120 ms)."""
        if not self.active:
            return 0.0
        t = min(1.0, (time.perf_counter() - self._lift_t) / 0.12)
        return 8.0 * _ease_out_cubic(t)

    def draw(self, surf: pygame.Surface, renderer):
        if not self.active or self.piece is None:
            return
        mx, my  = self.mouse_pos
        lift    = self.lift_offset
        renderer._draw_piece_at_center(
            self.piece, mx, my - lift, alpha=230, scale=1.12)


# ══════════════════════════════════════════════════════════
# AnimationManager  –  owns all running animations
# ══════════════════════════════════════════════════════════
class AnimationManager:
    """
    Single object that holds all active animations.
    Call `trigger_move()` after every board push.
    Call `draw()` every frame (before the dragged piece).
    """

    def __init__(self):
        self._slides  : list[SlideAnimation]   = []
        self._captures: list[CaptureAnimation] = []
        self.drag     = DragState()

    # ── Public API ────────────────────────────────────────
    def trigger_move(self, move: chess.Move,
                     moving_piece: chess.Piece,
                     captured_piece: Optional[chess.Piece],
                     flipped: bool = False):
        """
        Start a slide for `moving_piece` and (if any) a capture pop.
        Call this BEFORE pushing the move to the board so the board
        still shows the original position while animating.
        Actually: call it right after push — renderer will skip
        the animating square via `skip_sq`.
        """
        # Slide animation
        self._slides.append(
            SlideAnimation(moving_piece, move.from_square,
                           move.to_square, flipped))

        # Capture animation
        if captured_piece is not None:
            self._captures.append(
                CaptureAnimation(captured_piece, move.to_square, flipped))

    def trigger_ai_move(self, move: chess.Move,
                        moving_piece: chess.Piece,
                        captured_piece: Optional[chess.Piece],
                        flipped: bool = False):
        """Same as trigger_move, alias for clarity."""
        self.trigger_move(move, moving_piece, captured_piece, flipped)

    def update_flipped(self, flipped: bool):
        """Update flipped flag on all active animations."""
        for a in self._slides:   a.flipped = flipped
        for a in self._captures: a.flipped = flipped
        self.drag.from_sq  # drag from_sq unchanged, renderer handles it

    @property
    def slide_dst(self) -> Optional[chess.Square]:
        """Square currently occupied by a sliding piece (skip normal draw)."""
        for s in self._slides:
            if not s.done:
                return s.dst_sq
        return None

    @property
    def slide_src(self) -> Optional[chess.Square]:
        """Source square of the current slide (hide the original piece)."""
        for s in self._slides:
            if not s.done:
                return s.src_sq
        return None

    @property
    def animating(self) -> bool:
        return any(not s.done for s in self._slides) or \
               any(not c.done for c in self._captures)

    def draw_captures(self, surf: pygame.Surface, renderer):
        """Draw capture pops (behind sliding piece)."""
        for c in self._captures:
            if not c.done:
                c.draw(surf, renderer)
        self._captures = [c for c in self._captures if not c.done]

    def draw_slides(self, surf: pygame.Surface, renderer):
        """Draw sliding pieces (on top of board)."""
        for s in self._slides:
            if not s.done:
                s.draw(surf, renderer)
        self._slides = [s for s in self._slides if not s.done]

    def draw_drag(self, surf: pygame.Surface, renderer):
        self.drag.draw(surf, renderer)