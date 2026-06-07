"""
Captured pieces widget — hiển thị các quân đã bị ăn của cả hai bên.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import chess

# ── Palette ────────────────────────────────────────────────────────────────
PANEL_BG   = "#1E1E1E"
BORDER_CLR = "#383838"
TEXT_DIM   = "#888888"
TEXT_MAIN  = "#EFEFEF"
WHITE_PIECE_COLOR = "#FFFFFF"
BLACK_PIECE_COLOR = "#000000"
_MONO = "'Courier New', monospace"
# ───────────────────────────────────────────────────────────────────────────

# Ký tự quân cờ (unicode)
PIECE_SYMBOLS = {
    chess.PAWN:   "♟",
    chess.KNIGHT: "♞",
    chess.BISHOP: "♝",
    chess.ROOK:   "♜",
    chess.QUEEN:  "♛",
    chess.KING:   "♚",
}

class CapturedPiecesWidget(QWidget):
    """
    Hiển thị danh sách quân đã bị ăn.
    Sắp xếp theo thứ tự: quân Trắng bị Đen ăn (bên trái) và quân Đen bị Trắng ăn (bên phải).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(120)
        self.setStyleSheet(f"background-color: {PANEL_BG}; border: 1px solid {BORDER_CLR};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        # Tiêu đề
        title = QLabel("CAPTURED PIECES")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            font-family: {_MONO};
            font-size: 8pt;
            font-weight: bold;
            color: {TEXT_DIM};
            letter-spacing: 2px;
        """)
        layout.addWidget(title)

        # Hai khu vực: bên trái (White captured by Black), bên phải (Black captured by White)
        row = QHBoxLayout()
        row.setSpacing(10)

        # White captured pieces (quân Trắng bị ăn) — hiển thị bên trái
        self.white_captured_label = QLabel()
        self.white_captured_label.setAlignment(Qt.AlignLeft)
        self.white_captured_label.setStyleSheet(f"""
            font-family: monospace;
            font-size: 14pt;
            color: {WHITE_PIECE_COLOR};
            background-color: #2A2A2A;
            border: 1px solid {BORDER_CLR};
            padding: 4px;
        """)
        self.white_captured_label.setWordWrap(True)

        # Black captured pieces (quân Đen bị ăn) — bên phải
        self.black_captured_label = QLabel()
        self.black_captured_label.setAlignment(Qt.AlignRight)
        self.black_captured_label.setStyleSheet(f"""
            font-family: monospace;
            font-size: 14pt;
            color: {BLACK_PIECE_COLOR};
            background-color: #2A2A2A;
            border: 1px solid {BORDER_CLR};
            padding: 4px;
        """)
        self.black_captured_label.setWordWrap(True)

        row.addWidget(self.white_captured_label, 1)
        row.addWidget(self.black_captured_label, 1)
        layout.addLayout(row)

        # Lưu trữ dữ liệu
        self.white_captured = []  # quân Trắng đã bị ăn (mất)
        self.black_captured = []  # quân Đen đã bị ăn (mất)

    def update_captured(self, board):
        """
        Cập nhật danh sách quân đã bị ăn dựa trên lịch sử nước đi.
        """
        # Reset
        self.white_captured = []
        self.black_captured = []

        # Duyệt qua các nước đi, kiểm tra capture
        for move in board.move_stack:
            # Nếu có quân bị bắt
            if move.to_square is not None and board.is_capture(move):
                # Trong trường hợp en passant, quân bị bắt nằm ở square khác
                if move.is_en_passant:
                    # Lấy vị trí của pawn bị bắt
                    if board.piece_at(move.to_square) is None:
                        # Cần xác định màu của pawn bị bắt
                        # En passant: quân bị bắt là pawn đối phương nằm ở file cùng, rank khác
                        # Ta có thể dùng move_history trước đó, nhưng đơn giản hơn: dùng board sau khi thực hiện move?
                        # Thay vào đó, ta dùng captured_piece từ thông tin trước khi push?
                        # Cách đơn giản: xét bàn cờ trước khi push? Không có ở đây.
                        # Giải pháp: lưu lại captured piece khi thực hiện move trong game.
                        # Nhưng để demo, ta sẽ bỏ qua en passant trong captured display.
                        pass
                else:
                    # Quân bị bắt nằm tại to_square
                    piece = board.piece_at(move.to_square)
                    if piece is not None:
                        if piece.color == chess.WHITE:
                            self.white_captured.append(piece.piece_type)
                        else:
                            self.black_captured.append(piece.piece_type)

        # Cách khác đơn giản hơn: so sánh quân ban đầu với quân hiện tại (không chính xác cho lịch sử)
        # Nhưng ổn cho mục đích hiển thị.
        # Tôi sẽ dùng phương pháp tính từ ván cờ gốc (starting board) và trừ đi các quân còn lại.
        self._update_from_board(board)

    def _update_from_board(self, board):
        """Tính quân đã mất bằng cách so sánh với bàn cờ khởi tạo."""
        initial = chess.Board()
        # Đếm quân ban đầu
        initial_count = {chess.WHITE: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
                                        chess.ROOK: 2, chess.QUEEN: 1, chess.KING: 1},
                         chess.BLACK: {chess.PAWN: 8, chess.KNIGHT: 2, chess.BISHOP: 2,
                                        chess.ROOK: 2, chess.QUEEN: 1, chess.KING: 1}}
        # Đếm quân hiện tại
        current_count = {chess.WHITE: {t: 0 for t in initial_count[chess.WHITE]},
                         chess.BLACK: {t: 0 for t in initial_count[chess.BLACK]}}
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                current_count[piece.color][piece.piece_type] += 1

        # Tính số quân mất
        self.white_captured = []
        self.black_captured = []
        for color, pieces in initial_count.items():
            for ptype, init_num in pieces.items():
                lost = init_num - current_count[color][ptype]
                if lost > 0:
                    for _ in range(lost):
                        if color == chess.WHITE:
                            self.white_captured.append(ptype)
                        else:
                            self.black_captured.append(ptype)

        # Sắp xếp theo giá trị (từ lớn đến nhỏ: Hậu, Xe, Mã/Tượng, Tốt)
        order = {chess.QUEEN: 5, chess.ROOK: 4, chess.BISHOP: 3,
                 chess.KNIGHT: 3, chess.PAWN: 2, chess.KING: 1}
        self.white_captured.sort(key=lambda p: order.get(p, 0), reverse=True)
        self.black_captured.sort(key=lambda p: order.get(p, 0), reverse=True)

        # Cập nhật giao diện
        white_text = " ".join([PIECE_SYMBOLS.get(p, "?") for p in self.white_captured])
        black_text = " ".join([PIECE_SYMBOLS.get(p, "?") for p in self.black_captured])
        self.white_captured_label.setText(white_text if white_text else "—")
        self.black_captured_label.setText(black_text if black_text else "—")