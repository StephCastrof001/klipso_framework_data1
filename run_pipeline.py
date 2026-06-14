"""
Pipeline orchestrator — runs Model A agents in sequence.

Usage:
    python run_pipeline.py --main-csv inputs/foo.csv --competition-csv inputs/bar.csv

The pipeline passes df_merged from Agent 2 → Agent 3 to avoid re-reading and re-cleaning.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
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
    for h in hypothesis_result.get("hypotheses", []):
        print(f"  {h['hypothesis']}: {h['verdict']} ({h['statement']})")

    # --- Eval JSON (Capa 5): captura hallazgos para benchmark/acumulación ---
    eval_obj = {
        "rows": eda_result.get("rows"),
        "n_cols": eda_result.get("n_cols"),
        "column_types": eda_result.get("column_types"),
        "top_correlations": eda_result.get("top_correlations"),
        "hypotheses": hypothesis_result.get("hypotheses"),
        "skew_warnings": hypothesis_result.get("skew_warnings"),
        "n_confirmed": hypothesis_result.get("n_confirmed"),
        "n_tested": hypothesis_result.get("n_tested"),
        "null_counts": recon_result.get("null_counts"),
    }
    eval_path = Path(outputs_dir) / "eval.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_obj, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nEval → {eval_path}")

    print(f"\nOutputs saved to: {outputs_dir}")
    for f in Path(outputs_dir).glob("*"):
        print(f"  {f.name}")

    return {
        "recon": recon_result,
        "eda": eda_result,
        "hypothesis": hypothesis_result,
        "brief": brief,
        "eval": eval_obj,
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
