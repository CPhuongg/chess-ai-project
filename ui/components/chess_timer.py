"""Chess clock widget with two synchronized player displays."""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from ui.theme import MONO_FONT, color


def _time_color(ms: int) -> str:
    if ms <= 30_000:
        return color("danger")
    if ms <= 60_000:
        return color("warning")
    return color("text")


class _PlayerClock(QFrame):
    def __init__(self, player_label: str, accent: str, parent=None):
        super().__init__(parent)
        self.accent = accent
        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        self._name_lbl = QLabel(player_label.upper())
        self._name_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._name_lbl)

        self._time_lbl = QLabel("00:00")
        self._time_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._time_lbl)

        self.set_active(False)
        self.set_time(0)

    def set_time(self, ms: int):
        self._time_lbl.setText(self._format_time(ms))
        self._time_lbl.setStyleSheet(f"""
            font-family: {MONO_FONT};
            font-size: 28pt;
            font-weight: bold;
            color: {_time_color(ms)};
            background: transparent;
            border: none;
        """)

    def set_active(self, active: bool):
        border = self.accent if active else color("border")
        background = color("surface_alt") if active else color("panel")
        name_color = self.accent if active else color("muted")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {background};
                border: 2px solid {border};
                border-radius: 4px;
            }}
        """)
        self._name_lbl.setStyleSheet(f"""
            font-family: {MONO_FONT};
            font-size: 8pt;
            font-weight: bold;
            color: {name_color};
            background: transparent;
            border: none;
        """)

    def set_name(self, name: str):
        self._name_lbl.setText(name.upper())

    @staticmethod
    def _format_time(ms: int) -> str:
        total_seconds = ms // 1000
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"


class ChessTimer(QWidget):
    """Public timer API used by the board controller."""

    time_expired = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {color("panel")};
                border-bottom: 1px solid {color("border")};
            }}
        """)

        self.white_time_ms = 0
        self.black_time_ms = 0
        self.active_player = None
        self.is_paused = True
        self.is_time_mode = False

        self._tick = QTimer(self)
        self._tick.setInterval(100)
        self._tick.timeout.connect(self._on_tick)

        self._build_ui()
        self.hide()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)

        self.white_clock = _PlayerClock("White", color("light_square"))
        self.black_clock = _PlayerClock("Black", color("dark_square"))
        layout.addWidget(self.white_clock)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet(f"color: {color('border')}; max-width: 1px;")
        layout.addWidget(separator)
        layout.addWidget(self.black_clock)

    def set_time_mode(self, enabled: bool, white_time_ms=0, black_time_ms=0):
        self.is_time_mode = enabled
        if not enabled:
            self.stop_timer()
            self.hide()
            return

        self.white_time_ms = white_time_ms
        self.black_time_ms = black_time_ms
        self._refresh_displays()
        self.show()

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

    def switch_timer_to_player(self, player: str, apply_increment=False, increment_ms=0):
        if not self.is_time_mode:
            return
        if apply_increment and increment_ms and self.active_player:
            self.add_increment(self.active_player, increment_ms)
        self.active_player = player
        self._update_active_display()

    def switch_player(self, player: str):
        self.switch_timer_to_player(player)

    def add_increment(self, player: str, increment_ms: int):
        if not self.is_time_mode:
            return
        if player == "white":
            self.white_time_ms += increment_ms
        elif player == "black":
            self.black_time_ms += increment_ms
        self._refresh_displays()

    def get_remaining_times(self):
        return self.white_time_ms, self.black_time_ms

    def set_player_names(self, white_name: str, black_name: str):
        self.white_clock.set_name(white_name)
        self.black_clock.set_name(black_name)

    def _on_tick(self):
        if self.is_paused or not self.active_player:
            return

        if self.active_player == "white":
            self.white_time_ms = max(0, self.white_time_ms - 100)
            if self.white_time_ms == 0:
                self.time_expired.emit("white")
                self.stop_timer()
        else:
            self.black_time_ms = max(0, self.black_time_ms - 100)
            if self.black_time_ms == 0:
                self.time_expired.emit("black")
                self.stop_timer()
        self._refresh_displays()

    def _refresh_displays(self):
        self.white_clock.set_time(self.white_time_ms)
        self.black_clock.set_time(self.black_time_ms)

    def _update_active_display(self):
        self.white_clock.set_active(self.active_player == "white")
        self.black_clock.set_active(self.active_player == "black")

    def update_display(self):
        self._refresh_displays()

    def update_active_player_display(self):
        self._update_active_display()

    def reset_player_displays(self):
        self.white_clock.set_active(False)
        self.black_clock.set_active(False)
