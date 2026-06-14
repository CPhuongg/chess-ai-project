"""Evaluation bar showing which side is better."""

from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QPen

from ui import theme


BG_DARK = theme.APP_BG
BAR_WHITE = "#F7F0DE"
BAR_BLACK = "#080D12"
TEXT_MAIN = theme.TEXT
TEXT_DIM = theme.TEXT_MUTED
ZERO_LINE = theme.ACCENT
MARKER_LINE = theme.WARNING
MONO = theme.FONT_MONO


class EvaluationBar(QWidget):
    """Vertical evaluation bar. Positive values favor White, negative values favor Black."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(74)
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self._value = 0.0
        self._black_percent = 0.5

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.black_label = QLabel("BLACK")
        self.black_label.setAlignment(Qt.AlignCenter)
        self.black_label.setStyleSheet(self._side_label_style())
        layout.addWidget(self.black_label)

        self.value_label = QLabel("EVEN")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"""
            font-family: {MONO};
            font-size: 8pt;
            font-weight: 800;
            color: {TEXT_MAIN};
            background-color: {BG_DARK};
            border: 1px solid {theme.BORDER};
            border-radius: 6px;
            padding: 4px 2px;
        """)
        layout.addWidget(self.value_label)

        self.bar_widget = _BarWidget(self)
        layout.addWidget(self.bar_widget, 1)

        self.white_label = QLabel("WHITE")
        self.white_label.setAlignment(Qt.AlignCenter)
        self.white_label.setStyleSheet(self._side_label_style())
        layout.addWidget(self.white_label)

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)

    def set_evaluation(self, value: float):
        self._value = max(-10.0, min(10.0, value))
        self._black_percent = (-self._value + 10.0) / 20.0

        abs_value = abs(self._value)
        if abs_value < 0.05:
            self.value_label.setText("EVEN")
        elif self._value > 0:
            self.value_label.setText(f"W +{abs_value:.1f}")
        else:
            self.value_label.setText(f"B +{abs_value:.1f}")

        self.bar_widget.update()

    def get_value(self) -> float:
        return self._value

    @staticmethod
    def _side_label_style() -> str:
        return f"""
            font-family: {theme.FONT_UI};
            font-size: 7.5pt;
            font-weight: 800;
            color: {TEXT_DIM};
            background: transparent;
            border: none;
        """


class _BarWidget(QWidget):
    """Paints black advantage at the top and white advantage at the bottom."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        if h <= 0 or w <= 0:
            return

        eval_bar = self.parent()
        if isinstance(eval_bar, EvaluationBar):
            black_ratio = eval_bar._black_percent
            value = eval_bar._value
        else:
            black_ratio = 0.5
            value = 0.0

        black_height = int(h * black_ratio)
        outer = QRectF(0.5, 0.5, w - 1, h - 1)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(BG_DARK))
        painter.drawRoundedRect(outer, 7, 7)

        if black_height > 1:
            painter.fillRect(1, 1, w - 2, black_height - 1, QColor(BAR_BLACK))
        if black_height < h - 1:
            painter.fillRect(1, black_height, w - 2, h - black_height - 1, QColor(BAR_WHITE))

        center_y = h // 2
        painter.setPen(QPen(QColor(ZERO_LINE), 2))
        painter.drawLine(4, center_y, w - 5, center_y)

        marker_y = max(3, min(h - 4, black_height))
        painter.setPen(QPen(QColor(MARKER_LINE), 2))
        painter.drawLine(3, marker_y, w - 4, marker_y)

        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QPen(QColor(theme.BORDER), 1))
        painter.drawLine(w - 16, center_y, w - 5, center_y)
        painter.setPen(QColor(ZERO_LINE))
        painter.drawText(5, center_y - 8, 26, 16, Qt.AlignLeft | Qt.AlignVCenter, "0")

        if abs(value) >= 0.05:
            pointer_text = "W" if value > 0 else "B"
            text_y = max(3, min(h - 19, marker_y - 8))
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            painter.setPen(QColor(theme.APP_BG if value > 0 else theme.TEXT))
            painter.drawText(w - 22, text_y, 18, 16, Qt.AlignCenter, pointer_text)

        painter.setPen(QPen(QColor(theme.BORDER), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(outer, 7, 7)
