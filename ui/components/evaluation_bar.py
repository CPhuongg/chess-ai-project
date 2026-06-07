"""
Evaluation bar component — Pygame-inspired dark design.
Hiển thị lợi thế của thế cờ dưới dạng thanh dọc.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont

# ── Palette ────────────────────────────────────────────────────────────────
BG_DARK    = "#1A1A1A"
PANEL_BG   = "#242424"
ACCENT_WHITE = "#F0D9B5"   # Màu cho lợi thế Trắng
ACCENT_BLACK = "#B58863"   # Màu cho lợi thế Đen
TEXT_MAIN  = "#EFEFEF"
TEXT_DIM   = "#888888"
_MONO      = "'Courier New', monospace"
# ───────────────────────────────────────────────────────────────────────────


class EvaluationBar(QWidget):
    """
    Thanh dọc hiển thị lợi thế (từ -10 đến +10).
    Giá trị dương = lợi thế cho Trắng, âm = lợi thế cho Đen.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(40)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setMinimumHeight(200)

        self._value = 0.0  # -10..+10
        self._white_percent = 0.5  # 0..1

        # Layout chứa label và thanh vẽ
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Label hiển thị số (cp hoặc pawn)
        self.value_label = QLabel("0.00")
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 9pt;
            font-weight: bold;
            color: {TEXT_MAIN};
            background-color: {BG_DARK};
            border: 1px solid #383838;
            border-radius: 2px;
            padding: 2px;
        """)
        layout.addWidget(self.value_label)

        # Thanh vẽ tay
        self.bar_widget = _BarWidget(self)
        layout.addWidget(self.bar_widget, 1)

        # Khoảng trống bên dưới
        layout.addSpacing(4)

        # Timer để cập nhật mượt (nếu cần)
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)

    def set_evaluation(self, value: float):
        """
        Cập nhật giá trị đánh giá.
        value: centi-pawn (cp) hoặc pawn (ví dụ 1.5 = lợi 1.5 pawn).
        """
        # Giới hạn trong khoảng [-10, 10]
        self._value = max(-10.0, min(10.0, value))
        # Chuyển sang tỷ lệ % cho Trắng (0..1)
        # value = +10 -> 100% trắng, value = -10 -> 0% trắng
        self._white_percent = (self._value + 10.0) / 20.0
        self.value_label.setText(f"{self._value:+.2f}")
        self.bar_widget.update()

    def get_value(self) -> float:
        return self._value


class _BarWidget(QWidget):
    """Widget vẽ thanh ngang (thực chất là dọc) mô phỏng nhiệt độ."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        if h <= 0:
            return

        # Lấy tỷ lệ từ EvaluationBar
        eval_bar = self.parent()
        if isinstance(eval_bar, EvaluationBar):
            white_ratio = eval_bar._white_percent
        else:
            white_ratio = 0.5

        # Chiều cao phần Trắng (từ trên xuống)
        white_height = int(h * white_ratio)

        # Vẽ nền tối
        painter.fillRect(0, 0, w, h, QColor(BG_DARK))

        # Vẽ phần Trắng (phía trên)
        if white_height > 0:
            painter.fillRect(0, 0, w, white_height, QColor(ACCENT_WHITE))
        # Vẽ phần Đen (phía dưới)
        if white_height < h:
            painter.fillRect(0, white_height, w, h - white_height, QColor(ACCENT_BLACK))

        # Vẽ đường kẻ phân cách
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawLine(0, white_height, w, white_height)

        # Vẽ viền
        painter.setPen(QPen(QColor("#383838"), 1))
        painter.drawRect(0, 0, w - 1, h - 1)