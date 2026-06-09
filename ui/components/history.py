"""Move history panel with captured-piece summary."""

import chess
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.theme import MONO_FONT, color as theme_color


_PIECE_LETTER = {
    chess.PAWN: "P",
    chess.KNIGHT: "N",
    chess.BISHOP: "B",
    chess.ROOK: "R",
    chess.QUEEN: "Q",
}

_PIECE_ORDER = {
    chess.QUEEN: 5,
    chess.ROOK: 4,
    chess.BISHOP: 3,
    chess.KNIGHT: 3,
    chess.PAWN: 2,
    chess.KING: 1,
}


def _build_captured_text(pieces: list[int]) -> str:
    if not pieces:
        return "-"
    ordered = sorted(pieces, key=lambda piece: _PIECE_ORDER.get(piece, 0), reverse=True)
    return " ".join(_PIECE_LETTER.get(piece, "?") for piece in ordered)


class MoveHistoryWidget(QFrame):
    """Displays SAN-like move rows and the material missing from each side."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(f"background-color: {theme_color('panel')}; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("MOVE HISTORY")
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(30)
        header.setStyleSheet(f"""
            font-family: {MONO_FONT};
            font-size: 9pt;
            font-weight: bold;
            color: {theme_color("accent")};
            background-color: {theme_color("panel")};
            border-bottom: 1px solid {theme_color("border")};
        """)
        layout.addWidget(header)

        layout.addWidget(self._build_captured_row())
        layout.addWidget(self._build_column_header())

        self.move_list = QListWidget()
        self.move_list.setAlternatingRowColors(True)
        self.move_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {theme_color("panel")};
                alternate-background-color: {theme_color("panel_alt")};
                font-family: {MONO_FONT};
                font-size: 10pt;
                border: none;
                padding: 0;
                outline: none;
            }}
            QListWidget::item {{
                color: {theme_color("text")};
                padding: 3px 6px;
                border-bottom: 1px solid {theme_color("border")};
                min-height: 22px;
            }}
            QListWidget::item:selected {{
                background-color: {theme_color("surface_alt")};
                color: {theme_color("text")};
            }}
            QListWidget::item:hover {{
                background-color: {theme_color("surface")};
            }}
        """)
        layout.addWidget(self.move_list)

    def _build_captured_row(self):
        row = QWidget()
        row.setFixedHeight(36)
        row.setStyleSheet(
            f"background-color: {theme_color('panel')}; border-bottom: 1px solid {theme_color('border')};"
        )
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(6, 2, 6, 2)
        row_layout.setSpacing(4)

        label_style = f"""
            font-family: {MONO_FONT};
            font-size: 9pt;
            font-weight: bold;
            background: transparent;
            padding: 0 2px;
        """

        self._white_cap_lbl = QLabel("-")
        self._white_cap_lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._white_cap_lbl.setToolTip("White pieces captured by Black")
        self._white_cap_lbl.setStyleSheet(label_style + f"color: {theme_color('light_square')};")

        separator = QLabel("|")
        separator.setFixedWidth(10)
        separator.setAlignment(Qt.AlignCenter)
        separator.setStyleSheet(f"color: {theme_color('border')}; background: transparent;")

        self._black_cap_lbl = QLabel("-")
        self._black_cap_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._black_cap_lbl.setToolTip("Black pieces captured by White")
        self._black_cap_lbl.setStyleSheet(label_style + f"color: {theme_color('dark_square')};")

        row_layout.addWidget(self._white_cap_lbl, 1)
        row_layout.addWidget(separator)
        row_layout.addWidget(self._black_cap_lbl, 1)
        return row

    def _build_column_header(self):
        header = QLabel("  #    WHITE                      BLACK")
        header.setFixedHeight(22)
        header.setStyleSheet(f"""
            font-family: {MONO_FONT};
            font-size: 8pt;
            color: {theme_color("muted")};
            background-color: {theme_color("panel")};
            padding: 0 6px;
            border-bottom: 1px solid {theme_color("border")};
        """)
        return header

    def add_move(
        self,
        piece,
        from_square,
        to_square,
        color="White",
        capture=False,
        check=False,
        promotion=None,
        castling=False,
        en_passant=False,
    ):
        try:
            notation = self._format_move(
                piece,
                from_square,
                to_square,
                capture,
                check,
                promotion,
                castling,
                en_passant,
            )
            route = f"{from_square}-{to_square}"

            if color == "White":
                move_num = self.move_list.count() + 1
                text = f"  {move_num:>2}.  {notation:<8} ({route:<7})"
                item = QListWidgetItem(text)
                item.setForeground(QBrush(QColor(theme_color("light_square"))))
                self.move_list.addItem(item)
            else:
                last = self.move_list.item(self.move_list.count() - 1)
                if last:
                    black_part = f"  {notation:<8} ({route})"
                    last.setText(last.text().ljust(30) + black_part)
                else:
                    move_num = self.move_list.count() + 1
                    text = f"  {move_num:>2}.  {'...':8}       {notation:<8} ({route})"
                    item = QListWidgetItem(text)
                    item.setForeground(QBrush(QColor(theme_color("dark_square"))))
                    self.move_list.addItem(item)
            self.move_list.scrollToBottom()

        except Exception as exc:
            print(f"Error adding move to history: {exc}")
            move_num = self.move_list.count() + 1
            self.move_list.addItem(f"  {move_num}.  {from_square}-{to_square}")

    def _format_move(
        self,
        piece,
        from_square,
        to_square,
        capture,
        check,
        promotion,
        castling,
        en_passant,
    ):
        if castling:
            notation = "O-O" if ord(to_square[0]) > ord(from_square[0]) else "O-O-O"
        else:
            piece_symbols = {
                chess.PAWN: "",
                chess.KNIGHT: "N",
                chess.BISHOP: "B",
                chess.ROOK: "R",
                chess.QUEEN: "Q",
                chess.KING: "K",
            }
            promotion_symbols = {
                chess.QUEEN: "Q",
                chess.ROOK: "R",
                chess.BISHOP: "B",
                chess.KNIGHT: "N",
            }
            notation = piece_symbols.get(piece.piece_type, "")
            if capture and piece.piece_type == chess.PAWN:
                notation += from_square[0]
            if capture or en_passant:
                notation += "x"
            notation += to_square
            if en_passant:
                notation += " e.p."
            if promotion:
                notation += "=" + promotion_symbols.get(promotion, "Q")
        if check:
            notation += "+"
        return notation

    def update_captured(self, board: chess.Board):
        initial = {
            chess.WHITE: {
                chess.PAWN: 8,
                chess.KNIGHT: 2,
                chess.BISHOP: 2,
                chess.ROOK: 2,
                chess.QUEEN: 1,
            },
            chess.BLACK: {
                chess.PAWN: 8,
                chess.KNIGHT: 2,
                chess.BISHOP: 2,
                chess.ROOK: 2,
                chess.QUEEN: 1,
            },
        }
        current = {
            chess.WHITE: {piece: 0 for piece in initial[chess.WHITE]},
            chess.BLACK: {piece: 0 for piece in initial[chess.BLACK]},
        }
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type in current[piece.color]:
                current[piece.color][piece.piece_type] += 1

        white_lost = []
        black_lost = []
        for piece_type in initial[chess.WHITE]:
            white_lost.extend(
                [piece_type] * max(0, initial[chess.WHITE][piece_type] - current[chess.WHITE][piece_type])
            )
            black_lost.extend(
                [piece_type] * max(0, initial[chess.BLACK][piece_type] - current[chess.BLACK][piece_type])
            )

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
        parts = text.split("  ")
        if len(parts) > 4:
            last.setText("  ".join(parts[:4]))
        else:
            self.move_list.takeItem(count - 1)
