"""Board-square and status widgets."""

from PyQt5.QtCore import Qt, QTimer, QSize, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QLabel, QSizePolicy

from ui.theme import MONO_FONT, color


class ChessSquare(QLabel):
    """Single board square painted with lightweight QPainter overlays."""

    clicked = pyqtSignal(int, int)

    def __init__(self, row, col, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(40, 40)

        self.is_highlighted = False
        self.is_last_move = False
        self.is_valid_move = False
        self.is_castling_move = False
        self.is_en_passant_move = False
        self.is_selected = False
        self.is_checked = False
        self._base_color = self._calc_base_color()

    def _calc_base_color(self):
        square = "light_square" if (self.row + self.col) % 2 == 0 else "dark_square"
        return QColor(color(square))

    def _square_color(self):
        if self.is_selected:
            return QColor(color("highlight")).lighter(115)
        if self.is_last_move:
            highlighted = QColor(color("highlight"))
            highlighted.setAlpha(210)
            return highlighted
        return self._base_color

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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width()
        height = self.height()

        background = self._square_color()
        if self.is_highlighted and not self.is_selected and not self.is_last_move:
            background = background.lighter(108)
        painter.fillRect(0, 0, width, height, background)

        if self.is_checked:
            painter.setPen(QPen(QColor(color("check")), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(1, 1, width - 2, height - 2)

        if self.is_valid_move or self.is_castling_move or self.is_en_passant_move:
            radius = min(width, height) * 0.16
            center_x = width / 2
            center_y = height / 2
            dot_color = QColor(color("valid_move"))
            if self.is_castling_move:
                dot_color = QColor(color("castle"))
            elif self.is_en_passant_move:
                dot_color = QColor(color("en_passant"))
            dot_color.setAlpha(190)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(dot_color))
            painter.drawEllipse(
                int(center_x - radius),
                int(center_y - radius),
                int(radius * 2),
                int(radius * 2),
            )

        painter.end()
        super().paintEvent(event)

    def update_appearance(self):
        self._base_color = self._calc_base_color()
        self.setStyleSheet(f"background-color: {self._square_color().name()}; border: none;")
        self.update()

    def sizeHint(self):
        return QSize(64, 64)

    def minimumSizeHint(self):
        return QSize(40, 40)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return width


class ThinkingIndicator(QLabel):
    """Compact status bar used for game state and AI thinking feedback."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(36)
        self.setStyleSheet(f"""
            QLabel {{
                font-family: {MONO_FONT};
                font-size: 11pt;
                font-weight: bold;
                color: {color("accent_hover")};
                background-color: {color("panel")};
                border-top: 1px solid {color("border")};
                padding: 0 12px;
            }}
        """)

        self.dots = 0
        self.base_text = ""
        self._dot_timer = QTimer(self)
        self._dot_timer.timeout.connect(self._tick_dots)
        self.hide()

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
        self.setText(message)
        self.show()

    def _tick_dots(self):
        self.dots = (self.dots + 1) % 4
        self._update_text()

    def _update_text(self):
        dot_text = "." * self.dots + "   "[self.dots:]
        self.setText(f"{self.base_text}{dot_text}")
