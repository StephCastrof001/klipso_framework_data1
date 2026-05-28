"""CLI — Agent 2: EDA. Descriptive statistics, correlations, optional profiling."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import argparse
from pathlib import Path

from klipso.agents.eda import run_eda


def main():
    parser = argparse.ArgumentParser(description="Agent 2 — EDA")
    parser.add_argument("--main-csv",        required=True, help="Path to main platform CSV")
    parser.add_argument("--competition-csv", required=True, help="Path to cross-platform CSV")
    parser.add_argument("--outputs-dir",     default="outputs", help="Directory to save results")
    args = parser.parse_args()

    result = run_eda(
        spotify_path=args.main_csv,
        competition_path=args.competition_csv,
        outputs_dir=args.outputs_dir,
    )

    out_path = Path(args.outputs_dir)
    out_path.mkdir(exist_ok=True)
    saveable = {k: v for k, v in result.items() if isinstance(v, (str, dict, bool, int, float))}
    (out_path / "eda_result.json").write_text(
        json.dumps(saveable, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nSaved → {out_path / 'eda_result.json'}")


if __name__ == "__main__":
    main()
