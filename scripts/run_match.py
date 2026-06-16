"""Run a Cute Chess match for the local UCI engine.

Example:
    python scripts/run_match.py --time-control bullet_1_0 --opponent stockfish_1320 --games 2
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


MY_ENGINE_NAME = "MyAI"
DEFAULT_CUTECHESS_PATH = Path("tools") / "cutechess" / "cutechess-cli.exe"


def project_root():
    return Path(__file__).resolve().parents[1]


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def flatten_time_controls(time_controls):
    controls_by_id = {}
    for entries in time_controls.values():
        for entry in entries:
            controls_by_id[entry["id"]] = entry
    return controls_by_id


def index_by_id(entries):
    return {entry["id"]: entry for entry in entries}


def resolve_from_root(root, path_value):
    path = Path(path_value)
    if path.is_absolute():
        return path
    return root / path


def require_file(path, label):
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")


def shell_display(command):
    if sys.platform.startswith("win"):
        return subprocess.list2cmdline([str(part) for part in command])

    import shlex

    return shlex.join(str(part) for part in command)


def build_command(root, cutechess_path, time_control, opponent, games, pgn_path):
    python_exe = Path(sys.executable)
    uci_engine = root / "uci_engine.py"
    stockfish_exe = resolve_from_root(root, opponent["cmd"])

    command = [
        str(cutechess_path),
        "-engine",
        f"cmd={python_exe}",
        f"arg={uci_engine}",
        f"dir={root}",
        f"name={MY_ENGINE_NAME}",
        "proto=uci",
        "-engine",
        f"cmd={stockfish_exe}",
        f"name={opponent['name']}",
        f"proto={opponent.get('proto', 'uci')}",
    ]

    for option_name, option_value in opponent.get("options", {}).items():
        command.append(f"option.{option_name}={option_value}")

    command.extend(
        [
            "-each",
            f"tc={time_control['cutechess_tc']}",
            "-games",
            str(games),
            "-repeat",
            "-pgnout",
            str(pgn_path),
        ]
    )

    return command


def parse_args():
    parser = argparse.ArgumentParser(description="Run MyAI vs a configured Stockfish opponent.")
    parser.add_argument("--time-control", required=True, help="Time control id, e.g. bullet_1_0.")
    parser.add_argument("--opponent", required=True, help="Opponent id, e.g. stockfish_1320.")
    parser.add_argument("--games", required=True, type=int, help="Number of games to run.")
    parser.add_argument(
        "--cutechess-path",
        default=str(DEFAULT_CUTECHESS_PATH),
        help="Path to cutechess-cli.exe. Defaults to tools/cutechess/cutechess-cli.exe.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the command without running it.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = project_root()

    if args.games <= 0:
        raise ValueError("--games must be a positive integer.")

    uci_engine = root / "uci_engine.py"
    time_controls_path = root / "configs" / "time_controls.json"
    stockfish_levels_path = root / "configs" / "stockfish_levels.json"
    cutechess_path = resolve_from_root(root, args.cutechess_path)

    require_file(uci_engine, "UCI engine")
    require_file(time_controls_path, "Time controls config")
    require_file(stockfish_levels_path, "Stockfish levels config")
    require_file(cutechess_path, "cutechess-cli")

    time_controls = flatten_time_controls(load_json(time_controls_path))
    opponents = index_by_id(load_json(stockfish_levels_path))

    if args.time_control not in time_controls:
        available = ", ".join(sorted(time_controls))
        raise KeyError(f"Unknown time control: {args.time_control}. Available: {available}")

    if args.opponent not in opponents:
        available = ", ".join(sorted(opponents))
        raise KeyError(f"Unknown opponent: {args.opponent}. Available: {available}")

    time_control = time_controls[args.time_control]
    opponent = opponents[args.opponent]
    stockfish_exe = resolve_from_root(root, opponent["cmd"])
    require_file(stockfish_exe, "Stockfish executable")

    results_dir = root / "results" / time_control["category"]
    results_dir.mkdir(parents=True, exist_ok=True)

    file_stem = f"myai_vs_{opponent['id']}_{time_control['id']}"
    pgn_path = results_dir / f"{file_stem}.pgn"
    stdout_path = results_dir / f"{file_stem}_out.txt"
    stderr_path = results_dir / f"{file_stem}_err.txt"

    command = build_command(root, cutechess_path, time_control, opponent, args.games, pgn_path)

    print("Cute Chess command:")
    print(shell_display(command))

    if args.dry_run:
        print("Dry run: command was not executed.")
        return 0

    with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        result = subprocess.run(
            command,
            cwd=str(root),
            stdout=stdout_file,
            stderr=stderr_file,
            check=False,
        )

    print(f"Exit code: {result.returncode}")
    print(f"PGN path: {pgn_path}")
    print(f"stdout log path: {stdout_path}")
    print(f"stderr log path: {stderr_path}")

    if result.returncode != 0:
        print("stderr:")
        print(stderr_path.read_text(encoding="utf-8", errors="replace"))

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
