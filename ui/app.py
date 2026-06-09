"""Application bootstrap for the PyQt chess UI."""

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox

from ui.board import ChessBoard
from ui.components.load_game_dialog import LoadGameDialog
from ui.components.popups import StartScreen
from ui.components.time_mode_dialog import TimeModeDialog
from ui.theme import FONT_FAMILY, apply_app_palette


class ChessApp(QApplication):
    """Coordinates the start screen, time selection, and board window."""

    def __init__(self, args):
        super().__init__(args)
        self.setStyle("Fusion")
        apply_app_palette(self)
        self.setFont(QFont(FONT_FAMILY, 10))

        self.chess_window = None
        self.show_start_screen()

    def show_start_screen(self):
        self._close_active_board()

        start_screen = StartScreen()
        start_screen.load_game_button.clicked.connect(self.load_saved_game)

        if start_screen.exec_() == QDialog.Accepted:
            mode = start_screen.get_mode()
            player_color = start_screen.get_player_color()
            if mode:
                self.start_new_game_with_time_selection(mode, player_color)

    def start_new_game_with_time_selection(self, mode, player_color="white"):
        time_dialog = TimeModeDialog()
        if time_dialog.exec_() != QDialog.Accepted:
            self.show_start_screen()
            return

        (
            is_time_mode,
            white_time_ms,
            black_time_ms,
            white_inc_ms,
            black_inc_ms,
        ) = time_dialog.get_time_settings()

        self.chess_window = ChessBoard(mode, self, player_color=player_color)
        self.chess_window.setup_time_mode(
            is_time_mode,
            white_time_ms,
            black_time_ms,
            white_inc_ms,
            black_inc_ms,
        )
        if mode in ("human_ai", "human_human") and is_time_mode:
            self.chess_window.switch_timer_to_board_turn()
        self.chess_window.showMaximized()

    def load_saved_game(self):
        load_dialog = LoadGameDialog()
        load_dialog.game_selected.connect(self.start_loaded_game)
        load_dialog.exec_()

    def start_loaded_game(self, game_data):
        try:
            mode = game_data.get("mode", "human_ai")
            player_color = game_data.get("player_color", "white")
            self._close_active_board()

            (
                is_time_mode,
                white_time_ms,
                black_time_ms,
                white_inc_ms,
                black_inc_ms,
            ) = self._loaded_timer_settings(game_data)

            self.chess_window = ChessBoard(
                mode,
                self,
                game_data,
                player_color=player_color,
            )
            self.chess_window.setup_time_mode(
                is_time_mode,
                white_time_ms,
                black_time_ms,
                white_inc_ms,
                black_inc_ms,
            )

            if is_time_mode:
                current = game_data.get("turn", "human")
                if mode in ("human_ai", "human_human"):
                    self.chess_window.switch_timer_to_board_turn()
                else:
                    self.chess_window.switch_timer_to_player(
                        "ai1" if current == "ai1" else "ai2"
                    )

            self.chess_window.showMaximized()

            sender = self.sender()
            if sender:
                parent = sender.parent()
                if parent:
                    parent.done(QDialog.Accepted)
                sender.done(QDialog.Accepted)

        except Exception as exc:
            QMessageBox.critical(None, "Error", f"Failed to load game: {exc}")
            print(f"Error loading game: {exc}")

    def _close_active_board(self):
        if not self.chess_window:
            return

        popup = getattr(self.chess_window, "popup", None)
        if popup:
            popup.close()
            self.chess_window.popup = None

        self.chess_window.close()
        self.chess_window.deleteLater()
        self.chess_window = None

    def _loaded_timer_settings(self, game_data):
        timer_settings = game_data.get("timer_settings")
        if timer_settings:
            return (
                timer_settings.get("enabled", False),
                timer_settings.get("white_time_ms", 0),
                timer_settings.get("black_time_ms", 0),
                timer_settings.get("white_increment_ms", 3000),
                timer_settings.get("black_increment_ms", 3000),
            )

        time_dialog = TimeModeDialog()
        time_dialog.setWindowTitle("Time Control for Loaded Game")
        if time_dialog.exec_() == QDialog.Accepted:
            return time_dialog.get_time_settings()
        return False, 0, 0, 3000, 3000
