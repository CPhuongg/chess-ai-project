"""
renderer.py  –  All Pygame drawing: board, pieces, highlights, panel.
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


class Renderer:
    def __init__(self, surface, font_reg, font_bold, pieces_dir="assets/images/pieces"):
        self.surf       = surface
        self.fr         = font_reg
        self.fb         = font_bold
        self.pdir       = pieces_dir
        self._imgs: dict = {}
        self._fallback_font = None
        self._load_pieces()

    # ── Asset loading ────────────────────────────────────
    def _load_pieces(self):
        for color, prefix in ((True,"w"),(False,"b")):
            for pt, sym in PIECE_SYMBOL.items():
                key  = f"{prefix}{sym}"
                path = os.path.join(self.pdir, f"{key}.png")
                if os.path.isfile(path):
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.smoothscale(img,(SQUARE_SIZE-10, SQUARE_SIZE-10))
                    self._imgs[key] = img
                else:
                    self._imgs[key] = None

    def _get_img(self, piece: chess.Piece):
        key = ("w" if piece.color else "b") + PIECE_SYMBOL[piece.piece_type]
        return self._imgs.get(key)

    def _fallback(self) -> pygame.font.Font:
        if self._fallback_font is None:
            self._fallback_font = pygame.font.SysFont(
                "segoeuisymbol,symbola,dejavusans,freesans", SQUARE_SIZE - 12)
        return self._fallback_font

    # ── Coord helpers ────────────────────────────────────
    @staticmethod
    def sq_to_px(sq, flipped=False):
        f = chess.square_file(sq); r = chess.square_rank(sq)
        if flipped: f,r = 7-f, 7-r
        x = BOARD_OFFSET_X + f * SQUARE_SIZE
        y = BOARD_OFFSET_Y + (7-r) * SQUARE_SIZE
        return x,y

    @staticmethod
    def px_to_sq(px, py, flipped=False):
        col = (px - BOARD_OFFSET_X) // SQUARE_SIZE
        row = (py - BOARD_OFFSET_Y) // SQUARE_SIZE
        if not (0<=col<8 and 0<=row<8): return None
        f = col; r = 7-row
        if flipped: f,r = 7-f, 7-r
        return chess.square(f,r)

    # ── Draw helpers ─────────────────────────────────────
    def _fill_sq(self, sq, color, flipped):
        x,y = self.sq_to_px(sq, flipped)
        if len(color)==4:
            s = pygame.Surface((SQUARE_SIZE,SQUARE_SIZE),pygame.SRCALPHA)
            s.fill(color)
            self.surf.blit(s,(x,y))
        else:
            pygame.draw.rect(self.surf,color,pygame.Rect(x,y,SQUARE_SIZE,SQUARE_SIZE))

    # ── Public API ───────────────────────────────────────
    def fill_bg(self):
        self.surf.fill(C_BG)

    def draw_panel_bg(self, x, y, w, h):
        pygame.draw.rect(self.surf, C_PANEL, pygame.Rect(x,y,w,h), border_radius=12)

    def draw_board(self, board, selected_sq=None, legal_moves=(), last_move=None, flipped=False):
        for sq in chess.SQUARES:
            f = chess.square_file(sq); r = chess.square_rank(sq)
            base = C_LIGHT if (f+r)%2==0 else C_DARK
            self._fill_sq(sq, base, flipped)

            if last_move and sq in (last_move.from_square, last_move.to_square):
                self._fill_sq(sq, C_HL_MOV, flipped)
            if sq == selected_sq:
                self._fill_sq(sq, C_HL_SEL, flipped)
            if board.is_check() and sq == board.king(board.turn):
                self._fill_sq(sq, C_HL_CHK, flipped)

        # Legal move dots
        for m in legal_moves:
            sq = m.to_square
            x,y = self.sq_to_px(sq, flipped)
            s = pygame.Surface((SQUARE_SIZE,SQUARE_SIZE), pygame.SRCALPHA)
            if board.piece_at(sq):
                pygame.draw.circle(s, C_DOT,(SQUARE_SIZE//2,SQUARE_SIZE//2),
                                   SQUARE_SIZE//2-2,4)
            else:
                pygame.draw.circle(s, C_DOT,(SQUARE_SIZE//2,SQUARE_SIZE//2),
                                   SQUARE_SIZE//7)
            self.surf.blit(s,(x,y))

    def draw_pieces(self, board, flipped=False, skip_sq=None):
        for sq in chess.SQUARES:
            if sq == skip_sq: continue
            piece = board.piece_at(sq)
            if piece is None: continue
            x,y = self.sq_to_px(sq, flipped)
            img = self._get_img(piece)
            if img:
                self.surf.blit(img,(x+5,y+5))
            else:
                sym = PIECE_UNICODE.get((piece.piece_type, piece.color),"?")
                tc  = (250,250,250) if piece.color==chess.WHITE else (20,20,20)
                lbl = self._fallback().render(sym, True, tc)
                self.surf.blit(lbl,(x+(SQUARE_SIZE-lbl.get_width())//2,
                                    y+(SQUARE_SIZE-lbl.get_height())//2))

    def draw_dragged(self, piece, pos):
        img = self._get_img(piece)
        if img:
            self.surf.blit(img,(pos[0]-img.get_width()//2, pos[1]-img.get_height()//2))
        else:
            sym = PIECE_UNICODE.get((piece.piece_type, piece.color),"?")
            tc  = (250,250,250) if piece.color==chess.WHITE else (20,20,20)
            lbl = self._fallback().render(sym, True, tc)
            self.surf.blit(lbl,(pos[0]-lbl.get_width()//2, pos[1]-lbl.get_height()//2))

    def draw_coords(self, flipped=False):
        files = "abcdefgh"
        for i in range(8):
            fc = files[i if not flipped else 7-i]
            rn = str(i+1 if not flipped else 8-i)
            # file labels bottom
            lbl = self.fr.render(fc, True, C_GREY)
            self.surf.blit(lbl,(BOARD_OFFSET_X + i*SQUARE_SIZE + SQUARE_SIZE//2 - lbl.get_width()//2,
                                BOARD_OFFSET_Y + BOARD_SIZE + 4))
            # rank labels left
            lbl = self.fr.render(rn, True, C_GREY)
            self.surf.blit(lbl,(BOARD_OFFSET_X - lbl.get_width() - 5,
                                BOARD_OFFSET_Y + (7-i)*SQUARE_SIZE + SQUARE_SIZE//2 - lbl.get_height()//2))

    def draw_border(self):
        r = pygame.Rect(BOARD_OFFSET_X-2, BOARD_OFFSET_Y-2, BOARD_SIZE+4, BOARD_SIZE+4)
        pygame.draw.rect(self.surf, C_ACCENT, r, 2, border_radius=4)

    def draw_text(self, text, x, y, font=None, color=None):
        f = font or self.fr
        c = color or C_WHITE
        lbl = f.render(text, True, c)
        self.surf.blit(lbl,(x,y))
        return lbl.get_width()