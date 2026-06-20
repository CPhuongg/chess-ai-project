# Path: ui/board.py
# Description:
# Core chess board GUI component using PyQt5.
# Handles board rendering, piece movement, user input, and game flow.
# Supports two modes: Human vs AI and AI vs AI.
# Integrates chess timer with increment support, move animation, and thinking indicator.
# Manages AI computation via ResponsiveAIManager (separate process).
# Features include: undo move, resign, save/load game, pause/resume, and game over popups.
# Uses SquareGridLayout to maintain board square aspect ratio.
# Communicates with bot logic via ChessBot instances.

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QDialog,
    QSplitter, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, QPropertyAnimation
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from ui.components.popups import ResignConfirmationDialog, GameOverPopup

import chess
import sys
import traceback
import datetime
import os

from ui.components.board_components import ChessSquare, ThinkingIndicator
from ui.components.history import MoveHistoryWidget
from ui.components.sidebar import AIControlPanel, SavedGameManager
from ui.components.popups import PawnPromotionDialog, GameOverPopup, SaveGameDialog
from ui.components.animations import AnimatedLabel
from ui.components.evaluation_bar import EvaluationBar
# from ui.workers.ai_worker import AIWorker
from ui.workers.ai_worker import ResponsiveAIManager
from ui.components.chess_timer import ChessTimer
from ui.components.time_mode_dialog import TimeModeDialog
from evaluation.evaluation import Evaluation

def exception_hook(exctype, value, tb):
    print(f"Ngoại lệ không được xử lý: {exctype}")
    print(f"Giá trị: {value}")
    traceback.print_tb(tb)

class ChessBoard(QMainWindow):
    # Fix the ChessBoard __init__ method to prevent double dialog

    def __init__(self, mode="human_ai", parent_app=None, load_game_data=None, player_color="white"):
        super().__init__()

        self.patch_board_for_resignation()

        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(10)
        QApplication.setFont(font)

        self.setFont(font)
        
        self.popup = None
        self.mode = mode
        self.parent_app = parent_app
        self.player_color = chess.WHITE if player_color != "black" else chess.BLACK
        self.board_flipped = self.mode == "human_ai" and self.player_color == chess.BLACK
        self.game_started = load_game_data is not None
        
        self.ai_manager = ResponsiveAIManager(self)
        
        if self.mode == "human_ai":
            self.setWindowTitle("Chess - Human vs AI")
        elif self.mode == "human_human":
            self.setWindowTitle("Chess - Human vs Human")
        else:
            self.setWindowTitle("Chess - AI vs AI")
            
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
        """)
        
        self.board = chess.Board()
        self.selected_square = None
        self._evaluator = Evaluation()   # dùng để tính thanh lượng giá
        
        # Initialize chess bots ONCE here
        from bot import ChessBot
        if self.mode == "human_ai":
            # One bot for human vs AI mode
            self.ai_bot = ChessBot(opening_book_path="resources/komodo.bin")
            self.turn = 'human' if self.board.turn == self.player_color else 'ai'
        elif self.mode == "ai_ai":
            # Two bots for AI vs AI mode
            self.ai_bot1 = ChessBot(opening_book_path="resources/komodo.bin")
            self.ai_bot2 = ChessBot()  # Different bot without opening book for variety
            self.turn = 'ai1'
        else:
            self.turn = 'human_white'
            
        if self.mode == "human_ai":
            self.turn = 'human' if self.board.turn == self.player_color else 'ai'
        elif self.mode == "human_human":
            self.turn = 'human_white'
        else:
            self.turn = 'ai1'
            
        self.valid_moves = []
        self.castling_moves = []
        self.last_move_from = None
        self.last_move_to = None
        
        self.ai_game_running = False
        self.move_delay = 800
        self.ai_depth = 4
        self.ai_time_limit_ms = 6000
        self.ai_difficulty = "Medium"
        self.ai_worker = None
        self.ai_computation_active = False

        # Create the main layout with splitter for resizable panels
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: #2c3e50;")

        main_layout = QHBoxLayout(self.central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Create a splitter for resizable sections
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(2)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #455a64;
            }
        """)
        main_layout.addWidget(self.main_splitter)

        # Create the game area
        game_area = QWidget()
        game_layout = QVBoxLayout(game_area)
        game_layout.setSpacing(15)
        
        # Setup chess timer first
        self.setup_timer()
        game_layout.addWidget(self.chess_timer)
        
        # Create board container with a nice border
        board_container = QFrame()
        board_container.setFrameShape(QFrame.StyledPanel)
        board_container.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 10px;
                padding: 15px;
                border: 2px solid #455a64;
            }
        """)
        board_layout = QVBoxLayout(board_container)

        # ── Evaluation bar + board side by side ──────────────────────────
        board_row = QHBoxLayout()
        board_row.setSpacing(6)

        self.eval_bar = EvaluationBar()
        board_row.addWidget(self.eval_bar)

        # Create board widget with fixed size
        board_widget = QWidget()
        board_widget.setStyleSheet("background-color: #455a64; padding: 5px; border-radius: 5px;")
        
        from ui.board_layout_manager import SquareGridLayout
        self.board_layout = SquareGridLayout(board_widget)
        self.board_layout.setSpacing(0)
        self.board_layout.setContentsMargins(5, 5, 5, 5)

        for i in range(9):
            self.board_layout.setColumnMinimumWidth(i, 60)
            if i < 9:
                self.board_layout.setRowMinimumHeight(i, 60)
        
        # Create coordinate labels and squares. Labels are updated when the board flips.
        self.file_labels = []
        self.rank_labels = []
        label_style = "color: white; font-weight: bold; font-size: 12pt;"
        for j in range(8):
            col_label = QLabel()
            col_label.setAlignment(Qt.AlignCenter)
            col_label.setStyleSheet(label_style)
            self.board_layout.addWidget(col_label, 8, j)
            self.file_labels.append(col_label)

            row_label = QLabel()
            row_label.setAlignment(Qt.AlignCenter)
            row_label.setStyleSheet(label_style)
            self.board_layout.addWidget(row_label, j, 8)
            self.rank_labels.append(row_label)

        self.squares = []
        for i in range(8):
            row = []
            for j in range(8):
                square = ChessSquare(i, j)
                square.clicked.connect(self.player_move)
                self.board_layout.addWidget(square, i, j)
                row.append(square)
            self.squares.append(row)

        board_row.addWidget(board_widget)
        board_layout.addLayout(board_row)

        # Create thinking indicator
        indicator_space = QWidget()
        indicator_space.setFixedHeight(60)
        indicator_layout = QVBoxLayout(indicator_space)
        indicator_layout.setContentsMargins(0, 5, 0, 0)
        
        self.thinking_indicator = ThinkingIndicator()
        indicator_layout.addWidget(self.thinking_indicator)
        
        board_layout.addWidget(indicator_space)
        game_layout.addWidget(board_container)
        
        # Create right sidebar (existing code...)
        sidebar = QWidget()
        sidebar.setMinimumWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(15)
        
        sidebar_splitter = QSplitter(Qt.Vertical)
        sidebar_layout.addWidget(sidebar_splitter)
        
        self.move_history = MoveHistoryWidget()
        sidebar_splitter.addWidget(self.move_history)
        
        self.control_panel = AIControlPanel()
        sidebar_splitter.addWidget(self.control_panel)
        
        sidebar_splitter.setSizes([300, 300])
        
        # Connect control panel signals
        self.control_panel.start_button.clicked.connect(self.start_game)
        if self.mode in ("human_ai", "human_human"):
            self.control_panel.pause_button.clicked.connect(self.pause_human_ai_game)
        else:
            self.control_panel.pause_button.clicked.connect(self.pause_ai_game)
        self.control_panel.reset_button.clicked.connect(self.reset_game)
        self.control_panel.home_button.clicked.connect(self.return_to_home)
        self.control_panel.save_button.clicked.connect(self.save_game)
        self.control_panel.flip_button.clicked.connect(self.toggle_board_orientation)
        self.control_panel.difficulty_combo.currentTextChanged.connect(self.update_ai_difficulty)
        
        self.control_panel.start_button.setEnabled(True)
        self.control_panel.pause_button.setEnabled(False)
        self.control_panel.depth_slider.valueChanged.connect(self.update_ai_depth)
        
        # Add to main splitter
        self.main_splitter.addWidget(game_area)
        self.main_splitter.addWidget(sidebar)
        self.main_splitter.setSizes([800, 450])
        self.main_splitter.setStretchFactor(0, 3)
        self.main_splitter.setStretchFactor(1, 1)


        if self.mode == "human_ai":
            # Show start button for Human vs AI mode too
            self.control_panel.start_button.show()
            self.control_panel.pause_button.show()
            
            self.control_panel.start_button.setText("▶ Start Game")
            self.control_panel.pause_button.setText("⏸ Pause Game")
            
            # Update the title
            for i in range(self.control_panel.widget().layout().count()):
                item = self.control_panel.widget().layout().itemAt(i)
                if item.widget() and isinstance(item.widget(), QLabel):
                    if "AI Controls" in item.widget().text() or "AI Difficulty" in item.widget().text():
                        item.widget().setText("Game Controls")
                        break
        else:
            # AI vs AI mode
            self.control_panel.start_button.setText("▶ Start AI Game")
            self.control_panel.pause_button.setText("⏸ Pause AI Game")
        
        # Set initial status
        if self.mode == "human_ai":
            self.thinking_indicator.show_status("Press 'Start Game' to begin")
        else:
            self.thinking_indicator.show_status("Press 'Start AI Game' to begin")
        self.configure_mode_controls()
        
        # Set up timers
        self.ai_timer = QTimer(self)
        self.ai_timer.timeout.connect(self.ai_vs_ai_step)
        
        self.animated_pieces = {}
        self.piece_symbols = self.initialize_piece_symbols()
        
        sys.excepthook = exception_hook

        # Time selection is owned by app.py; the board only restores or renders state.
        if load_game_data:
            self.load_game_state(load_game_data)
        else:
            # Initialize the board for new games
            self.update_board()
            # Time dialog will be handled by app.py after window creation

        self.setup_undo_button()

    def setup_timer(self):
        """Setup the chess timer component."""
        self.chess_timer = ChessTimer(self)
        self.chess_timer.time_expired.connect(self.on_time_expired)
        
        # Timer state
        self.is_time_mode = False
        self.white_time_ms = 0
        self.black_time_ms = 0

    def mode_display_name(self):
        names = {
            "human_ai": "Human vs AI",
            "human_human": "Human vs Human",
            "ai_ai": "AI vs AI",
        }
        return names.get(self.mode, self.mode)

    def color_name(self, color):
        return "White" if color == chess.WHITE else "Black"

    def ai_color(self):
        return not self.player_color

    def sync_turn_state(self):
        """Keep the legacy self.turn label in sync with python-chess board.turn."""
        if self.mode == "human_ai":
            self.turn = "human" if self.board.turn == self.player_color else "ai"
        elif self.mode == "human_human":
            self.turn = "human_white" if self.board.turn == chess.WHITE else "human_black"
        else:
            self.turn = "ai1" if self.board.turn == chess.WHITE else "ai2"

    def is_human_turn(self):
        if self.mode == "human_human":
            return True
        if self.mode == "human_ai":
            return self.board.turn == self.player_color
        return False

    def square_to_ui(self, square):
        file_index = chess.square_file(square)
        rank_index = chess.square_rank(square)
        if self.board_flipped:
            return (rank_index, 7 - file_index)
        return (7 - rank_index, file_index)

    def ui_to_square(self, row, col):
        if self.board_flipped:
            return chess.square(7 - col, row)
        return chess.square(col, 7 - row)

    def update_coordinate_labels(self):
        files = list("abcdefgh")
        ranks = [str(i) for i in range(8, 0, -1)]
        if self.board_flipped:
            files = list(reversed(files))
            ranks = list(reversed(ranks))
        for idx, label in enumerate(getattr(self, "file_labels", [])):
            label.setText(files[idx])
        for idx, label in enumerate(getattr(self, "rank_labels", [])):
            label.setText(ranks[idx])

    def toggle_board_orientation(self):
        self.board_flipped = not self.board_flipped
        self.update_board()

    def game_status_text(self):
        if self.board.is_checkmate():
            winner = self.color_name(not self.board.turn)
            return f"Checkmate - {winner} wins"
        if self.board.is_stalemate():
            return "Draw - stalemate"
        if self.board.is_insufficient_material():
            return "Draw - insufficient material"
        if self.board.is_fifty_moves():
            return "Draw - fifty-move rule"
        if self.board.is_repetition():
            return "Draw - repetition"
        if self.board.is_check():
            return f"Check - {self.color_name(self.board.turn)} to move"
        if self.board.is_game_over():
            return "Game over"
        return "Playing" if self.game_started else "Ready"

    def current_turn_text(self):
        color = self.color_name(self.board.turn)
        if self.mode == "human_ai":
            side = "You" if self.board.turn == self.player_color else "AI"
            return f"{color} ({side})"
        if self.mode == "human_human":
            return f"{color} player"
        return "AI 1 (White)" if self.board.turn == chess.WHITE else "AI 2 (Black)"

    def update_status_panel(self):
        if not hasattr(self, "control_panel"):
            return
        self.sync_turn_state()
        self.control_panel.mode_label.setText(f"Mode: {self.mode_display_name()}")
        self.control_panel.turn_label.setText(f"Turn: {self.current_turn_text()}")
        self.control_panel.status_label.setText(f"Status: {self.game_status_text()}")
        if self.mode == "human_ai":
            self.control_panel.color_label.setText(f"Human: {self.color_name(self.player_color)}")
        elif self.mode == "human_human":
            self.control_panel.color_label.setText("Human: both sides")
        else:
            self.control_panel.color_label.setText("Human: spectator")

    def configure_mode_controls(self):
        if self.mode == "human_ai":
            self.control_panel.set_human_ai_mode()
            self.control_panel.start_button.setText("Start Game")
            self.control_panel.pause_button.setText("Pause Game")
            self.thinking_indicator.show_status("Press 'Start Game' to begin")
        elif self.mode == "human_human":
            self.control_panel.set_human_human_mode()
            self.control_panel.start_button.setText("Start Game")
            self.control_panel.pause_button.setText("Pause Game")
            self.thinking_indicator.show_status("Press 'Start Game' to begin")
        else:
            self.control_panel.set_ai_ai_mode()
            self.control_panel.start_button.setText("Start AI Game")
            self.control_panel.pause_button.setText("Pause AI Game")
            self.thinking_indicator.show_status("Press 'Start AI Game' to begin")
        self.control_panel.difficulty_combo.setEnabled(self.mode != "human_human")
        self.update_status_panel()

    def switch_timer_to_board_turn(self):
        if self.is_time_mode:
            self.chess_timer.switch_player("white" if self.board.turn == chess.WHITE else "black")
    
    def setup_time_mode(self, enabled, white_time_ms, black_time_ms, white_inc_ms=3000, black_inc_ms=3000):
        """Setup time mode with specified settings including increments."""
        self.is_time_mode = enabled
        self.white_time_ms = white_time_ms
        self.black_time_ms = black_time_ms
        
        # Store increment values for smart time management
        from utils.config import Config
        self.white_increment_ms = white_inc_ms if white_inc_ms is not None else Config.DEFAULT_WHITE_INCREMENT_MS
        self.black_increment_ms = black_inc_ms if black_inc_ms is not None else Config.DEFAULT_BLACK_INCREMENT_MS
        
        if enabled:
            # Set player names based on game mode
            if self.mode == "human_ai":
                if self.player_color == chess.WHITE:
                    self.chess_timer.set_player_names("You (White)", "AI (Black)")
                else:
                    self.chess_timer.set_player_names("AI (White)", "You (Black)")
            elif self.mode == "human_human":
                self.chess_timer.set_player_names("White Player", "Black Player")
            else:
                self.chess_timer.set_player_names("AI 1 (White)", "AI 2 (Black)")
        
        self.chess_timer.set_time_mode(enabled, white_time_ms, black_time_ms)
            
    def on_time_expired(self, player):
        """Handle when a player's time expires."""
        self.chess_timer.stop_timer()
        
        # Determine the winner
        if player == 'white':
            winner_text = "Black wins on time!"
            result = '0-1'
        else:
            winner_text = "White wins on time!"
            result = '1-0'
        
        # Stop any ongoing AI processes
        if hasattr(self, 'ai_computation_active') and self.ai_computation_active:
            if hasattr(self, 'ai_worker') and self.ai_worker and self.ai_worker.isRunning():
                self.ai_worker.terminate()
                self.ai_worker = None
                self.ai_computation_active = False
        
        # Stop AI game if running
        if hasattr(self, 'ai_game_running') and self.ai_game_running:
            self.ai_game_running = False
            if hasattr(self, 'ai_timer') and self.ai_timer.isActive():
                self.ai_timer.stop()
        
        # Force the board into a game over state
        self.board.set_result(result)
        
        # Update the UI
        self.thinking_indicator.stop_thinking()
        self.thinking_indicator.show_status(f"Game Over - {winner_text}")
        
        # Show game over popup
        self.show_game_over_popup(custom_message=winner_text)
    
    def start_game(self):
        """Start the game - works for both Human vs AI and AI vs AI modes."""
        if self.mode == "human_ai":
            self.start_human_ai_game()
        elif self.mode == "human_human":
            self.start_human_human_game()
        else:
            self.start_ai_game()
    
    def start_human_ai_game(self):
        """Start Human vs AI game with timer support."""
        if not self.board.is_game_over():
            self.game_started = True
            self.sync_turn_state()
            # Update button states
            self.control_panel.start_button.setEnabled(False)
            self.control_panel.pause_button.setEnabled(True)
            
            # Start timer for current player if time mode is enabled
            if self.is_time_mode:
                current_player = 'white' if self.board.turn == chess.WHITE else 'black'
                self.chess_timer.start_timer(current_player)
            
            # Update status based on whose turn it is
            if self.is_human_turn():
                self.thinking_indicator.show_status("Your turn - Game Started!")
                # Clear status after 2 seconds
                QTimer.singleShot(2000, lambda: self.thinking_indicator.show_status("Your turn"))
            else:
                # If it's AI's turn, start AI immediately
                self.thinking_indicator.start_thinking("AI")
                QTimer.singleShot(100, self.ai_move)
            self.update_status_panel()

    def start_human_human_game(self):
        """Start local two-player mode without invoking the AI."""
        if not self.board.is_game_over():
            self.game_started = True
            self.sync_turn_state()
            self.control_panel.start_button.setEnabled(False)
            self.control_panel.pause_button.setEnabled(True)
            if self.is_time_mode:
                self.chess_timer.start_timer("white" if self.board.turn == chess.WHITE else "black")
            self.thinking_indicator.show_status(f"{self.color_name(self.board.turn)} to move")
            self.update_status_panel()

    def pause_human_ai_game(self):
        """Pause Human vs AI game."""
        self.game_started = False
        # Update button states
        self.control_panel.start_button.setEnabled(True)
        self.control_panel.pause_button.setEnabled(False)
        
        # Pause the chess timer
        if self.is_time_mode:
            self.chess_timer.pause_timer()
        
        # Stop any AI computation
        if hasattr(self, 'ai_manager'):
            self.ai_manager.cancel_computation()
        
        self.ai_computation_active = False
        self.thinking_indicator.stop_thinking()
        self.thinking_indicator.show_status("Game paused")

    def start_player_timer(self, player):
        """Start the timer for a specific player."""
        if self.is_time_mode:
            timer_player = self.timer_player_for_token(player)
            self.chess_timer.start_timer(timer_player)
    
    def switch_timer_to_player(self, player):
        """Switch the active timer to the specified player."""
        if self.is_time_mode:
            timer_player = self.timer_player_for_token(player)
            self.chess_timer.switch_player(timer_player)

    def timer_player_for_token(self, player):
        if self.mode == "human_ai":
            if player == "human":
                return "white" if self.player_color == chess.WHITE else "black"
            if player == "ai":
                return "black" if self.player_color == chess.WHITE else "white"
        if player in ["human_white", "ai1", "white"]:
            return "white"
        return "black"
    
    def pause_timer(self):
        """Pause the game timer."""
        if self.is_time_mode:
            self.chess_timer.pause_timer()
    
    def resume_timer(self):
        """Resume the game timer."""
        if self.is_time_mode:
            self.chess_timer.resume_timer()

    def save_game(self):
        """Save the current game state to a file with improved error handling and timer support"""
        try:
            # Pause the game if it's running
            was_running = self.ai_game_running
            if was_running:
                self.pause_ai_game()
            
            # Pause timer if active
            timer_was_active = False
            if self.is_time_mode and hasattr(self.chess_timer, 'update_timer'):
                timer_was_active = self.chess_timer.update_timer.isActive()
                self.chess_timer.pause_timer()
            
            # Prepare timer settings if in time mode - NOW WITH INCREMENTS
            timer_settings = None
            if self.is_time_mode:
                white_time_ms, black_time_ms = self.chess_timer.get_remaining_times()
                timer_settings = {
                    'enabled': True,
                    'initial_white_time_ms': self.white_time_ms,
                    'initial_black_time_ms': self.black_time_ms,
                    'white_time_ms': white_time_ms,
                    'black_time_ms': black_time_ms,
                    'active_player': self.chess_timer.active_player,
                    # Save increment values
                    'white_increment_ms': getattr(self, 'white_increment_ms', 3000),
                    'black_increment_ms': getattr(self, 'black_increment_ms', 3000)
                }
            
            # Call the SavedGameManager to save the game
            try:
                success, filepath = SavedGameManager.save_game(
                    self.board, 
                    self.mode, 
                    self.turn,
                    self.last_move_from,
                    self.last_move_to,
                    timer_settings=timer_settings,
                    player_color="white" if self.player_color == chess.WHITE else "black",
                    board_flipped=self.board_flipped
                )
                
                if success:
                    # Track the state at which the game was saved
                    self.last_saved_state = {
                        'fen': self.board.fen(),
                        'move_count': len(self.board.move_stack),
                        'timer_state': timer_settings
                    }
                    
                    filename = os.path.basename(filepath)
                    QMessageBox.information(self, "Game Saved", 
                                        f"Game successfully saved to {filename}")
                else:
                    if filepath is not None:  # User canceled
                        QMessageBox.warning(self, "Save Canceled", 
                                        "Game was not saved.")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", 
                                f"An error occurred while saving the game: {str(e)}")
                print(f"Error saving game: {str(e)}")
                traceback.print_exc()
            
            # Resume timer if it was active
            if timer_was_active and self.is_time_mode:
                self.chess_timer.resume_timer()
            
            # Resume the game if it was running
            if was_running:
                try:
                    self.start_ai_game()
                except Exception as e:
                    QMessageBox.warning(self, "Resuming Game", 
                                    f"Couldn't resume the game: {str(e)}\nClick Start to continue.")
                    print(f"Error resuming game: {str(e)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Critical Error", 
                            f"A critical error occurred: {str(e)}")
            print(f"Critical error in save_game: {str(e)}")
            traceback.print_exc()
        
    def load_game_state(self, game_data):
        """Load a saved game state with timer support including increments"""
        try:
            # Setup the board with the saved FEN position
            self.board = chess.Board(game_data['fen'])
            
            # Set the mode and turn
            self.mode = game_data['mode']
            self.turn = game_data['turn']
            loaded_color = game_data.get('player_color', 'white')
            self.player_color = chess.WHITE if loaded_color != "black" else chess.BLACK
            self.board_flipped = game_data.get(
                'board_flipped',
                self.mode == "human_ai" and self.player_color == chess.BLACK
            )
            self.game_started = True
            
            # Update bot positions to match loaded game
            if self.mode == "human_ai":
                self.ai_bot.set_position(fen=game_data['fen'])
            elif self.mode == "ai_ai":
                self.ai_bot1.set_position(fen=game_data['fen'])
                self.ai_bot2.set_position(fen=game_data['fen'])
            
            # Set the last move for highlighting
            self.last_move_from = game_data.get('last_move_from')
            self.last_move_to = game_data.get('last_move_to')
            
            # Load timer settings if available - NOW WITH INCREMENTS
            timer_settings = game_data.get('timer_settings')
            if timer_settings:
                self.is_time_mode = timer_settings.get('enabled', False)
                if self.is_time_mode:
                    white_time_ms = timer_settings.get('white_time_ms', 0)
                    black_time_ms = timer_settings.get('black_time_ms', 0)
                    self.white_time_ms = timer_settings.get('initial_white_time_ms', white_time_ms)
                    self.black_time_ms = timer_settings.get('initial_black_time_ms', black_time_ms)
                    
                    # Load increment values
                    self.white_increment_ms = timer_settings.get('white_increment_ms', 3000)
                    self.black_increment_ms = timer_settings.get('black_increment_ms', 3000)
                    
                    # Set player names based on game mode
                    if self.mode == "human_ai":
                        if self.player_color == chess.WHITE:
                            self.chess_timer.set_player_names("You (White)", "AI (Black)")
                        else:
                            self.chess_timer.set_player_names("AI (White)", "You (Black)")
                    elif self.mode == "human_human":
                        self.chess_timer.set_player_names("White Player", "Black Player")
                    else:
                        self.chess_timer.set_player_names("AI 1 (White)", "AI 2 (Black)")
                    
                    # Setup timer with current remaining times
                    self.chess_timer.set_time_mode(True, white_time_ms, black_time_ms)
                    self.chess_timer.white_time_ms = white_time_ms
                    self.chess_timer.black_time_ms = black_time_ms
                    
                    # Don't auto-start timer - let user decide when to resume
                    active_player = timer_settings.get('active_player')
                    if active_player:
                        self.chess_timer.active_player = active_player
                        self.chess_timer.update_active_player_display()
            
            # Rebuild move history
            self.move_history.clear_history()
            temp_board = chess.Board()
            for i, move_uci in enumerate(game_data['move_history']):
                move = chess.Move.from_uci(move_uci)
                from_square = chess.square_name(move.from_square)
                to_square = chess.square_name(move.to_square)
                piece = temp_board.piece_at(move.from_square)
                
                is_capture = temp_board.is_capture(move)
                is_check = False  # We'll determine this after making the move
                
                # Make the move on our temporary board
                temp_board.push(move)
                is_check = temp_board.is_check()
                
                # Determine if it's castling
                is_castling = (piece and piece.piece_type == chess.KING and 
                            abs(move.from_square % 8 - move.to_square % 8) > 1)
                
                # Add to move history
                self.move_history.add_move(
                    piece,
                    from_square,
                    to_square,
                    "White" if i % 2 == 0 else "Black",
                    is_capture,
                    is_check,
                    move.promotion,
                    is_castling
                )
            
            # Update the board display
            self.update_board()
            
            # Update status message
            self.configure_mode_controls()
            if self.mode in ("human_ai", "human_human"):
                self.thinking_indicator.show_status("Press 'Start Game' to resume")
            else:
                self.thinking_indicator.show_status("Press 'Start AI Game' to resume")
            self.update_status_panel()
            
            return True
        except Exception as e:
            print(f"Error loading game: {str(e)}")
            QMessageBox.critical(self, "Error", f"Could not load game: {str(e)}")
            return False
    
    def initialize_piece_symbols(self):
        """Create enhanced chess piece symbols with better visibility and style"""
        # Using filled/solid symbols for white pieces instead of outline versions
        piece_symbols = {
            (chess.PAWN, chess.WHITE): "♟︎",    # Solid white pawn
            (chess.PAWN, chess.BLACK): "♟",     # Black pawn
            (chess.KNIGHT, chess.WHITE): "♞︎",   # Solid white knight
            (chess.KNIGHT, chess.BLACK): "♞",    # Black knight
            (chess.BISHOP, chess.WHITE): "♝︎",   # Solid white bishop
            (chess.BISHOP, chess.BLACK): "♝",    # Black bishop
            (chess.ROOK, chess.WHITE): "♜︎",     # Solid white rook
            (chess.ROOK, chess.BLACK): "♜",      # Black rook
            (chess.QUEEN, chess.WHITE): "♛︎",    # Solid white queen
            (chess.QUEEN, chess.BLACK): "♛",     # Black queen
            (chess.KING, chess.WHITE): "♚︎",     # Solid white king
            (chess.KING, chess.BLACK): "♚",      # Black king
        }
        return piece_symbols
    
    def return_to_home(self):
        """Return to the start screen - MULTIPROCESS VERSION."""
        try:
            # Stop any AI computation first
            self.stop_thinking()
            
            # Force stop any running processes or timers
            if hasattr(self, 'ai_timer') and self.ai_timer.isActive():
                self.ai_timer.stop()
            
            # Stop chess timer
            if self.is_time_mode:
                self.chess_timer.stop_timer()
            
            # Cancel any AI manager processes
            if hasattr(self, 'ai_manager'):
                self.ai_manager.cancel_computation()
            
            # Reset flags
            self.ai_computation_active = False
            self.ai_game_running = False
    
            
            # Clean up any popup
            if hasattr(self, 'popup') and self.popup:
                try:
                    self.popup.close()
                    self.popup.deleteLater()
                except Exception as e:
                    print(f"Error closing popup: {str(e)}")
                finally:
                    self.popup = None
            
            # Track if we need to save game
            # Add this attribute to track when the game was last saved
            last_saved_state = getattr(self, 'last_saved_state', None)
            current_state = {
                'fen': self.board.fen(),
                'move_count': len(self.board.move_stack)
            }
            
            # Ask if user wants to save game only if it has changed since last save
            if not self.board.is_game_over() and len(self.board.move_stack) > 0 and current_state != last_saved_state:
                try:
                    reply = QMessageBox.question(
                        self, 
                        "Save Game", 
                        "Do you want to save your game before leaving?",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                    )
                    
                    if reply == QMessageBox.Yes:
                        try:
                            # Prepare timer settings if in time mode
                            timer_settings = None
                            if self.is_time_mode:
                                white_time_ms, black_time_ms = self.chess_timer.get_remaining_times()
                                timer_settings = {
                                    'enabled': True,
                                    'initial_white_time_ms': self.white_time_ms,
                                    'initial_black_time_ms': self.black_time_ms,
                                    'white_time_ms': white_time_ms,
                                    'black_time_ms': black_time_ms,
                                    'active_player': self.chess_timer.active_player
                                }
                            
                            success, _ = SavedGameManager.save_game(
                                self.board, 
                                self.mode, 
                                self.turn,
                                self.last_move_from,
                                self.last_move_to,
                                timer_settings=timer_settings,
                                player_color="white" if self.player_color == chess.WHITE else "black",
                                board_flipped=self.board_flipped
                            )
                            if success:
                                # Remember the state at which we saved
                                self.last_saved_state = current_state
                            if not success:
                                return  # Cancel the return to home if save was canceled
                        except Exception as e:
                            print(f"Error saving game: {str(e)}")
                            msgBox = QMessageBox.warning(
                                self, 
                                "Save Failed", 
                                f"Failed to save game: {str(e)}\n\nContinue returning home?",
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if msgBox == QMessageBox.No:
                                return
                    elif reply == QMessageBox.Cancel:
                        return  # Cancel the return to home
                except Exception as e:
                    print(f"Error during save prompt: {str(e)}")
            
            # Finally, return to home screen
            if self.parent_app:
                # Queue the show_start_screen call to happen after this event has finished processing
                QTimer.singleShot(0, self.parent_app.show_start_screen)
            
            # Close this window
            self.close()
            
        except Exception as e:
            print(f"Error in return_to_home: {str(e)}")
            # Force return to home even after error
            if self.parent_app:
                self.parent_app.show_start_screen()
                self.close()
        
    def update_move_speed(self, value):
        """Update the AI move animation speed based on depth."""
        # Convert depth to move delay (higher depth = slower moves)
        self.move_delay = 800  # Default value
        # No longer needed since we're using depth-based timing
    
    def update_ai_depth(self, value):
        """Update the AI thinking depth"""
        self.ai_depth = value
        self.control_panel.depth_value.setText(f"Current depth: {value}")

    def update_ai_difficulty(self, difficulty):
        """Map user-facing difficulty to search depth and time budget."""
        settings = {
            "Easy": (2, 2500),
            "Medium": (4, 6000),
            "Hard": (6, 12000),
        }
        self.ai_difficulty = difficulty
        self.ai_depth, self.ai_time_limit_ms = settings.get(difficulty, settings["Medium"])
        self.update_status_panel()
    
    def start_ai_game(self):
        """Start AI vs AI game with timer support."""
        if not self.ai_game_running and not self.board.is_game_over() and not self.ai_computation_active:
            self.game_started = True
            self.ai_game_running = True
            self.control_panel.start_button.setEnabled(False)
            self.control_panel.pause_button.setEnabled(True)
            self.turn = 'ai1' if self.board.turn == chess.WHITE else 'ai2'
            
            # Start timer for current player if time mode is enabled
            if self.is_time_mode:
                current_player = 'white' if self.turn == 'ai1' else 'black'
                self.chess_timer.start_timer(current_player)
            
            # Clear the status label and show thinking indicator
            self.thinking_indicator.show_status("")
            if self.turn == 'ai1':
                self.thinking_indicator.start_thinking("AI 1")
            else:
                self.thinking_indicator.start_thinking("AI 2")
            
            # Start the AI move timer
            self.ai_timer.start(self.move_delay)
            self.update_status_panel()
    
    def pause_ai_game(self):
        """Pause the AI vs AI game - MULTIPROCESS VERSION."""
        self.game_started = False
        self.ai_game_running = False
        self.ai_timer.stop()
        self.thinking_indicator.stop_thinking()
        
        # Pause the chess timer
        if self.is_time_mode:
            self.chess_timer.pause_timer()
        
        # Cancel any ongoing AI computation
        if hasattr(self, 'ai_manager'):
            self.ai_manager.cancel_computation()
        
        self.ai_computation_active = False
        self.control_panel.start_button.setEnabled(True)
        self.control_panel.pause_button.setEnabled(False)
        self.thinking_indicator.show_status("Game paused")
        self.update_status_panel()

    def reset_game(self):
        """Reset the game to initial state - with proper time dialog handling."""
        # Stop and cleanup AI processes first
        self.stop_thinking()
        
        self.ai_game_running = False
        self.ai_timer.stop()
        self.thinking_indicator.stop_thinking()
        
        # Stop and reset timer
        if self.is_time_mode:
            self.chess_timer.stop_timer()
        
        # Cancel any ongoing AI computation
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.terminate()
            self.ai_worker = None
            self.ai_computation_active = False
            
        self.board = chess.Board()
        self.board_flipped = self.mode == "human_ai" and self.player_color == chess.BLACK
        self.game_started = False
        
        # Reset bot positions
        if self.mode == "human_ai":
            self.ai_bot.set_position()  # Reset to starting position
            self.ai_bot.notify_new_game()  # Clear transposition tables
            self.turn = 'human' if self.board.turn == self.player_color else 'ai'
        elif self.mode == "ai_ai":
            self.ai_bot1.set_position()  # Reset to starting position
            self.ai_bot1.notify_new_game()
            self.ai_bot2.set_position()  # Reset to starting position
            self.ai_bot2.notify_new_game()
            self.turn = 'ai1'
        else:
            self.turn = 'human_white'
        
        self.control_panel.start_button.setEnabled(True)
        self.control_panel.pause_button.setEnabled(False)
        
        # Clear selection and move indicators
        self.selected_square = None
        self.valid_moves = []
        self.castling_moves = []
            
        self.last_move_from = None
        self.last_move_to = None
        self.move_history.clear_history()
        self.update_board()

        if hasattr(self, 'popup') and self.popup:
            self.popup.close()
            self.popup = None
        
        # Show time dialog and restart with new settings
        from ui.components.time_mode_dialog import TimeModeDialog
        
        def show_time_dialog_and_restart():
            try:
                time_dialog = TimeModeDialog(self)
                if time_dialog.exec_() == QDialog.Accepted:
                    # Get new time settings
                    is_time_mode, white_time_ms, black_time_ms, white_inc_ms, black_inc_ms = time_dialog.get_time_settings()
                    
                    # Apply new time settings
                    self.setup_time_mode(is_time_mode, white_time_ms, black_time_ms, white_inc_ms, black_inc_ms)
                    
                    # Start timer for current player if time mode enabled
                    if is_time_mode and self.mode in ("human_ai", "human_human"):
                        self.switch_timer_to_board_turn()
                    
                    # Set appropriate status
                    if self.mode in ("human_ai", "human_human"):
                        self.thinking_indicator.show_status("Press 'Start Game' to begin")
                    else:
                        self.thinking_indicator.show_status("Press 'Start AI Game' to begin")
                else:
                    # User canceled - just show status without time mode
                    if self.mode in ("human_ai", "human_human"):
                        self.thinking_indicator.show_status("Press 'Start Game' to begin")
                    else:
                        self.thinking_indicator.show_status("Press 'Start AI Game' to begin")
                        
            except Exception as e:
                print(f"Error in time dialog: {str(e)}")
                # Fallback to no time mode
                if self.mode in ("human_ai", "human_human"):
                    self.thinking_indicator.show_status("Press 'Start Game' to begin")
                else:
                    self.thinking_indicator.show_status("Press 'Start AI Game' to begin")
        
        # Show time dialog after UI updates
        QTimer.singleShot(200, show_time_dialog_and_restart)
    
    def animate_piece_movement(self, from_pos, to_pos, piece_symbol, piece_color, capture=False, callback=None):
        """Animate a piece between two board squares."""
        from_square = self.squares[from_pos[0]][from_pos[1]]
        to_square = self.squares[to_pos[0]][to_pos[1]]

        from_top_left = from_square.mapTo(self.central_widget, QPoint(0, 0))
        to_top_left = to_square.mapTo(self.central_widget, QPoint(0, 0))
        from_rect = QRect(from_top_left, from_square.size())
        to_rect = QRect(to_top_left, to_square.size())
        font_size = max(28, int(min(from_rect.width(), from_rect.height()) * 0.68))

        animated_piece = AnimatedLabel(self.central_widget)
        animated_piece.setText(piece_symbol)
        animated_piece.setAlignment(Qt.AlignCenter)
        animated_piece.setStyleSheet(f"""
            font-size: {font_size}px;
            background-color: transparent;
            color: {piece_color};
            font-weight: bold;
        """)
        animated_piece.setGeometry(from_rect)

        source_text = from_square.text()
        target_text = to_square.text() if capture else None
        from_square.setText("")
        if capture:
            to_square.setText("")

        animated_piece.raise_()
        animated_piece.show()

        animated_piece.animation.finished.connect(
            lambda: self.finish_animation(
                animated_piece,
                callback,
                from_square=from_square,
                to_square=to_square,
                source_text=source_text,
                target_text=target_text,
            )
        )

        self.animated_pieces[id(animated_piece)] = animated_piece
        animated_piece.move_to(to_rect)
    
    def finish_animation(
        self,
        animated_piece,
        callback=None,
        from_square=None,
        to_square=None,
        source_text=None,
        target_text=None,
    ):
        """Clean up a movement overlay and continue the move flow."""
        animated_piece.hide()
        self.animated_pieces.pop(id(animated_piece), None)
        try:
            if callback:
                callback()
            else:
                if from_square is not None and source_text is not None:
                    from_square.setText(source_text)
                if to_square is not None and target_text is not None:
                    to_square.setText(target_text)
        finally:
            animated_piece.deleteLater()
    
    def ai_vs_ai_step(self):
        """Execute a single step in the AI vs AI game with smart time management."""
        if self.ai_game_running and not self.board.is_game_over() and not self.ai_computation_active:
            # Set flag to prevent overlapping computations
            self.ai_computation_active = True
            
            # Determine current player
            current_ai = "AI 1" if self.turn == 'ai1' else "AI 2"
            
            # Update thinking indicator
            self.thinking_indicator.start_thinking(current_ai)
            
            # Stop the AI timer during calculation
            self.ai_timer.stop()
            
            # Get current board state
            board_fen = self.board.fen()
            
            # Prepare time management parameters
            from utils.config import Config
            
            if self.is_time_mode:
                # Get current time remaining for both players
                white_time_ms, black_time_ms = self.chess_timer.get_remaining_times()
                # Use stored increment values
                white_inc_ms = getattr(self, 'white_increment_ms', Config.DEFAULT_WHITE_INCREMENT_MS)
                black_inc_ms = getattr(self, 'black_increment_ms', Config.DEFAULT_BLACK_INCREMENT_MS)
                max_time_ms = self.ai_time_limit_ms
            else:
                # No time control - use fixed time
                white_time_ms = black_time_ms = None
                white_inc_ms = black_inc_ms = None
                max_time_ms = self.ai_time_limit_ms
            
            # Define callbacks
            def on_ai_move_ready(move_uci):
                """Called when AI finds a move."""
                self.ai_computation_active = False
                if move_uci:
                    self.handle_ai_move_result(move_uci)
                else:
                    self.handle_ai_vs_ai_error("AI could not find a valid move")
            
            def on_ai_error(error_msg):
                """Called when AI has an error."""
                print(f"AI vs AI Error: {error_msg}")
                self.ai_computation_active = False
                self.handle_ai_vs_ai_error(error_msg)
            
            # Start AI computation with smart time management
            self.ai_manager.compute_move(
                board_fen=board_fen,
                depth=self.ai_depth,
                time_ms=max_time_ms,
                on_finished=on_ai_move_ready,
                on_error=on_ai_error,
                white_time_ms=white_time_ms,
                black_time_ms=black_time_ms,
                white_inc_ms=white_inc_ms,
                black_inc_ms=black_inc_ms
            )
        
    def handle_ai_vs_ai_error(self, error_message):
        """Handle AI vs AI computation errors."""
        print(f"AI vs AI Error: {error_message}")
        self.ai_computation_active = False
        self.thinking_indicator.stop_thinking()
        
        # Try to continue with a random move
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            import random
            move = random.choice(legal_moves)
            self.handle_ai_move_result(move.uci())
        else:
            # No legal moves - game should be over
            self.ai_game_running = False
            if self.is_time_mode:
                self.chess_timer.stop_timer()
            self.thinking_indicator.show_status("No legal moves available")
    
    def handle_ai_move_result(self, best_move_uci):
        """Handle the result from the AI computation thread with timer support."""
        # Reset the AI computation flag
        self.ai_computation_active = False
        
        if not self.ai_game_running:
            return
                
        if best_move_uci:
            try:
                # Convert the move to chess.Move object
                move = chess.Move.from_uci(best_move_uci)
                
                from_pos = self.square_to_ui(move.from_square)
                to_pos = self.square_to_ui(move.to_square)
                
                # Get the piece information
                piece = self.board.piece_at(move.from_square)
                if piece is None:
                    print(f"Error: No piece found at {move.from_square}")
                    self.thinking_indicator.stop_thinking()
                    self.ai_game_running = False
                    if self.is_time_mode:
                        self.chess_timer.stop_timer()
                    self.control_panel.start_button.setEnabled(True)
                    self.control_panel.pause_button.setEnabled(False)
                    self.thinking_indicator.show_status("Invalid move: No piece found")
                    return
                    
                piece_color = "#FFFFFF" if piece.color == chess.WHITE else "#000000"
                
                # Determine piece symbol for animation
                piece_symbol = self.piece_symbols.get((piece.piece_type, piece.color), "")
                
                # Check if move is a capture
                is_capture = self.board.is_capture(move)
                
                # Check if move is castling
                is_castling = piece and piece.piece_type == chess.KING and abs(move.from_square % 8 - move.to_square % 8) > 1
                
                # Stop thinking indicator during animation
                self.thinking_indicator.stop_thinking()
                
                # Switch timer to next player
                next_turn = 'ai2' if self.turn == 'ai1' else 'ai1'
                if self.is_time_mode:
                    next_player = 'black' if next_turn == 'ai2' else 'white'
                    self.chess_timer.switch_player(next_player)
                
                # Function to execute after animation completes
                def after_animation():
                    try:
                        # Make the move on the actual board
                        self.board.push(move)
                        
                        # Update the appropriate bot's position
                        if self.turn == 'ai1':
                            self.ai_bot1.make_move(move.uci())
                        else:
                            self.ai_bot2.make_move(move.uci())
                        
                        self.apply_time_increment(self.turn)
                        
                        # Add move to history
                        from_uci = chess.square_name(move.from_square)
                        to_uci = chess.square_name(move.to_square)
                        is_check = self.board.is_check()
                        
                        self.move_history.add_move(
                            piece, 
                            from_uci, 
                            to_uci, 
                            "White" if piece.color == chess.WHITE else "Black",
                            is_capture,
                            is_check,
                            move.promotion,
                            is_castling
                        )
                        
                        # Update the board display
                        self.last_move_from = from_pos
                        self.last_move_to = to_pos
                        self.update_board()
                        
                        # Check if game is over
                        if self.board.is_game_over():
                            self.ai_game_running = False
                            if self.is_time_mode:
                                self.chess_timer.stop_timer()
                            self.control_panel.start_button.setEnabled(False)
                            self.control_panel.pause_button.setEnabled(False)
                            self.show_game_over_popup()
                        else:
                            # Switch to next AI
                            self.turn = next_turn
                            
                            # Update status text
                            next_ai = "AI 1" if self.turn == 'ai1' else "AI 2"
                            self.thinking_indicator.start_thinking(next_ai)
                            self.thinking_indicator.show_status("")
                            
                            # Resume the AI timer for next move
                            self.ai_timer.start(self.move_delay)
                    except Exception as e:
                        print(f"Error in after_animation: {str(e)}")
                        self.ai_game_running = False
                        if self.is_time_mode:
                            self.chess_timer.stop_timer()
                        self.thinking_indicator.stop_thinking()
                        self.thinking_indicator.show_status(f"Error: {str(e)}")
                
                # Animate the piece movement
                self.animate_piece_movement(from_pos, to_pos, piece_symbol, piece_color, is_capture, after_animation)
            except Exception as e:
                print(f"Error handling AI move: {str(e)}")
                self.ai_game_running = False
                if self.is_time_mode:
                    self.chess_timer.stop_timer()
                self.thinking_indicator.stop_thinking()
                self.control_panel.start_button.setEnabled(True)
                self.control_panel.pause_button.setEnabled(False)
                self.thinking_indicator.show_status(f"Error: {str(e)}")
        else:
            # No valid move found
            self.ai_game_running = False
            if self.is_time_mode:
                self.chess_timer.stop_timer()
            self.thinking_indicator.stop_thinking()
            self.control_panel.start_button.setEnabled(True)
            self.control_panel.pause_button.setEnabled(False)
            self.thinking_indicator.show_status("No valid moves available")
    
    def find_valid_moves(self, from_square):
        """Find all valid moves for a piece on the given square"""
        valid_moves = []
        castling_moves = []
        from_square_index = chess.parse_square(from_square)
        
        piece = self.board.piece_at(from_square_index)
        
        for move in self.board.legal_moves:
            if move.from_square == from_square_index:
                # Identify castling moves for special highlighting
                if piece and piece.piece_type == chess.KING and abs(move.from_square % 8 - move.to_square % 8) > 1:
                    castling_moves.append(move)
                else:
                    valid_moves.append(move)
                
        return valid_moves, castling_moves

    def _refresh_eval_and_captured(self):
        """Cập nhật thanh lượng giá và danh sách quân đã bị ăn."""
        # ── Evaluation bar ────────────────────────────────────────────────
        try:
            if not self.board.is_game_over():
                raw = self._evaluator.evaluate(self.board)
                # evaluate() trả về điểm từ góc nhìn của bên đang đi.
                # Ta muốn: dương = lợi thế Trắng, âm = lợi thế Đen.
                score_white_pov = raw if self.board.turn == chess.WHITE else -raw
                # Clamp về pawn units (1 pawn = 100 cp), giới hạn ±10 pawn
                pawn_score = max(-10.0, min(10.0, score_white_pov / 100.0))
                self.eval_bar.set_evaluation(pawn_score)
            else:
                result = self.board.result()
                self.eval_bar.set_evaluation(10.0 if result == "1-0" else
                                             -10.0 if result == "0-1" else 0.0)
        except Exception as e:
            print(f"Eval bar error: {e}")

        # ── Captured pieces (hiển thị trong move history header) ──────────
        try:
            self.move_history.update_captured(self.board)
        except Exception as e:
            print(f"Captured pieces error: {e}")

    def update_board(self):
        """Update the visual representation of the chess board"""
        self.update_coordinate_labels()
        self._refresh_eval_and_captured()
        self.update_status_panel()

        selected = chess.parse_square(self.selected_square) if self.selected_square else None
        valid_destinations = [move.to_square for move in self.valid_moves]
        castling_destinations = [move.to_square for move in self.castling_moves]
        
        # Check if kings are in check
        white_king_in_check = False
        black_king_in_check = False
        
        if self.board.is_check():
            white_king_in_check = self.board.turn == chess.WHITE
            black_king_in_check = self.board.turn == chess.BLACK
        
        # Find king squares
        white_king_square = None
        black_king_square = None
        
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece and piece.piece_type == chess.KING:
                if piece.color == chess.WHITE:
                    white_king_square = sq
                else:
                    black_king_square = sq

        for i in range(8):
            for j in range(8):
                square = self.ui_to_square(i, j)
                piece = self.board.piece_at(square)
                square_widget = self.squares[i][j]

                # Reset states
                square_widget.is_selected = False
                square_widget.is_last_move = False
                square_widget.is_valid_move = False
                square_widget.is_castling_move = False
                square_widget.is_checked = False
                
                # Set states based on game state
                if selected == square:
                    square_widget.is_selected = True
                if (i, j) == self.last_move_from or (i, j) == self.last_move_to:
                    square_widget.is_last_move = True
                if square in valid_destinations:
                    square_widget.is_valid_move = True
                if square in castling_destinations:
                    square_widget.is_castling_move = True
                    
                # Highlight king in check
                if (white_king_in_check and square == white_king_square) or \
                (black_king_in_check and square == black_king_square):
                    square_widget.is_checked = True
                    
                # Update the square appearance before setting text
                square_widget.update_appearance()
                
                # Draw piece or empty square
                if piece:
                    symbol = self.piece_symbols.get((piece.piece_type, piece.color), "")
                    piece_color = "#000000" if piece.color == chess.BLACK else "#FFFFFF"
                    
                    # Ensure king is visible even when checked
                    square_widget.setText(symbol)
                    
                    # Use a special style for the king when in check
                    if square_widget.is_checked and piece.piece_type == chess.KING:
                        # Make king clearly visible against the check highlight
                        square_widget.setStyleSheet(square_widget.styleSheet() + f"""
                            font-size: 40px; 
                            color: {piece_color};
                            font-weight: bold;
                            margin: 2px;
                            background-color: transparent;
                        """)
                    else:
                        square_widget.setStyleSheet(square_widget.styleSheet() + f"""
                            font-size: 40px; 
                            color: {piece_color};
                            font-weight: bold;
                        """)
                else:
                    square_widget.setText("")
                    


        # Check for game over
        if self.board.is_game_over():
            result = self.board.result()
            if result == '1-0':
                winner = "Player (White)" if self.mode == "human_ai" else "AI 1 (White)"
                self.thinking_indicator.show_status(f"{winner} Wins!")
            elif result == '0-1':
                winner = "AI (Black)" if self.mode == "human_ai" else "AI 2 (Black)"
                self.thinking_indicator.show_status(f"{winner} Wins!")
            else:
                self.thinking_indicator.show_status("It's a Draw!")
            
            # Stop the AI game if running
            if self.ai_game_running:
                self.ai_game_running = False
                self.ai_timer.stop()
                self.thinking_indicator.stop_thinking()
                if self.ai_worker and self.ai_worker.isRunning():
                    self.ai_worker.terminate()
                    self.ai_worker = None
                    self.ai_computation_active = False
                    
                self.control_panel.start_button.setEnabled(False)
                self.control_panel.pause_button.setEnabled(False)
                self.show_game_over_popup()
        else:
            # Status update based on game mode and state
            if self.mode == "human_ai":
                if self.turn == 'human':
                    self.thinking_indicator.show_status("Your turn")
                else:
                    # Don't update status here for AI turn, let the AI move function handle it
                    pass
            else:  # AI vs AI mode
                if self.ai_game_running:
                    # Status is handled by the thinking indicator
                    pass
                else:
                    # Game not running, show start message
                    if self.turn == 'ai1':
                        self.thinking_indicator.show_status("Press 'Start' to begin AI vs AI game")
                    else:
                        self.thinking_indicator.show_status("Press 'Start' to continue AI vs AI game")

    def player_move(self, i, j):
        """Handle player move selection with timer support."""
        if (
            self.mode not in ("human_ai", "human_human") or
            not self.game_started or
            not self.is_human_turn() or
            self.board.is_game_over() or
            self.ai_computation_active
        ):
            return
            
        square = self.ui_to_square(i, j)
        current_square = chess.SQUARE_NAMES[square]

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = current_square
                self.valid_moves, self.castling_moves = self.find_valid_moves(current_square)
                self.update_board()
        else:
            if self.selected_square == current_square:
                self.selected_square = None
                self.valid_moves = []
                self.castling_moves = []
                self.update_board()
                return
                
            move_made = False
            
            # Check both regular and castling moves
            all_valid_moves = self.valid_moves + self.castling_moves
            
            for move in all_valid_moves:
                if move.to_square == square:
                    from_square = chess.parse_square(self.selected_square)
                    piece = self.board.piece_at(from_square)
                    
                    # Handle pawn promotion
                    is_promotion = (piece and piece.piece_type == chess.PAWN and
                                (chess.square_rank(square) == 0 or chess.square_rank(square) == 7))

                    if is_promotion:
                        try:
                            promotion_color = "white" if piece.color == chess.WHITE else "black"
                            dialog = PawnPromotionDialog(promotion_color, self)
                            if dialog.exec_() == QDialog.Accepted:
                                promotion_piece = dialog.get_choice()
                                move = chess.Move(from_square, square, 
                                                promotion=chess.Piece.from_symbol(promotion_piece.upper()).piece_type)
                            else:
                                # User canceled, don't make the move
                                self.selected_square = None
                                self.valid_moves = []
                                self.castling_moves = []
                                self.update_board()
                                return
                        except Exception as e:
                            print(f"Error in pawn promotion: {str(e)}")
                            # Default to queen promotion if error
                            move = chess.Move(from_square, square, promotion=chess.QUEEN)
                    
                    # Check if move is castling
                    is_castling = piece and piece.piece_type == chess.KING and abs(move.from_square % 8 - move.to_square % 8) > 1
                    
                    # Get animation info
                    from_pos = self.square_to_ui(from_square)
                    to_pos = self.square_to_ui(square)
                    
                    # Determine piece symbol for animation
                    piece_symbol = self.piece_symbols.get((piece.piece_type, piece.color), "")
                    piece_color = "#FFFFFF" if piece.color == chess.WHITE else "#000000"
                    is_capture = self.board.is_capture(move)
                    
                    # Reset selection
                    self.selected_square = None
                    self.valid_moves = []
                    self.castling_moves = []
                    
                    moving_color = piece.color
                    
                    # Animate move
                    def after_player_move():
                        # Execute move on the board
                        self.board.push(move)
                        
                        if self.mode == "human_ai":
                            self.ai_bot.make_move(move.uci())
                        
                        increment_token = (
                            "human_white" if moving_color == chess.WHITE else "human_black"
                        ) if self.mode == "human_human" else "human"
                        self.apply_time_increment(increment_token)
                        
                        # Add to move history
                        from_uci = chess.square_name(from_square)
                        to_uci = chess.square_name(square)
                        is_check = self.board.is_check()
                        
                        self.move_history.add_move(
                            piece, 
                            from_uci, 
                            to_uci, 
                            self.color_name(moving_color),
                            is_capture,
                            is_check,
                            move.promotion if is_promotion else None,
                            is_castling
                        )
                        
                        # Update last move highlighting
                        self.last_move_from = from_pos
                        self.last_move_to = to_pos
                        
                        # Update board display
                        self.update_board()
                        
                        # Check if game is over
                        if not self.board.is_game_over():
                            self.sync_turn_state()
                            self.switch_timer_to_board_turn()
                            if self.mode == "human_ai":
                                self.thinking_indicator.start_thinking("AI")
                                QTimer.singleShot(100, self.ai_move)
                            else:
                                self.thinking_indicator.show_status(f"{self.color_name(self.board.turn)} to move")
                        else:
                            if self.is_time_mode:
                                self.chess_timer.stop_timer()
                            self.show_game_over_popup()
                        self.update_status_panel()
                    
                    # Start animation
                    self.animate_piece_movement(from_pos, to_pos, piece_symbol, piece_color, is_capture, after_player_move)
                    move_made = True
                    break
            
            if not move_made:
                # If clicking another piece of the same color, select it instead
                piece = self.board.piece_at(square)
                if piece and piece.color == self.board.turn:
                    self.selected_square = current_square
                    self.valid_moves, self.castling_moves = self.find_valid_moves(current_square)
                else:
                    # Invalid move - deselect
                    self.valid_moves = []
                    self.castling_moves = []
                    self.selected_square = None
                
                self.update_board()

    def ai_move(self):
        """Calculate and execute the AI's move using smart time management."""
        try:
            # Check if game is already over
            if self.board.is_game_over():
                self.thinking_indicator.stop_thinking()
                if self.is_time_mode:
                    self.chess_timer.stop_timer()
                self.show_game_over_popup()
                return
            if self.mode == "human_ai" and self.board.turn == self.player_color:
                self.ai_computation_active = False
                return

            # Set flag to prevent overlapping AI computations
            self.ai_computation_active = True
            
            # Update status with thinking animation
            self.thinking_indicator.start_thinking("AI")
            
            # Get current board state
            board_fen = self.board.fen()
            
            # Prepare time management parameters
            from utils.config import Config
            
            if self.is_time_mode:
                # Get current time remaining for both players
                white_time_ms, black_time_ms = self.chess_timer.get_remaining_times()
                # Use stored increment values
                white_inc_ms = getattr(self, 'white_increment_ms', Config.DEFAULT_WHITE_INCREMENT_MS)
                black_inc_ms = getattr(self, 'black_increment_ms', Config.DEFAULT_BLACK_INCREMENT_MS)
                max_time_ms = self.ai_time_limit_ms
            else:
                # No time control - use fixed time
                white_time_ms = black_time_ms = None
                white_inc_ms = black_inc_ms = None
                max_time_ms = self.ai_time_limit_ms
            
            # Define callbacks that will run on UI thread
            def on_ai_move_ready(move_uci):
                """Called when AI finds a move - runs on UI thread."""
                self.ai_computation_active = False
                if move_uci:
                    self.handle_human_ai_move_result(move_uci)
                else:
                    self.handle_ai_error("AI could not find a valid move")
            
            def on_ai_error(error_msg):
                """Called when AI has an error - runs on UI thread."""
                print(f"AI Error: {error_msg}")
                self.ai_computation_active = False
                self.handle_ai_error(error_msg)
            
            def on_ai_progress(percent):
                """Called to update progress - runs on UI thread."""
                # Keep thinking indicator active
                if percent > 0 and not self.thinking_indicator.timer.isActive():
                    self.thinking_indicator.start_thinking("AI")
            
            # Start AI computation with smart time management
            self.ai_manager.compute_move(
                board_fen=board_fen,
                depth=self.ai_depth,
                time_ms=max_time_ms,
                on_finished=on_ai_move_ready,
                on_error=on_ai_error,
                on_progress=on_ai_progress,
                white_time_ms=white_time_ms,
                black_time_ms=black_time_ms,
                white_inc_ms=white_inc_ms,
                black_inc_ms=black_inc_ms
            )
            
            print("AI computation started with smart time management - UI remains responsive!")
            
        except Exception as e:
            self.thinking_indicator.stop_thinking()
            self.ai_computation_active = False
            self.thinking_indicator.show_status(f"Error starting AI move: {str(e)}")
        
    def handle_ai_error(self, error_message):
        """Handle AI computation errors without crashing the game."""
        print(f"AI Error: {error_message}")
        self.ai_computation_active = False
        self.thinking_indicator.stop_thinking()
        
        # Don't crash the game - make a random legal move instead
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            import random
            move = random.choice(legal_moves)
            # Simulate the move result
            self.handle_human_ai_move_result(move.uci())
        else:
            self.thinking_indicator.show_status("No legal moves available")
            if self.is_time_mode:
                self.switch_timer_to_board_turn()
    
    def update_ai_progress(self, progress):
        """Update AI thinking progress (optional visual feedback)."""
        # You could update a progress bar here if desired
        # For now, just ensure the thinking indicator is still active
        if progress > 0 and not self.thinking_indicator.timer.isActive():
            self.thinking_indicator.start_thinking("AI")
    
    def handle_human_ai_move_result(self, best_move_uci):
        """Handle the result of AI computation for human vs AI mode with timer support."""
        # Reset the AI computation flag
        self.ai_computation_active = False
        
        try:
            if best_move_uci:
                move = chess.Move.from_uci(best_move_uci)
                
                # Get animation info
                from_square = move.from_square
                to_square = move.to_square
                piece = self.board.piece_at(from_square)
                
                if piece is None:
                    print(f"Error: No piece found at {from_square}")
                    self.thinking_indicator.stop_thinking()
                    self.sync_turn_state()
                    if self.is_time_mode:
                        self.switch_timer_to_board_turn()
                    self.thinking_indicator.show_status("AI made an invalid move. Your turn.")
                    return
                    
                from_pos = self.square_to_ui(from_square)
                to_pos = self.square_to_ui(to_square)
                
                # Determine piece symbol and color for animation
                piece_symbol = self.piece_symbols.get((piece.piece_type, piece.color), "")
                piece_color = "#FFFFFF" if piece.color == chess.WHITE else "#000000"
                is_capture = self.board.is_capture(move)
                
                # Check if move is castling
                is_castling = piece and piece.piece_type == chess.KING and abs(move.from_square % 8 - move.to_square % 8) > 1
                
                # Stop thinking indicator during animation
                self.thinking_indicator.stop_thinking()
                
                # Animate the move
                def after_ai_move():
                    try:
                        # Execute move on the board
                        self.board.push(move)
                        
                        # Update bot's position to keep it in sync
                        if self.mode == "human_ai":
                            self.ai_bot.make_move(move.uci())
                            
                        self.apply_time_increment('ai')
                        
                        # Add to move history
                        from_uci = chess.square_name(from_square)
                        to_uci = chess.square_name(to_square)
                        is_check = self.board.is_check()
                        
                        self.move_history.add_move(
                            piece, 
                            from_uci, 
                            to_uci, 
                            self.color_name(piece.color),
                            is_capture,
                            is_check,
                            move.promotion,
                            is_castling
                        )
                        
                        # Update last move highlighting
                        self.last_move_from = from_pos
                        self.last_move_to = to_pos
                        
                        # Update board and switch back to human's turn
                        self.update_board()
                        self.sync_turn_state()
                        if self.is_time_mode:
                            self.switch_timer_to_board_turn()

                        self.thinking_indicator.stop_thinking()
                        if not self.board.is_game_over():
                            self.thinking_indicator.show_status("Your turn")
                        
                        # Check if game is over
                        if self.board.is_game_over():
                            if self.is_time_mode:
                                self.chess_timer.stop_timer()
                            self.show_game_over_popup()
                    except Exception as e:
                        print(f"Error after AI move: {str(e)}")
                        self.sync_turn_state()
                        if self.is_time_mode:
                            self.switch_timer_to_board_turn()
                        self.thinking_indicator.show_status("Your turn")
                
                # Start animation
                self.animate_piece_movement(from_pos, to_pos, piece_symbol, piece_color, is_capture, after_ai_move)
            else:
                self.thinking_indicator.stop_thinking()
                self.thinking_indicator.show_status("AI could not find a valid move! Your turn.")
                self.sync_turn_state()
                if self.is_time_mode:
                    self.switch_timer_to_board_turn()
        except Exception as e:
            print(f"Error in handle_human_ai_move_result: {str(e)}")
            self.thinking_indicator.stop_thinking()
            self.thinking_indicator.show_status("AI error. Your turn.")
            self.sync_turn_state()
            if self.is_time_mode:
                self.switch_timer_to_board_turn()

    def show_game_over_popup(self, custom_message=None):
        """Show a simple game over popup with retry and home options."""
        try:
            # Delete any existing popup first
            if hasattr(self, 'popup') and self.popup:
                self.popup.close()
                self.popup = None
                    
            result = self.board.result()
            
            # Create the new simplified popup
            title = custom_message or self.game_status_text()
            self.popup = GameOverPopup(title, result, self)
            
            # Connect signals
            self.popup.play_again_signal.connect(self.reset_game)
            self.popup.return_home_signal.connect(self.return_to_home)
            
            # Show the popup
            self.popup.exec_()
            
        except Exception as e:
            print(f"Error showing game over popup: {str(e)}")
            # If the popup fails, at least update the status
            self.thinking_indicator.show_status("Game Over!")
    
    def stop_thinking(self):
        """Stop any ongoing AI computation - MULTIPROCESS VERSION."""
        # Cancel any active AI computation
        if hasattr(self, 'ai_manager'):
            self.ai_manager.cancel_computation()
        
        # Reset flags
        self.ai_computation_active = False
        
        # Stop thinking indicator
        if hasattr(self, 'thinking_indicator'):
            self.thinking_indicator.stop_thinking()

    def close_game(self):
        """Close the game window"""
        self.close()
    
    def apply_time_increment(self, player_who_moved):
        """
        Apply time increment after a player makes a move.
        
        Args:
            player_who_moved (str): The player who just made a move ('human', 'ai', 'ai1', 'ai2')
        """
        if not self.is_time_mode:
            return
            
        try:
            # Determine which timer to increment based on game mode and player
            if self.mode == "human_ai":
                moved_color = self.player_color if player_who_moved == 'human' else self.ai_color()
                if moved_color == chess.WHITE:
                    increment = getattr(self, 'white_increment_ms', 3000)
                    self.chess_timer.white_time_ms += increment
                else:
                    increment = getattr(self, 'black_increment_ms', 3000)
                    self.chess_timer.black_time_ms += increment
                print(f"Added {increment}ms increment to {self.color_name(moved_color)}")
            elif self.mode == "human_human":
                moved_color = chess.WHITE if player_who_moved in ("human_white", "white") else chess.BLACK
                if moved_color == chess.WHITE:
                    increment = getattr(self, 'white_increment_ms', 3000)
                    self.chess_timer.white_time_ms += increment
                else:
                    increment = getattr(self, 'black_increment_ms', 3000)
                    self.chess_timer.black_time_ms += increment
                print(f"Added {increment}ms increment to {self.color_name(moved_color)}")
            else:  # AI vs AI mode
                if player_who_moved == 'ai1':
                    # AI1 (White) gets white increment
                    increment = getattr(self, 'white_increment_ms', 3000)
                    self.chess_timer.white_time_ms += increment
                    print(f"Added {increment}ms increment to AI1 player")
                elif player_who_moved == 'ai2':
                    # AI2 (Black) gets black increment
                    increment = getattr(self, 'black_increment_ms', 3000)
                    self.chess_timer.black_time_ms += increment
                    print(f"Added {increment}ms increment to AI2 player")
                    
            # Update the timer display to show the new times
            self.chess_timer.update_display()
            
        except Exception as e:
            print(f"Error applying time increment: {str(e)}")
    
    def resizeEvent(self, event):
        """Handle window resize events to ensure proper layout - OPTIMIZED FOR FULLSCREEN"""
        super().resizeEvent(event)
        
        # Get current window width
        window_width = self.width()
        
        # For fullscreen or large screens
        if window_width >= 1200:
            # Large screens: give board 70-75%, sidebar 25-30%
            board_portion = int(window_width * 0.72)
            sidebar_portion = int(window_width * 0.28)
        elif window_width >= 900:
            # Medium screens: adjust proportionally
            board_portion = int(window_width * 0.7)
            sidebar_portion = int(window_width * 0.3)
        else:
            # Smaller screens: ensure sidebar is usable
            board_portion = int(window_width * 0.68)
            sidebar_portion = int(window_width * 0.32)
        
        # Ensure minimum sidebar width (280px)
        if sidebar_portion < 280:
            sidebar_portion = 280
            board_portion = window_width - sidebar_portion - 20  # Account for splitter handle
        
        # Ensure board portion is at least 400px
        if board_portion < 400:
            board_portion = 400
            sidebar_portion = window_width - board_portion - 20
        
        # Apply the new sizes
        self.main_splitter.setSizes([board_portion, sidebar_portion])
    
    def setup_undo_button(self):
        """Set up the undo button and resign button - call this method from __init__"""
        # Import here to avoid circular imports
        from ui.components.controls import UndoButton, ResignButton
        
        # Create undo button
        self.undo_button = UndoButton(self)
        self.undo_button.clicked.connect(self.undo_move)

        if hasattr(self.control_panel, 'undo_button_layout'):
            self.control_panel.undo_button_layout.addWidget(self.undo_button)
            if hasattr(self.control_panel, 'resign_button'):
                self.control_panel.resign_button.clicked.connect(self.resign_game)
            return True
        
        # Add button to control panel - find the right layout
        try:
            # Find button container in the control panel
            for i in range(self.control_panel.widget().layout().count()):
                item = self.control_panel.widget().layout().itemAt(i)
                if isinstance(item, QHBoxLayout):
                    # Check if this is the responsive layout
                    for j in range(item.count()):
                        subitem = item.itemAt(j)
                        if isinstance(subitem.widget(), QWidget) and subitem.widget().layout() and isinstance(subitem.widget().layout(), QVBoxLayout):
                            # This should be the button container
                            button_layout = subitem.widget().layout()
                            # Insert undo button at a good position (before reset)
                            button_layout.insertWidget(2, self.undo_button)  # Adjust index as needed
                            
                            # Connect resign button if it exists
                            for k in range(button_layout.count()):
                                btn_item = button_layout.itemAt(k)
                                if btn_item and isinstance(btn_item.widget(), ResignButton):
                                    btn_item.widget().clicked.connect(self.resign_game)
                                    return True
                            return True
            
            # Fallback in case layout structure is different
            print("Couldn't find expected layout structure, using fallback method")
            if hasattr(self.control_panel, 'main_layout'):
                self.control_panel.main_layout.addWidget(self.undo_button)
                
                # Try to find and connect the resign button
                if hasattr(self.control_panel, 'resign_button'):
                    self.control_panel.resign_button.clicked.connect(self.resign_game)
                return True
                
            return False
        except Exception as e:
            print(f"Error adding undo button: {e}")
            return False

    def undo_move(self):
        """Undo the last move made in the game with improved turn tracking"""
        try:
            if len(self.board.move_stack) == 0:
                self.thinking_indicator.show_status("No moves to undo")
                return

            if hasattr(self, 'ai_manager'):
                self.ai_manager.cancel_computation()
            self.ai_computation_active = False

            def pop_one_move():
                self.board.pop()
                self.update_move_history_after_undo()

            pop_one_move()

            # In Human vs AI, undo until it is the human's turn again.
            if self.mode == "human_ai":
                while len(self.board.move_stack) > 0 and self.board.turn != self.player_color:
                    pop_one_move()
                self.ai_bot.set_position(fen=self.board.fen())
            elif self.mode == "ai_ai":
                if hasattr(self, 'ai_game_running') and self.ai_game_running:
                    self.pause_ai_game()
                self.ai_bot1.set_position(fen=self.board.fen())
                self.ai_bot2.set_position(fen=self.board.fen())

            self.sync_turn_state()
            if self.is_time_mode:
                self.switch_timer_to_board_turn()
            if hasattr(self, 'thinking_indicator'):
                self.thinking_indicator.stop_thinking()
                    
            # Update last move highlighting
            if len(self.board.move_stack) > 0:
                last_move_uci = self.board.move_stack[-1].uci()
                from_square = chess.parse_square(last_move_uci[:2])
                to_square = chess.parse_square(last_move_uci[2:4])
                
                self.last_move_from = self.square_to_ui(from_square)
                self.last_move_to = self.square_to_ui(to_square)
            else:
                # No previous moves, clear highlighting
                self.last_move_from = None
                self.last_move_to = None
                
            # Update the board display
            self.update_board()
            
            # Notify the user about the undo
            self.thinking_indicator.show_status("Move undone!")
            
            # Update the status message after a short delay
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1500, self.update_status_after_undo)
            
        except Exception as e:
            import traceback
            print(f"Error in undo_move: {str(e)}")
            traceback.print_exc()
            self.thinking_indicator.show_status(f"Could not undo move")

    def update_status_after_undo(self):
        """Update the status message after an undo"""
        if self.board.is_game_over():
            return
            
        if self.mode == "human_ai":
            if self.is_human_turn():
                self.thinking_indicator.show_status("Your turn")
            else:
                self.thinking_indicator.show_status("AI's turn")
        elif self.mode == "human_human":
            self.thinking_indicator.show_status(f"{self.color_name(self.board.turn)} to move")
        else:  # AI vs AI mode
            if not hasattr(self, 'ai_game_running') or not self.ai_game_running:
                self.thinking_indicator.show_status("Press 'Start' to continue AI vs AI game")
        self.update_status_panel()

    def update_move_history_after_undo(self):
        """Update the move history display after an undo operation"""
        try:
            if not hasattr(self, 'move_history'):
                return
                    
            # Get the current count of items in the move list
            move_list = self.move_history.move_list
            if not move_list:
                print("Move list is not available")
                return
                    
            count = move_list.count()
            
            if count == 0:
                return
                    
            # Get the last item in the list
            current_item = move_list.item(count - 1)
            if current_item is None:
                return
                    
            current_text = current_item.text()
            
            # Check if the item contains both white and black moves
            if " (" in current_text and ") " in current_text and ")" not in current_text.split(") ")[0]:
                try:
                    # Remove just the black move part (keep white's move)
                    white_move_part = current_text.split(") ")[0] + ")"
                    current_item.setText(white_move_part)
                    # Remove any formatting that was added for combined moves
                    font = current_item.font()
                    font.setBold(False)
                    current_item.setFont(font)
                except Exception as e:
                    print(f"Error formatting move text: {str(e)}")
            else:
                try:
                    # Remove the entire item if it's just a white move or already formatted
                    move_list.takeItem(count - 1)
                except Exception as e:
                    print(f"Error removing move item: {str(e)}")
        except Exception as e:
            import traceback
            print(f"Error updating move history after undo: {str(e)}")
            traceback.print_exc()
        
    def save_game_with_dialog(self):
        """Save the current game state to a file with a dialog for metadata"""
        try:
            # Pause the game if it's running
            was_running = self.ai_game_running
            if was_running:
                self.pause_ai_game()
            
            # Show the enhanced save dialog
            save_dialog = SaveGameDialog(self)
            if save_dialog.exec_() == QDialog.Accepted:
                game_name = save_dialog.get_game_name()
                game_notes = save_dialog.get_game_notes()
                
                # Prepare timer settings if in time mode
                timer_settings = None
                if self.is_time_mode:
                    white_time_ms, black_time_ms = self.chess_timer.get_remaining_times()
                    timer_settings = {
                        'enabled': True,
                        'initial_white_time_ms': self.white_time_ms,
                        'initial_black_time_ms': self.black_time_ms,
                        'white_time_ms': white_time_ms,
                        'black_time_ms': black_time_ms,
                        'active_player': self.chess_timer.active_player
                    }
                
                # Prepare game data with metadata
                game_data = {
                    'fen': self.board.fen(),
                    'mode': self.mode,
                    'turn': self.turn,
                    'player_color': "white" if self.player_color == chess.WHITE else "black",
                    'board_flipped': self.board_flipped,
                    'last_move_from': self.last_move_from,
                    'last_move_to': self.last_move_to,
                    'move_history': [move.uci() for move in self.board.move_stack],
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'game_name': game_name,
                    'game_notes': game_notes
                }
                
                if timer_settings:
                    game_data['timer_settings'] = timer_settings
                
                # Call the SavedGameManager to save the game
                try:
                    # Open file dialog to select save location
                    from PyQt5.QtWidgets import QFileDialog
                    import json
                    file_path, _ = QFileDialog.getSaveFileName(
                        self, 
                        "Save Game", 
                        os.path.expanduser("~/Desktop"), 
                        "Chess Game Files (*.chess);;All Files (*)"
                    )
                    
                    if file_path:
                        # Add .chess extension if not provided
                        if not file_path.endswith('.chess'):
                            file_path += '.chess'
                            
                        # Save the data to the file
                        with open(file_path, 'w') as f:
                            json.dump(game_data, f, indent=4)
                        
                        QMessageBox.information(self, "Game Saved", 
                                        f"Game \"{game_name}\" successfully saved to {os.path.basename(file_path)}")
                        return True, file_path
                    else:
                        QMessageBox.warning(self, "Save Canceled", "Game was not saved.")
                        return False, None
                        
                except Exception as e:
                    QMessageBox.critical(self, "Save Error", 
                                    f"An error occurred while saving the game: {str(e)}")
                    print(f"Error saving game: {str(e)}")
                    traceback.print_exc()
                    return False, None
                
            else:
                # User canceled save dialog
                if was_running:
                    try:
                        self.start_ai_game()
                    except Exception as e:
                        QMessageBox.warning(self, "Resuming Game", 
                                        f"Couldn't resume the game: {str(e)}\nClick Start to continue.")
                        print(f"Error resuming game: {str(e)}")
                return False, None
                    
        except Exception as e:
            QMessageBox.critical(self, "Critical Error", 
                            f"A critical error occurred: {str(e)}")
            print(f"Critical error in save_game_with_dialog: {str(e)}")
            traceback.print_exc()
            return False, None

    def resign_game(self):
        """Handle the player resigning from the game"""
        try:
            # Stop any ongoing AI processes
            if hasattr(self, 'ai_computation_active') and self.ai_computation_active:
                if hasattr(self, 'ai_worker') and self.ai_worker and self.ai_worker.isRunning():
                    self.ai_worker.terminate()
                    self.ai_worker = None
                    self.ai_computation_active = False
                    
            # Stop AI game if running
            if hasattr(self, 'ai_game_running') and self.ai_game_running:
                self.ai_game_running = False
                if hasattr(self, 'ai_timer') and self.ai_timer.isActive():
                    self.ai_timer.stop()
                    
            # Stop timer
            if self.is_time_mode:
                self.chess_timer.stop_timer()
                    
            # Stop thinking indicator
            if hasattr(self, 'thinking_indicator'):
                self.thinking_indicator.stop_thinking()
            
            # Show confirmation dialog
            confirmation = ResignConfirmationDialog(self)
            if confirmation.exec_() == QDialog.Accepted:
                # Handle resignation based on current game state and mode
                if self.mode == "human_ai":
                    result = '0-1' if self.player_color == chess.WHITE else '1-0'
                    self.board.set_result(result)
                    self.thinking_indicator.show_status("You resigned. Game over.")
                    self.show_game_over_popup(custom_message="You resigned the game")
                elif self.mode == "human_human":
                    resigning_color = self.board.turn
                    result = '0-1' if resigning_color == chess.WHITE else '1-0'
                    winner = self.color_name(not resigning_color)
                    self.board.set_result(result)
                    self.thinking_indicator.show_status("Game resigned")
                    self.show_game_over_popup(custom_message=f"{winner} wins by resignation")
                else:  # AI vs AI mode
                    # Determine which AI was supposed to move next and award the win to the other
                    result = '0-1'  # Black wins
                    winner_text = "Game resigned. AI 2 (Black) Wins!"
                    
                    if self.turn == 'ai2':
                        result = '1-0'  # White wins
                        winner_text = "Game resigned. AI 1 (White) Wins!"
                    
                    # Force the board into a game over state
                    self.board.set_result(result)
                    
                    # Update the UI
                    self.thinking_indicator.show_status("Game resigned")
                    
                    # Show game over popup
                    self.show_game_over_popup(custom_message=winner_text)
        
        except Exception as e:
            import traceback
            print(f"Error in resign_game: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to resign game: {str(e)}")

    def patch_board_for_resignation(self):
        """Add the set_result method to the chess.Board class if not present"""
        if not hasattr(chess.Board, 'set_result'):
            def set_result(board, result):
                """Force a game result without changing the board position.
                This is used for resignation and similar game end scenarios."""
                # Store the result for later retrieval
                board._result = result
                
                # Override the is_game_over method to return True
                original_is_game_over = board.is_game_over
                def patched_is_game_over():
                    return True
                board.is_game_over = patched_is_game_over
                
                # Override the result method to return our stored result
                original_result = board.result
                def patched_result():
                    return board._result
                board.result = patched_result
                
                # Store original methods to be able to restore them if needed
                board._original_is_game_over = original_is_game_over
                board._original_result = original_result
                
            # Add the method to the chess.Board class
            chess.Board.set_result = set_result
