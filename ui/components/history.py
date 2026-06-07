# Description:
# Move history widget showing game moves in two columns (White / Black).
# Uses QListWidget with alternating row colors, monospace font.
# Automatically formats moves with standard chess notation (N for knight, x for capture, O-O for castling, + for check).
# Adds promotion notation (=Q, etc.) and en-passant (e.p.) markers.
# Scrolls to bottom automatically when new moves are added.

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont
import chess

# ── Palette ────────────────────────────────────────────────────────────────
BG_PANEL   = "#1E1E1E"
ROW_ALT    = "#252525"
BORDER_CLR = "#383838"
WHITE_CLR  = "#E8C97A"   # Warm gold for White moves
BLACK_CLR  = "#A8C8A8"   # Soft green for Black moves
TEXT_DIM   = "#666666"
ACCENT     = "#769656"
# ───────────────────────────────────────────────────────────────────────────


class MoveHistoryWidget(QFrame):
    """
    Bảng lịch sử nước đi.
    Hai cột per dòng: số thứ tự | nước Trắng | nước Đen.
    Nền tối, font monospace.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(f"background-color: {BG_PANEL}; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────
        header = QLabel("MOVE HISTORY")
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(30)
        header.setStyleSheet(f"""
            font-family: 'Courier New', monospace;
            font-size: 9pt;
            font-weight: bold;
            color: {ACCENT};
            letter-spacing: 3px;
            background-color: #1A1A1A;
            border-bottom: 1px solid {BORDER_CLR};
            padding: 0px;
        """)
        layout.addWidget(header)

        # ── Column headers ─────────────────────────────────────────────────
        col_hdr = QLabel("  #    WHITE                      BLACK")
        col_hdr.setFixedHeight(20)
        col_hdr.setStyleSheet(f"""
            font-family: 'Courier New', monospace;
            font-size: 8pt;
            color: {TEXT_DIM};
            background-color: #1A1A1A;
            padding: 0px 6px;
            border-bottom: 1px solid {BORDER_CLR};
            letter-spacing: 0.5px;
        """)
        layout.addWidget(col_hdr)

        # ── List ───────────────────────────────────────────────────────────
        self.move_list = QListWidget()
        self.move_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BG_PANEL};
                alternate-background-color: {ROW_ALT};
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                border: none;
                padding: 0px;
                outline: none;
            }}
            QListWidget::item {{
                color: #CCCCCC;
                padding: 3px 6px;
                border-bottom: 1px solid #282828;
                min-height: 22px;
            }}
            QListWidget::item:selected {{
                background-color: #2A3A2A;
                color: #EFEFEF;
            }}
            QListWidget::item:hover {{
                background-color: #2A2A2A;
            }}
        """)
        self.move_list.setAlternatingRowColors(True)
        layout.addWidget(self.move_list)

    # ── Public API ─────────────────────────────────────────────────────────
    def add_move(self, piece, from_square, to_square, color="White",
                 capture=False, check=False, promotion=None,
                 castling=False, en_passant=False):
        try:
            piece_sym = {
                chess.PAWN: "", chess.KNIGHT: "N", chess.BISHOP: "B",
                chess.ROOK: "R", chess.QUEEN: "Q", chess.KING: "K"
            }
            promo_sym = {
                chess.QUEEN: "Q", chess.ROOK: "R",
                chess.BISHOP: "B", chess.KNIGHT: "N"
            }

            notation = ""
            if castling:
                notation = "O-O" if ord(to_square[0]) > ord(from_square[0]) else "O-O-O"
            else:
                notation += piece_sym.get(piece.piece_type, "")
                if capture and piece.piece_type == chess.PAWN:
                    notation += from_square[0]
                if capture or en_passant:
                    notation += "x"
                notation += to_square
                if en_passant:
                    notation += " e.p."
                if promotion:
                    notation += "=" + promo_sym.get(promotion, "Q")
            if check:
                notation += "+"

            route = f"{from_square}-{to_square}"

            if color == "White":
                move_num = self.move_list.count() + 1
                # Formatted: "  1. e4           "  (padded for black column)
                text = f"  {move_num:>2}.  {notation:<8} ({route:<7})"
                item = QListWidgetItem(text)
                item.setForeground(QBrush(QColor(WHITE_CLR)))
                self.move_list.addItem(item)
            else:
                last = self.move_list.item(self.move_list.count() - 1)
                if last:
                    black_part = f"  {notation:<8} ({route})"
                    last.setText(last.text().ljust(30) + black_part)
                    last.setForeground(QBrush(QColor(WHITE_CLR)))  # keep consistent row
                else:
                    move_num = self.move_list.count() + 1
                    text = f"  {move_num:>2}.  {'...':8}       {notation:<8} ({route})"
                    item = QListWidgetItem(text)
                    item.setForeground(QBrush(QColor(BLACK_CLR)))
                    self.move_list.addItem(item)

            self.move_list.scrollToBottom()

        except Exception as e:
            print(f"Error adding move to history: {e}")
            move_num = (self.move_list.count() // 2) + 1
            if color == "White":
                self.move_list.addItem(f"  {move_num}.  {from_square}-{to_square}")
            else:
                self.move_list.addItem(f"  ...   {from_square}-{to_square}")

    def clear_history(self):
        self.move_list.clear()

    def remove_last_move(self):
        count = self.move_list.count()
        if count == 0:
            return
        last = self.move_list.item(count - 1)
        text = last.text().rstrip()
        # If the row has both white and black columns, trim black part
        # Detect by checking if the text is significantly longer than white-only
        parts = text.split("  ")  # split by double space
        if len(parts) > 4:
            # Has black move — remove it (keep only white half)
            white_half = "  ".join(parts[:4])
            last.setText(white_half)
        else:
            self.move_list.takeItem(count - 1)