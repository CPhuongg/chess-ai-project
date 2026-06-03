"""
renderer.py  –  All Pygame drawing: board, pieces, highlights, panel.
Piece rendering: PNG image → Unicode glyph (if font supports) → ASCII letter fallback.
"""

import os
import pygame
import chess
from typing import Optional
from src.engine.constants import (
    BOARD_SIZE, SQUARE_SIZE, BOARD_OFFSET_X, BOARD_OFFSET_Y,
    C_LIGHT, C_DARK, C_BG, C_PANEL, C_ACCENT, C_GREY, C_WHITE,
    C_HL_SEL, C_HL_MOV, C_HL_CHK, C_DOT,
    PIECE_SYMBOL, PIECE_UNICODE,
)

# ASCII fallback letters
_PIECE_LETTER = {1:"P", 2:"N", 3:"B", 4:"R", 5:"Q", 6:"K"}

_unicode_font_cache: dict = {}

def _unicode_font(size: int) -> Optional[pygame.font.Font]:
    """Return a font that can render chess Unicode glyphs, or None."""
    if size in _unicode_font_cache:
        return _unicode_font_cache[size]
    candidates = [
        "segoeuisymbol", "seguisym", "segoeui",
        "dejavusans", "freesans", "liberationsans",
        "notosans", "unifont", "symbola", "arial",
    ]
    chosen = None
    for name in candidates:
        try:
            f    = pygame.font.SysFont(name, size)
            test = f.render("♙", True, (255, 255, 255))
            if test.get_width() > 5:
                chosen = f
                break
        except Exception:
            pass
    _unicode_font_cache[size] = chosen
    return chosen


class Renderer:
    def __init__(self, surface, font_reg, font_bold,
                 pieces_dir="assets/images/pieces"):
        self.surf  = surface
        self.fr    = font_reg
        self.fb    = font_bold
        self.pdir  = pieces_dir
        self._imgs: dict = {}
        self._fallback_font: Optional[pygame.font.Font] = None
        self._load_pieces()

    # ── Asset loading ────────────────────────────────────────
    def _load_pieces(self):
        for color, prefix in ((True, "w"), (False, "b")):
            for pt, sym in PIECE_SYMBOL.items():
                key  = f"{prefix}{sym}"
                path = os.path.join(self.pdir, f"{key}.png")
                if os.path.isfile(path):
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(
                        img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                    self._imgs[key] = img
                else:
                    self._imgs[key] = None

    def _get_img(self, piece: chess.Piece) -> Optional[pygame.Surface]:
        key = ("w" if piece.color else "b") + PIECE_SYMBOL[piece.piece_type]
        return self._imgs.get(key)

    def _piece_font(self) -> pygame.font.Font:
        """Font for rendering pieces as Unicode glyphs (board size)."""
        f = _unicode_font(SQUARE_SIZE - 10)
        if f is None:
            if self._fallback_font is None:
                self._fallback_font = pygame.font.Font(None, SQUARE_SIZE - 6)
            return self._fallback_font
        return f

    # ── Coord helpers ────────────────────────────────────────
    @staticmethod
    def sq_to_px(sq: chess.Square, flipped: bool = False) -> tuple[int, int]:
        f = chess.square_file(sq); r = chess.square_rank(sq)
        if flipped: f, r = 7 - f, 7 - r
        x = BOARD_OFFSET_X + f * SQUARE_SIZE
        y = BOARD_OFFSET_Y + (7 - r) * SQUARE_SIZE
        return x, y

    @staticmethod
    def px_to_sq(px: int, py: int,
                 flipped: bool = False) -> Optional[chess.Square]:
        col = (px - BOARD_OFFSET_X) // SQUARE_SIZE
        row = (py - BOARD_OFFSET_Y) // SQUARE_SIZE
        if not (0 <= col < 8 and 0 <= row < 8):
            return None
        f = col; r = 7 - row
        if flipped: f, r = 7 - f, 7 - r
        return chess.square(f, r)

    # ── Draw helpers ─────────────────────────────────────────
    def _fill_sq(self, sq, color, flipped):
        x, y = self.sq_to_px(sq, flipped)
        if len(color) == 4:
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(color)
            self.surf.blit(s, (x, y))
        else:
            pygame.draw.rect(self.surf, color,
                             pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE))

    # ── Public API ───────────────────────────────────────────
    def fill_bg(self):
        self.surf.fill(C_BG)

    def draw_panel_bg(self, x, y, w, h):
        pygame.draw.rect(self.surf, C_PANEL,
                         pygame.Rect(x, y, w, h), border_radius=12)

    def draw_board(self, board, selected_sq=None,
                   legal_moves=(), last_move=None, flipped=False):
        for sq in chess.SQUARES:
            f = chess.square_file(sq); r = chess.square_rank(sq)
            base = C_LIGHT if (f + r) % 2 == 0 else C_DARK
            self._fill_sq(sq, base, flipped)

            if last_move and sq in (last_move.from_square, last_move.to_square):
                self._fill_sq(sq, C_HL_MOV, flipped)
            if sq == selected_sq:
                self._fill_sq(sq, C_HL_SEL, flipped)
            if board.is_check() and sq == board.king(board.turn):
                self._fill_sq(sq, C_HL_CHK, flipped)

        # Legal-move hints
        for m in legal_moves:
            sq   = m.to_square
            x, y = self.sq_to_px(sq, flipped)
            s    = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            if board.piece_at(sq):
                pygame.draw.circle(s, C_DOT,
                    (SQUARE_SIZE // 2, SQUARE_SIZE // 2),
                    SQUARE_SIZE // 2 - 2, 4)
            else:
                pygame.draw.circle(s, C_DOT,
                    (SQUARE_SIZE // 2, SQUARE_SIZE // 2),
                    SQUARE_SIZE // 7)
            self.surf.blit(s, (x, y))

    def draw_pieces(self, board: chess.Board,
                    flipped: bool = False,
                    skip_sq: Optional[chess.Square] = None):
        pf = self._piece_font()
        for sq in chess.SQUARES:
            if sq == skip_sq:
                continue
            piece = board.piece_at(sq)
            if piece is None:
                continue
            self._draw_one_piece(piece, sq, flipped, pf)

    def _draw_one_piece(self, piece: chess.Piece, sq: chess.Square,
                        flipped: bool, pf: pygame.font.Font):
        x, y = self.sq_to_px(sq, flipped)
        img  = self._get_img(piece)
        if img:
            self.surf.blit(img, (x + 5, y + 5))
            return

        # Try Unicode glyph
        sym = PIECE_UNICODE.get((piece.piece_type, piece.color))
        tc  = (252, 252, 252) if piece.color == chess.WHITE else (20, 20, 20)
        outline = (20, 20, 20) if piece.color == chess.WHITE else (200, 200, 200)

        uf = _unicode_font(SQUARE_SIZE - 10)
        if uf and sym:
            rendered = uf.render(sym, True, tc)
            if rendered.get_width() > 5:
                # Subtle outline for contrast
                for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                    ol = uf.render(sym, True, outline)
                    self.surf.blit(ol, (x + (SQUARE_SIZE-ol.get_width())//2 + dx,
                                       y + (SQUARE_SIZE-ol.get_height())//2 + dy))
                self.surf.blit(rendered,
                               (x + (SQUARE_SIZE - rendered.get_width())  // 2,
                                y + (SQUARE_SIZE - rendered.get_height()) // 2))
                return

        # ASCII letter fallback – coloured circle + letter
        cx_  = x + SQUARE_SIZE // 2
        cy_  = y + SQUARE_SIZE // 2
        r_   = SQUARE_SIZE // 2 - 6
        bg   = (230, 230, 230) if piece.color == chess.WHITE else (40, 40, 40)
        border_c = (80, 80, 80) if piece.color == chess.WHITE else (180, 180, 180)
        pygame.draw.circle(self.surf, bg, (cx_, cy_), r_)
        pygame.draw.circle(self.surf, border_c, (cx_, cy_), r_, 2)
        letter = _PIECE_LETTER.get(piece.piece_type, "?")
        lbl    = pf.render(letter, True, tc)
        self.surf.blit(lbl, lbl.get_rect(center=(cx_, cy_)))

    def draw_dragged(self, piece: chess.Piece, pos: tuple[int, int]):
        img = self._get_img(piece)
        if img:
            self.surf.blit(img, (pos[0] - img.get_width()  // 2,
                                 pos[1] - img.get_height() // 2))
            return
        # fallback circle
        r_  = SQUARE_SIZE // 2 - 4
        bg  = (230, 230, 230) if piece.color == chess.WHITE else (40, 40, 40)
        pygame.draw.circle(self.surf, bg, pos, r_)
        pygame.draw.circle(self.surf, C_ACCENT, pos, r_, 2)
        pf     = self._piece_font()
        tc     = (20, 20, 20) if piece.color == chess.WHITE else (210, 210, 210)
        letter = _PIECE_LETTER.get(piece.piece_type, "?")
        lbl    = pf.render(letter, True, tc)
        self.surf.blit(lbl, lbl.get_rect(center=pos))

    def draw_coords(self, flipped: bool = False):
        files = "abcdefgh"
        for i in range(8):
            fc = files[i if not flipped else 7 - i]
            rn = str(i + 1 if not flipped else 8 - i)
            lbl = self.fr.render(fc, True, C_GREY)
            self.surf.blit(lbl,
                (BOARD_OFFSET_X + i * SQUARE_SIZE + SQUARE_SIZE//2 - lbl.get_width()//2,
                 BOARD_OFFSET_Y + BOARD_SIZE + 4))
            lbl = self.fr.render(rn, True, C_GREY)
            self.surf.blit(lbl,
                (BOARD_OFFSET_X - lbl.get_width() - 5,
                 BOARD_OFFSET_Y + (7 - i) * SQUARE_SIZE + SQUARE_SIZE//2 - lbl.get_height()//2))

    def draw_border(self):
        r = pygame.Rect(BOARD_OFFSET_X - 2, BOARD_OFFSET_Y - 2,
                        BOARD_SIZE + 4, BOARD_SIZE + 4)
        pygame.draw.rect(self.surf, C_ACCENT, r, 2, border_radius=4)

    def draw_text(self, text: str, x: int, y: int,
                  font=None, color=None) -> int:
        f   = font  or self.fr
        c   = color or C_WHITE
        lbl = f.render(text, True, c)
        self.surf.blit(lbl, (x, y))
        return lbl.get_width()

    # ── Animation support ─────────────────────────────────
    def _draw_piece_at_center(self, piece: chess.Piece,
                               cx: float, cy: float,
                               alpha: int = 255,
                               scale: float = 1.0):
        """
        Draw `piece` centred on pixel (cx, cy).
        Supports alpha transparency and uniform scaling.
        Used by animation system.
        """
        SIZE = int(SQUARE_SIZE * scale)
        img  = self._get_img(piece)

        if img:
            scaled = pygame.transform.smoothscale(img, (SIZE - 8, SIZE - 8))
            if alpha < 255:
                scaled = scaled.copy()
                scaled.set_alpha(alpha)
            self.surf.blit(scaled, (int(cx) - (SIZE - 8) // 2,
                                    int(cy) - (SIZE - 8) // 2))
            return

        # Unicode / ASCII fallback with alpha surface
        pf  = self._piece_font()
        sym = PIECE_UNICODE.get((piece.piece_type, piece.color))
        tc  = (252, 252, 252) if piece.color == chess.WHITE else (20, 20, 20)
        ol  = (20, 20, 20)   if piece.color == chess.WHITE else (200, 200, 200)

        uf = _unicode_font(int((SQUARE_SIZE - 10) * scale))
        if uf and sym:
            rendered = uf.render(sym, True, tc)
            if rendered.get_width() > 5:
                tmp = pygame.Surface(rendered.get_size(), pygame.SRCALPHA)
                tmp.blit(rendered, (0, 0))
                tmp.set_alpha(alpha)
                self.surf.blit(tmp, (int(cx) - rendered.get_width()  // 2,
                                     int(cy) - rendered.get_height() // 2))
                return

        # Circle fallback
        r_   = int((SQUARE_SIZE // 2 - 5) * scale)
        bg   = (230, 230, 230) if piece.color == chess.WHITE else (40, 40, 40)
        tmp  = pygame.Surface((r_ * 2 + 4, r_ * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(tmp, (*bg, alpha), (r_ + 2, r_ + 2), r_)
        letter = _PIECE_LETTER.get(piece.piece_type, "?")
        lbl    = pf.render(letter, True, (*tc, alpha) if len(tc) == 3 else tc)
        tmp.blit(lbl, lbl.get_rect(center=(r_ + 2, r_ + 2)))
        self.surf.blit(tmp, (int(cx) - r_ - 2, int(cy) - r_ - 2))