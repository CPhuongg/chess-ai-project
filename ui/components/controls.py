# Path: ui/components/controls.py
# Description:
# Pygame-inspired flat UI control buttons and slider components.
# ControlButton: flat button with hover/pressed states, monospace font.
# UndoButton and ResignButton: specialized buttons with preset styling.
# EnhancedSlider: compact vertical slider with min/current/max labels, styled with chess-green accent.
# All components use solid colors (no gradients/shadows) for a clean, retro look.

from PyQt5.QtWidgets import (
    QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont

from utils.config import Config
from ui import theme

# ── Color palette (Pygame-style) ───────────────────────────────────────────
PANEL_BG    = theme.SURFACE
BTN_DEFAULT = theme.SURFACE_2
BTN_HOVER   = theme.SURFACE_3
BTN_PRESSED = theme.APP_BG
BTN_BORDER  = theme.BORDER
TEXT_MAIN   = theme.TEXT
ACCENT_GRN  = theme.ACCENT
ACCENT_RED  = theme.DANGER
ACCENT_BLU  = theme.ACCENT_BLUE
ACCENT_YLW  = theme.WARNING
ACCENT_GRY  = theme.TEXT_DIM
# ───────────────────────────────────────────────────────────────────────────


def _btn_style(bg: str, hover: str = None, pressed: str = None,
               text_color: str = TEXT_MAIN, border: str = BTN_BORDER) -> str:
    if not hover:
        hover = theme.lighten(bg, 112)
    if not pressed:
        pressed = theme.darken(bg, 118)
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {text_color};
            font-family: {theme.FONT_UI};
            font-size: 10pt;
            font-weight: 700;
            padding: 7px 12px;
            border: 1px solid {border};
            border-radius: 6px;
            letter-spacing: 0px;
        }}
        QPushButton:hover {{
            background-color: {hover};
            border-color: {theme.ACCENT};
        }}
        QPushButton:pressed {{
            background-color: {pressed};
        }}
        QPushButton:disabled {{
            background-color: {theme.SURFACE_2};
            color: {theme.TEXT_DIM};
            border-color: {theme.BORDER_SOFT};
        }}
    """


class ControlButton(QPushButton):
    """Flat, monospace-font button. Kiểu toolbar của Pygame game."""

    def __init__(self, text, color, icon=None, parent=None):
        super().__init__(text, parent)
        self.base_color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(38)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(_btn_style(color))

    def sizeHint(self):
        return QSize(max(super().sizeHint().width(), 110), 38)


class UndoButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("↶ Undo", parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(38)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolTip("Undo the last move")
        self.setStyleSheet(_btn_style(BTN_DEFAULT, border="#888888"))

    def sizeHint(self):
        return QSize(110, 38)


class ResignButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__("Resign", parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(38)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setToolTip("Resign the current game")
        self.setStyleSheet(_btn_style(ACCENT_RED))

    def sizeHint(self):
        return QSize(110, 38)


class EnhancedSlider(QWidget):
    """Slider tối giản — label trên, thanh kéo màu xanh lá."""

    valueChanged = pyqtSignal(int)

    def __init__(self, title, min_val, max_val, default_val,
                 min_label, max_label, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        # Title
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet("""
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 9pt;
            font-weight: 700;
            color: #9FB0BF;
            letter-spacing: 0px;
        """)
        layout.addWidget(title_lbl)

        # Slider
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(default_val)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 5px;
                background: #314657;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4FB477;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
                border: 1px solid #3d9a63;
            }
            QSlider::sub-page:horizontal {
                background: #4FB477;
                border-radius: 2px;
            }
        """)
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

        # Min / value / max row
        row = QHBoxLayout()
        self.min_lbl = QLabel(min_label)
        self.val_lbl = QLabel(str(default_val))
        self.max_lbl = QLabel(max_label)
        for lbl in (self.min_lbl, self.val_lbl, self.max_lbl):
            lbl.setStyleSheet("""
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 9pt;
                color: #9FB0BF;
            """)
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.max_lbl.setAlignment(Qt.AlignRight)
        row.addWidget(self.min_lbl)
        row.addWidget(self.val_lbl)
        row.addWidget(self.max_lbl)
        layout.addLayout(row)

    def _on_change(self, v):
        self.val_lbl.setText(str(v))
        self.valueChanged.emit(v)

    def value(self):      return self.slider.value()
    def setValue(self, v): self.slider.setValue(v)
    def setMinLabel(self, t): self.min_lbl.setText(t)
    def setMaxLabel(self, t): self.max_lbl.setText(t)
    def setValueLabel(self, t): self.val_lbl.setText(t)
