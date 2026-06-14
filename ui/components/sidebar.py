# Path: ui/components/sidebar.py
# Description:
# Right sidebar container with game controls and saved game management.
# AIControlPanel: scrollable panel with game control buttons (Start/Pause/Reset/Save),
# action buttons (Resign/Home), and placeholder for undo button.
# SavedGameManager: static methods for saving/loading .chess JSON files with board state,
# move history, timer settings, and metadata (game name, notes, timestamp).

import os
import json
import datetime
from PyQt5.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QFileDialog, QMessageBox, QSizePolicy, QGridLayout, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont

from utils.config import Config
from utils.error_handler import ErrorHandler
from ui.components.controls import ControlButton, ResignButton, UndoButton
from ui import theme

# ── Palette ────────────────────────────────────────────────────────────────
BG_DARK   = theme.APP_BG
PANEL_BG  = theme.SURFACE
DIVIDER   = theme.BORDER
TEXT_DIM  = theme.TEXT_MUTED
TEXT_MAIN = theme.TEXT
ACCENT    = theme.ACCENT
# ───────────────────────────────────────────────────────────────────────────


class SavedGameManager:
    """Quản lý save / load game. Logic không đổi, chỉ bỏ style cũ."""

    @staticmethod
    def save_game(board, game_mode, turn, last_move_from, last_move_to,
                  game_name=None, game_notes=None, timer_settings=None,
                  player_color=None, board_flipped=None):
        try:
            if not board:
                raise ValueError("Cannot save an empty board")

            game_data = {
                'version': '2.0',
                'fen': board.fen(),
                'mode': game_mode,
                'turn': turn,
                'player_color': player_color or 'white',
                'board_flipped': bool(board_flipped),
                'last_move_from': last_move_from,
                'last_move_to': last_move_to,
                'move_history': [move.uci() for move in board.move_stack],
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if timer_settings:
                game_data['timer_settings'] = {
                    'enabled': timer_settings.get('enabled', False),
                    'initial_white_time_ms': timer_settings.get('initial_white_time_ms', 0),
                    'initial_black_time_ms': timer_settings.get('initial_black_time_ms', 0),
                    'white_time_ms': timer_settings.get('white_time_ms', 0),
                    'black_time_ms': timer_settings.get('black_time_ms', 0),
                    'active_player': timer_settings.get('active_player', None),
                    'white_increment_ms': timer_settings.get('white_increment_ms', 3000),
                    'black_increment_ms': timer_settings.get('black_increment_ms', 3000)
                }

            if game_name and isinstance(game_name, str):
                game_data['game_name'] = game_name.strip()[:100]
            if game_notes and isinstance(game_notes, str):
                game_data['game_notes'] = game_notes.strip()[:500]

            file_path, _ = QFileDialog.getSaveFileName(
                None, "Save Chess Game",
                os.path.expanduser("~/Desktop"),
                "Chess Game Files (*.chess);;All Files (*)"
            )
            if not file_path:
                return False, None

            if not file_path.lower().endswith('.chess'):
                file_path += '.chess'
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=4, ensure_ascii=False)
            return True, file_path

        except PermissionError:
            ErrorHandler.show_error(None, "Save Error",
                "Permission denied. Cannot save file in the selected location.")
        except Exception as e:
            print(f"Unexpected error in save_game: {e}")
            ErrorHandler.show_error(None, "Save Error",
                f"An unexpected error occurred: {str(e)}")
        return False, None

    @staticmethod
    def load_game(file_path=None):
        try:
            if not file_path:
                file_path, _ = QFileDialog.getOpenFileName(
                    None, "Load Chess Game",
                    os.path.expanduser("~/Desktop"),
                    "Chess Game Files (*.chess);;All Files (*)"
                )
            if not file_path or not os.path.exists(file_path):
                return False, None
            if not file_path.lower().endswith('.chess'):
                ErrorHandler.show_error(None, "Invalid File",
                    "Please select a valid .chess game file.")
                return False, None

            with open(file_path, 'r', encoding='utf-8') as f:
                contents = f.read()
            if not contents.strip():
                ErrorHandler.show_error(None, "Empty File",
                    "The selected game file is empty.")
                return False, None
            try:
                game_data = json.loads(contents)
            except json.JSONDecodeError:
                ErrorHandler.show_error(None, "JSON Error",
                    "The game file is corrupted or not in the correct format.")
                return False, None

            required = ['fen', 'mode', 'turn', 'move_history']
            if not all(k in game_data for k in required):
                ErrorHandler.show_error(None, "Invalid Game Data",
                    "The saved game is missing critical information.")
                return False, None
            return True, game_data

        except PermissionError:
            ErrorHandler.show_error(None, "Permission Denied",
                "Cannot read the selected file. Check file permissions.")
        except Exception as e:
            print(f"Unexpected error in load_game: {e}")
            ErrorHandler.show_error(None, "Load Error",
                f"An unexpected error occurred: {str(e)}")
        return False, None


class _SectionLabel(QLabel):
    """Tiêu đề section nhỏ kiểu Pygame overlay text."""

    def __init__(self, text, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(f"""
            font-family: {theme.FONT_UI};
            font-size: 8pt;
            font-weight: 700;
            color: {TEXT_DIM};
            letter-spacing: 0px;
            padding: 8px 0px 2px 0px;
        """)


class _Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setStyleSheet(f"color: {DIVIDER}; max-height: 1px; margin: 2px 0;")


class AIControlPanel(QScrollArea):
    """
    Control panel tối — bố cục: game title → nút 2 cột → move controls.
    Phong cách: terminal / Pygame HUD overlay.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(390)
        self.setMinimumHeight(500)  # THÊM: đảm bảo chiều cao tối thiểu
        self.setStyleSheet(f"""
            QScrollArea {{
                background-color: {PANEL_BG};
                border: none;
                border-left: 1px solid {DIVIDER};
            }}
            QScrollBar:vertical {{
                background: {BG_DARK};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {theme.SURFACE_3};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {ACCENT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        inner = QWidget()
        inner.setStyleSheet(f"""
            background-color: {PANEL_BG};
            QPushButton {{
                min-width: 0px;
                padding: 7px 8px;
                font-size: 10pt;
            }}
        """)
        self.setWidget(inner)

        self.main_layout = QVBoxLayout(inner)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(14, 14, 14, 14)

        # ── Title ──────────────────────────────────────────────────────────
        self.title = QLabel("GAME CONTROLS")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet(f"""
            font-family: {theme.FONT_UI};
            font-size: 13pt;
            font-weight: 800;
            color: {ACCENT};
            letter-spacing: 0px;
            padding: 8px 0px 6px 0px;
        """)
        self.main_layout.addWidget(self.title)
        self.main_layout.addWidget(_Divider())

        self.main_layout.addWidget(_SectionLabel("state"))
        self.mode_label = QLabel("Mode: -")
        self.turn_label = QLabel("Turn: -")
        self.status_label = QLabel("Status: Ready")
        self.color_label = QLabel("Human: White")
        for lbl in (self.mode_label, self.turn_label, self.status_label, self.color_label):
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"""
                font-family: {theme.FONT_UI};
                font-size: 9.5pt;
                color: {TEXT_MAIN};
                background-color: {BG_DARK};
                border: 1px solid {DIVIDER};
                border-radius: 6px;
                padding: 7px 9px;
            """)
            self.main_layout.addWidget(lbl)
        self.main_layout.addWidget(_Divider())

        # ── Game control buttons (2×2 grid) ────────────────────────────────
        self.main_layout.addWidget(_SectionLabel("game"))
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.start_button  = ControlButton("Start", theme.ACCENT)
        self.pause_button  = ControlButton("Pause", theme.WARNING)
        self.reset_button  = ControlButton("New Game", theme.SURFACE_3)
        self.save_button   = ControlButton("Save", theme.ACCENT_BLUE)

        for btn in (self.start_button, self.pause_button,
                    self.reset_button, self.save_button):
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(36)  # TĂNG height lên 36
            btn.setMinimumWidth(110)  # THÊM minimum width

        grid.addWidget(self.start_button,  0, 0)
        grid.addWidget(self.pause_button,  0, 1)
        grid.addWidget(self.reset_button,  1, 0)
        grid.addWidget(self.save_button,   1, 1)
        self.main_layout.addWidget(grid_widget)

        # ── Action buttons ─────────────────────────────────────────────────
        self.main_layout.addWidget(_SectionLabel("actions"))

        self.resign_button = ResignButton()
        self.resign_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.resign_button.setFixedHeight(36)
        self.resign_button.setMinimumWidth(110)
        self.main_layout.addWidget(self.resign_button)

        self.home_button = ControlButton("Choose Mode", theme.SURFACE_3)
        self.home_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.home_button.setFixedHeight(36)
        self.home_button.setMinimumWidth(110)
        self.main_layout.addWidget(self.home_button)

        self.flip_button = ControlButton("Flip Board", theme.ACCENT_BLUE)
        self.flip_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.flip_button.setFixedHeight(36)
        self.flip_button.setMinimumWidth(110)
        self.main_layout.addWidget(self.flip_button)

        self.main_layout.addWidget(_Divider())
        self.main_layout.addWidget(_SectionLabel("difficulty"))
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Medium", "Hard"])
        self.difficulty_combo.setCurrentText("Medium")
        self.difficulty_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {BG_DARK};
                color: {TEXT_MAIN};
                border: 1px solid {DIVIDER};
                border-radius: 6px;
                padding: 7px 9px;
                font-family: {theme.FONT_UI};
                font-size: 9.5pt;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 22px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {PANEL_BG};
                color: {TEXT_MAIN};
                selection-background-color: {ACCENT};
            }}
        """)
        self.main_layout.addWidget(self.difficulty_combo)

        # ── Undo container ─────────────────────────────────────────────────
        self.main_layout.addWidget(_SectionLabel(""))
        self.undo_button_container = QWidget()
        self.undo_button_layout = QVBoxLayout(self.undo_button_container)
        self.undo_button_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.undo_button_container)

        # Thêm spacer để đẩy nội dung lên trên
        self.main_layout.addStretch(1)

        # ── Initial button states ──────────────────────────────────────────
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)

        # Dummy sliders for backward compatibility
        from PyQt5.QtCore import pyqtSignal as _sig

        class _DummySlider(QWidget):
            valueChanged = _sig(int)
            def setValue(self, v): pass
            def value(self): return Config.DEFAULT_AI_SEARCH_DEPTH

        self.depth_slider = _DummySlider()
        self.speed_slider = self.depth_slider
        self.depth_value  = QLabel("")
        self.depth_value.hide()

    # ── Mode helpers ───────────────────────────────────────────────────────
    def set_human_ai_mode(self):
        self.title.setText("HUMAN vs AI")
        self.start_button.show()
        self.pause_button.show()

    def set_human_human_mode(self):
        self.title.setText("HUMAN vs HUMAN")
        self.start_button.show()
        self.pause_button.show()

    def set_ai_ai_mode(self):
        self.title.setText("AI vs AI")
        self.start_button.show()
        self.pause_button.show()

    def sizeHint(self):
        return QSize(390, 500)
