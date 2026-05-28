"""Agente 2 — EDA Auto: estadísticas, correlaciones, ydata-profiling, sweetviz."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np
from pathlib import Path
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).parent))
from setup_llm import get_llm

SPOTIFY_PATH = Path(__file__).parent.parent / "inputs" / "track_in_spotify_skill_academy.csv"
COMPETITION_PATH = Path(__file__).parent.parent / "inputs" / "track_in_competition _skill_academy.csv"
OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"


def fix_types(df_spotify: pd.DataFrame, df_competition: pd.DataFrame) -> tuple:
    """Corrige tipos sucios detectados en Agente 1."""
    df_s = df_spotify.copy()
    df_c = df_competition.copy()

    df_s["streams"] = pd.to_numeric(
        df_s["streams"].astype(str).str.replace(",", ""), errors="coerce"
    )
    df_c["in_deezer_playlists"] = pd.to_numeric(df_c["in_deezer_playlists"], errors="coerce")
    df_c["in_shazam_charts"] = pd.to_numeric(df_c["in_shazam_charts"], errors="coerce")
    df_c["track_id"] = pd.to_numeric(df_c["track_id"], errors="coerce").astype("Int64")
    df_s["track_id"] = df_s["track_id"].astype("Int64")

    return df_s, df_c


def merge_tables(df_spotify: pd.DataFrame, df_competition: pd.DataFrame) -> pd.DataFrame:
    return df_spotify.merge(df_competition, on="track_id", how="inner")


def _build_stats_text(df: pd.DataFrame) -> str:
    lines = ["=== EDA STATS REPORT ===\n"]
    lines.append(f"Filas tras merge inner: {len(df)}")
    lines.append(f"Columnas: {list(df.columns)}\n")

    key_cols = [c for c in [
        "streams", "in_spotify_playlists", "in_apple_playlists",
        "in_deezer_playlists", "in_spotify_charts", "in_apple_charts",
        "in_deezer_charts", "in_shazam_charts", "artist_count",
    ] if c in df.columns]

    lines.append("--- Estadísticas descriptivas ---")
    lines.append(df[key_cols].describe().round(0).to_string())
    lines.append("")

    lines.append("--- Correlación con streams (Pearson) ---")
    for col in key_cols:
        if col != "streams":
            mask = df[["streams", col]].dropna()
            if len(mask) > 10:
                r = mask["streams"].corr(mask[col])
                lines.append(f"  streams ↔ {col}: r={r:.3f}")

    lines.append("\n--- Top 5 géneros por mediana de streams ---")
    lines.append(
        df.groupby("main_music_genre")["streams"]
        .agg(count="count", median_streams="median")
        .sort_values("median_streams", ascending=False)
        .head(5)
        .to_string()
    )

    lines.append("\n--- Top 5 países por mediana de streams ---")
    lines.append(
        df.groupby("main_country")["streams"]
        .agg(count="count", median_streams="median")
        .sort_values("median_streams", ascending=False)
        .head(5)
        .to_string()
    )

    return "\n".join(lines)


def run_eda(
    spotify_path: str = str(SPOTIFY_PATH),
    competition_path: str = str(COMPETITION_PATH),
) -> dict:
    OUTPUTS_DIR.mkdir(exist_ok=True)

    df_spotify = pd.read_csv(spotify_path)
    df_competition = pd.read_csv(competition_path)
    df_spotify, df_competition = fix_types(df_spotify, df_competition)
    df_merged = merge_tables(df_spotify, df_competition)

    print(f"Merge inner: {len(df_merged)} tracks con datos cross-platform")

    stats_text = _build_stats_text(df_merged)
    print(stats_text)

    profile_path = None
    try:
        from ydata_profiling import ProfileReport
        profile = ProfileReport(df_merged, minimal=True, title="Spotify Editorial EDA")
        profile_path = OUTPUTS_DIR / "eda_profile.html"
        profile.to_file(profile_path)
        print(f"\nydata-profiling → {profile_path}")
    except ImportError:
        print("\nydata-profiling no instalado")

    sv_path = None
    try:
        import sweetviz as sv
        sv_cols = [c for c in [
            "streams", "in_spotify_playlists", "in_apple_playlists",
            "in_spotify_charts", "in_apple_charts",
        ] if c in df_merged.columns]
        report = sv.analyze(df_merged[sv_cols])
        sv_path = OUTPUTS_DIR / "eda_sweetviz.html"
        report.show_html(str(sv_path), open_browser=False)
        print(f"sweetviz → {sv_path}")
    except ImportError:
        print("sweetviz no instalado")

    llm = get_llm()
    prompt = f"""Eres analista de datos del equipo editorial de Spotify.
Analiza estos resultados y responde en español:
1. ¿Qué 3 variables tienen correlación más fuerte con streams? ¿Qué significa para el editor?
2. ¿Qué géneros y países lideran? ¿Algo sorpresivo?
3. ¿Hay outliers o distribuciones que advertir al equipo editorial?
4. ¿Cuál es la variable más importante para predecir éxito?

ESTADÍSTICAS:
{stats_text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    print("\n=== INTERPRETACIÓN EDITORIAL (LLM) ===")
    print(response.content)

    return {
        "merge_rows": len(df_merged),
        "spotify_playlist_corr": float(df_merged["streams"].corr(df_merged["in_spotify_playlists"])) if "in_spotify_playlists" in df_merged.columns else None,
        "profile_path": str(profile_path) if profile_path else None,
        "sweetviz_path": str(sv_path) if sv_path else None,
        "llm_interpretation": response.content,
        "df_merged": df_merged,
    }


if __name__ == "__main__":
    results = run_eda()
    print("\n=== RESULTADO ===")
    for k, v in results.items():
        if k not in ["llm_interpretation", "df_merged"]:
            print(f"  {k}: {v}")
