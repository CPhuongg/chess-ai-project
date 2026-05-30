"""
ui/renderer.py
Chịu trách nhiệm vẽ bàn cờ, quân cờ, highlight ô, animation, và các hiệu ứng trực quan.
"""

import pygame
import math
from typing import Optional, List, Tuple, Dict

# ── Màu sắc (Dark Luxury Theme) ──────────────────────────────────────────────
COLORS = {
    "light_square":     (237, 220, 192),   # Ô sáng – kem ngà
    "dark_square":      (101,  67,  33),   # Ô tối – nâu gỗ
    "highlight":        (186, 202,  68, 180),  # Ô được chọn – xanh olive
    "move_dot":         ( 40,  40,  40,  90),  # Chấm nước đi hợp lệ
    "last_move_light":  (246, 246, 105, 160),  # Nước đi cuối – ô sáng
    "last_move_dark":   (186, 202,  68, 160),  # Nước đi cuối – ô tối
    "check":            (220,  50,  50, 200),  # Vua đang bị chiếu
    "board_border":     ( 44,  27,   6),   # Viền bàn cờ
    "coord_light":      (101,  67,  33),   # Chữ tọa độ trên ô sáng
    "coord_dark":       (237, 220, 192),   # Chữ tọa độ trên ô tối
    "background":       ( 26,  20,  14),   # Nền tổng thể
    "shadow":           (  0,   0,   0, 120),
}

# Unicode quân cờ
PIECE_UNICODE: Dict[str, str] = {
    "wK": "♔", "wQ": "♕", "wR": "♖", "wB": "♗", "wN": "♘", "wP": "♙",
    "bK": "♚", "bQ": "♛", "bR": "♜", "bB": "♝", "bN": "♞", "bP": "♟",
}


class ChessRenderer:
    """
    Vẽ toàn bộ bàn cờ và trạng thái game.

    Parameters
    ----------
    surface   : pygame.Surface – bề mặt vẽ chính
    board_rect: pygame.Rect    – vùng chứa bàn cờ (không kể viền)
    flipped   : bool           – True → bàn cờ lật (góc nhìn đen)
    """

    def __init__(
        self,
        surface: pygame.Surface,
        board_rect: pygame.Rect,
        flipped: bool = False,
    ) -> None:
        self.surface = surface
        self.board_rect = board_rect
        self.flipped = flipped
        self.square_size = board_rect.width // 8

        # Font chữ quân cờ & tọa độ
        self._piece_font: Optional[pygame.font.Font] = None
        self._coord_font: Optional[pygame.font.Font] = None
        self._init_fonts()

        # Trạng thái animation
        self._anim_piece: Optional[str] = None   # e.g. "wQ"
        self._anim_start: Optional[Tuple[int, int]] = None   # pixel
        self._anim_end:   Optional[Tuple[int, int]] = None   # pixel
        self._anim_t:     float = 0.0   # 0.0 → 1.0
        self._anim_speed: float = 0.08  # tốc độ (tăng để nhanh hơn)

        # Cache surface quân cờ
        self._piece_surfaces: Dict[str, pygame.Surface] = {}

    # ── Khởi tạo ─────────────────────────────────────────────────────────────

    def _init_fonts(self) -> None:
        """Tải font; fallback sang SysFont nếu không có file."""
        size = int(self.square_size * 0.82)
        coord_size = max(10, self.square_size // 6)
        try:
            self._piece_font = pygame.font.SysFont("Segoe UI Symbol", size)
            self._coord_font = pygame.font.SysFont("Georgia", coord_size, bold=True)
        except Exception:
            self._piece_font = pygame.font.Font(None, size)
            self._coord_font = pygame.font.Font(None, coord_size)

    # ── Public API ────────────────────────────────────────────────────────────

    def draw(
        self,
        board: List[List[Optional[str]]],
        selected_sq: Optional[Tuple[int, int]] = None,
        valid_moves: Optional[List[Tuple[int, int]]] = None,
        last_move: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
        in_check_sq: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Vẽ toàn bộ bàn cờ một lần.

        Parameters
        ----------
        board        : ma trận 8×8, mỗi ô None hoặc chuỗi như "wQ", "bK"…
        selected_sq  : ô đang được chọn (row, col)
        valid_moves  : danh sách ô có thể đi
        last_move    : ((r0,c0),(r1,c1)) – nước đi vừa thực hiện
        in_check_sq  : ô vua đang bị chiếu
        """
        self._draw_border()
        self._draw_squares(selected_sq, valid_moves, last_move, in_check_sq)
        self._draw_coordinates()
        self._draw_pieces(board, skip_sq=self._anim_start if self._anim_piece else None)
        if self.is_animating():
            self._draw_animated_piece()

    def start_move_animation(
        self,
        piece: str,
        from_sq: Tuple[int, int],
        to_sq: Tuple[int, int],
    ) -> None:
        """Bắt đầu animation di chuyển quân."""
        self._anim_piece = piece
        self._anim_start = self._sq_to_pixel(*from_sq)
        self._anim_end   = self._sq_to_pixel(*to_sq)
        self._anim_t = 0.0

    def update_animation(self) -> bool:
        """
        Cập nhật tiến độ animation.
        Trả về True khi animation vẫn đang chạy.
        """
        if not self.is_animating():
            return False
        self._anim_t = min(1.0, self._anim_t + self._anim_speed)
        if self._anim_t >= 1.0:
            self._anim_piece = None
        return self._anim_piece is not None

    def is_animating(self) -> bool:
        return self._anim_piece is not None

    def pixel_to_square(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        """Chuyển tọa độ pixel → (row, col) ô cờ; None nếu ngoài bàn."""
        bx = px - self.board_rect.x
        by = py - self.board_rect.y
        if not (0 <= bx < self.board_rect.width and 0 <= by < self.board_rect.height):
            return None
        col = bx // self.square_size
        row = by // self.square_size
        if self.flipped:
            row = 7 - row
            col = 7 - col
        return (row, col)

    def set_flipped(self, flipped: bool) -> None:
        self.flipped = flipped

    # ── Vẽ nội bộ ────────────────────────────────────────────────────────────

    def _draw_border(self) -> None:
        border = 8
        outer = self.board_rect.inflate(border * 2, border * 2)
        pygame.draw.rect(self.surface, COLORS["board_border"], outer, border_radius=4)

        # Đổ bóng nhẹ (vẽ nhiều rect mờ dần)
        shadow_surf = pygame.Surface(
            (outer.width + 12, outer.height + 12), pygame.SRCALPHA
        )
        for i in range(6):
            alpha = 30 - i * 5
            pygame.draw.rect(
                shadow_surf,
                (0, 0, 0, alpha),
                shadow_surf.get_rect().inflate(-i * 2, -i * 2),
                border_radius=4 + i,
            )
        self.surface.blit(shadow_surf, (outer.x - 6, outer.y - 6))

    def _draw_squares(
        self,
        selected_sq, valid_moves, last_move, in_check_sq
    ) -> None:
        ss = self.square_size
        for row in range(8):
            for col in range(8):
                x, y = self._sq_to_pixel(row, col)
                is_light = (row + col) % 2 == 0
                base_color = COLORS["light_square"] if is_light else COLORS["dark_square"]
                pygame.draw.rect(self.surface, base_color, (x, y, ss, ss))

                # Nước đi cuối
                if last_move and ((row, col) == last_move[0] or (row, col) == last_move[1]):
                    ov = pygame.Surface((ss, ss), pygame.SRCALPHA)
                    c = COLORS["last_move_light"] if is_light else COLORS["last_move_dark"]
                    ov.fill(c)
                    self.surface.blit(ov, (x, y))

                # Ô được chọn
                if selected_sq and (row, col) == selected_sq:
                    ov = pygame.Surface((ss, ss), pygame.SRCALPHA)
                    ov.fill(COLORS["highlight"])
                    self.surface.blit(ov, (x, y))

                # Nước đi hợp lệ
                if valid_moves and (row, col) in valid_moves:
                    self._draw_move_dot(x, y, ss)

                # Vua bị chiếu
                if in_check_sq and (row, col) == in_check_sq:
                    self._draw_check_glow(x, y, ss)

    def _draw_move_dot(self, x: int, y: int, ss: int) -> None:
        dot_surf = pygame.Surface((ss, ss), pygame.SRCALPHA)
        cx, cy = ss // 2, ss // 2
        r = ss // 7
        pygame.draw.circle(dot_surf, COLORS["move_dot"], (cx, cy), r)
        self.surface.blit(dot_surf, (x, y))

    def _draw_check_glow(self, x: int, y: int, ss: int) -> None:
        glow = pygame.Surface((ss, ss), pygame.SRCALPHA)
        for radius in range(ss // 2, 0, -3):
            alpha = max(0, 200 - radius * 6)
            pygame.draw.circle(
                glow, (*COLORS["check"][:3], alpha),
                (ss // 2, ss // 2), radius,
            )
        self.surface.blit(glow, (x, y))

    def _draw_coordinates(self) -> None:
        ss = self.square_size
        padding = 3
        for i in range(8):
            # Số hàng (1–8) – góc trái ô đầu cột
            row = i if not self.flipped else 7 - i
            rank_label = str(8 - row)
            x, y = self._sq_to_pixel(row, 0)
            is_light = (row + 0) % 2 == 0
            color = COLORS["coord_light"] if is_light else COLORS["coord_dark"]
            surf = self._coord_font.render(rank_label, True, color)
            self.surface.blit(surf, (x + padding, y + padding))

            # Chữ cột (a–h) – góc phải ô cuối hàng
            col = i if not self.flipped else 7 - i
            file_label = chr(ord("a") + col)
            x2, y2 = self._sq_to_pixel(7, col)
            is_light2 = (7 + col) % 2 == 0
            color2 = COLORS["coord_light"] if is_light2 else COLORS["coord_dark"]
            surf2 = self._coord_font.render(file_label, True, color2)
            self.surface.blit(
                surf2,
                (x2 + ss - surf2.get_width() - padding, y2 + ss - surf2.get_height() - padding),
            )

    def _draw_pieces(
        self,
        board: List[List[Optional[str]]],
        skip_sq: Optional[Tuple[int, int]] = None,
    ) -> None:
        ss = self.square_size
        for row in range(8):
            for col in range(8):
                if skip_sq and (row, col) == skip_sq:
                    continue
                piece = board[row][col]
                if piece:
                    px, py = self._sq_to_pixel(row, col)
                    self._blit_piece(piece, px, py, ss)

    def _blit_piece(self, piece: str, px: int, py: int, ss: int) -> None:
        if piece not in self._piece_surfaces:
            self._piece_surfaces[piece] = self._render_piece_surface(piece, ss)
        surf = self._piece_surfaces[piece]
        ox = (ss - surf.get_width()) // 2
        oy = (ss - surf.get_height()) // 2
        # Đổ bóng nhẹ
        shadow = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 0))
        for dy in range(1, 4):
            for dx in range(1, 4):
                shadow_char = self._piece_font.render(
                    PIECE_UNICODE.get(piece, "?"), True, (0, 0, 0, 60)
                )
                self.surface.blit(shadow_char, (px + ox + dx, py + oy + dy))
        self.surface.blit(surf, (px + ox, py + oy))

    def _render_piece_surface(self, piece: str, ss: int) -> pygame.Surface:
        char = PIECE_UNICODE.get(piece, "?")
        is_white = piece.startswith("w")
        fg = (255, 252, 240) if is_white else (30, 20, 10)
        outline = (80, 50, 20) if is_white else (230, 210, 180)
        surf = self._piece_font.render(char, True, fg)
        # Outline: render lại offset nhiều hướng
        base = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    o = self._piece_font.render(char, True, outline)
                    base.blit(o, (dx, dy))
        base.blit(surf, (0, 0))
        return base

    def _draw_animated_piece(self) -> None:
        if not self._anim_piece or not self._anim_start or not self._anim_end:
            return
        t = self._ease_in_out(self._anim_t)
        ax = self._anim_start[0] + (self._anim_end[0] - self._anim_start[0]) * t
        ay = self._anim_start[1] + (self._anim_end[1] - self._anim_start[1]) * t
        # Quỹ đạo hơi cong (parabola nhỏ)
        arc = -self.square_size * 0.3 * math.sin(math.pi * self._anim_t)
        ay += arc
        ss = self.square_size
        self._blit_piece(self._anim_piece, int(ax), int(ay - ss * 0.1), ss)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sq_to_pixel(self, row: int, col: int) -> Tuple[int, int]:
        ss = self.square_size
        disp_row = (7 - row) if self.flipped else row
        disp_col = (7 - col) if self.flipped else col
        return (
            self.board_rect.x + disp_col * ss,
            self.board_rect.y + disp_row * ss,
        )

    @staticmethod
    def _ease_in_out(t: float) -> float:
        return t * t * (3 - 2 * t)
