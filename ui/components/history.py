# Description:
# Move history widget showing game moves in two columns (White / Black).
# Uses QListWidget with alternating row colors, monospace font.
# Automatically formats moves with standard chess notation (N for knight, x for capture, O-O for castling, + for check).
# Adds promotion notation (=Q, etc.) and en-passant (e.p.) markers.
# Scrolls to bottom automatically when new moves are added.

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QSizePolicy, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont
import chess
from ui import theme

# ── Palette ────────────────────────────────────────────────────────────────
BG_PANEL   = theme.SURFACE
ROW_ALT    = theme.SURFACE_2
BORDER_CLR = theme.BORDER
WHITE_CLR  = "#F0D69A"
BLACK_CLR  = "#A9D7B6"
TEXT_DIM   = theme.TEXT_MUTED
ACCENT     = theme.ACCENT
# ───────────────────────────────────────────────────────────────────────────

# Ký tự chữ cái cho quân cờ (P, N, B, R, Q)
_PIECE_LETTER = {
    chess.PAWN:   "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK:   "R",
    chess.QUEEN:  "Q",
}

# Thứ tự sắp xếp: hậu > xe > tượng = mã > tốt
_PIECE_ORDER = {chess.QUEEN: 5, chess.ROOK: 4, chess.BISHOP: 3,
                chess.KNIGHT: 3, chess.PAWN: 2, chess.KING: 1}


def _build_captured_text(pieces: list[int]) -> str:
    """Chuyển list piece_type → chuỗi ký tự, sắp xếp theo giá trị."""
    if not pieces:
        return "-"
    sorted_p = sorted(pieces, key=lambda p: _PIECE_ORDER.get(p, 0), reverse=True)
    return " ".join(_PIECE_LETTER.get(p, "?") for p in sorted_p)


class MoveHistoryWidget(QFrame):
    """
    Bảng lịch sử nước đi + hiển thị quân bị ăn ngay bên dưới header.
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
            font-family: {theme.FONT_UI};
            font-size: 10pt;
            font-weight: 800;
            color: {ACCENT};
            letter-spacing: 0px;
            background-color: {theme.APP_BG};
            border-bottom: 1px solid {BORDER_CLR};
            padding: 0px;
        """)
        layout.addWidget(header)

        # ── Captured pieces row ────────────────────────────────────────────
        cap_row = QWidget()
        cap_row.setFixedHeight(36)
        cap_row.setStyleSheet(f"background-color: {theme.APP_BG}; border-bottom: 1px solid {BORDER_CLR};")
        cap_layout = QHBoxLayout(cap_row)
        cap_layout.setContentsMargins(6, 2, 6, 2)
        cap_layout.setSpacing(4)

        _cap_style = f"""
            font-family: {theme.FONT_MONO};
            font-size: 9pt;
            font-weight: 700;
            background: transparent;
            padding: 0px 2px;
        """

        # Trắng bị ăn (hiển thị bên trái)
        self._white_cap_lbl = QLabel("-")
        self._white_cap_lbl.setStyleSheet(_cap_style + f"color: #D4C5A9;")  # kem nhạt
        self._white_cap_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._white_cap_lbl.setToolTip("White pieces captured by Black")

        sep = QLabel("|")
        sep.setStyleSheet(f"color: {BORDER_CLR}; background: transparent;")
        sep.setFixedWidth(10)
        sep.setAlignment(Qt.AlignCenter)

        # Đen bị ăn (hiển thị bên phải)
        self._black_cap_lbl = QLabel("-")
        self._black_cap_lbl.setStyleSheet(_cap_style + f"color: #8B7355;")  # nâu đậm
        self._black_cap_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._black_cap_lbl.setToolTip("Black pieces captured by White")

        cap_layout.addWidget(self._white_cap_lbl, 1)
        cap_layout.addWidget(sep)
        cap_layout.addWidget(self._black_cap_lbl, 1)
        layout.addWidget(cap_row)

        # ── Column headers ─────────────────────────────────────────────────
        col_hdr = QLabel("  #    WHITE                      BLACK")
        col_hdr.setFixedHeight(20)
        col_hdr.setStyleSheet(f"""
            font-family: {theme.FONT_MONO};
            font-size: 8pt;
            color: {TEXT_DIM};
            background-color: {theme.APP_BG};
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
                font-family: {theme.FONT_MONO};
                font-size: 10pt;
                border: none;
                padding: 0px;
                outline: none;
            }}
            QListWidget::item {{
                color: #CCCCCC;
                padding: 3px 6px;
                border-bottom: 1px solid {theme.BORDER_SOFT};
                min-height: 24px;
            }}
            QListWidget::item:selected {{
                background-color: {theme.SURFACE_3};
                color: {theme.TEXT};
            }}
            QListWidget::item:hover {{
                background-color: {theme.SURFACE_2};
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

    def update_captured(self, board: chess.Board):
        """
        Tính quân bị ăn từ board hiện tại (so sánh với vị trí ban đầu)
        rồi cập nhật 2 label trong header.
        Trắng bị ăn → hiển thị bên trái (quân Trắng mất).
        Đen bị ăn  → hiển thị bên phải (quân Đen mất).
        """
        initial = {
            chess.WHITE: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
                          chess.ROOK: 2, chess.QUEEN: 1},
            chess.BLACK: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
                          chess.ROOK: 2, chess.QUEEN: 1},
        }
        current = {
            chess.WHITE: {t: 0 for t in initial[chess.WHITE]},
            chess.BLACK: {t: 0 for t in initial[chess.BLACK]},
        }
        for sq in chess.SQUARES:
            p = board.piece_at(sq)
            if p and p.piece_type in current[p.color]:
                current[p.color][p.piece_type] += 1

        white_lost, black_lost = [], []
        for pt in initial[chess.WHITE]:
            diff = initial[chess.WHITE][pt] - current[chess.WHITE][pt]
            white_lost.extend([pt] * max(0, diff))
        for pt in initial[chess.BLACK]:
            diff = initial[chess.BLACK][pt] - current[chess.BLACK][pt]
            black_lost.extend([pt] * max(0, diff))

        self._white_cap_lbl.setText(_build_captured_text(white_lost))
        self._black_cap_lbl.setText(_build_captured_text(black_lost))

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
