"""Vertical material/evaluation advantage bar."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ui.theme import MONO_FONT, color


class EvaluationBar(QWidget):
    """Shows evaluation in the range -10.00 to +10.00 pawns."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(40)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        self._value = 0.0
        self._black_percent = 0.5

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.value_label = QLabel("+0.00")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"""
            font-family: {MONO_FONT};
            font-size: 9pt;
            font-weight: bold;
            color: {color("text")};
            background-color: {color("panel")};
            border: 1px solid {color("border")};
            border-radius: 3px;
            padding: 2px;
        """)
        layout.addWidget(self.value_label)

        self.bar_widget = _BarWidget(self)
        layout.addWidget(self.bar_widget, 1)

    def set_evaluation(self, value: float):
        self._value = max(-10.0, min(10.0, value))
        self._black_percent = (-self._value + 10.0) / 20.0
        self.value_label.setText(f"{self._value:+.2f}")
        self.bar_widget.update()

    def get_value(self) -> float:
        return self._value


class _BarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        if height <= 0:
            return

        parent = self.parent()
        black_ratio = parent._black_percent if isinstance(parent, EvaluationBar) else 0.5
        black_height = int(height * black_ratio)

        painter.fillRect(0, 0, width, height, QColor(color("panel")))
        if black_height > 0:
            painter.fillRect(0, 0, width, black_height, QColor(color("black_piece")))
        if black_height < height:
            painter.fillRect(
                0,
                black_height,
                width,
                height - black_height,
                QColor(color("white_piece")),
            )

        painter.setPen(QPen(QColor(color("border")), 1))
        painter.drawLine(0, black_height, width, black_height)
        painter.drawRect(0, 0, width - 1, height - 1)
