"""CLI — Agent 1: Data Recon. Audits schema, types, nulls, and JOIN issues."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import argparse
from pathlib import Path

from klipso.agents.data_recon import run_recon


def main():
    parser = argparse.ArgumentParser(description="Agent 1 — Data Recon")
    parser.add_argument("--main-csv",        required=True, help="Path to main platform CSV")
    parser.add_argument("--competition-csv", required=True, help="Path to cross-platform CSV")
    parser.add_argument("--outputs-dir",     default="outputs", help="Directory to save results")
    args = parser.parse_args()

    result = run_recon(
        spotify_path=args.main_csv,
        competition_path=args.competition_csv,
    )

    # Save serializable keys for downstream agents
    out_path = Path(args.outputs_dir)
    out_path.mkdir(exist_ok=True)
    saveable = {k: v for k, v in result.items() if isinstance(v, (str, dict, bool, int, float))}
    (out_path / "recon_result.json").write_text(
        json.dumps(saveable, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nSaved → {out_path / 'recon_result.json'}")


if __name__ == "__main__":
    main()
