"""Analyze Cute Chess PGN results and estimate relative Elo.

Example:
    python scripts/analyze_results.py --pgn results/bullet/myai_vs_stockfish_1320_bullet_1_0.pgn --engine MyAI --opponent-elo 1320
"""

import argparse
import math
from pathlib import Path

import chess.pgn


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze a Cute Chess PGN match result.")
    parser.add_argument("--pgn", required=True, help="Path to the PGN file to analyze.")
    parser.add_argument("--engine", required=True, help="Engine name to score, e.g. MyAI.")
    parser.add_argument(
        "--opponent-elo",
        type=float,
        default=None,
        help="Opponent Elo used to estimate the engine Elo.",
    )
    parser.add_argument("--output", help="Optional markdown output path.")
    return parser.parse_args()


def normalize_name(name):
    return (name or "").strip().casefold()


def game_score_for_engine(game, engine_name):
    white = normalize_name(game.headers.get("White"))
    black = normalize_name(game.headers.get("Black"))
    engine = normalize_name(engine_name)
    result = game.headers.get("Result", "*")

    if engine == white:
        if result == "1-0":
            return 1.0
        if result == "0-1":
            return 0.0
        if result == "1/2-1/2":
            return 0.5
    elif engine == black:
        if result == "0-1":
            return 1.0
        if result == "1-0":
            return 0.0
        if result == "1/2-1/2":
            return 0.5

    return None


def analyze_pgn(pgn_path, engine_name):
    wins = 0
    draws = 0
    losses = 0
    skipped = 0

    with pgn_path.open("r", encoding="utf-8", errors="replace") as pgn_file:
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break

            score = game_score_for_engine(game, engine_name)
            if score is None:
                skipped += 1
            elif score == 1.0:
                wins += 1
            elif score == 0.5:
                draws += 1
            else:
                losses += 1

    total_games = wins + draws + losses
    score = None if total_games == 0 else (wins + 0.5 * draws) / total_games
    return {
        "total_games": total_games,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "skipped": skipped,
        "score": score,
    }


def estimate_elo(score, opponent_elo):
    if score is None or score <= 0.0 or score >= 1.0:
        return None, None

    elo_diff = 400 * math.log10(score / (1 - score))
    estimated_elo = None if opponent_elo is None else opponent_elo + elo_diff
    return elo_diff, estimated_elo


def format_percent(score):
    if score is None:
        return "N/A"
    return f"{score:.3f} ({score * 100:.1f}%)"


def format_elo(value):
    if value is None:
        return "N/A"
    return f"{value:.1f}"


def build_report(pgn_path, engine_name, opponent_elo, stats):
    elo_diff, estimated_elo = estimate_elo(stats["score"], opponent_elo)
    unstable = stats["score"] in (0.0, 1.0) if stats["score"] is not None else True

    lines = [
        f"PGN: {pgn_path}",
        f"Engine: {engine_name}",
        f"Opponent Elo: {format_elo(opponent_elo)}",
        "",
        f"Games: {stats['total_games']}",
        f"Wins: {stats['wins']}",
        f"Draws: {stats['draws']}",
        f"Losses: {stats['losses']}",
        f"Score: {format_percent(stats['score'])}",
        f"Elo diff: {format_elo(elo_diff)}",
        f"Estimated Elo: {format_elo(estimated_elo)}",
    ]

    if stats["skipped"]:
        lines.append(f"Skipped games: {stats['skipped']}")

    if unstable:
        lines.extend(
            [
                "",
                "Note: the result is too one-sided or the sample is too small for a stable Elo estimate.",
            ]
        )

    return "\n".join(lines)


def write_markdown(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "# PGN Match Analysis\n\n```text\n" + report + "\n```\n"
    path.write_text(content, encoding="utf-8")


def main():
    args = parse_args()
    pgn_path = Path(args.pgn)
    if not pgn_path.is_file():
        raise FileNotFoundError(f"PGN file not found: {pgn_path}")

    stats = analyze_pgn(pgn_path, args.engine)
    report = build_report(pgn_path, args.engine, args.opponent_elo, stats)
    print(report)

    if args.output:
        output_path = Path(args.output)
        write_markdown(output_path, report)
        print("")
        print(f"Wrote markdown report: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
