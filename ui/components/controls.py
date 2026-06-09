"""Reusable controls used by the chess UI."""

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QPushButton,
    QHBoxLayout,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ui.theme import MONO_FONT, button_stylesheet, color, section_label_stylesheet


class ControlButton(QPushButton):
    """Consistent fixed-height button for the game control panels."""

    def __init__(self, text, background=None, icon=None, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(38)
        self.setMinimumWidth(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(button_stylesheet(background or color("button")))

    def sizeHint(self):
        return QSize(max(super().sizeHint().width(), 110), 38)


class UndoButton(ControlButton):
    def __init__(self, parent=None):
        super().__init__("Undo", color("button"), parent=parent)
        self.setToolTip("Undo the last move")


class ResignButton(ControlButton):
    def __init__(self, parent=None):
        super().__init__("Resign", color("danger"), parent=parent)
        self.setToolTip("Resign the current game")


class EnhancedSlider(QWidget):
    """Horizontal slider with a title and min/current/max labels."""

    valueChanged = pyqtSignal(int)

    def __init__(
        self,
        title,
        min_val,
        max_val,
        default_val,
        min_label,
        max_label,
        parent=None,
    ):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(section_label_stylesheet())
        layout.addWidget(title_label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default_val)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: {color("border")};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {color("accent")};
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
                border: 1px solid {color("accent_hover")};
            }}
            QSlider::sub-page:horizontal {{
                background: {color("accent")};
                border-radius: 2px;
            }}
        """)
        self.slider.valueChanged.connect(self._on_change)
        layout.addWidget(self.slider)

        value_row = QHBoxLayout()
        self.min_lbl = QLabel(min_label)
        self.val_lbl = QLabel(str(default_val))
        self.max_lbl = QLabel(max_label)
        for label in (self.min_lbl, self.val_lbl, self.max_lbl):
            label.setStyleSheet(f"""
                font-family: {MONO_FONT};
                font-size: 9pt;
                color: {color("muted")};
            """)
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.max_lbl.setAlignment(Qt.AlignRight)
        value_row.addWidget(self.min_lbl)
        value_row.addWidget(self.val_lbl)
        value_row.addWidget(self.max_lbl)
        layout.addLayout(value_row)

    def _on_change(self, value):
        self.val_lbl.setText(str(value))
        self.valueChanged.emit(value)

    def value(self):
        return self.slider.value()

    def setValue(self, value):
        self.slider.setValue(value)

    def setMinLabel(self, text):
        self.min_lbl.setText(text)

    def setMaxLabel(self, text):
        self.max_lbl.setText(text)

    def setValueLabel(self, text):
        self.val_lbl.setText(text)
