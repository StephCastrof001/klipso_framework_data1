"""Agent 2 — EDA: descriptive statistics, correlations, optional profiling reports."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from pathlib import Path
from langchain_core.messages import HumanMessage

from klipso.llm.provider import get_llm
from klipso.utils.data_cleaning import load_and_fix


def _build_stats_text(df: pd.DataFrame) -> str:
    lines = ["=== EDA STATS REPORT ===\n"]
    lines.append(f"Rows after inner merge: {len(df)}")
    lines.append(f"Columns: {list(df.columns)}\n")

    key_cols = [c for c in [
        "streams", "in_spotify_playlists", "in_apple_playlists",
        "in_deezer_playlists", "in_spotify_charts", "in_apple_charts",
        "in_deezer_charts", "in_shazam_charts", "artist_count",
    ] if c in df.columns]

    lines.append("--- Descriptive statistics ---")
    lines.append(df[key_cols].describe().round(0).to_string())
    lines.append("")

    lines.append("--- Pearson correlation with streams ---")
    for col in key_cols:
        if col != "streams":
            mask = df[["streams", col]].dropna()
            if len(mask) > 10:
                r = mask["streams"].corr(mask[col])
                lines.append(f"  streams ↔ {col}: r={r:.3f}")

    lines.append("\n--- Top 5 genres by median streams ---")
    lines.append(
        df.groupby("main_music_genre")["streams"]
        .agg(count="count", median_streams="median")
        .sort_values("median_streams", ascending=False)
        .head(5)
        .to_string()
    )

    lines.append("\n--- Top 5 countries by median streams ---")
    lines.append(
        df.groupby("main_country")["streams"]
        .agg(count="count", median_streams="median")
        .sort_values("median_streams", ascending=False)
        .head(5)
        .to_string()
    )

    return "\n".join(lines)


def run_eda(
    spotify_path: str,
    competition_path: str,
    outputs_dir: str = "outputs",
    llm=None,
    df_merged: pd.DataFrame = None,
) -> dict:
    """
    Runs exploratory data analysis on the merged dataset.

    Args:
        spotify_path: Path to main platform CSV.
        competition_path: Path to cross-platform CSV.
        outputs_dir: Directory for optional HTML profile reports.
        llm: Optional pre-built LangChain LLM.
        df_merged: Pre-merged DataFrame (skips load+merge if provided).

    Returns:
        dict with keys: merge_rows, spotify_playlist_corr, profile_path,
                        sweetviz_path, llm_interpretation, df_merged
    """
    Path(outputs_dir).mkdir(exist_ok=True)

    if df_merged is None:
        _, _, df_merged = load_and_fix(spotify_path, competition_path)

    print(f"Merge inner: {len(df_merged)} tracks with cross-platform data")

    stats_text = _build_stats_text(df_merged)
    print(stats_text)

    profile_path = None
    try:
        from ydata_profiling import ProfileReport
        profile = ProfileReport(df_merged, minimal=True, title="Spotify Editorial EDA")
        profile_path = str(Path(outputs_dir) / "eda_profile.html")
        profile.to_file(profile_path)
        print(f"\nydata-profiling → {profile_path}")
    except ImportError:
        print("\nydata-profiling not installed (pip install klipso[profiling])")

    sv_path = None
    try:
        import sweetviz as sv
        sv_cols = [c for c in [
            "streams", "in_spotify_playlists", "in_apple_playlists",
            "in_spotify_charts", "in_apple_charts",
        ] if c in df_merged.columns]
        report = sv.analyze(df_merged[sv_cols])
        sv_path = str(Path(outputs_dir) / "eda_sweetviz.html")
        report.show_html(sv_path, open_browser=False)
        print(f"sweetviz → {sv_path}")
    except ImportError:
        print("sweetviz not installed (pip install klipso[profiling])")

    if llm is None:
        llm = get_llm()

    prompt = f"""You are a data analyst for a music editorial team.
Analyze these results and respond in Spanish:
1. Which 3 variables have the strongest correlation with streams? What does it mean for the editor?
2. Which genres and countries lead? Anything surprising?
3. Are there outliers or distributions the editorial team should be warned about?
4. Which is the most important variable for predicting success?

STATISTICS:
{stats_text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    print("\n=== INTERPRETACIÓN EDITORIAL (LLM) ===")
    print(response.content)

    return {
        "merge_rows": len(df_merged),
        "spotify_playlist_corr": float(df_merged["streams"].corr(df_merged["in_spotify_playlists"]))
            if "in_spotify_playlists" in df_merged.columns else None,
        "profile_path": profile_path,
        "sweetviz_path": sv_path,
        "llm_interpretation": response.content,
        "df_merged": df_merged,
    }
