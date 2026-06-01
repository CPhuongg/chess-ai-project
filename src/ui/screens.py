"""
ui/screens.py
Tất cả các màn hình (Screen) của game cờ vua:
  - MenuScreen    : Màn hình chính
  - GameScreen    : Màn hình gameplay
  - GameOverScreen: Kết quả ván đấu
  - PauseScreen   : Tạm dừng
  - SettingsScreen: Cài đặt
"""

import pygame
from typing import Callable, Optional, Dict, Any, List, Tuple

from .renderer import ChessRenderer
from .components import Button, Label, Panel, MoveHistory

# ── Hằng số giao diện ────────────────────────────────────────────────────────
C = {
    "bg":         ( 18,  12,   6),
    "gold":       (180, 140,  60),
    "gold_light": (237, 200, 110),
    "cream":      (237, 220, 192),
    "brown_dark": ( 44,  27,   6),
    "brown_mid":  ( 72,  50,  20),
    "brown_light":( 120, 85,  35),
    "white_piece":(255, 252, 240),
    "black_piece":( 30,  20,  10),
    "danger":     (200,  60,  60),
    "success":    ( 80, 160,  80),
}


def _make_font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


# ══════════════════════════════════════════════════════════════════════════════
#  BaseScreen
# ══════════════════════════════════════════════════════════════════════════════

class BaseScreen:
    """Lớp cơ sở chung cho mọi màn hình."""

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.W, self.H = surface.get_size()
        self._buttons: List[Button] = []
        self._next_screen: Optional[str] = None
        self._next_data: Dict[str, Any] = {}

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self._buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        pass

    def draw(self) -> None:
        raise NotImplementedError

    def get_next(self) -> Optional[Tuple[str, Dict[str, Any]]]:
        if self._next_screen:
            result = (self._next_screen, self._next_data)
            self._next_screen = None
            self._next_data = {}
            return result
        return None

    def _go_to(self, screen_name: str, **kwargs: Any) -> None:
        self._next_screen = screen_name
        self._next_data = kwargs

    def _draw_bg(self, pattern: bool = True) -> None:
        """Vẽ nền tối với họa tiết bàn cờ mờ."""
        self.surface.fill(C["bg"])
        if pattern:
            cell = 48
            alpha = 12
            for row in range(self.H // cell + 1):
                for col in range(self.W // cell + 1):
                    if (row + col) % 2 == 0:
                        r = pygame.Rect(col * cell, row * cell, cell, cell)
                        s = pygame.Surface((cell, cell), pygame.SRCALPHA)
                        s.fill((255, 255, 255, alpha))
                        self.surface.blit(s, r)

    def _draw_title(
        self, text: str, y: int, size: int = 64, color=None
    ) -> None:
        color = color or C["gold_light"]
        font = _make_font("Georgia", size, bold=True)
        surf = font.render(text, True, color)
        # Bóng chữ
        shadow = font.render(text, True, (0, 0, 0))
        self.surface.blit(shadow, (self.W // 2 - surf.get_width() // 2 + 3, y + 3))
        self.surface.blit(surf, (self.W // 2 - surf.get_width() // 2, y))

    def _draw_divider(self, y: int, width: int = 300) -> None:
        x = self.W // 2 - width // 2
        pygame.draw.line(self.surface, C["gold"], (x, y), (x + width, y), 1)
        # Diamante central
        pygame.draw.polygon(
            self.surface, C["gold"],
            [(self.W // 2, y - 4), (self.W // 2 + 4, y),
             (self.W // 2, y + 4), (self.W // 2 - 4, y)],
        )


# ══════════════════════════════════════════════════════════════════════════════
#  MenuScreen
# ══════════════════════════════════════════════════════════════════════════════

class MenuScreen(BaseScreen):
    """
    Màn hình chính với các nút: Chơi, Cài đặt, Thoát.
    """

    LOGO = "♛  CỜ VUA  ♟"

    def __init__(self, surface: pygame.Surface) -> None:
        super().__init__(surface)
        self._build_buttons()
        self._tick = 0.0   # dùng cho animation logo

    def _build_buttons(self) -> None:
        cx = self.W // 2
        btn_w, btn_h = 240, 52
        spacing = 18
        start_y = self.H // 2 + 20

        btn_defs = [
            ("Chơi với bạn bè",  lambda: self._go_to("game", mode="pvp")),
            ("Chơi với máy",     lambda: self._go_to("game", mode="ai")),
            ("Cài đặt",          lambda: self._go_to("settings")),
            ("Thoát",            lambda: self._go_to("quit")),
        ]

        for i, (txt, cb) in enumerate(btn_defs):
            y = start_y + i * (btn_h + spacing)
            btn = Button(
                rect=pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h),
                text=txt,
                on_click=cb,
                color=C["brown_mid"],
                hover_color=C["brown_light"],
                border_radius=10,
            )
            self._buttons.append(btn)

    def update(self, dt: float) -> None:
        self._tick += dt

    def draw(self) -> None:
        self._draw_bg()

        # Logo cờ vua nổi bật
        import math
        float_y = int(math.sin(self._tick * 1.5) * 5)
        self._draw_title(self.LOGO, self.H // 4 + float_y, size=62)

        # Phụ đề
        sub_font = _make_font("Georgia", 18)
        sub = sub_font.render("— Enjoy the Classic Game of Kings —", True, C["gold"])
        self.surface.blit(
            sub, (self.W // 2 - sub.get_width() // 2, self.H // 4 + 80 + float_y)
        )

        self._draw_divider(self.H // 2 + 8)

        for btn in self._buttons:
            btn.draw(self.surface)

        # Footer
        ft_font = _make_font("Georgia", 12)
        ft = ft_font.render("v1.0  ·  Chess Engine Python", True, C["brown_light"])
        self.surface.blit(ft, (self.W // 2 - ft.get_width() // 2, self.H - 26))


# ══════════════════════════════════════════════════════════════════════════════
#  GameScreen
# ══════════════════════════════════════════════════════════════════════════════

class GameScreen(BaseScreen):
    """
    Màn hình gameplay: bàn cờ + sidebar (thông tin, lịch sử nước đi, nút).

    Parameters
    ----------
    mode        : "pvp" | "ai"
    game_state  : object cung cấp .board, .current_turn, v.v. (inject từ ngoài)
    """

    SIDEBAR_W = 260

    def __init__(
        self,
        surface: pygame.Surface,
        mode: str = "pvp",
        game_state: Optional[Any] = None,
    ) -> None:
        super().__init__(surface)
        self.mode = mode
        self.game_state = game_state

        # Tính toán vùng bàn cờ (vuông, căn trái)
        board_size = min(self.H - 40, self.W - self.SIDEBAR_W - 40)
        board_x = 20
        board_y = (self.H - board_size) // 2
        self.board_rect = pygame.Rect(board_x, board_y, board_size, board_size)

        self.renderer = ChessRenderer(surface, self.board_rect)

        # Sidebar
        sb_x = self.board_rect.right + 16
        self.sidebar_rect = pygame.Rect(sb_x, 20, self.SIDEBAR_W, self.H - 40)
        self.sidebar_panel = Panel(self.sidebar_rect, title="Thông tin ván đấu")

        # Lịch sử nước đi
        hist_rect = pygame.Rect(
            sb_x + 8, self.H // 2 - 20, self.SIDEBAR_W - 16, self.H // 2 - 30
        )
        self.move_history = MoveHistory(hist_rect, max_visible=12)

        # Nút trong sidebar
        self._build_sidebar_buttons(sb_x)

        # Trạng thái UI
        self._selected_sq: Optional[Tuple[int, int]] = None
        self._valid_moves: List[Tuple[int, int]] = []
        self._last_move: Optional[Any] = None
        self._in_check_sq: Optional[Tuple[int, int]] = None
        self._promotion_dialog: Optional[Any] = None
        self._clock_white = 0.0
        self._clock_black = 0.0

    def _build_sidebar_buttons(self, sb_x: int) -> None:
        btn_w = self.SIDEBAR_W - 24
        btn_h = 38
        gap = 10
        btn_y = 90

        defs = [
            ("⟳  Chơi lại",    lambda: self._go_to("game", mode=self.mode)),
            ("⏸  Tạm dừng",    lambda: self._go_to("pause")),
            ("⬡  Menu chính",  lambda: self._go_to("menu")),
        ]
        for txt, cb in defs:
            self._buttons.append(
                Button(
                    pygame.Rect(sb_x + 12, btn_y, btn_w, btn_h),
                    txt, cb,
                    color=C["brown_mid"], hover_color=C["brown_light"],
                    border_radius=8,
                )
            )
            btn_y += btn_h + gap

    def handle_event(self, event: pygame.event.Event) -> None:
        super().handle_event(event)

        # Click bàn cờ
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            sq = self.renderer.pixel_to_square(*event.pos)
            if sq:
                self._on_square_clicked(sq)

        # Scroll lịch sử
        self.move_history.handle_event(event)

        # Hộp thoại phong cấp
        if self._promotion_dialog:
            self._promotion_dialog.handle_event(event)

    def update(self, dt: float) -> None:
        self.renderer.update_animation()
        # Cập nhật đồng hồ (nếu game_state cung cấp)
        if self.game_state:
            turn = getattr(self.game_state, "current_turn", "white")
            if turn == "white":
                self._clock_white += dt
            else:
                self._clock_black += dt

    def draw(self) -> None:
        self._draw_bg(pattern=False)
        self.surface.fill(C["bg"])

        # Sidebar
        self.sidebar_panel.draw(self.surface)
        self._draw_clocks()
        self._draw_captured_pieces()

        # Bàn cờ
        board = self._get_board()
        self.renderer.draw(
            board,
            selected_sq=self._selected_sq,
            valid_moves=self._valid_moves,
            last_move=self._last_move,
            in_check_sq=self._in_check_sq,
        )

        # Lịch sử
        self.move_history.draw(self.surface)

        # Các nút
        for btn in self._buttons:
            btn.draw(self.surface)

        # Hộp thoại phong cấp (vẽ trên cùng)
        if self._promotion_dialog:
            self._promotion_dialog.draw(self.surface)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _on_square_clicked(self, sq: Tuple[int, int]) -> None:
        """
        Logic click ô cờ: chọn quân / thực hiện nước đi.
        Kết nối với game logic bên ngoài qua game_state.
        """
        if self.game_state is None:
            # Demo: chỉ highlight ô được click
            self._selected_sq = sq
            return

        if self._selected_sq is None:
            # Chọn quân
            piece = self.game_state.board[sq[0]][sq[1]]
            if piece and self.game_state.is_own_piece(piece):
                self._selected_sq = sq
                self._valid_moves = self.game_state.get_valid_moves(sq)
        else:
            if sq in self._valid_moves:
                # Thực hiện nước đi
                self.game_state.make_move(self._selected_sq, sq)
                self._last_move = (self._selected_sq, sq)
            self._selected_sq = None
            self._valid_moves = []

    def _get_board(self) -> List[List[Optional[str]]]:
        """Lấy bàn cờ từ game_state hoặc trả về bàn trống để demo."""
        if self.game_state:
            return self.game_state.board
        # Bàn cờ demo (vị trí ban đầu)
        return _default_board()

    def _draw_clocks(self) -> None:
        font = _make_font("Consolas", 26, bold=True)
        sb = self.sidebar_rect
        # Đồng hồ Đen (trên)
        t_b = int(self._clock_black)
        s_b = f"♟  {t_b // 60:02d}:{t_b % 60:02d}"
        surf_b = font.render(s_b, True, C["cream"])
        self.surface.blit(surf_b, (sb.x + 12, sb.y + 45))
        # Đồng hồ Trắng (dưới)
        t_w = int(self._clock_white)
        s_w = f"♙  {t_w // 60:02d}:{t_w % 60:02d}"
        surf_w = font.render(s_w, True, C["gold_light"])
        self.surface.blit(surf_w, (sb.x + 12, sb.y + 72))

    def _draw_captured_pieces(self) -> None:
        pass   # Mở rộng sau khi tích hợp game logic


# ══════════════════════════════════════════════════════════════════════════════
#  GameOverScreen
# ══════════════════════════════════════════════════════════════════════════════

class GameOverScreen(BaseScreen):
    """
    Màn hình kết thúc ván đấu.

    Parameters
    ----------
    winner  : "white" | "black" | "draw"
    reason  : lý do kết thúc (checkmate, stalemate, resignation…)
    """

    WINNER_TEXT = {
        "white": ("Trắng chiến thắng!", C["gold_light"]),
        "black": ("Đen chiến thắng!", C["cream"]),
        "draw":  ("Hoà cờ!",          C["gold"]),
    }

    def __init__(
        self,
        surface: pygame.Surface,
        winner: str = "white",
        reason: str = "Chiếu hết",
    ) -> None:
        super().__init__(surface)
        self.winner = winner
        self.reason = reason
        self._build_buttons()

    def _build_buttons(self) -> None:
        cx = self.W // 2
        btn_w, btn_h = 220, 50
        y0 = self.H // 2 + 80
        self._buttons = [
            Button(
                pygame.Rect(cx - btn_w // 2, y0, btn_w, btn_h),
                "Chơi lại", lambda: self._go_to("game"),
                color=C["brown_mid"], hover_color=C["brown_light"],
            ),
            Button(
                pygame.Rect(cx - btn_w // 2, y0 + 68, btn_w, btn_h),
                "Menu chính", lambda: self._go_to("menu"),
                color=C["brown_dark"], hover_color=C["brown_mid"],
            ),
        ]

    def draw(self) -> None:
        self._draw_bg()
        # Overlay mờ
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        self.surface.blit(ov, (0, 0))

        # Card kết quả
        card_w, card_h = 420, 320
        card = pygame.Rect(
            self.W // 2 - card_w // 2,
            self.H // 2 - card_h // 2 - 40,
            card_w, card_h,
        )
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        pygame.draw.rect(
            card_surf, (28, 20, 10, 230), card_surf.get_rect(), border_radius=16
        )
        self.surface.blit(card_surf, card.topleft)
        pygame.draw.rect(self.surface, C["gold"], card, width=2, border_radius=16)

        txt, color = self.WINNER_TEXT.get(self.winner, ("Kết thúc", C["cream"]))
        self._draw_title(txt, card.y + 30, size=42, color=color)

        reason_font = _make_font("Georgia", 22)
        r_surf = reason_font.render(self.reason, True, C["cream"])
        self.surface.blit(
            r_surf, (self.W // 2 - r_surf.get_width() // 2, card.y + 100)
        )

        self._draw_divider(card.y + 140, width=200)

        trophy_font = _make_font("Segoe UI Symbol", 70)
        trophy = "♛" if self.winner != "draw" else "♞"
        t_surf = trophy_font.render(trophy, True, color)
        self.surface.blit(
            t_surf, (self.W // 2 - t_surf.get_width() // 2, card.y + 155)
        )

        for btn in self._buttons:
            btn.draw(self.surface)


# ══════════════════════════════════════════════════════════════════════════════
#  PauseScreen
# ══════════════════════════════════════════════════════════════════════════════

class PauseScreen(BaseScreen):
    """Màn hình tạm dừng, hiển thị lên trên game đang chơi."""

    def __init__(self, surface: pygame.Surface) -> None:
        super().__init__(surface)
        cx, cy = self.W // 2, self.H // 2
        btn_w, btn_h = 200, 46

        self._buttons = [
            Button(
                pygame.Rect(cx - btn_w // 2, cy - 20, btn_w, btn_h),
                "Tiếp tục", lambda: self._go_to("resume"),
                color=C["brown_mid"], hover_color=C["brown_light"],
            ),
            Button(
                pygame.Rect(cx - btn_w // 2, cy + 46, btn_w, btn_h),
                "Menu chính", lambda: self._go_to("menu"),
                color=C["brown_dark"], hover_color=C["brown_mid"],
            ),
        ]

    def draw(self) -> None:
        # Không xóa màn hình – vẽ đè lên GameScreen
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        self.surface.blit(ov, (0, 0))

        self._draw_title("TẠM DỪNG", self.H // 2 - 100, size=52)
        self._draw_divider(self.H // 2 - 35, width=180)

        for btn in self._buttons:
            btn.draw(self.surface)


# ══════════════════════════════════════════════════════════════════════════════
#  SettingsScreen
# ══════════════════════════════════════════════════════════════════════════════

class SettingsScreen(BaseScreen):
    """
    Màn hình cài đặt: âm thanh, lật bàn cờ, chủ đề màu, độ khó AI.
    """

    def __init__(self, surface: pygame.Surface) -> None:
        super().__init__(surface)
        self.settings: Dict[str, Any] = {
            "sound":       True,
            "flip_board":  False,
            "ai_level":    2,      # 1-5
            "show_hints":  True,
            "theme":       "classic",
        }
        self._build_ui()

    def _build_ui(self) -> None:
        cx = self.W // 2
        btn_w, btn_h = 200, 44
        y = self.H // 2 - 80

        toggle_defs = [
            ("Âm thanh",       "sound"),
            ("Lật bàn cờ",     "flip_board"),
            ("Hiển thị gợi ý", "show_hints"),
        ]
        for label, key in toggle_defs:
            k = key   # closure capture
            self._buttons.append(
                Button(
                    pygame.Rect(cx - btn_w // 2, y, btn_w, btn_h),
                    f"{label}: {'BẬT' if self.settings[k] else 'TẮT'}",
                    on_click=lambda _k=k: self._toggle(_k),
                    color=C["brown_mid"], hover_color=C["brown_light"],
                    border_radius=8,
                )
            )
            y += btn_h + 14

        # Nút quay lại
        self._buttons.append(
            Button(
                pygame.Rect(cx - btn_w // 2, y + 20, btn_w, btn_h),
                "← Quay lại", lambda: self._go_to("menu"),
                color=C["brown_dark"], hover_color=C["brown_mid"],
            )
        )

    def _toggle(self, key: str) -> None:
        self.settings[key] = not self.settings[key]
        # Cập nhật nhãn nút
        labels = {"sound": "Âm thanh", "flip_board": "Lật bàn cờ", "show_hints": "Hiển thị gợi ý"}
        keys = ["sound", "flip_board", "show_hints"]
        for i, k in enumerate(keys):
            val = "BẬT" if self.settings[k] else "TẮT"
            self._buttons[i].set_text(f"{labels[k]}: {val}")

    def draw(self) -> None:
        self._draw_bg()
        self._draw_title("CÀI ĐẶT", self.H // 6, size=48)
        self._draw_divider(self.H // 6 + 70, width=200)

        # Độ khó AI
        ai_font = _make_font("Georgia", 18)
        ai_txt = ai_font.render(
            f"Độ khó AI: {'★' * self.settings['ai_level']}{'☆' * (5 - self.settings['ai_level'])}",
            True, C["gold"],
        )
        self.surface.blit(
            ai_txt, (self.W // 2 - ai_txt.get_width() // 2, self.H // 2 + 80)
        )

        for btn in self._buttons:
            btn.draw(self.surface)


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _default_board() -> List[List[Optional[str]]]:
    """Bàn cờ ban đầu theo chuẩn cờ vua (dùng để demo khi chưa có game_state)."""
    b: List[List[Optional[str]]] = [[None] * 8 for _ in range(8)]
    back = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    for c, p in enumerate(back):
        b[0][c] = "b" + p
        b[7][c] = "w" + p
    for c in range(8):
        b[1][c] = "bP"
        b[6][c] = "wP"
    return b