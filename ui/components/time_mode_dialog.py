# Path: ui/components/time_mode_dialog.py
# Description:
# Frameless dialog for selecting time control mode.
# Options: "No time limit" or "Time control (Fischer/Blitz)".
# Provides quick presets (1/3/5/10/15 minutes) and custom minute/second input.
# Supports Fischer increment (seconds added per move, default 3s).
# Returns tuple: (enabled, white_time_ms, black_time_ms, white_increment_ms, black_increment_ms).

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QRadioButton, QButtonGroup, QFrame,
    QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from ui import theme

# ── Palette ────────────────────────────────────────────────────────────────
BG_DARK    = theme.APP_BG
PANEL_BG   = theme.SURFACE
PANEL2     = theme.SURFACE_2
BORDER_CLR = theme.BORDER
ACCENT_GRN = theme.ACCENT
ACCENT_RED = theme.DANGER
TEXT_MAIN  = theme.TEXT
TEXT_DIM   = theme.TEXT_MUTED
INPUT_BG   = theme.SURFACE_2
_MONO      = theme.FONT_UI
# ───────────────────────────────────────────────────────────────────────────


def _label(text, dim=False, size=10):
    lbl = QLabel(text)
    color = TEXT_DIM if dim else TEXT_MAIN
    lbl.setStyleSheet(f"""
        font-family: {_MONO};
        font-size: {size}pt;
        color: {color};
        background: transparent;
        border: none;
    """)
    return lbl


def _spinbox(min_v, max_v, default, suffix=""):
    sb = QSpinBox()
    sb.setRange(min_v, max_v)
    sb.setValue(default)
    if suffix:
        sb.setSuffix(f" {suffix}")
    sb.setFixedHeight(38)
    sb.setFixedWidth(158)
    sb.setStyleSheet(f"""
        QSpinBox {{
            font-family: {_MONO};
            font-size: 11pt;
            font-weight: 700;
            color: {TEXT_MAIN};
            background-color: {INPUT_BG};
            border: 1px solid {BORDER_CLR};
            border-radius: 6px;
            padding: 4px 32px 4px 10px;
        }}
        QSpinBox:focus {{
            border-color: {ACCENT_GRN};
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            width: 22px;
            background-color: {theme.SURFACE_3};
            border-left: 1px solid {BORDER_CLR};
        }}
        QSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            border-top-right-radius: 6px;
            border-bottom: 1px solid {BORDER_CLR};
        }}
        QSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            border-bottom-right-radius: 6px;
        }}
    """)
    return sb


def _preset_btn(text, parent_dialog, ms):
    btn = QPushButton(text)
    btn.setFixedHeight(34)
    btn.setMinimumWidth(76)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setStyleSheet(f"""
        QPushButton {{
            font-family: {_MONO};
            font-size: 10pt;
            font-weight: 700;
            color: {TEXT_DIM};
            background-color: {INPUT_BG};
            border: 1px solid {BORDER_CLR};
            border-radius: 6px;
            padding: 4px 10px;
        }}
        QPushButton:hover {{
            color: {TEXT_MAIN};
            border-color: {ACCENT_GRN};
            background-color: {theme.SURFACE_3};
        }}
    """)
    btn.clicked.connect(lambda: parent_dialog._set_preset(ms))
    return btn


class TimeModeDialog(QDialog):
    """Dialog chọn chế độ thời gian — compact, dark, monospace."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Time Control")
        self.setModal(True)
        self.setFixedSize(700, 640)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet(f"background-color: {PANEL_BG};")

        self._drag_pos = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Title bar ──────────────────────────────────────────────────────
        title_bar = QFrame()
        title_bar.setObjectName("timeTitleBar")
        title_bar.setFixedHeight(44)
        title_bar.setStyleSheet(f"""
            #timeTitleBar {{
                background-color: {BG_DARK};
                border-bottom: 1px solid {ACCENT_GRN};
            }}
        """)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(20, 0, 18, 0)
        lbl = QLabel("  TIME CONTROL")
        lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 12pt;
            font-weight: 800;
            color: {ACCENT_GRN};
            letter-spacing: 0px;
            background: transparent;
            border: none;
        """)
        tb_layout.addWidget(lbl)
        tb_layout.addStretch()
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: none;
                font-size: 12pt;
            }}
            QPushButton:hover {{ color: {TEXT_MAIN}; }}
        """)
        close_btn.clicked.connect(self.reject)
        tb_layout.addWidget(close_btn)
        outer.addWidget(title_bar)

        # ── Content ────────────────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background-color: {PANEL_BG};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(26, 20, 26, 18)
        cl.setSpacing(14)

        # Mode select
        mode_sec = QLabel("MODE")
        mode_sec.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 9pt;
            color: {TEXT_DIM};
            letter-spacing: 0px;
            background: transparent;
            border: none;
        """)
        cl.addWidget(mode_sec)

        self._mode_grp = QButtonGroup(self)

        def _radio(text, btn_id):
            rb = QRadioButton(text)
            rb.setStyleSheet(f"""
                QRadioButton {{
                    font-family: {_MONO};
                    font-size: 13pt;
                    color: {TEXT_MAIN};
                    spacing: 8px;
                    background: transparent;
                }}
                QRadioButton::indicator {{
                    width: 14px; height: 14px;
                }}
                QRadioButton::indicator:unchecked {{
                    border: 1px solid {TEXT_DIM};
                    border-radius: 7px;
                    background: {INPUT_BG};
                }}
                QRadioButton::indicator:checked {{
                    border: 1px solid {ACCENT_GRN};
                    border-radius: 7px;
                    background: {ACCENT_GRN};
                }}
            """)
            self._mode_grp.addButton(rb, btn_id)
            return rb

        self._no_time = _radio("No time limit", 0)
        self._no_time.setChecked(True)
        self._timed   = _radio("Time control (Fischer / Blitz)", 1)
        cl.addWidget(self._no_time)
        cl.addWidget(self._timed)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {BORDER_CLR};")
        cl.addWidget(sep)

        # Time settings container
        self._settings_box = QFrame()
        self._settings_box.setObjectName("timeSettingsBox")
        self._settings_box.setStyleSheet(f"""
            #timeSettingsBox {{
                background-color: {PANEL2};
                border: 1px solid {BORDER_CLR};
                border-radius: 8px;
            }}
        """)
        self._settings_box.setEnabled(False)
        self._settings_box.setMinimumHeight(345)
        sbl = QVBoxLayout(self._settings_box)
        sbl.setContentsMargins(16, 14, 16, 14)
        sbl.setSpacing(12)

        # Quick presets
        presets_lbl = QLabel("QUICK PRESETS")
        presets_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 9pt;
            color: {TEXT_DIM};
            letter-spacing: 0px;
            background: transparent;
            border: none;
        """)
        sbl.addWidget(presets_lbl)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        presets = [("1 min", 60_000), ("3 min", 180_000), ("5 min", 300_000),
                   ("10 min", 600_000), ("15 min", 900_000)]
        for name, ms in presets:
            preset_row.addWidget(_preset_btn(name, self, ms))
        preset_row.addStretch()
        sbl.addLayout(preset_row)

        # Custom time
        time_lbl = QLabel("CUSTOM TIME")
        time_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 9pt;
            color: {TEXT_DIM};
            letter-spacing: 0px;
            margin-top: 4px;
            background: transparent;
            border: none;
        """)
        sbl.addWidget(time_lbl)

        time_row = QHBoxLayout()
        time_row.setSpacing(10)
        time_row.addWidget(_label("Min:"))
        self._minutes = _spinbox(0, 60, 5, "min")
        time_row.addWidget(self._minutes)
        time_row.addSpacing(8)
        time_row.addWidget(_label("Sec:"))
        self._seconds = _spinbox(0, 59, 0, "sec")
        time_row.addWidget(self._seconds)
        time_row.addStretch()
        sbl.addLayout(time_row)

        # Increment
        inc_lbl = QLabel("INCREMENT (Fischer)")
        inc_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 9pt;
            color: {TEXT_DIM};
            letter-spacing: 0px;
            margin-top: 4px;
            background: transparent;
            border: none;
        """)
        sbl.addWidget(inc_lbl)

        inc_row = QHBoxLayout()
        inc_row.setSpacing(10)
        self._increment = _spinbox(0, 30, 3, "sec")
        inc_row.addWidget(self._increment)
        note = _label("added after each move", dim=True, size=11)
        note.setMinimumWidth(260)
        inc_row.addWidget(note)
        inc_row.addStretch()
        sbl.addLayout(inc_row)

        cl.addWidget(self._settings_box)
        outer.addWidget(content)

        # ── Bottom button bar ──────────────────────────────────────────────
        btn_frame = QFrame()
        btn_frame.setObjectName("timeButtonBar")
        btn_frame.setStyleSheet(f"""
            #timeButtonBar {{
                background-color: {BG_DARK};
                border-top: 1px solid {BORDER_CLR};
            }}
        """)
        bfl = QHBoxLayout(btn_frame)
        bfl.setContentsMargins(20, 12, 20, 12)
        bfl.setSpacing(10)
        bfl.addStretch()

        self._ok_btn = QPushButton("Start Game")
        self._ok_btn.setFixedHeight(42)
        self._ok_btn.setMinimumWidth(150)
        self._ok_btn.setCursor(Qt.PointingHandCursor)
        self._ok_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {_MONO};
                font-size: 11pt;
                font-weight: 800;
                color: {TEXT_MAIN};
                background-color: {ACCENT_GRN};
                border: none;
                border-radius: 6px;
                padding: 7px 18px;
                letter-spacing: 0px;
            }}
            QPushButton:hover {{ background-color: {QColor(ACCENT_GRN).lighter(115).name()}; }}
            QPushButton:pressed {{ background-color: {QColor(ACCENT_GRN).darker(115).name()}; }}
        """)
        self._ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setFixedHeight(42)
        cancel_btn.setMinimumWidth(112)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                font-family: {_MONO};
                font-size: 11pt;
                font-weight: 800;
                color: {TEXT_DIM};
                background-color: transparent;
                border: 1px solid {BORDER_CLR};
                border-radius: 6px;
                padding: 7px 18px;
            }}
            QPushButton:hover {{ color: {TEXT_MAIN}; border-color: {ACCENT_GRN}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        bfl.addWidget(self._ok_btn)
        bfl.addWidget(cancel_btn)
        outer.addWidget(btn_frame)

        # Connect mode toggle
        self._mode_grp.buttonClicked.connect(self._on_mode_change)

    # ── drag ───────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.pos().y() < 44:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_pos:
            self.move(e.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    # ── slots ──────────────────────────────────────────────────────────────
    def _on_mode_change(self, _btn):
        timed = self._timed.isChecked()
        self._settings_box.setEnabled(timed)
        self._ok_btn.setText("Start Timed" if timed else "Start Game")

    def _set_preset(self, ms):
        self._timed.setChecked(True)
        self._settings_box.setEnabled(True)
        self._minutes.setValue(ms // 60_000)
        self._seconds.setValue((ms % 60_000) // 1000)
        self._ok_btn.setText(f"Start ({ms//60000}:{(ms%60000)//1000:02d})")

    # ── public API (compatible with original) ─────────────────────────────
    def get_time_settings(self):
        is_timed = self._timed.isChecked()
        if not is_timed:
            return False, 0, 0, 0, 0
        m, s = self._minutes.value(), self._seconds.value()
        time_ms = (m * 60 + s) * 1000
        inc_ms  = self._increment.value() * 1000
        return True, time_ms, time_ms, inc_ms, inc_ms

    def accept(self):
        is_timed, wt, bt, wi, bi = self.get_time_settings()
        if is_timed and wt <= 0:
            orig = self._ok_btn.text()
            self._ok_btn.setText("SET VALID TIME!")
            self._ok_btn.setStyleSheet(self._ok_btn.styleSheet().replace(
                ACCENT_GRN, ACCENT_RED))
            QTimer.singleShot(1800, lambda: (
                self._ok_btn.setText(orig),
                self._ok_btn.setStyleSheet(self._ok_btn.styleSheet().replace(
                    ACCENT_RED, ACCENT_GRN))
            ))
            return
        super().accept()
