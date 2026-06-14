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


def _build_recon_text(spotify_audit: dict, competition_audit: dict, join_key: str = None) -> str:
    audits = [spotify_audit] if spotify_audit is competition_audit else [spotify_audit, competition_audit]
    lines = ["=== DATA RECON REPORT ===\n"]
    for audit in audits:
        lines.append(f"--- {audit['name']} ---")
        lines.append(f"Shape: {audit['shape']}")
        lines.append("Column types:")
        for col, dtype in audit["dtypes"].items():
            null_pct = audit["null_pct"][col]
            null_flag = f"  ← {null_pct}% nulls" if null_pct > 0 else ""
            lines.append(f"  {col}: {dtype}{null_flag}")
        lines.append("")

    # JOIN analysis solo si hay clave de join compartida y dos datasets distintos
    if join_key and spotify_audit is not competition_audit:
        lines.append(f"--- JOIN ANALYSIS ({join_key}) ---")
        lines.append(f"  main  {join_key} dtype: {spotify_audit['dtypes'].get(join_key, 'N/A')}")
        lines.append(f"  competition {join_key} dtype: {competition_audit['dtypes'].get(join_key, 'N/A')}")
        lines.append(f"  rows main: {spotify_audit['shape'][0]}")
        lines.append(f"  rows competition: {competition_audit['shape'][0]}")
        lines.append(f"  delta: {abs(spotify_audit['shape'][0] - competition_audit['shape'][0])} rows without match")

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
    # Single-CSV mode: si main == competition, no hay segundo dataset real.
    single_mode = (spotify_path == competition_path)
    df_competition = df_spotify if single_mode else pd.read_csv(competition_path)

    # Detectar clave de join compartida (track_id u otra col comun) si hay 2 datasets.
    join_key = None
    if not single_mode:
        common = set(df_spotify.columns) & set(df_competition.columns)
        for cand in ("track_id", "id"):
            if cand in common:
                join_key = cand
                break

    spotify_audit = _audit_df(df_spotify, "main")
    competition_audit = spotify_audit if single_mode else _audit_df(df_competition, "competition")

    recon_text = _build_recon_text(spotify_audit, competition_audit, join_key)
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

    # JOIN warning solo aplica si hay clave de join real entre 2 datasets.
    join_warning = False
    join_detail = "single-dataset (sin join)"
    if join_key and not single_mode:
        main_id_type = str(df_spotify[join_key].dtype)
        comp_id_type = str(df_competition[join_key].dtype)
        join_warning = main_id_type != comp_id_type
        join_detail = f"main {join_key}={main_id_type}, competition {join_key}={comp_id_type}"

    return {
        "schema_issues": {
            col: str(dtype)
            for col, dtype in df_spotify.dtypes.items()
            if dtype == "object" and col in ["streams", "in_deezer_playlists"]
        },
        "null_counts": spotify_audit["null_counts"],
        "join_warning": join_warning,
        "join_detail": join_detail,
        "llm_summary": response.content,
    }
