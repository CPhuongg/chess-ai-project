import subprocess
import sys
import unittest
from pathlib import Path

import chess


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UCI_ENGINE = PROJECT_ROOT / "uci_engine.py"
TIMEOUT_SECONDS = 10
DEBUG_LOG_MARKERS = (
    "Initializing searcher",
    "Starting search",
    "Found new best move",
    "Search completed",
    "Finding best move",
)


class UCIProtocolTest(unittest.TestCase):
    def run_engine(self, commands, timeout=TIMEOUT_SECONDS):
        process_input = "\n".join(commands) + "\n"
        try:
            return subprocess.run(
                [sys.executable, str(UCI_ENGINE)],
                input=process_input,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(PROJECT_ROOT),
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(
                f"uci_engine.py timed out after {timeout} seconds. "
                f"Partial stdout: {exc.stdout!r}; partial stderr: {exc.stderr!r}"
            )

    def assert_stdout_clean(self, stdout):
        for marker in DEBUG_LOG_MARKERS:
            self.assertNotIn(marker, stdout)

    def bestmove_from_stdout(self, stdout):
        for line in stdout.splitlines():
            if line.startswith("bestmove "):
                return line.split(maxsplit=1)[1].strip()
        self.fail(f"No bestmove line found in stdout: {stdout!r}")

    def assert_bestmove_is_legal(self, stdout, board):
        move_uci = self.bestmove_from_stdout(stdout)
        self.assertNotEqual(move_uci, "0000")
        try:
            move = chess.Move.from_uci(move_uci)
        except ValueError as exc:
            self.fail(f"bestmove is not valid UCI: {move_uci!r}; error: {exc}")
        self.assertIn(move, board.legal_moves)

    def test_uci_command_returns_uciok(self):
        result = self.run_engine(["uci", "quit"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("uciok", result.stdout)
        self.assertIn(
            "option name MyAI_DefaultDepth type spin default 3 min 1 max 10",
            result.stdout,
        )
        self.assert_stdout_clean(result.stdout)

    def test_isready_command_returns_readyok(self):
        result = self.run_engine(["isready", "quit"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("readyok", result.stdout)
        self.assert_stdout_clean(result.stdout)

    def test_setoption_default_depth_does_not_crash(self):
        result = self.run_engine(
            ["setoption name MyAI_DefaultDepth value 5", "isready", "quit"]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("readyok", result.stdout)
        self.assert_stdout_clean(result.stdout)

    def test_go_movetime_returns_legal_starting_position_move(self):
        result = self.run_engine(
            ["uci", "isready", "position startpos", "go movetime 1000", "quit"]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("uciok", result.stdout)
        self.assertIn("readyok", result.stdout)
        self.assert_stdout_clean(result.stdout)
        self.assert_bestmove_is_legal(result.stdout, chess.Board())

    def test_setoption_default_depth_then_go_returns_legal_move(self):
        result = self.run_engine(
            [
                "setoption name MyAI_DefaultDepth value 5",
                "position startpos",
                "go movetime 1000",
                "quit",
            ]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_stdout_clean(result.stdout)
        self.assert_bestmove_is_legal(result.stdout, chess.Board())

    def test_position_startpos_moves_returns_legal_move(self):
        moves = ["e2e4", "e7e5"]
        board = chess.Board()
        for move_uci in moves:
            board.push_uci(move_uci)

        result = self.run_engine(
            ["position startpos moves e2e4 e7e5", "go movetime 1000", "quit"]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_stdout_clean(result.stdout)
        self.assert_bestmove_is_legal(result.stdout, board)

    def test_position_fen_returns_bestmove(self):
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        result = self.run_engine(
            [f"position fen {fen}", "go movetime 1000", "quit"]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_stdout_clean(result.stdout)
        self.assertTrue(
            self.bestmove_from_stdout(result.stdout),
            f"Expected a bestmove in stdout: {result.stdout!r}",
        )


if __name__ == "__main__":
    unittest.main()
