"""Agent 3 — Hypothesis Testing: statistical tests for H1-H4."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from scipy import stats
from langchain_core.messages import HumanMessage

from klipso.llm.provider import get_llm
from klipso.utils.data_cleaning import load_and_fix


def _test_h1(df: pd.DataFrame) -> dict:
    """H1: More cross-platform playlists → more streams."""
    playlist_cols = [c for c in [
        "in_spotify_playlists", "in_apple_playlists", "in_deezer_playlists"
    ] if c in df.columns]
    df = df.copy()
    df["total_playlists"] = df[playlist_cols].sum(axis=1)

    mask = df[["total_playlists", "streams"]].dropna()
    r, p = stats.pearsonr(mask["total_playlists"], mask["streams"])
    rho, p_s = stats.spearmanr(mask["total_playlists"], mask["streams"])

    return {
        "hypothesis": "H1",
        "statement": "Más playlists cross-platform → más streams",
        "pearson_r": round(r, 3),
        "pearson_p": round(p, 4),
        "spearman_rho": round(rho, 3),
        "spearman_p": round(p_s, 4),
        "verdict": "CONFIRMADA" if p < 0.05 and abs(r) > 0.3 else "DÉBIL" if p < 0.05 else "RECHAZADA",
    }


def _test_h2(df: pd.DataFrame) -> dict:
    """H2: Presence in multiple charts → more streams."""
    chart_cols = [c for c in [
        "in_spotify_charts", "in_apple_charts", "in_deezer_charts", "in_shazam_charts"
    ] if c in df.columns]
    df = df.copy()
    df["total_charts"] = df[chart_cols].sum(axis=1)

    mask = df[["total_charts", "streams"]].dropna()
    r, p = stats.pearsonr(mask["total_charts"], mask["streams"])

    threshold = df["total_charts"].quantile(0.75)
    top = df.loc[df["total_charts"] >= threshold, "streams"].dropna()
    rest = df.loc[df["total_charts"] < threshold, "streams"].dropna()
    _, p_mw = stats.mannwhitneyu(top, rest, alternative="greater")

    return {
        "hypothesis": "H2",
        "statement": "Charts múltiples cross-platform → más streams",
        "pearson_r": round(r, 3),
        "pearson_p": round(p, 4),
        "mann_whitney_p": round(p_mw, 4),
        "top25pct_charts_median_streams": int(top.median()),
        "rest_median_streams": int(rest.median()),
        "verdict": "CONFIRMADA" if p_mw < 0.05 else "RECHAZADA",
    }


def _test_h3(df: pd.DataFrame) -> dict:
    """H3: Recent songs entering playlists quickly → more streams."""
    rho_year, p_year = stats.spearmanr(df["released_year"], df["streams"], nan_policy="omit")

    df_recent = df[df["released_year"] >= df["released_year"].quantile(0.75)]
    rho_recent, p_recent = stats.spearmanr(
        df_recent["in_spotify_playlists"], df_recent["streams"], nan_policy="omit"
    )

    return {
        "hypothesis": "H3",
        "statement": "Canciones recientes en playlists rápido → más streams",
        "year_vs_streams_rho": round(rho_year, 3),
        "year_vs_streams_p": round(p_year, 4),
        "recent_playlist_rho": round(rho_recent, 3),
        "recent_playlist_p": round(p_recent, 4),
        "verdict": (
            "CONFIRMADA" if p_recent < 0.05 and rho_recent > 0.3
            else "PARCIAL" if p_recent < 0.05
            else "RECHAZADA"
        ),
    }


def _test_h4(df: pd.DataFrame) -> dict:
    """H4: Genre / country / collaborators predict streams."""
    rho_collab, p_collab = stats.spearmanr(df["artist_count"], df["streams"], nan_policy="omit")

    genre_groups = [
        group["streams"].dropna().values
        for _, group in df.groupby("main_music_genre")
        if len(group) >= 5
    ]
    f_stat, p_anova = stats.f_oneway(*genre_groups) if len(genre_groups) >= 2 else (None, None)

    top_genres = (
        df.groupby("main_music_genre")["streams"]
        .median()
        .sort_values(ascending=False)
        .head(3)
        .to_dict()
    )

    return {
        "hypothesis": "H4",
        "statement": "Género / país / colaboradores predicen streams",
        "artist_count_rho": round(rho_collab, 3),
        "artist_count_p": round(p_collab, 4),
        "genre_anova_f": round(f_stat, 2) if f_stat is not None else None,
        "genre_anova_p": round(p_anova, 4) if p_anova is not None else None,
        "top3_genres_by_median_streams": {k: int(v) for k, v in top_genres.items()},
        "verdict": (
            "CONFIRMADA"
            if p_collab < 0.05 or (p_anova is not None and p_anova < 0.05)
            else "RECHAZADA"
        ),
    }


def _build_hypothesis_text(results: list) -> str:
    lines = ["=== HYPOTHESIS TESTING REPORT ===\n"]
    for h in results:
        lines.append(f"--- {h['hypothesis']}: {h['statement']} ---")
        lines.append(f"  Verdict: {h['verdict']}")
        for k, v in h.items():
            if k not in ["hypothesis", "statement", "verdict"]:
                lines.append(f"  {k}: {v}")
        lines.append("")
    return "\n".join(lines)


def run_hypothesis(
    spotify_path: str = None,
    competition_path: str = None,
    df_merged: pd.DataFrame = None,
    llm=None,
) -> dict:
    """
    Runs H1-H4 statistical hypothesis tests.

    Args:
        spotify_path: Path to main platform CSV. Required if df_merged is None.
        competition_path: Path to cross-platform CSV. Required if df_merged is None.
        df_merged: Pre-merged DataFrame (skips load+merge if provided).
        llm: Optional pre-built LangChain LLM.

    Returns:
        dict with keys: h1, h2, h3, h4, llm_interpretation
    """
    if df_merged is None:
        if spotify_path is None or competition_path is None:
            raise ValueError("Either df_merged or both spotify_path and competition_path are required")
        _, _, df_merged = load_and_fix(spotify_path, competition_path)

    h1 = _test_h1(df_merged)
    h2 = _test_h2(df_merged)
    h3 = _test_h3(df_merged)
    h4 = _test_h4(df_merged)

    hypothesis_text = _build_hypothesis_text([h1, h2, h3, h4])
    print(hypothesis_text)

    if llm is None:
        llm = get_llm()

    prompt = f"""You are a data analyst for a music editorial team.
Analyze these hypothesis results and respond in Spanish:
1. Which hypothesis has the strongest evidence? What does it mean for the editor?
2. Any surprising or counter-intuitive results?
3. Limitations of the analysis (max 2)
4. The 3 most actionable statistical signals for editorial criteria

RESULTS:
{hypothesis_text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    print("\n=== INTERPRETACIÓN EDITORIAL (LLM) ===")
    print(response.content)

    return {
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "h4": h4,
        "llm_interpretation": response.content,
    }
