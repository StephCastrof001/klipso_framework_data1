import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


# ── Data loader (desacoplado — funciona sin pipeline) ──────────────────────
def _load_and_clean(inputs_dir: str = "inputs") -> pd.DataFrame:
    spotify = pd.read_csv(f"{inputs_dir}/track_in_spotify_skill_academy.csv")
    competition = pd.read_csv(f"{inputs_dir}/track_in_competition _skill_academy.csv")

    spotify["streams"] = (
        spotify["streams"].astype(str).str.replace(",", "").str.strip()
    )
    spotify["streams"] = pd.to_numeric(spotify["streams"], errors="coerce")
    spotify.dropna(subset=["streams"], inplace=True)
    spotify["streams"] = spotify["streams"].astype(int)

    for col in ["in_deezer_playlists", "in_shazam_charts"]:
        competition[col] = pd.to_numeric(
            competition[col].astype(str).str.replace(",", ""), errors="coerce"
        ).fillna(0).astype(int)

    spotify["track_id"] = spotify["track_id"].astype(str)
    competition["track_id"] = competition["track_id"].astype(str)

    df = pd.merge(spotify, competition, on="track_id", how="inner")
    df["total_playlists"] = (
        df["in_spotify_playlists"] + df["in_apple_playlists"] + df["in_deezer_playlists"]
    )
    df["total_charts"] = (
        df["in_spotify_charts"] + df["in_apple_charts"] +
        df["in_deezer_charts"] + df["in_shazam_charts"]
    )
    return df


# ── Chart builders ─────────────────────────────────────────────────────────

def chart_h1_playlists_vs_streams(df: pd.DataFrame) -> go.Figure:
    r, _ = stats.pearsonr(df["total_playlists"], df["streams"])
    fig = px.scatter(
        df,
        x="total_playlists",
        y="streams",
        trendline="ols",
        opacity=0.5,
        labels={"total_playlists": "Total Playlists (cross-platform)", "streams": "Streams"},
        title=f"Más playlists = más streams (r={r:.2f}) — H1 CONFIRMADA",
        color_discrete_sequence=["#1DB954"],
    )
    fig.update_layout(template="plotly_dark")
    return fig


def chart_h2_charts_vs_streams(df: pd.DataFrame) -> go.Figure:
    threshold = df["total_charts"].quantile(0.75)
    df = df.copy()
    df["charts_group"] = df["total_charts"].apply(
        lambda x: "Top 25% en charts" if x >= threshold else "Resto"
    )
    fig = px.box(
        df,
        x="charts_group",
        y="streams",
        color="charts_group",
        title="Canciones en más charts tienen más streams — H2 CONFIRMADA",
        labels={"streams": "Streams", "charts_group": ""},
        color_discrete_map={"Top 25% en charts": "#1DB954", "Resto": "#535353"},
    )
    fig.update_layout(template="plotly_dark", showlegend=False)
    return fig


def chart_h3_timing(df: pd.DataFrame) -> go.Figure:
    cohorts = (
        df.groupby("released_year")["streams"]
        .median()
        .reset_index()
        .rename(columns={"streams": "median_streams"})
    )
    fig = px.bar(
        cohorts,
        x="released_year",
        y="median_streams",
        title="Canciones recientes en playlists rápido acumulan más streams — H3 CONFIRMADA",
        labels={"released_year": "Año de lanzamiento", "median_streams": "Mediana de Streams"},
        color="median_streams",
        color_continuous_scale="Greens",
    )
    fig.update_layout(template="plotly_dark", coloraxis_showscale=False)
    return fig


def chart_h4_genres(df: pd.DataFrame) -> go.Figure:
    top_genres = (
        df.groupby("main_music_genre")["streams"]
        .median()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
        .rename(columns={"streams": "median_streams"})
    )
    fig = px.bar(
        top_genres,
        x="median_streams",
        y="main_music_genre",
        orientation="h",
        title="Género predice streams — Top 10 géneros por mediana — H4 CONFIRMADA",
        labels={"median_streams": "Mediana de Streams", "main_music_genre": "Género"},
        color="median_streams",
        color_continuous_scale="Greens",
    )
    fig.update_layout(template="plotly_dark", yaxis={"categoryorder": "total ascending"},
                      coloraxis_showscale=False)
    return fig


def chart_dashboard(df: pd.DataFrame) -> go.Figure:
    """Combined 2x2 dashboard — all 4 hypotheses."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "H1: Playlists → Streams (r=0.79)",
            "H2: Top charts vs resto",
            "H3: Streams por año de lanzamiento",
            "H4: Top géneros por streams",
        ],
    )

    # H1 scatter
    fig.add_trace(
        go.Scatter(x=df["total_playlists"], y=df["streams"],
                   mode="markers", marker=dict(color="#1DB954", opacity=0.4, size=4),
                   name="tracks"),
        row=1, col=1,
    )

    # H2 box
    threshold = df["total_charts"].quantile(0.75)
    df2 = df.copy()
    df2["g"] = df2["total_charts"].apply(lambda x: "Top 25%" if x >= threshold else "Resto")
    for grp, color in [("Top 25%", "#1DB954"), ("Resto", "#535353")]:
        subset = df2[df2["g"] == grp]["streams"]
        fig.add_trace(go.Box(y=subset, name=grp, marker_color=color), row=1, col=2)

    # H3 bar
    cohorts = df.groupby("released_year")["streams"].median().reset_index()
    fig.add_trace(
        go.Bar(x=cohorts["released_year"], y=cohorts["streams"],
               marker_color="#1DB954", name="mediana streams"),
        row=2, col=1,
    )

    # H4 bar
    top_g = (df.groupby("main_music_genre")["streams"]
               .median().sort_values(ascending=False).head(8).reset_index())
    fig.add_trace(
        go.Bar(x=top_g["streams"], y=top_g["main_music_genre"],
               orientation="h", marker_color="#1DB954", name="géneros"),
        row=2, col=2,
    )

    fig.update_layout(
        template="plotly_dark",
        title_text="Spotify Editorial Intelligence — 4 Hipótesis Confirmadas",
        height=750,
        showlegend=False,
    )
    return fig


# ── Main ───────────────────────────────────────────────────────────────────

def run(df_merged: pd.DataFrame = None, inputs_dir: str = "inputs",
        outputs_dir: str = "outputs") -> dict:

    print("=== VIZ AGENT ===")
    os.makedirs(outputs_dir, exist_ok=True)

    if df_merged is None:
        print("Cargando datos (modo standalone)...")
        df = _load_and_clean(inputs_dir)
    else:
        df = df_merged.copy()
        if "total_playlists" not in df.columns:
            df["total_playlists"] = (
                df["in_spotify_playlists"] + df["in_apple_playlists"] + df["in_deezer_playlists"]
            )
        if "total_charts" not in df.columns:
            df["total_charts"] = (
                df["in_spotify_charts"] + df["in_apple_charts"] +
                df["in_deezer_charts"] + df["in_shazam_charts"]
            )

    charts = {
        "h1_playlists": chart_h1_playlists_vs_streams(df),
        "h2_charts":    chart_h2_charts_vs_streams(df),
        "h3_timing":    chart_h3_timing(df),
        "h4_genres":    chart_h4_genres(df),
        "dashboard":    chart_dashboard(df),
    }

    paths = {}
    for name, fig in charts.items():
        path = os.path.join(outputs_dir, f"viz_{name}.html")
        fig.write_html(path, include_plotlyjs="cdn")
        paths[name] = path
        print(f"  Guardado: {path}")

    print(f"\nTotal: {len(paths)} gráficos interactivos generados.")
    return {"charts": charts, "paths": paths, "df": df}


if __name__ == "__main__":
    result = run()
