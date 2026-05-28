"""
Pipeline orchestrator — runs Model A agents in sequence.

Usage:
    python run_pipeline.py --main-csv inputs/foo.csv --competition-csv inputs/bar.csv

The pipeline passes df_merged from Agent 2 → Agent 3 to avoid re-reading and re-cleaning.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import time
from pathlib import Path

from klipso.agents.data_recon import run_recon
from klipso.agents.eda import run_eda
from klipso.agents.hypothesis import run_hypothesis
from klipso.agents.business_tx import run_business_tx


def run_pipeline(main_csv: str, competition_csv: str, outputs_dir: str = "outputs") -> dict:
    print("=" * 60)
    print("KLIPSO MODEL A PIPELINE — START")
    print("=" * 60)

    Path(outputs_dir).mkdir(exist_ok=True)

    print("\n[1/4] DATA RECON")
    print("-" * 40)
    t0 = time.time()
    recon_result = run_recon(spotify_path=main_csv, competition_path=competition_csv)
    print(f"Agent 1 done in {time.time() - t0:.1f}s")

    print("\n[2/4] EDA")
    print("-" * 40)
    t0 = time.time()
    eda_result = run_eda(
        spotify_path=main_csv,
        competition_path=competition_csv,
        outputs_dir=outputs_dir,
    )
    print(f"Agent 2 done in {time.time() - t0:.1f}s")

    print("\n[3/4] HYPOTHESIS TESTING")
    print("-" * 40)
    t0 = time.time()
    hypothesis_result = run_hypothesis(
        df_merged=eda_result.get("df_merged"),  # reuses cleaned df — avoids re-reading CSVs
    )
    print(f"Agent 3 done in {time.time() - t0:.1f}s")

    print("\n[4/4] BUSINESS TRANSLATION")
    print("-" * 40)
    t0 = time.time()
    brief = run_business_tx(
        recon_result=recon_result,
        eda_result=eda_result,
        hypothesis_result=hypothesis_result,
        outputs_dir=outputs_dir,
    )
    print(f"Agent 4 done in {time.time() - t0:.1f}s")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    print("\nHypothesis verdicts:")
    for h in ["h1", "h2", "h3", "h4"]:
        print(f"  {h.upper()}: {hypothesis_result[h]['verdict']}")

    print(f"\nOutputs saved to: {outputs_dir}")
    for f in Path(outputs_dir).glob("*"):
        print(f"  {f.name}")

    return {
        "recon": recon_result,
        "eda": eda_result,
        "hypothesis": hypothesis_result,
        "brief": brief,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Klipso Model A — full pipeline")
    parser.add_argument("--main-csv",        required=True, help="Path to main platform CSV")
    parser.add_argument("--competition-csv", required=True, help="Path to cross-platform CSV")
    parser.add_argument("--outputs-dir",     default="outputs", help="Output directory")
    args = parser.parse_args()

    run_pipeline(
        main_csv=args.main_csv,
        competition_csv=args.competition_csv,
        outputs_dir=args.outputs_dir,
    )
