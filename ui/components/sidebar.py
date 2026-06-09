"""Sidebar controls and saved-game helpers."""

import datetime
import json
import os

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog,
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.components.controls import ControlButton, ResignButton
from ui.theme import (
    MONO_FONT,
    button_stylesheet,
    color,
    section_label_stylesheet,
    value_label_stylesheet,
)
from utils.config import Config
from utils.error_handler import ErrorHandler


class SavedGameManager:
    """Read and write `.chess` save files."""

    @staticmethod
    def save_game(
        board,
        game_mode,
        turn,
        last_move_from,
        last_move_to,
        game_name=None,
        game_notes=None,
        timer_settings=None,
        player_color=None,
        board_flipped=None,
    ):
        try:
            if not board:
                raise ValueError("Cannot save an empty board")

            game_data = {
                "version": "2.0",
                "fen": board.fen(),
                "mode": game_mode,
                "turn": turn,
                "player_color": player_color or "white",
                "board_flipped": bool(board_flipped),
                "last_move_from": last_move_from,
                "last_move_to": last_move_to,
                "move_history": [move.uci() for move in board.move_stack],
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            if timer_settings:
                game_data["timer_settings"] = {
                    "enabled": timer_settings.get("enabled", False),
                    "initial_white_time_ms": timer_settings.get("initial_white_time_ms", 0),
                    "initial_black_time_ms": timer_settings.get("initial_black_time_ms", 0),
                    "white_time_ms": timer_settings.get("white_time_ms", 0),
                    "black_time_ms": timer_settings.get("black_time_ms", 0),
                    "active_player": timer_settings.get("active_player"),
                    "white_increment_ms": timer_settings.get("white_increment_ms", 3000),
                    "black_increment_ms": timer_settings.get("black_increment_ms", 3000),
                }

            if game_name and isinstance(game_name, str):
                game_data["game_name"] = game_name.strip()[:100]
            if game_notes and isinstance(game_notes, str):
                game_data["game_notes"] = game_notes.strip()[:500]

            file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Save Chess Game",
                os.path.expanduser("~/Desktop"),
                "Chess Game Files (*.chess);;All Files (*)",
            )
            if not file_path:
                return False, None

            if not file_path.lower().endswith(".chess"):
                file_path += ".chess"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(game_data, file, indent=4, ensure_ascii=False)
            return True, file_path

        except PermissionError:
            ErrorHandler.show_error(
                None,
                "Save Error",
                "Permission denied. Cannot save file in the selected location.",
            )
        except Exception as exc:
            print(f"Unexpected error in save_game: {exc}")
            ErrorHandler.show_error(
                None,
                "Save Error",
                f"An unexpected error occurred: {exc}",
            )
        return False, None

    @staticmethod
    def load_game(file_path=None):
        try:
            if not file_path:
                file_path, _ = QFileDialog.getOpenFileName(
                    None,
                    "Load Chess Game",
                    os.path.expanduser("~/Desktop"),
                    "Chess Game Files (*.chess);;All Files (*)",
                )
            if not file_path or not os.path.exists(file_path):
                return False, None
            if not file_path.lower().endswith(".chess"):
                ErrorHandler.show_error(
                    None,
                    "Invalid File",
                    "Please select a valid .chess game file.",
                )
                return False, None

            with open(file_path, "r", encoding="utf-8") as file:
                game_data = json.load(file)

            required = ["fen", "mode", "turn", "move_history"]
            if not all(key in game_data for key in required):
                ErrorHandler.show_error(
                    None,
                    "Invalid Game Data",
                    "The saved game is missing critical information.",
                )
                return False, None
            return True, game_data

        except PermissionError:
            ErrorHandler.show_error(
                None,
                "Permission Denied",
                "Cannot read the selected file. Check file permissions.",
            )
        except json.JSONDecodeError:
            ErrorHandler.show_error(
                None,
                "JSON Error",
                "The game file is corrupted or not in the correct format.",
            )
        except Exception as exc:
            print(f"Unexpected error in load_game: {exc}")
            ErrorHandler.show_error(None, "Load Error", f"An unexpected error occurred: {exc}")
        return False, None


class _SectionLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(section_label_stylesheet())


class _Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet(f"color: {color('border')}; max-height: 1px;")


class AIControlPanel(QScrollArea):
    """Scrollable right panel for status, game actions, and AI options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(450)
        self.setMinimumHeight(500)
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {color("panel")};
                border: none;
                border-left: 1px solid {color("border")};
            }}
            QScrollBar:vertical {{
                background: {color("panel")};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {color("border")};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {color("accent")};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        inner = QWidget()
        inner.setStyleSheet(f"background-color: {color('panel')};")
        self.setWidget(inner)

        self.main_layout = QVBoxLayout(inner)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(8)

        self.title = QLabel("GAME CONTROLS")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(f"""
            font-family: {MONO_FONT};
            font-size: 11pt;
            font-weight: bold;
            color: {color("accent")};
            letter-spacing: 1px;
            padding: 8px 0 6px 0;
        """)
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(_Divider())

        self._build_status_section()
        self._build_game_buttons()
        self._build_action_buttons()
        self._build_difficulty_section()
        self._build_undo_slot()

        self.main_layout.addStretch(1)
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self._build_legacy_slider_shims()

    def _build_status_section(self):
        self.main_layout.addWidget(_SectionLabel("State"))
        self.mode_label = QLabel("Mode: -")
        self.turn_label = QLabel("Turn: -")
        self.status_label = QLabel("Status: Ready")
        self.color_label = QLabel("Human: White")

        for label in (self.mode_label, self.turn_label, self.status_label, self.color_label):
            label.setWordWrap(True)
            label.setStyleSheet(value_label_stylesheet())
            self.main_layout.addWidget(label)
        self.main_layout.addWidget(_Divider())

    def _build_game_buttons(self):
        self.main_layout.addWidget(_SectionLabel("Game"))
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.start_button = ControlButton("Start", color("accent"))
        self.pause_button = ControlButton("Pause", color("warning"))
        self.reset_button = ControlButton("New Game")
        self.save_button = ControlButton("Save", color("info"))

        grid.addWidget(self.start_button, 0, 0)
        grid.addWidget(self.pause_button, 0, 1)
        grid.addWidget(self.reset_button, 1, 0)
        grid.addWidget(self.save_button, 1, 1)
        self.main_layout.addWidget(grid_widget)

    def _build_action_buttons(self):
        self.main_layout.addWidget(_SectionLabel("Actions"))
        self.resign_button = ResignButton()
        self.home_button = ControlButton("Choose Mode")
        self.flip_button = ControlButton("Flip Board", color("info"))
        self.main_layout.addWidget(self.resign_button)
        self.main_layout.addWidget(self.home_button)
        self.main_layout.addWidget(self.flip_button)
        self.main_layout.addWidget(_Divider())

    def _build_difficulty_section(self):
        self.main_layout.addWidget(_SectionLabel("Difficulty"))
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentText("Medium")
        self.difficulty_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {color("panel_alt")};
                color: {color("text")};
                border: 1px solid {color("border")};
                border-radius: 3px;
                padding: 5px 7px;
                font-family: {MONO_FONT};
                font-size: 9pt;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 22px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {color("panel")};
                color: {color("text")};
                selection-background-color: {color("accent")};
            }}
        """)
        self.main_layout.addWidget(self.difficulty_combo)

    def _build_undo_slot(self):
        self.undo_button_container = QWidget()
        self.undo_button_layout = QVBoxLayout(self.undo_button_container)
        self.undo_button_layout.setContentsMargins(0, 0, 0, 0)
        self.undo_button_layout.setSpacing(6)
        self.main_layout.addWidget(self.undo_button_container)

    def _build_legacy_slider_shims(self):
        class _DummySlider(QWidget):
            valueChanged = pyqtSignal(int)

            def setValue(self, value):
                pass

            def value(self):
                return Config.DEFAULT_AI_SEARCH_DEPTH

        self.depth_slider = _DummySlider()
        self.speed_slider = self.depth_slider
        self.depth_value = QLabel("")
        self.depth_value.hide()

    def set_human_ai_mode(self):
        self.title.setText("HUMAN VS AI")
        self._set_ai_controls_visible(True)

    def set_human_human_mode(self):
        self.title.setText("HUMAN VS HUMAN")
        self._set_ai_controls_visible(False)

    def set_ai_ai_mode(self):
        self.title.setText("AI VS AI")
        self._set_ai_controls_visible(True)

    def _set_ai_controls_visible(self, visible):
        self.difficulty_combo.setVisible(visible)

    def sizeHint(self):
        return QSize(450, 500)
