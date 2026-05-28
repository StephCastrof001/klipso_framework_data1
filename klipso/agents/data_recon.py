"""Agent 1 — Data Recon: audits schema, types, nulls, and JOIN issues."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from langchain_core.messages import HumanMessage

from klipso.llm.provider import get_llm


def _audit_df(df: pd.DataFrame, name: str) -> dict:
    return {
        "name": name,
        "shape": df.shape,
        "dtypes": df.dtypes.to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "null_pct": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "sample_values": {col: df[col].dropna().head(3).tolist() for col in df.columns},
    }


def _build_recon_text(spotify_audit: dict, competition_audit: dict) -> str:
    lines = ["=== DATA RECON REPORT ===\n"]
    for audit in [spotify_audit, competition_audit]:
        lines.append(f"--- {audit['name']} ---")
        lines.append(f"Shape: {audit['shape']}")
        lines.append("Column types:")
        for col, dtype in audit["dtypes"].items():
            null_pct = audit["null_pct"][col]
            null_flag = f"  ← {null_pct}% nulls" if null_pct > 0 else ""
            lines.append(f"  {col}: {dtype}{null_flag}")
        lines.append("")

    lines.append("--- JOIN ANALYSIS (track_id) ---")
    lines.append(f"  spotify  track_id dtype: {spotify_audit['dtypes'].get('track_id', 'N/A')}")
    lines.append(f"  competition track_id dtype: {competition_audit['dtypes'].get('track_id', 'N/A')}")
    lines.append(f"  rows spotify: {spotify_audit['shape'][0]}")
    lines.append(f"  rows competition: {competition_audit['shape'][0]}")
    lines.append(f"  delta: {abs(spotify_audit['shape'][0] - competition_audit['shape'][0])} tracks without match")

    return "\n".join(lines)


def run_recon(
    spotify_path: str,
    competition_path: str,
    llm=None,
) -> dict:
    """
    Audits two CSVs for schema issues, null values, and JOIN compatibility.

    Args:
        spotify_path: Path to the main platform CSV.
        competition_path: Path to the cross-platform competition CSV.
        llm: Optional pre-built LangChain LLM. If None, loads from .env via get_llm().

    Returns:
        dict with keys: schema_issues, null_counts, join_warning, join_detail, llm_summary
    """
    df_spotify = pd.read_csv(spotify_path)
    df_competition = pd.read_csv(competition_path)

    spotify_audit = _audit_df(df_spotify, "track_in_spotify")
    competition_audit = _audit_df(df_competition, "track_in_competition")

    recon_text = _build_recon_text(spotify_audit, competition_audit)
    print(recon_text)

    if llm is None:
        llm = get_llm()

    prompt = f"""You are a data analyst for a music editorial team.
Review this data quality report and respond in Spanish with:
1. List of critical problems blocking analysis (max 5 bullets)
2. Business impact of each problem (1 line per problem)
3. Recommendation on what to clean first

TECHNICAL REPORT:
{recon_text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    print("\n=== INTERPRETACIÓN EDITORIAL (LLM) ===")
    print(response.content)

    spotify_id_type = str(df_spotify["track_id"].dtype)
    competition_id_type = str(df_competition["track_id"].dtype)

    return {
        "schema_issues": {
            col: str(dtype)
            for col, dtype in df_spotify.dtypes.items()
            if dtype == "object" and col in ["streams", "in_deezer_playlists"]
        },
        "null_counts": spotify_audit["null_counts"],
        "join_warning": spotify_id_type != competition_id_type,
        "join_detail": f"spotify track_id={spotify_id_type}, competition track_id={competition_id_type}",
        "llm_summary": response.content,
    }
