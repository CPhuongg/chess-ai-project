# Path: ui/components/board_components.py
# Description:
# Custom chess square widget and thinking indicator with Pygame-inspired dark theme.
# ChessSquare uses QPainter for rendering (no complex stylesheets): light/dark squares,
# valid move dots (green), castling indicators (blue), en-passant (orange), check highlight (red pulsing).
# Maintains square aspect ratio via size hints and heightForWidth().
# ThinkingIndicator shows a terminal-style status bar with animated dots while AI computes.

from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QEvent, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QResizeEvent

from utils.config import Config


# ── Palette ────────────────────────────────────────────────────────────────
LIGHT_SQ   = "#F0D9B5"   # Lichess-style light square
DARK_SQ    = "#B58863"   # Lichess-style dark square
HIGHLIGHT  = "#CDD26A"   # Yellow-green: last move / selected
VALID_DOT  = "#769656"   # Dark green dot: legal move
CHECK_RED  = "#FF4444"   # Check border
CASTLE_CLR = "#4EA1D3"   # Castling indicator
EP_CLR     = "#E8A838"   # En-passant indicator
BG_DARK    = "#1E1E1E"   # Application background
PANEL_BG   = "#2A2A2A"   # Sidebar / panel
TEXT_WHITE = "#EFEFEF"
ACCENT     = "#769656"   # Green accent (chess.com-like)
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

        self._base_color = self._calc_base_color()

    # ── helpers ────────────────────────────────────────────────────────────
    def _calc_base_color(self):
        return QColor(LIGHT_SQ) if (self.row + self.col) % 2 == 0 else QColor(DARK_SQ)

    def _square_color(self):
        if self.is_selected:
            return QColor(HIGHLIGHT).lighter(115)
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
            pen = QPen(QColor(CHECK_RED), 3)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(1, 1, W - 2, H - 2)

        # 3. Valid-move indicator — small filled circle
        if self.is_valid_move or self.is_castling_move or self.is_en_passant_move:
            r = min(W, H) * 0.16
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

        painter.end()

        # 4. Let parent draw the piece text/pixmap on top
        super().paintEvent(event)

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
                font-family: 'Courier New', monospace;
                font-size: 12pt;
                font-weight: bold;
                color: #A8D8A8;
                background-color: #1A1A1A;
                border-top: 2px solid #383838;
                padding: 0px 12px;
                letter-spacing: 1px;
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
        self.base_text = f"[ {ai_name} đang tính ]"
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