"""
components/__init__.py  –  All reusable UI widgets.

Layout zones (reference):
  Eval bar  : x=736..756  (between board and side panel, standalone)
  Side panel: x=760..1166
"""

import chess
import pygame
from src.engine.constants import (
    C_ACCENT, C_WHITE, C_GREY, C_PANEL, C_CARD,
    C_GREEN, C_RED, C_YELLOW, SQUARE_SIZE,
)

PIECE_LETTER = {
    chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B",
    chess.ROOK: "R", chess.QUEEN:  "Q", chess.KING:   "K",
}

# ── font helpers ──────────────────────────────────────────
_unicode_font_cache: dict = {}

def _get_unicode_font(size: int):
    if size in _unicode_font_cache:
        return _unicode_font_cache[size]
    candidates = ["segoeuisymbol","seguisym","segoeui","dejavusans",
                  "freesans","liberationsans","notosans","unifont","arial"]
    chosen = None
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, size)
            if f.render("P", True, (255,255,255)).get_width() > 3:
                chosen = f; break
        except Exception:
            pass
    _unicode_font_cache[size] = chosen
    return chosen


# ══════════════════════════════════════════════════════════
# Button
# ══════════════════════════════════════════════════════════
class Button:
    def __init__(self, x, y, w, h, text, font,
                 color=(55,55,65), hover=(75,75,90),
                 text_color=None, radius=8, accent_border=True):
        self.rect     = pygame.Rect(x, y, w, h)
        self.text     = text
        self.font     = font
        self.color    = color
        self.hover    = hover
        self.tc       = text_color or C_WHITE
        self.radius   = radius
        self.bordered = accent_border
        self._hov     = False

    def handle_event(self, ev) -> bool:
        if ev.type == pygame.MOUSEMOTION:
            self._hov = self.rect.collidepoint(ev.pos)
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            return self.rect.collidepoint(ev.pos)
        return False

    def draw(self, surf):
        c = self.hover if self._hov else self.color
        pygame.draw.rect(surf, c, self.rect, border_radius=self.radius)
        if self.bordered:
            pygame.draw.rect(surf, C_ACCENT, self.rect, 1, border_radius=self.radius)
        lbl = self.font.render(self.text, True, self.tc)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))


# ══════════════════════════════════════════════════════════
# ToggleButton
# ══════════════════════════════════════════════════════════
class ToggleButton(Button):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.selected = False

    def draw(self, surf):
        c  = C_ACCENT if self.selected else (self.hover if self._hov else self.color)
        tc = (15, 15, 15) if self.selected else self.tc
        pygame.draw.rect(surf, c, self.rect, border_radius=self.radius)
        lbl = self.font.render(self.text, True, tc)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))


# ══════════════════════════════════════════════════════════
# EvalBar  –  standalone vertical bar (placed BETWEEN board and panel)
# ══════════════════════════════════════════════════════════
class EvalBar:
    """
    Vertical centipawn bar.
    x, y  : top-left of the bar itself
    height: total height (should match BOARD_SIZE)
    width : bar width in pixels (default 20)
    """
    CLAMP = 800

    def __init__(self, x: int, y: int, height: int, font,
                 width: int = 20):
        self.x      = x
        self.y      = y
        self.h      = height
        self.w      = width
        self.font   = font
        self.score  = 0          # centipawns, White POV
        self._disp  = 0.0        # smoothed display value

    def update(self, cp: int):
        self.score = cp

    def draw(self, surf: pygame.Surface):
        # Smooth animation toward target
        self._disp += (self.score - self._disp) * 0.18

        clamped = max(-self.CLAMP, min(self.CLAMP, self._disp))
        wfrac   = (clamped + self.CLAMP) / (2 * self.CLAMP)
        wh      = max(4, int(wfrac * self.h))
        bh      = self.h - wh

        bar_rect = pygame.Rect(self.x, self.y, self.w, self.h)

        # Background track
        pygame.draw.rect(surf, (28, 28, 32), bar_rect, border_radius=6)

        # Black portion (top)
        if bh > 0:
            pygame.draw.rect(surf, (55, 55, 65),
                pygame.Rect(self.x, self.y, self.w, bh),
                border_radius=6)

        # White portion (bottom)
        if wh > 0:
            pygame.draw.rect(surf, (205, 205, 215),
                pygame.Rect(self.x, self.y + bh, self.w, wh),
                border_radius=6)

        # Centre divider tick
        mid_y = self.y + self.h // 2
        pygame.draw.line(surf, C_ACCENT,
                         (self.x, mid_y), (self.x + self.w, mid_y), 1)

        # Border
        pygame.draw.rect(surf, (70, 70, 80), bar_rect, 1, border_radius=6)

        # Score label below the bar
        pawns = self._disp / 100.0
        if abs(pawns) >= 100:
            label = "+M" if pawns > 0 else "-M"
        else:
            label = f"{pawns:+.1f}"
        lbl = self.font.render(label, True, C_GREY)
        surf.blit(lbl, (self.x + self.w // 2 - lbl.get_width() // 2,
                        self.y + self.h + 4))

        # "W" / "B" labels at top and bottom
        w_lbl = self.font.render("W", True, (200, 200, 200))
        b_lbl = self.font.render("B", True, (120, 120, 130))
        surf.blit(b_lbl, (self.x + self.w // 2 - b_lbl.get_width() // 2,
                           self.y + 3))
        surf.blit(w_lbl, (self.x + self.w // 2 - w_lbl.get_width() // 2,
                           self.y + self.h - w_lbl.get_height() - 3))


# ══════════════════════════════════════════════════════════
# ClockDisplay  –  pure ASCII text, no Unicode
# ══════════════════════════════════════════════════════════
class ClockDisplay:
    def __init__(self, x, y, w, h, font_big, font_small, color, label):
        self.rect     = pygame.Rect(x, y, w, h)
        self.fb       = font_big
        self.fs       = font_small
        self.label    = label        # "White" / "Black"
        self.time_str = "--:--"
        self.active   = False
        self.flagged  = False

    def draw(self, surf):
        bg = (90, 20, 20) if self.flagged else \
             (38, 58, 85) if self.active  else C_CARD
        pygame.draw.rect(surf, bg, self.rect, border_radius=8)
        border_c = C_ACCENT if self.active else (60, 60, 72)
        pygame.draw.rect(surf, border_c, self.rect, 1, border_radius=8)

        # Side label (top-left, small)
        lbl = self.fs.render(self.label, True,
                             C_ACCENT if self.active else C_GREY)
        surf.blit(lbl, (self.rect.x + 8, self.rect.y + 6))

        # Time string (centred, large)
        tc   = C_RED if self.flagged else (C_WHITE if self.active else (160,160,170))
        time = self.fb.render(self.time_str, True, tc)
        surf.blit(time, time.get_rect(
            centerx=self.rect.centerx,
            centery=self.rect.centery + 7))


# ══════════════════════════════════════════════════════════
# CapturedDisplay  –  coloured letter badges
# ══════════════════════════════════════════════════════════
class CapturedDisplay:
    BOX = 16
    GAP = 2

    def __init__(self, x, y, font):
        self.x = x; self.y = y; self.font = font

    def _row(self, surf, pieces: list, piece_white: bool,
             label: str, dy: int):
        PV = {chess.PAWN:1, chess.KNIGHT:3, chess.BISHOP:3,
              chess.ROOK:5, chess.QUEEN:9}
        adv = sum(PV.get(p, 0) for p in pieces)
        lbl = self.font.render(label, True, C_GREY)
        surf.blit(lbl, (self.x, self.y + dy))
        ox = self.x + lbl.get_width() + 3
        for pt in sorted(pieces):
            box = pygame.Rect(ox, self.y + dy, self.BOX, self.BOX)
            bg  = (215, 215, 215) if piece_white else (45, 45, 50)
            tc  = (20,  20,  20)  if piece_white else (200, 200, 200)
            pygame.draw.rect(surf, bg, box, border_radius=3)
            letter = PIECE_LETTER.get(pt, "?")
            sl = self.font.render(letter, True, tc)
            surf.blit(sl, sl.get_rect(center=box.center))
            ox += self.BOX + self.GAP
        if adv > 0:
            al = self.font.render(f"+{adv}", True, C_ACCENT)
            surf.blit(al, (ox + 2, self.y + dy))

    def draw(self, surf, captured: dict):
        self._row(surf, captured["b"], False, "W:", 0)
        self._row(surf, captured["w"], True,  "B:", 20)


# ══════════════════════════════════════════════════════════
# MoveHistoryPanel  –  scrollable with mouse wheel
# ══════════════════════════════════════════════════════════
class MoveHistoryPanel:
    """
    Scrollable move list. Supports:
      - Mouse wheel scrolling
      - Auto-scroll to latest move
      - Highlighted current move pair
    """
    SCROLLBAR_W = 6

    def __init__(self, x, y, w, h, font):
        self.rect      = pygame.Rect(x, y, w, h)
        self.font      = font
        self.lh        = font.get_height() + 6
        self._scroll   = 0          # pixel offset from top
        self._max_sc   = 0
        self._auto_sc  = True       # auto-scroll to bottom

    # ── mouse wheel support (call from event loop) ────────
    def handle_event(self, ev) -> bool:
        if ev.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self._scroll = max(0, min(
                    self._max_sc,
                    self._scroll - ev.y * self.lh))
                self._auto_sc = (self._scroll >= self._max_sc - 2)
                return True
        return False

    def draw(self, surf, san_list: list):
        # Background + border
        pygame.draw.rect(surf, (26, 26, 32), self.rect, border_radius=8)
        pygame.draw.rect(surf, (55, 55, 68), self.rect, 1, border_radius=8)

        if not san_list:
            lbl = self.font.render("No moves yet", True, (65, 65, 78))
            surf.blit(lbl, (self.rect.x + 10, self.rect.y + 10))
            return

        # Build pairs: [(move_num, white_san, black_san), ...]
        pairs = []
        for i in range(0, len(san_list), 2):
            pairs.append((i // 2 + 1, san_list[i],
                          san_list[i + 1] if i + 1 < len(san_list) else ""))

        total_h      = len(pairs) * self.lh
        self._max_sc = max(0, total_h - self.rect.height + 8)

        # Auto-scroll to bottom when new move added
        if self._auto_sc:
            self._scroll = self._max_sc

        # Clip region
        inner_w = self.rect.width - self.SCROLLBAR_W - 6
        clip_r  = pygame.Rect(self.rect.x, self.rect.y,
                               inner_w + 4, self.rect.height)
        # Use a subsurface for clipping
        try:
            clip = surf.subsurface(
                pygame.Rect(self.rect.x + 2, self.rect.y + 2,
                            inner_w + 2, self.rect.height - 4))
        except ValueError:
            return
        clip.fill((26, 26, 32))

        last_idx = len(pairs) - 1
        for idx, (num, w, b) in enumerate(pairs):
            ry = idx * self.lh - self._scroll
            if ry + self.lh < 0 or ry > self.rect.height:
                continue

            # Row background: alternate + highlight last
            if idx == last_idx:
                row_bg = pygame.Rect(0, ry, inner_w, self.lh)
                pygame.draw.rect(clip, (48, 52, 70), row_bg, border_radius=4)
            elif idx % 2 == 0:
                row_bg = pygame.Rect(0, ry, inner_w, self.lh)
                pygame.draw.rect(clip, (30, 30, 38), row_bg)

            # Number column
            nl = self.font.render(f"{num}.", True, (75, 75, 92))
            clip.blit(nl, (4, ry + 3))

            # White move
            wl = self.font.render(w, True, C_WHITE)
            clip.blit(wl, (36, ry + 3))

            # Black move
            if b:
                bl = self.font.render(b, True, (175, 175, 185))
                clip.blit(bl, (106, ry + 3))

        # ── Scrollbar ──────────────────────────────────────
        if self._max_sc > 0:
            sb_x    = self.rect.right - self.SCROLLBAR_W - 2
            sb_h    = self.rect.height - 8
            sb_y    = self.rect.y + 4
            # Track
            pygame.draw.rect(surf, (40, 40, 48),
                pygame.Rect(sb_x, sb_y, self.SCROLLBAR_W, sb_h),
                border_radius=3)
            # Thumb
            thumb_h = max(20, int(sb_h * self.rect.height / (total_h + 8)))
            thumb_y = sb_y + int((sb_h - thumb_h) *
                                  self._scroll / max(1, self._max_sc))
            thumb_c = (100, 100, 120) if not self._auto_sc else (80, 100, 140)
            pygame.draw.rect(surf, thumb_c,
                pygame.Rect(sb_x, thumb_y, self.SCROLLBAR_W, thumb_h),
                border_radius=3)


# ══════════════════════════════════════════════════════════
# PromotionDialog  –  ASCII letter badges, no Unicode
# ══════════════════════════════════════════════════════════
class PromotionDialog:
    OPTIONS = [
        (chess.QUEEN,  "Q", "Queen"),
        (chess.ROOK,   "R", "Rook"),
        (chess.BISHOP, "B", "Bishop"),
        (chess.KNIGHT, "N", "Knight"),
    ]
    SIZE = 72

    def __init__(self, cx, cy, font_big):
        self.font    = font_big
        self.visible = False
        self.color   = chess.WHITE
        self.result  = None
        n  = len(self.OPTIONS)
        xs = [cx - (n * (self.SIZE + 8)) // 2 + i * (self.SIZE + 8)
              for i in range(n)]
        self.rects = [pygame.Rect(x, cy - self.SIZE // 2, self.SIZE, self.SIZE)
                      for x in xs]

    def show(self, color):
        self.color = color; self.visible = True; self.result = None

    def handle_event(self, ev):
        if not self.visible: return None
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            for i, rect in enumerate(self.rects):
                if rect.collidepoint(ev.pos):
                    self.result = self.OPTIONS[i][0]
                    self.visible = False
                    return self.result
        return None

    def draw(self, surf):
        if not self.visible: return
        ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        surf.blit(ov, (0, 0))
        small = pygame.font.Font(None, 17)
        bg_p  = (230, 230, 230) if self.color == chess.WHITE else (50, 50, 50)
        tc_p  = (20,  20,  20)  if self.color == chess.WHITE else (220, 220, 220)
        for rect, (_, letter, name) in zip(self.rects, self.OPTIONS):
            pygame.draw.rect(surf, C_CARD,   rect, border_radius=10)
            pygame.draw.rect(surf, C_ACCENT, rect, 2, border_radius=10)
            pl = self.font.render(letter, True, bg_p)
            surf.blit(pl, pl.get_rect(centerx=rect.centerx, centery=rect.centery - 8))
            nl = small.render(name, True, C_GREY)
            surf.blit(nl, nl.get_rect(centerx=rect.centerx, y=rect.bottom - 20))