"""CLI — Agent 5: Visualization. 5 interactive Plotly charts for the 4 hypotheses."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse

from klipso.agents.viz import run


def main():
    parser = argparse.ArgumentParser(description="Agent 5 — Visualization")
    parser.add_argument("--main-csv",        required=True, help="Path to main platform CSV")
    parser.add_argument("--competition-csv", required=True, help="Path to cross-platform CSV")
    parser.add_argument("--outputs-dir",     default="outputs", help="Directory to save HTML charts")
    args = parser.parse_args()

    run(
        spotify_path=args.main_csv,
        competition_path=args.competition_csv,
        outputs_dir=args.outputs_dir,
    )


if __name__ == "__main__":
    main()
