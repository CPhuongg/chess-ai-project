# Path: ui/components/chess_timer.py
# Description:
# Chess timer widget with Pygame-inspired HUD design.
# Two side-by-side clocks with monospace font, active player highlighted with colored border.
# Supports Fischer increment (time added after each move).
# Color-coded time display: normal (white), warning (yellow under 60s), critical (red under 30s).
# Emits time_expired signal when either player runs out of time.

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor

# ── Palette ────────────────────────────────────────────────────────────────
BG_TIMER     = "#1A1A1A"
BORDER_CLR   = "#383838"
ACTIVE_BDR   = "#769656"    # Green: active player
INACTIVE_BDR = "#2C2C2C"
WHITE_CLR    = "#F0D9B5"    # Warm ivory: White's side
BLACK_CLR    = "#B58863"    # Brown: Black's side
TEXT_MAIN    = "#EFEFEF"
TEXT_DIM     = "#666666"
WARN_CLR     = "#D4AC0D"    # Yellow: < 60 s
CRIT_CLR     = "#C1392B"    # Red: < 30 s
_MONO        = "'Courier New', monospace"
# ───────────────────────────────────────────────────────────────────────────


def _time_color(ms: int) -> str:
    if ms <= 30_000:
        return CRIT_CLR
    if ms <= 60_000:
        return WARN_CLR
    return TEXT_MAIN


class _PlayerClock(QFrame):
    """
    Đồng hồ của một người chơi — player label trên, thời gian lớn dưới.
    """

    def __init__(self, player_label: str, accent: str, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setFrameShape(QFrame.NoFrame)

        self._active = False
        self._apply_style(active=False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        # Player label
        self._name_lbl = QLabel(player_label.upper())
        self._name_lbl.setAlignment(Qt.AlignCenter)
        self._name_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 8pt;
            font-weight: bold;
            color: {TEXT_DIM};
            letter-spacing: 2px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(self._name_lbl)

        # Time display
        self._time_lbl = QLabel("00:00")
        self._time_lbl.setAlignment(Qt.AlignCenter)
        self._time_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 28pt;
            font-weight: bold;
            color: {TEXT_MAIN};
            background: transparent;
            border: none;
            letter-spacing: 2px;
        """)
        layout.addWidget(self._time_lbl)

    def set_time(self, ms: int):
        self._time_lbl.setText(self._fmt(ms))
        color = _time_color(ms)
        self._time_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 28pt;
            font-weight: bold;
            color: {color};
            background: transparent;
            border: none;
            letter-spacing: 2px;
        """)

    def set_active(self, active: bool):
        self._active = active
        self._apply_style(active)
        if active:
            self._name_lbl.setStyleSheet(f"""
                font-family: {_MONO};
                font-size: 8pt;
                font-weight: bold;
                color: {self.accent};
                letter-spacing: 2px;
                background: transparent;
                border: none;
            """)
        else:
            self._name_lbl.setStyleSheet(f"""
                font-family: {_MONO};
                font-size: 8pt;
                font-weight: bold;
                color: {TEXT_DIM};
                letter-spacing: 2px;
                background: transparent;
                border: none;
            """)

    def set_name(self, name: str):
        self._name_lbl.setText(name.upper())

    # ── internals ──────────────────────────────────────────────────────────
    def _apply_style(self, active: bool):
        bdr = self.accent if active else INACTIVE_BDR
        bg  = "#1E1E1E" if active else BG_TIMER
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {bdr};
            }}
        """)

    @staticmethod
    def _fmt(ms: int) -> str:
        total_s = ms // 1000
        m, s = divmod(total_s, 60)
        return f"{m:02d}:{s:02d}"


class ChessTimer(QWidget):
    """
    Timer widget kiểu Pygame HUD — hai đồng hồ cạnh nhau, nền tối.
    API tương thích với code gốc.
    """

    time_expired = pyqtSignal(str)   # 'white' | 'black'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(80)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG_TIMER};
                border-bottom: 1px solid {BORDER_CLR};
            }}
        """)

        # Timer state
        self.white_time_ms  = 0
        self.black_time_ms  = 0
        self.active_player  = None
        self.is_paused      = True
        self.is_time_mode   = False

        # Internal 100 ms tick
        self._tick = QTimer(self)
        self._tick.timeout.connect(self._on_tick)
        self._tick.setInterval(100)

        self._build_ui()
        self.hide()

    # ── UI ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self.white_clock = _PlayerClock("White", WHITE_CLR)
        self.black_clock = _PlayerClock("Black", BLACK_CLR)

        layout.addWidget(self.white_clock)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {BORDER_CLR}; max-width: 1px;")
        layout.addWidget(sep)

        layout.addWidget(self.black_clock)

    # ── Public API (backward-compatible) ────────────────────────────────────
    def set_time_mode(self, enabled: bool, white_time_ms=0, black_time_ms=0):
        self.is_time_mode = enabled
        if enabled:
            self.white_time_ms = white_time_ms
            self.black_time_ms = black_time_ms
            self._refresh_displays()
            self.show()
        else:
            self.stop_timer()
            self.hide()

    def start_timer(self, player: str):
        if not self.is_time_mode:
            return
        self.active_player = player
        self.is_paused = False
        self._tick.start()
        self._update_active_display()

    def stop_timer(self):
        self._tick.stop()
        self.is_paused = True
        self.active_player = None
        self.white_clock.set_active(False)
        self.black_clock.set_active(False)

    def pause_timer(self):
        self.is_paused = True

    def resume_timer(self):
        if self.is_time_mode and self.active_player:
            self.is_paused = False

    def switch_timer_to_player(self, player: str,
                               apply_increment=False, increment_ms=0):
        if not self.is_time_mode:
            return
        if apply_increment and increment_ms and self.active_player:
            self.add_increment(self.active_player, increment_ms)
        self.active_player = player
        self._update_active_display()
    
    # THÊM PHƯƠNG THỨC switch_player (alias cho switch_timer_to_player)
    def switch_player(self, player: str):
        """
        Switch the active timer to the specified player.
        Alias for switch_timer_to_player for compatibility.
        """
        self.switch_timer_to_player(player)

    def add_increment(self, player: str, increment_ms: int):
        if not self.is_time_mode:
            return
        if player == 'white':
            self.white_time_ms += increment_ms
        elif player == 'black':
            self.black_time_ms += increment_ms
        self._refresh_displays()

    def get_remaining_times(self):
        return self.white_time_ms, self.black_time_ms

    def set_player_names(self, white_name: str, black_name: str):
        self.white_clock.set_name(white_name)
        self.black_clock.set_name(black_name)

    # ── Internals ──────────────────────────────────────────────────────────
    def _on_tick(self):
        if self.is_paused or not self.active_player:
            return
        if self.active_player == 'white':
            self.white_time_ms = max(0, self.white_time_ms - 100)
            if self.white_time_ms == 0:
                self.time_expired.emit('white')
                self.stop_timer()
        else:
            self.black_time_ms = max(0, self.black_time_ms - 100)
            if self.black_time_ms == 0:
                self.time_expired.emit('black')
                self.stop_timer()
        self._refresh_displays()

    def _refresh_displays(self):
        self.white_clock.set_time(self.white_time_ms)
        self.black_clock.set_time(self.black_time_ms)

    def _update_active_display(self):
        self.white_clock.set_active(self.active_player == 'white')
        self.black_clock.set_active(self.active_player == 'black')

    # Legacy alias kept for compatibility
    def update_display(self):
        self._refresh_displays()

    def update_active_player_display(self):
        self._update_active_display()

    def reset_player_displays(self):
        self.white_clock.set_active(False)
        self.black_clock.set_active(False)