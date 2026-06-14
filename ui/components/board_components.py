# Path: ui/components/board_components.py
# Description:
# Custom chess square widget and thinking indicator with Pygame-inspired dark theme.
# ChessSquare uses QPainter for rendering (no complex stylesheets): light/dark squares,
# valid move dots (green), castling indicators (blue), en-passant (orange), check highlight (red pulsing).
# Maintains square aspect ratio via size hints and heightForWidth().
# ThinkingIndicator shows a terminal-style status bar with animated dots while AI computes.

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QEvent, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QResizeEvent

from utils.config import Config
from ui import theme


# ── Palette ────────────────────────────────────────────────────────────────
LIGHT_SQ   = theme.BOARD_LIGHT
DARK_SQ    = theme.BOARD_DARK
HIGHLIGHT  = theme.BOARD_LAST_MOVE
VALID_DOT  = theme.VALID_MOVE
CHECK_RED  = theme.CHECK
CASTLE_CLR = theme.ACCENT_BLUE
EP_CLR     = theme.WARNING
BG_DARK    = theme.APP_BG
PANEL_BG   = theme.SURFACE
TEXT_WHITE = theme.TEXT
ACCENT     = theme.ACCENT
# ───────────────────────────────────────────────────────────────────────────


class ChessSquare(QLabel):
    """
    Một ô cờ — vẽ hoàn toàn bằng QPainter, không dùng stylesheet phức tạp.
    Phong cách: flat, gọn gàng như Pygame surface.
    """

    clicked = pyqtSignal(int, int)

    def __init__(self, row, col, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(40, 40)

        # State flags
        self.is_highlighted    = False
        self.is_last_move      = False
        self.is_valid_move     = False
        self.is_castling_move  = False
        self.is_en_passant_move = False
        self.is_selected       = False
        self.is_checked        = False
        self.piece_color       = None

        self._base_color = self._calc_base_color()

    # ── helpers ────────────────────────────────────────────────────────────
    def _calc_base_color(self):
        return QColor(LIGHT_SQ) if (self.row + self.col) % 2 == 0 else QColor(DARK_SQ)

    def _square_color(self):
        if self.is_selected:
            return QColor(theme.BOARD_SELECTED).lighter(110)
        if self.is_last_move:
            c = QColor(HIGHLIGHT)
            c.setAlpha(200)
            return c
        return self._base_color

    # ── events ─────────────────────────────────────────────────────────────
    def enterEvent(self, event):
        self.is_highlighted = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_highlighted = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)

    # ── painting ───────────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # 1. Base square color
        bg = self._square_color()
        if self.is_highlighted and not self.is_selected and not self.is_last_move:
            bg = bg.lighter(108)
        painter.fillRect(0, 0, W, H, bg)

        # 2. Check border (pulsing red outline)
        if self.is_checked:
            pen = QPen(QColor(CHECK_RED), 4)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(1, 1, W - 2, H - 2)

        # 3. Valid-move indicator — small filled circle
        if self.is_valid_move or self.is_castling_move or self.is_en_passant_move:
            r = min(W, H) * 0.15
            cx, cy = W / 2, H / 2
            if self.is_castling_move:
                dot_color = QColor(CASTLE_CLR)
            elif self.is_en_passant_move:
                dot_color = QColor(EP_CLR)
            else:
                dot_color = QColor(VALID_DOT)
            dot_color.setAlpha(190)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(
                int(cx - r), int(cy - r), int(r * 2), int(r * 2)
            )

        # 4. Draw piece text with an outline so white pieces remain visible on light squares.
        piece_text = self.text()
        if piece_text:
            font = QFont("Segoe UI Symbol")
            font.setPixelSize(max(28, int(min(W, H) * 0.70)))
            font.setWeight(QFont.Black)
            painter.setFont(font)

            fill = QColor(self.piece_color or theme.TEXT)
            outline = QColor(theme.BLACK_PIECE if fill.lightness() > 150 else theme.WHITE_PIECE)
            outline.setAlpha(210)

            rect = QRect(0, 0, W, H)
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2),
                           (-1, -1), (1, -1), (-1, 1), (1, 1)):
                painter.setPen(outline)
                painter.drawText(rect.adjusted(dx, dy, dx, dy), Qt.AlignCenter, piece_text)

            painter.setPen(fill)
            painter.drawText(rect, Qt.AlignCenter, piece_text)

        painter.end()

    def update_appearance(self):
        """Refresh sau khi state thay đổi."""
        self._base_color = self._calc_base_color()

        # Sync stylesheet color for piece text contrast
        bg = self._square_color()
        self.setStyleSheet(
            f"background-color: {bg.name()}; border: none;"
        )
        self.update()

    # ── size hints ─────────────────────────────────────────────────────────
    def sizeHint(self):          return QSize(64, 64)
    def minimumSizeHint(self):   return QSize(40, 40)
    def hasHeightForWidth(self): return True
    def heightForWidth(self, w): return w


class ThinkingIndicator(QLabel):
    """
    Status bar kiểu terminal — hiển thị trạng thái game / AI đang tính.
    Nền tối, chữ xanh lá, font monospace — giống terminal Pygame overlay.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(36)

        self._base_style = """
            QLabel {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 11pt;
                font-weight: 700;
                color: #F4F7FA;
                background-color: #17212B;
                border: 1px solid #314657;
                border-radius: 8px;
                padding: 0px 14px;
                letter-spacing: 0px;
            }
        """
        self.setStyleSheet(self._base_style)

        self.dots     = 0
        self.base_text = ""

        self._dot_timer  = QTimer(self)
        self._dot_timer.timeout.connect(self._tick_dots)

        self.hide()

    # ── public API ─────────────────────────────────────────────────────────
    def start_thinking(self, ai_name: str):
        self.base_text = f"{ai_name} is thinking"
        self.dots = 0
        self._update_text()
        self.show()
        self._dot_timer.start(400)

    def stop_thinking(self):
        self._dot_timer.stop()
        self.hide()

    def show_status(self, message: str):
        self._dot_timer.stop()
        self.setText(f"  {message}")
        self.show()

    # ── internals ──────────────────────────────────────────────────────────
    def _tick_dots(self):
        self.dots = (self.dots + 1) % 4
        self._update_text()

    def _update_text(self):
        dot_str = "." * self.dots + "   "[self.dots:]
        self.setText(f"  {self.base_text}{dot_str}")
