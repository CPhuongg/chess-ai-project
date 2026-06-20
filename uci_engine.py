"""Minimal UCI adapter for the existing ChessBot engine.

This file intentionally wraps the current bot without changing search, UI, or
engine internals. UCI protocol output is written only to the original stdout;
all existing debug prints from the engine are redirected to stderr.
"""

import sys
import traceback


UCI_STDOUT = sys.stdout
sys.stdout = sys.stderr

from bot import ChessBot  # noqa: E402


ENGINE_NAME = "MyChessBot"
ENGINE_AUTHOR = "chess-ai-project"
DEFAULT_SEARCH_MS = 30_000
DEFAULT_DEPTH = 3
MIN_DEPTH = 1
MAX_DEPTH = 10


def uci_write(message):
    """Write a single UCI protocol line to stdout."""
    UCI_STDOUT.write(message + "\n")
    UCI_STDOUT.flush()


def parse_int_option(tokens, name, default=None):
    if name not in tokens:
        return default

    index = tokens.index(name)
    if index + 1 >= len(tokens):
        return default

    try:
        return int(tokens[index + 1])
    except ValueError:
        return default


class UCIEngine:
    def __init__(self):
        self.chess_bot = ChessBot()
        self.default_depth = DEFAULT_DEPTH

    def run(self):
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue

            try:
                should_quit = self.handle_command(line)
            except Exception:
                traceback.print_exc(file=sys.stderr)
                should_quit = False

            if should_quit:
                break

    def handle_command(self, line):
        tokens = line.split()
        command = tokens[0]

        if command == "uci":
            uci_write(f"id name {ENGINE_NAME}")
            uci_write(f"id author {ENGINE_AUTHOR}")
            uci_write(
                "option name MyAI_DefaultDepth type spin "
                f"default {DEFAULT_DEPTH} min {MIN_DEPTH} max {MAX_DEPTH}"
            )
            uci_write("uciok")
            return False

        if command == "setoption":
            self.handle_setoption(tokens)
            return False

        if command == "isready":
            uci_write("readyok")
            return False

        if command == "ucinewgame":
            self.handle_new_game()
            return False

        if command == "position":
            self.handle_position(tokens)
            return False

        if command == "go":
            self.handle_go(tokens)
            return False

        if command == "stop":
            self.handle_stop()
            return False

        if command == "quit":
            self.handle_quit()
            return True

        return False

    def handle_new_game(self):
        self.handle_stop()
        self.chess_bot.set_position()
        if hasattr(self.chess_bot, "notify_new_game"):
            self.chess_bot.notify_new_game()

    def handle_setoption(self, tokens):
        name_index = self._find_token(tokens, "name", start_index=1)
        if name_index is None or name_index + 1 >= len(tokens):
            return

        value_index = self._find_token(tokens, "value", start_index=name_index + 1)
        if value_index is None:
            option_name = " ".join(tokens[name_index + 1:])
            option_value = None
        else:
            option_name = " ".join(tokens[name_index + 1:value_index])
            option_value = " ".join(tokens[value_index + 1:])

        if option_name != "MyAI_DefaultDepth" or option_value is None:
            return

        try:
            depth = int(option_value)
        except ValueError:
            return

        self.default_depth = max(MIN_DEPTH, min(MAX_DEPTH, depth))

    def handle_position(self, tokens):
        if len(tokens) < 2:
            return

        if tokens[1] == "startpos":
            moves = self._moves_after_token(tokens, start_index=2)
            self.chess_bot.set_position(moves=moves)
            return

        if tokens[1] == "fen":
            moves_index = self._find_token(tokens, "moves", start_index=2)
            fen_tokens = tokens[2:moves_index] if moves_index is not None else tokens[2:]
            fen = " ".join(fen_tokens)
            moves = tokens[moves_index + 1:] if moves_index is not None else None
            if fen:
                self.chess_bot.set_position(fen=fen, moves=moves)
            return

    def handle_go(self, tokens):
        depth = parse_int_option(tokens, "depth")

        if "movetime" in tokens:
            time_ms = parse_int_option(tokens, "movetime", DEFAULT_SEARCH_MS)
            best_move = self._get_best_move(depth=depth, time_ms=time_ms)
            uci_write(f"bestmove {best_move}")
            return

        if "wtime" in tokens or "btime" in tokens:
            wtime = parse_int_option(tokens, "wtime", 0)
            btime = parse_int_option(tokens, "btime", 0)
            winc = parse_int_option(tokens, "winc", 0)
            binc = parse_int_option(tokens, "binc", 0)
            think_time = self.chess_bot.choose_think_time(wtime, btime, winc, binc)
            best_move = self._get_best_move(depth=depth, time_ms=think_time)
            uci_write(f"bestmove {best_move}")
            return

        best_move = self._get_best_move(depth=depth, time_ms=DEFAULT_SEARCH_MS)
        uci_write(f"bestmove {best_move}")

    def handle_stop(self):
        if hasattr(self.chess_bot, "stop_thinking"):
            self.chess_bot.stop_thinking()

    def handle_quit(self):
        if hasattr(self.chess_bot, "quit"):
            self.chess_bot.quit()

    def _get_best_move(self, depth=None, time_ms=None):
        search_depth = depth if depth is not None else self.default_depth
        move = self.chess_bot.get_best_move(depth=search_depth, time_ms=time_ms)

        if move:
            return move

        legal_moves = self.chess_bot.get_legal_moves()
        if legal_moves:
            return legal_moves[0]

        return "0000"

    @staticmethod
    def _find_token(tokens, token, start_index=0):
        try:
            return tokens.index(token, start_index)
        except ValueError:
            return None

    @classmethod
    def _moves_after_token(cls, tokens, start_index=0):
        moves_index = cls._find_token(tokens, "moves", start_index=start_index)
        if moves_index is None:
            return None
        return tokens[moves_index + 1:]


def main():
    engine = UCIEngine()
    engine.run()


if __name__ == "__main__":
    main()
