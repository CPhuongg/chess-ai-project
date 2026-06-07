"""
Dialog và popup components — Pygame-inspired dark overlay dialogs.
Không frame hệ thống, nền tối, viền mỏng, font monospace.
"""

import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QWidget, QLineEdit, QFormLayout, QSpacerItem,
    QTextEdit, QFrame, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QColor, QFont, QPainter, QBrush

from utils.config import Config

# ── Palette ────────────────────────────────────────────────────────────────
BG_DARK    = "#141414"
PANEL_BG   = "#1E1E1E"
BORDER_CLR = "#383838"
ACCENT_GRN = "#769656"
ACCENT_RED = "#C1392B"
ACCENT_BLU = "#2E86C1"
TEXT_MAIN  = "#EFEFEF"
TEXT_DIM   = "#888888"
INPUT_BG   = "#2A2A2A"
INPUT_BDR  = "#444444"
# ───────────────────────────────────────────────────────────────────────────

_MONO = "'Courier New', monospace"

def _dlg_style():
    return f"""
        QDialog {{
            background-color: {PANEL_BG};
            border: 1px solid {BORDER_CLR};
        }}
        QLabel {{
            color: {TEXT_MAIN};
            font-family: {_MONO};
        }}
        QLineEdit, QTextEdit {{
            background-color: {INPUT_BG};
            color: {TEXT_MAIN};
            border: 1px solid {INPUT_BDR};
            border-radius: 2px;
            font-family: {_MONO};
            font-size: 10pt;
            padding: 4px 6px;
            selection-background-color: {ACCENT_GRN};
        }}
    """

def _btn(text, bg, hover=None, min_w=120):
    hover = hover or QColor(bg).lighter(115).name()
    pressed = QColor(bg).darker(115).name()
    btn = QPushButton(text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setMinimumWidth(min_w)
    btn.setFixedHeight(34)
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {bg};
            color: {TEXT_MAIN};
            font-family: {_MONO};
            font-size: 10pt;
            font-weight: bold;
            border: 1px solid {QColor(bg).lighter(130).name()};
            border-radius: 2px;
            padding: 4px 12px;
            letter-spacing: 0.5px;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; }}
    """)
    return btn


def _section_line(text):
    """Divider với label nhỏ."""
    lbl = QLabel(f"── {text.upper()} ──")
    lbl.setStyleSheet(f"""
        font-family: {_MONO};
        font-size: 8pt;
        color: {TEXT_DIM};
        letter-spacing: 2px;
        padding: 4px 0px 2px 0px;
    """)
    return lbl


class BaseDialog(QDialog):
    """Base dialog: frameless, dark, draggable via title bar."""

    def __init__(self, title, parent=None, modal=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        if modal:
            self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet(_dlg_style())
        self._drag_pos = None

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Title bar ──────────────────────────────────────────────────────
        self.title_bar = QFrame()
        self.title_bar.setFixedHeight(36)
        self.title_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_DARK};
                border-bottom: 1px solid {ACCENT_GRN};
            }}
        """)
        tbl = QHBoxLayout(self.title_bar)
        tbl.setContentsMargins(12, 0, 12, 0)

        self.title_label = QLabel(f"  {title.upper()}")
        self.title_label.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 10pt;
            font-weight: bold;
            color: {ACCENT_GRN};
            letter-spacing: 2px;
        """)
        tbl.addWidget(self.title_label)
        tbl.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
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
        tbl.addWidget(close_btn)
        outer.addWidget(self.title_bar)

        # ── Content area ───────────────────────────────────────────────────
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {PANEL_BG};")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 12, 16, 8)
        self.content_layout.setSpacing(8)
        outer.addWidget(self.content_widget)

        # ── Button row ─────────────────────────────────────────────────────
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_DARK};
                border-top: 1px solid {BORDER_CLR};
            }}
        """)
        self.button_layout = QHBoxLayout(btn_frame)
        self.button_layout.setContentsMargins(12, 8, 12, 8)
        self.button_layout.setSpacing(10)
        outer.addWidget(btn_frame)

    # ── drag support ───────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if self.title_bar.geometry().contains(event.pos()):
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
class SaveGameDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__("Save Game", parent)
        self.setFixedWidth(420)

        self.content_layout.addWidget(_section_line("details"))

        # Game name
        name_lbl = QLabel("Game Name")
        name_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9pt;")
        self.content_layout.addWidget(name_lbl)
        self.game_name = QLineEdit()
        self.game_name.setPlaceholderText("Enter a name (optional)")
        self.content_layout.addWidget(self.game_name)

        # Notes
        notes_lbl = QLabel("Notes")
        notes_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 9pt;")
        self.content_layout.addWidget(notes_lbl)
        self.game_notes = QTextEdit()
        self.game_notes.setPlaceholderText("Optional notes about this game...")
        self.game_notes.setFixedHeight(80)
        self.content_layout.addWidget(self.game_notes)

        # Buttons
        self.button_layout.addStretch()
        save_btn = _btn("SAVE", ACCENT_GRN)
        save_btn.clicked.connect(self.accept)
        cancel_btn = _btn("CANCEL", "#3A3A3A")
        cancel_btn.clicked.connect(self.reject)
        self.button_layout.addWidget(save_btn)
        self.button_layout.addWidget(cancel_btn)

        self.game_name.setFocus()

    def get_game_name(self):
        name = self.game_name.text().strip()
        return name or f"Chess Game - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

    def get_game_notes(self):
        return self.game_notes.toPlainText().strip()


# ══════════════════════════════════════════════════════════════════════════════
class PawnPromotionDialog(BaseDialog):
    """Chọn quân phong cấp — grid 4 quân."""
    piece_selected = pyqtSignal(int)

    def __init__(self, color="white", parent=None):
        super().__init__("Pawn Promotion", parent)
        self.setFixedWidth(340)

        import chess
        pieces = [
            (chess.QUEEN,  "♛ QUEEN"),
            (chess.ROOK,   "♜ ROOK"),
            (chess.BISHOP, "♝ BISHOP"),
            (chess.KNIGHT, "♞ KNIGHT"),
        ]
        if color == "white":
            pieces = [
                (chess.QUEEN,  "♕ QUEEN"),
                (chess.ROOK,   "♖ ROOK"),
                (chess.BISHOP, "♗ BISHOP"),
                (chess.KNIGHT, "♘ KNIGHT"),
            ]

        info = QLabel("Choose a piece for promotion:")
        info.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10pt; padding-bottom: 6px;")
        self.content_layout.addWidget(info)

        grid_w = QWidget()
        from PyQt5.QtWidgets import QGridLayout
        grid = QGridLayout(grid_w)
        grid.setSpacing(6)
        for idx, (piece_type, label) in enumerate(pieces):
            btn = QPushButton(label)
            btn.setFixedHeight(48)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2A2A2A;
                    color: {TEXT_MAIN};
                    font-family: {_MONO};
                    font-size: 13pt;
                    border: 1px solid {BORDER_CLR};
                    border-radius: 2px;
                }}
                QPushButton:hover {{
                    background-color: #3A4A3A;
                    border-color: {ACCENT_GRN};
                }}
            """)
            btn.clicked.connect(lambda _, pt=piece_type: self._select(pt))
            grid.addWidget(btn, idx // 2, idx % 2)
        self.content_layout.addWidget(grid_w)

    def _select(self, piece_type):
        self.piece_selected.emit(piece_type)
        self.accept()


# ══════════════════════════════════════════════════════════════════════════════
class GameOverPopup(QDialog):
    """
    Popup kết thúc trận — overlay tối toàn màn hình, nội dung căn giữa.
    """
    play_again_signal  = pyqtSignal()
    return_home_signal = pyqtSignal()

    def __init__(self, result_text, detail_text="", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 280)
        self.setStyleSheet("background: transparent;")

        # Outer wrapper (semi-transparent overlay feel via card)
        card = QFrame(self)
        card.setGeometry(0, 0, 420, 280)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {PANEL_BG};
                border: 1px solid {BORDER_CLR};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QFrame()
        header.setFixedHeight(40)
        header.setStyleSheet(f"background-color: {BG_DARK}; border-bottom: 1px solid {ACCENT_GRN};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        title_lbl = QLabel("GAME OVER")
        title_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 11pt;
            font-weight: bold;
            color: {ACCENT_GRN};
            letter-spacing: 3px;
        """)
        hl.addWidget(title_lbl)
        layout.addWidget(header)

        # Result
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 16)
        bl.setSpacing(10)

        result_lbl = QLabel(result_text)
        result_lbl.setAlignment(Qt.AlignCenter)
        result_lbl.setWordWrap(True)
        result_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 18pt;
            font-weight: bold;
            color: {TEXT_MAIN};
        """)
        bl.addWidget(result_lbl)

        if detail_text:
            detail_lbl = QLabel(detail_text)
            detail_lbl.setAlignment(Qt.AlignCenter)
            detail_lbl.setWordWrap(True)
            detail_lbl.setStyleSheet(f"""
                font-family: {_MONO};
                font-size: 10pt;
                color: {TEXT_DIM};
            """)
            bl.addWidget(detail_lbl)

        layout.addWidget(body)

        # Buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"background-color: {BG_DARK}; border-top: 1px solid {BORDER_CLR};")
        bfl = QHBoxLayout(btn_frame)
        bfl.setContentsMargins(16, 10, 16, 10)
        bfl.setSpacing(10)

        play_btn = _btn("▶ PLAY AGAIN", ACCENT_GRN)
        play_btn.clicked.connect(self._play_again)
        home_btn = _btn("⌂ HOME", "#3A3A3A")
        home_btn.clicked.connect(self._return_home)
        bfl.addWidget(play_btn)
        bfl.addWidget(home_btn)
        layout.addWidget(btn_frame)

    def _play_again(self):
        self.play_again_signal.emit()
        self.accept()

    def _return_home(self):
        self.return_home_signal.emit()
        self.accept()


# ══════════════════════════════════════════════════════════════════════════════
class ResignConfirmationDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__("Confirm Resignation", parent)
        self.setFixedWidth(380)

        warning = QLabel("Resign this game?")
        warning.setAlignment(Qt.AlignCenter)
        warning.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 16pt;
            font-weight: bold;
            color: {ACCENT_RED};
            padding: 12px 0px;
        """)
        self.content_layout.addWidget(warning)

        explanation = QLabel(
            "Resigning means you forfeit the game and\nyour opponent will be declared the winner."
        )
        explanation.setAlignment(Qt.AlignCenter)
        explanation.setWordWrap(True)
        explanation.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10pt;")
        self.content_layout.addWidget(explanation)

        self.button_layout.addStretch()
        resign_btn = _btn("YES, RESIGN", ACCENT_RED)
        resign_btn.clicked.connect(self.accept)
        cancel_btn = _btn("CANCEL", "#3A3A3A")
        cancel_btn.clicked.connect(self.reject)
        self.button_layout.addWidget(resign_btn)
        self.button_layout.addWidget(cancel_btn)


# ══════════════════════════════════════════════════════════════════════════════
class StartScreen(QDialog):
    """
    Màn hình chọn chế độ chơi — Pygame-inspired title screen.
    Nền tối, logo chữ lớn, hai nút to rõ ràng.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chess Game")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setFixedSize(480, 520)
        self.setStyleSheet(f"background-color: {BG_DARK};")
        self._mode = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)

        # ── Chess board icon (ASCII) ────────────────────────────────────────
        icon_lbl = QLabel("♛")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"""
            font-size: 64pt;
            color: {ACCENT_GRN};
            padding: 0px;
            margin: 0px;
        """)
        layout.addWidget(icon_lbl)

        # ── Title ──────────────────────────────────────────────────────────
        title_lbl = QLabel("CHESS")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 36pt;
            font-weight: bold;
            color: {TEXT_MAIN};
            letter-spacing: 8px;
            padding: 0px;
            margin: 0px;
        """)
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("MINIMAX  ·  ALPHA-BETA PRUNING")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 8pt;
            color: {TEXT_DIM};
            letter-spacing: 3px;
            padding-bottom: 32px;
        """)
        layout.addWidget(sub_lbl)

        # ── Mode label ─────────────────────────────────────────────────────
        mode_lbl = QLabel("SELECT MODE")
        mode_lbl.setAlignment(Qt.AlignCenter)
        mode_lbl.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 8pt;
            color: {TEXT_DIM};
            letter-spacing: 3px;
            padding-bottom: 8px;
        """)
        layout.addWidget(mode_lbl)

        # ── Human vs AI ────────────────────────────────────────────────────
        human_btn = QPushButton("♟  HUMAN  vs  AI")
        human_btn.setCursor(Qt.PointingHandCursor)
        human_btn.setFixedHeight(56)
        human_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_GRN};
                color: {TEXT_MAIN};
                font-family: {_MONO};
                font-size: 14pt;
                font-weight: bold;
                border: none;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {QColor(ACCENT_GRN).lighter(115).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(ACCENT_GRN).darker(115).name()};
            }}
        """)
        human_btn.clicked.connect(lambda: self._select("human_ai"))
        layout.addWidget(human_btn)

        layout.addSpacing(8)

        # ── AI vs AI ───────────────────────────────────────────────────────
        ai_btn = QPushButton("⚙  AI  vs  AI")
        ai_btn.setCursor(Qt.PointingHandCursor)
        ai_btn.setFixedHeight(56)
        ai_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2A3A4A;
                color: {TEXT_MAIN};
                font-family: {_MONO};
                font-size: 14pt;
                font-weight: bold;
                border: 1px solid #3A5A7A;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: #344A5A;
            }}
            QPushButton:pressed {{
                background-color: #1A2A3A;
            }}
        """)
        ai_btn.clicked.connect(lambda: self._select("ai_ai"))
        layout.addWidget(ai_btn)

        layout.addSpacing(8)

        # ── Load game ──────────────────────────────────────────────────────
        self.load_game_button = QPushButton("📂  LOAD SAVED GAME")
        self.load_game_button.setCursor(Qt.PointingHandCursor)
        self.load_game_button.setFixedHeight(38)
        self.load_game_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_DIM};
                font-family: {_MONO};
                font-size: 10pt;
                border: 1px solid {BORDER_CLR};
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                color: {TEXT_MAIN};
                border-color: #555555;
            }}
        """)
        layout.addWidget(self.load_game_button)

        layout.addStretch()

        # ── Footer ─────────────────────────────────────────────────────────
        footer = QLabel("ESC to quit")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(f"font-family: {_MONO}; font-size: 8pt; color: {TEXT_DIM};")
        layout.addWidget(footer)

    def _select(self, mode):
        self._mode = mode
        self.accept()

    def get_mode(self):
        return self._mode