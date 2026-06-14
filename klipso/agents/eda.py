"""Agent 2 — EDA: descriptive statistics + correlations, dataset-agnostic."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from pathlib import Path
from langchain_core.messages import HumanMessage

from klipso.llm.provider import get_llm, llm_intermediate_enabled
from klipso.utils.profiler import build_profile, profile_to_text


def _load_df(spotify_path: str, competition_path: str) -> pd.DataFrame:
    """Carga el dataset. Single-CSV si los paths coinciden; si no, intenta merge."""
    if spotify_path == competition_path:
        return pd.read_csv(spotify_path)
    # Dos datasets distintos: intentar merge por clave común; si falla, usar el main.
    try:
        from klipso.utils.data_cleaning import load_and_fix
        _, _, df = load_and_fix(spotify_path, competition_path)
        return df
    except Exception:
        return pd.read_csv(spotify_path)


def run_eda(
    spotify_path: str,
    competition_path: str,
    outputs_dir: str = "outputs",
    llm=None,
    df_merged: pd.DataFrame = None,
) -> dict:
    """
    EDA agnóstico: perfila cualquier DataFrame (tipos, stats, correlaciones).

    Returns:
        dict con: rows, profile, top_correlations, llm_interpretation, df_merged
    """
    Path(outputs_dir).mkdir(exist_ok=True)

    if df_merged is None:
        df_merged = _load_df(spotify_path, competition_path)

    print(f"Dataset: {len(df_merged)} rows x {df_merged.shape[1]} cols")

    profile = build_profile(df_merged)
    stats_text = profile_to_text(profile)
    print(stats_text)

    # E-LLM-FINAL: si LLM_INTERMEDIATE=false, queda determinístico (sin LLM).
    if not llm_intermediate_enabled():
        llm_text = stats_text  # el perfil determinístico ES la salida
    else:
        if llm is None:
            llm = get_llm()
        prompt = f"""Eres analista de datos senior. Analiza este perfil estadístico
de un dataset (puede ser de cualquier dominio) y responde en español:
1. ¿Cuáles son las 3 correlaciones más fuertes y significativas? ¿Qué implican?
2. ¿Hay distribuciones sesgadas (skew alto) donde la media engañaría? ¿Usar mediana?
3. ¿Qué columnas tienen calidad de datos problemática (nulls altos)?
4. ¿Cuál parece la variable más informativa del dataset?

PERFIL ESTADÍSTICO:
{stats_text}
"""
        llm_text = llm.invoke([HumanMessage(content=prompt)]).content
        print("\n=== INTERPRETACIÓN (LLM) ===")
        print(llm_text)

    # Back-compat: keys que Model B (HITL) espera de A-v1. None si no aplican.
    spotify_playlist_corr = None
    if "streams" in df_merged.columns and "in_spotify_playlists" in df_merged.columns:
        spotify_playlist_corr = float(df_merged["streams"].corr(df_merged["in_spotify_playlists"]))

    return {
        # --- A-v2 agnóstico ---
        "rows": len(df_merged),
        "n_cols": df_merged.shape[1],
        "column_types": profile["types"],
        "top_correlations": profile["top_correlations"],
        "llm_interpretation": llm_text,
        "df_merged": df_merged,
        # --- back-compat A-v1 / Model B ---
        "merge_rows": len(df_merged),
        "spotify_playlist_corr": spotify_playlist_corr,
    }
