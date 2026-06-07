# Path: opening_book.py
# Description:
# Custom opening book reader using a plain text format.
# Parses position FEN strings followed by move entries with play counts.
# Provides weighted random move selection based on play counts.
# Supports board state lookup after removing move counters from FEN.
# Used by the chess engine to play book moves during the opening phase.

import random
import chess

class OpeningBook:
    def __init__(self, file: str):
        self.rng = random.Random()
        self.moves_by_position = {}

        entries = file.strip().split("pos")[1:]

        for entry in entries:
            entry_data = entry.strip().split('\n')
            position_fen = entry_data[0].strip()
            all_move_data = entry_data[1:]

            book_moves = []

            for move_data in all_move_data:
                move_parts = move_data.split(' ')
                book_move = BookMove(move_parts[0], int(move_parts[1]))
                book_moves.append(book_move)

            self.moves_by_position[position_fen] = book_moves

    def has_book_move(self, position_fen: str) -> bool:
        """ Kiểm tra xem có nước đi nào trong sách khai cuộc cho vị trí này không """
        return self.remove_move_counters_from_fen(position_fen) in self.moves_by_position

    def try_get_book_move(self, board: chess.Board, weight_pow=0.5):
        """
        Cố gắng lấy nước đi từ sách khai cuộc, dựa vào trọng số cho mỗi nước đi.
        :param board: Bàn cờ hiện tại (phải có phương thức get_fen để lấy chuỗi FEN).
        :param weight_pow: Trọng số cho các lần chơi (0 là ngẫu nhiên, 1 là chọn nước đi nhiều lần hơn).
        :return: Trả về nước đi hoặc 'Null' nếu không tìm thấy nước đi trong sách khai cuộc.
        """
        position_fen = board.fen()  # Lấy chuỗi FEN từ đối tượng board của python-chess
        position_fen = self.remove_move_counters_from_fen(position_fen)

        if position_fen in self.moves_by_position:
            moves = self.moves_by_position[position_fen]
            total_play_count = sum(
                self.weighted_play_count(move.num_times_played, weight_pow) for move in moves
            )

            weights = [
                self.weighted_play_count(move.num_times_played, weight_pow) / total_play_count for move in moves
            ]
            weight_sum = sum(weights)

            prob_cumul = [0] * len(moves)
            for i in enumerate(weights):
                prob = weights[i] / weight_sum
                prob_cumul[i] = prob_cumul[max(0, i - 1)] + prob

            random_value = self.rng.random()
            for i, prob in enumerate(prob_cumul):
                if random_value <= prob:
                    return moves[i].move_string

        return None

    def remove_move_counters_from_fen(self, fen: str) -> str:
        """ Loại bỏ thông tin về số lần di chuyển từ chuỗi FEN """
        fen_without_move_count = fen[:fen.rfind(' ')]
        return fen_without_move_count[:fen_without_move_count.rfind(' ')]

    def weighted_play_count(self, play_count: int, weight_pow: float) -> int:
        """ Tính toán trọng số cho số lần chơi dựa trên trọng số (weight_pow) """
        return int((play_count) ** weight_pow)


class BookMove:
    def __init__(self, move_string: str, num_times_played: int):
        self.move_string = move_string
        self.num_times_played = num_times_played


# Ví dụ sử dụng OpeningBook với python-chess
if __name__ == "__main__":
    # Ví dụ: nội dung của file khai cuộc (có thể đọc từ tệp)
    BOOK_DATA = """
    pos rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    e2e4 50
    e2e3 30
    pos e2e4 50
    e7e5 40
    d2d4 60
    """

    # Khởi tạo sách khai cuộc
    opening_book = OpeningBook(BOOK_DATA)

    # Tạo đối tượng board
    board = chess.Board()

    # Cố gắng lấy một nước đi từ sách khai cuộc
    move = opening_book.try_get_book_move(board, weight_pow=0.7)
    print(f"Selected move: {move}")
