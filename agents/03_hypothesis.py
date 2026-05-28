"""Agente 3 — Hypothesis Testing: prueba estadística de H1-H4."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).parent))
from setup_llm import get_llm

SPOTIFY_PATH = Path(__file__).parent.parent / "inputs" / "track_in_spotify_skill_academy.csv"
COMPETITION_PATH = Path(__file__).parent.parent / "inputs" / "track_in_competition _skill_academy.csv"


def _fix_and_merge(spotify_path: str, competition_path: str) -> pd.DataFrame:
    """Re-usa la misma lógica de limpieza del Agente 2."""
    df_s = pd.read_csv(spotify_path)
    df_c = pd.read_csv(competition_path)

    df_s["streams"] = pd.to_numeric(
        df_s["streams"].astype(str).str.replace(",", ""), errors="coerce"
    )
    df_c["in_deezer_playlists"] = pd.to_numeric(df_c["in_deezer_playlists"], errors="coerce")
    df_c["in_shazam_charts"] = pd.to_numeric(df_c["in_shazam_charts"], errors="coerce")
    df_c["track_id"] = pd.to_numeric(df_c["track_id"], errors="coerce").astype("Int64")
    df_s["track_id"] = df_s["track_id"].astype("Int64")

    return df_s.merge(df_c, on="track_id", how="inner")


def _test_h1(df: pd.DataFrame) -> dict:
    """H1: Más playlists cross-platform → más streams."""
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
    """H2: Presencia en múltiples charts → más streams."""
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
    """H3: Canciones recientes en playlists rápido → más streams."""
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
    """H4: Género / país / colaboradores predicen streams."""
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
        lines.append(f"  Veredicto: {h['verdict']}")
        for k, v in h.items():
            if k not in ["hypothesis", "statement", "verdict"]:
                lines.append(f"  {k}: {v}")
        lines.append("")
    return "\n".join(lines)


def run_hypothesis(
    spotify_path: str = str(SPOTIFY_PATH),
    competition_path: str = str(COMPETITION_PATH),
    df_merged: pd.DataFrame = None,
) -> dict:
    if df_merged is None:
        df_merged = _fix_and_merge(spotify_path, competition_path)

    h1 = _test_h1(df_merged)
    h2 = _test_h2(df_merged)
    h3 = _test_h3(df_merged)
    h4 = _test_h4(df_merged)

    hypothesis_text = _build_hypothesis_text([h1, h2, h3, h4])
    print(hypothesis_text)

    llm = get_llm()
    prompt = f"""Eres analista de datos del equipo editorial de Spotify.
Analiza estos resultados de hipótesis y responde en español:
1. ¿Cuál hipótesis tiene evidencia más sólida? ¿Qué significa para el editor?
2. ¿Algún resultado sorpresivo o contra-intuitivo?
3. Limitaciones del análisis (máx 2)
4. Las 3 señales estadísticas más accionables para criterio editorial

RESULTADOS:
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


if __name__ == "__main__":
    results = run_hypothesis()
    print("\n=== VEREDICTOS ===")
    for key in ["h1", "h2", "h3", "h4"]:
        h = results[key]
        print(f"  {h['hypothesis']}: {h['verdict']}")
