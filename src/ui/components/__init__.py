"""
components/__init__.py  –  Reusable UI widgets.
"""

import pygame
from src.engine.constants import (
    C_ACCENT, C_WHITE, C_GREY, C_PANEL, C_CARD, C_GREEN, C_RED,
    SQUARE_SIZE,
)

PIECE_UNICODE = {
    1:{True:"♙",False:"♟"}, 2:{True:"♘",False:"♞"},
    3:{True:"♗",False:"♝"}, 4:{True:"♖",False:"♜"},
    5:{True:"♕",False:"♛"}, 6:{True:"♔",False:"♚"},
}


# ── Button ────────────────────────────────────────────────
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


# ── Toggle button (selected / unselected) ─────────────────
class ToggleButton(Button):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.selected = False

    def draw(self, surf):
        c = C_ACCENT if self.selected else (self.hover if self._hov else self.color)
        pygame.draw.rect(surf, c, self.rect, border_radius=self.radius)
        tc = (20, 20, 20) if self.selected else self.tc
        lbl = self.font.render(self.text, True, tc)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))


# ── EvalBar ───────────────────────────────────────────────
class EvalBar:
    CLAMP = 800

    def __init__(self, x, y, h, font):
        self.x = x; self.y = y; self.h = h; self.font = font
        self.score = 0
        self.W = 18

    def update(self, cp): self.score = cp

    def draw(self, surf):
        clamped  = max(-self.CLAMP, min(self.CLAMP, self.score))
        wfrac    = (clamped + self.CLAMP) / (2 * self.CLAMP)
        wh       = int(wfrac * self.h)
        bh       = self.h - wh

        bg = pygame.Rect(self.x, self.y, self.W, self.h)
        pygame.draw.rect(surf, (30,30,30), bg, border_radius=5)

        if bh > 0:
            pygame.draw.rect(surf,(45,45,45),
                pygame.Rect(self.x, self.y, self.W, bh), border_radius=5)
        if wh > 0:
            pygame.draw.rect(surf,(215,215,215),
                pygame.Rect(self.x, self.y+bh, self.W, wh), border_radius=5)

        pawns = self.score / 100
        lbl   = self.font.render(f"{pawns:+.1f}", True, C_GREY)
        surf.blit(lbl,(self.x + self.W + 3,
                       self.y + self.h//2 - lbl.get_height()//2))


# ── Clock display ─────────────────────────────────────────
class ClockDisplay:
    def __init__(self, x, y, w, h, font_big, font_small, color, label):
        self.rect  = pygame.Rect(x, y, w, h)
        self.fb    = font_big
        self.fs    = font_small
        self.color = color
        self.label = label
        self.time_str = "∞"
        self.active   = False
        self.flagged  = False

    def draw(self, surf):
        bg = (80,20,20) if self.flagged else \
             ((50,60,80) if self.active else C_CARD)
        pygame.draw.rect(surf, bg, self.rect, border_radius=8)
        pygame.draw.rect(surf, C_ACCENT if self.active else (60,60,70),
                         self.rect, 1, border_radius=8)

        lbl  = self.fs.render(self.label, True, C_GREY)
        surf.blit(lbl, (self.rect.x+8, self.rect.y+5))

        tc   = C_RED if self.flagged else (C_ACCENT if self.active else C_WHITE)
        time = self.fb.render(self.time_str, True, tc)
        surf.blit(time, time.get_rect(
            centerx=self.rect.centerx,
            centery=self.rect.centery+6))


# ── Captured pieces ───────────────────────────────────────
class CapturedDisplay:
    def __init__(self, x, y, font):
        self.x=x; self.y=y; self.font=font

    def draw(self, surf, captured):
        PV = {1:1,2:3,3:3,4:5,5:9}
        for i,(side,label) in enumerate([("b","▲"),("w","▼")]):
            pieces = captured[side]
            adv    = sum(PV.get(p,0) for p in pieces)
            syms   = "".join(PIECE_UNICODE[pt][side=="w"] for pt in sorted(pieces))
            row    = f"{label} {syms}  {'+'+str(adv) if adv else ''}"
            lbl    = self.font.render(row, True, C_GREY)
            surf.blit(lbl,(self.x, self.y + i*20))


# ── Move history panel ────────────────────────────────────
class MoveHistoryPanel:
    def __init__(self, x, y, w, h, font):
        self.rect   = pygame.Rect(x, y, w, h)
        self.font   = font
        self.lh     = font.get_height() + 5
        self._scroll= 0

    def draw(self, surf, san_list):
        pygame.draw.rect(surf, C_PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surf, (55,55,65), self.rect, 1, border_radius=8)

        if not san_list:
            lbl = self.font.render("No moves", True, (70,70,80))
            surf.blit(lbl,(self.rect.x+8, self.rect.y+8))
            return

        pairs = []
        for i in range(0, len(san_list), 2):
            pairs.append((i//2+1, san_list[i],
                          san_list[i+1] if i+1 < len(san_list) else ""))

        total = len(pairs) * self.lh
        if total > self.rect.height:
            self._scroll = total - self.rect.height + 8

        clip = surf.subsurface(self.rect)
        clip.fill(C_PANEL)

        for idx,(num,w,b) in enumerate(pairs):
            ry = idx*self.lh - self._scroll
            if ry + self.lh < 0 or ry > self.rect.height: continue
            # Highlight last pair
            is_last = (idx == len(pairs)-1)
            if is_last:
                hr = pygame.Rect(2, ry, self.rect.width-4, self.lh)
                pygame.draw.rect(clip,(50,50,65),hr,border_radius=4)

            nl = self.font.render(f"{num}.", True,(70,70,85))
            wl = self.font.render(w, True, C_WHITE)
            bl = self.font.render(b, True, C_GREY) if b else None
            clip.blit(nl,(4,  ry+2))
            clip.blit(wl,(32, ry+2))
            if bl: clip.blit(bl,(90, ry+2))


# ── Promotion dialog ──────────────────────────────────────
class PromotionDialog:
    """Modal dialog: pick queen/rook/bishop/knight."""

    PIECES = [
        (chess_pt, sym)
        for chess_pt, sym in [
            (5, "♛"), (4, "♜"), (3, "♝"), (2, "♞"),   # Black chars
        ]
    ]

    def __init__(self, cx, cy, font_big):
        import chess
        self._chess  = chess
        self.font    = font_big
        self.visible = False
        self.color   = chess.WHITE
        self.result  = None
        SIZE = 70
        xs = [cx - SIZE*2 + SIZE*i for i in range(4)]
        self.rects = [pygame.Rect(x - SIZE//2, cy - SIZE//2, SIZE, SIZE) for x in xs]

    def show(self, color):
        import chess
        self.color   = color
        self.visible = True
        self.result  = None

    def handle_event(self, ev):
        if not self.visible: return None
        if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            for i,(rect,_) in enumerate(zip(self.rects, self.PIECES)):
                if rect.collidepoint(ev.pos):
                    self.result  = self.PIECES[i][0]
                    self.visible = False
                    return self.result
        return None

    def draw(self, surf):
        if not self.visible: return
        import chess
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        overlay.fill((0,0,0,160))
        surf.blit(overlay,(0,0))
        SYMS_W = ["♕","♖","♗","♘"]
        SYMS_B = ["♛","♜","♝","♞"]
        syms = SYMS_W if self.color == chess.WHITE else SYMS_B
        for rect,sym in zip(self.rects, syms):
            pygame.draw.rect(surf, C_CARD, rect, border_radius=10)
            pygame.draw.rect(surf, C_ACCENT, rect, 2, border_radius=10)
            tc = C_WHITE if self.color == chess.WHITE else (220,220,220)
            lbl = self.font.render(sym, True, tc)
            surf.blit(lbl, lbl.get_rect(center=rect.center))