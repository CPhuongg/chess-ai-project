# Path: ui/app.py
# Description:
# Main application entry point with PyQt5-based dark theme setup.
# Sets a pygame-inspired dark color palette (backgrounds, text, buttons, accent).
# Manages the start screen, game mode selection (human vs AI or AI vs AI),
# time control dialog, and saved game loading.
# Coordinates between the start screen, time mode dialog, and main chess board window.
# Uses Fusion style with custom QPalette for consistent dark appearance.

# ui/app.py — Pygame-inspired dark theme setup
# Chỉ cập nhật phần styling của QApplication; logic không đổi.

from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtGui import QColor, QFont, QPalette
from ui.board import ChessBoard
from ui.components.popups import StartScreen
from ui.components.load_game_dialog import LoadGameDialog
from ui.components.sidebar import SavedGameManager
from ui.components.time_mode_dialog import TimeModeDialog


class ChessApp(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.setStyle("Fusion")

        # ── Pygame-inspired dark palette ───────────────────────────────────
        palette = QPalette()
        D  = QColor("#141414")   # darkest bg
        P  = QColor("#1E1E1E")   # panel bg
        T  = QColor("#EFEFEF")   # text main
        DT = QColor("#888888")   # text dim
        B  = QColor("#2A2A2A")   # button bg
        BT = QColor("#EFEFEF")   # button text
        A  = QColor("#769656")   # accent green

        palette.setColor(QPalette.Window,          P)
        palette.setColor(QPalette.WindowText,      T)
        palette.setColor(QPalette.Base,            D)
        palette.setColor(QPalette.AlternateBase,   QColor("#242424"))
        palette.setColor(QPalette.Text,            T)
        palette.setColor(QPalette.BrightText,      T)
        palette.setColor(QPalette.Button,          B)
        palette.setColor(QPalette.ButtonText,      BT)
        palette.setColor(QPalette.Highlight,       A)
        palette.setColor(QPalette.HighlightedText, T)
        palette.setColor(QPalette.ToolTipBase,     P)
        palette.setColor(QPalette.ToolTipText,     T)
        palette.setColor(QPalette.Disabled, QPalette.Text,       DT)
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, DT)
        self.setPalette(palette)
        # ───────────────────────────────────────────────────────────────────

        self.setFont(QFont("Courier New", 10))

        self.chess_window = None
        self.show_start_screen()

    def show_start_screen(self):
        if self.chess_window:
            if hasattr(self.chess_window, 'popup') and self.chess_window.popup:
                self.chess_window.popup.close()
                self.chess_window.popup = None
            self.chess_window.close()
            self.chess_window.deleteLater()
            self.chess_window = None

        start_screen = StartScreen()
        start_screen.load_game_button.clicked.connect(self.load_saved_game)

        if start_screen.exec_() == QDialog.Accepted:
            mode = start_screen.get_mode()
            player_color = start_screen.get_player_color()
            if mode:
                self.start_new_game_with_time_selection(mode, player_color)

    def start_new_game_with_time_selection(self, mode, player_color="white"):
        time_dialog = TimeModeDialog()
        if time_dialog.exec_() == QDialog.Accepted:
            is_time_mode, white_time_ms, black_time_ms, white_inc_ms, black_inc_ms = \
                time_dialog.get_time_settings()
            self.chess_window = ChessBoard(mode, self, player_color=player_color)
            self.chess_window.setup_time_mode(
                is_time_mode, white_time_ms, black_time_ms,
                white_inc_ms, black_inc_ms
            )
            if mode in ("human_ai", "human_human") and is_time_mode:
                self.chess_window.switch_timer_to_board_turn()
            # Set window to full screen by default
            self.chess_window.showMaximized()  # THAY ĐỔI: showMaximized thay vì show
        else:
            self.show_start_screen()

    def load_saved_game(self):
        load_dialog = LoadGameDialog()
        load_dialog.game_selected.connect(self.start_loaded_game)
        result = load_dialog.exec_()
        if result == QDialog.Accepted and hasattr(load_dialog, 'game_data'):
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QDialog) and widget.windowTitle() == "Chess Game":
                    widget.close()
                    break

    def start_loaded_game(self, game_data):
        try:
            mode = game_data.get('mode', 'human_ai')
            player_color = game_data.get('player_color', 'white')
            if self.chess_window:
                self.chess_window.close()
                self.chess_window.deleteLater()
                self.chess_window = None

            has_timer = 'timer_settings' in game_data
            is_time_mode = False
            white_time_ms = black_time_ms = 0
            white_inc_ms = black_inc_ms = 3000

            if has_timer:
                ts = game_data['timer_settings']
                is_time_mode  = ts.get('enabled', False)
                white_time_ms = ts.get('white_time_ms', 0)
                black_time_ms = ts.get('black_time_ms', 0)
                white_inc_ms  = ts.get('white_increment_ms', 3000)
                black_inc_ms  = ts.get('black_increment_ms', 3000)
            else:
                td = TimeModeDialog()
                td.setWindowTitle("Time Control for Loaded Game")
                if td.exec_() == QDialog.Accepted:
                    is_time_mode, white_time_ms, black_time_ms, white_inc_ms, black_inc_ms = \
                        td.get_time_settings()

            self.chess_window = ChessBoard(mode, self, game_data, player_color=player_color)
            self.chess_window.setup_time_mode(
                is_time_mode, white_time_ms, black_time_ms,
                white_inc_ms, black_inc_ms
            )

            if is_time_mode:
                current = game_data.get('turn', 'human')
                if mode in ("human_ai", "human_human"):
                    self.chess_window.switch_timer_to_board_turn()
                else:
                    self.chess_window.switch_timer_to_player(
                        'ai1' if current == 'ai1' else 'ai2'
                    )

            self.chess_window.showMaximized()  # THAY ĐỔI: showMaximized thay vì show

            sender = self.sender()
            if sender:
                start_screen = sender.parent()
                if start_screen:
                    start_screen.done(QDialog.Accepted)
                sender.done(QDialog.Accepted)

        except Exception as e:
            QMessageBox.critical(None, "Error", f"Failed to load game: {e}")
            print(f"Error loading game: {e}")
