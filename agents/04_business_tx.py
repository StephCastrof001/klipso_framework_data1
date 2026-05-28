"""CLI — Agent 4: Business Translation. Statistical findings → editorial criteria (LLM)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import argparse
from pathlib import Path

from klipso.agents.business_tx import run_business_tx


def _load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"[WARNING] {path} not found — agent 4 will run without this context")
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Agent 4 — Business Translation")
    parser.add_argument(
        "--outputs-dir", default="outputs",
        help="Directory containing recon_result.json, eda_result.json, hypothesis_result.json"
    )
    parser.add_argument(
        "--recon-json", default=None,
        help="Override path to recon_result.json"
    )
    parser.add_argument(
        "--eda-json", default=None,
        help="Override path to eda_result.json"
    )
    parser.add_argument(
        "--hypothesis-json", default=None,
        help="Override path to hypothesis_result.json"
    )
    args = parser.parse_args()

    out = args.outputs_dir
    recon     = _load_json(args.recon_json      or f"{out}/recon_result.json")
    eda       = _load_json(args.eda_json        or f"{out}/eda_result.json")
    hypothesis = _load_json(args.hypothesis_json or f"{out}/hypothesis_result.json")

    run_business_tx(
        recon_result=recon,
        eda_result=eda,
        hypothesis_result=hypothesis,
        outputs_dir=out,
    )


if __name__ == "__main__":
    main()
