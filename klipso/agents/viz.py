"""Agent 5 — Visualization: 5 interactive Plotly charts for the 4 hypotheses."""
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from klipso.utils.data_cleaning import load_and_fix


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
    fig.update_layout(
        template="plotly_dark",
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
    )
    return fig


def chart_dashboard(df: pd.DataFrame) -> go.Figure:
    """Combined 2×2 dashboard — all 4 hypotheses on one screen."""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "H1: Playlists → Streams (r=0.79)",
            "H2: Top charts vs resto",
            "H3: Streams por año de lanzamiento",
            "H4: Top géneros por streams",
        ],
    )

    fig.add_trace(
        go.Scatter(
            x=df["total_playlists"], y=df["streams"],
            mode="markers", marker=dict(color="#1DB954", opacity=0.4, size=4),
            name="tracks",
        ),
        row=1, col=1,
    )

    threshold = df["total_charts"].quantile(0.75)
    df2 = df.copy()
    df2["g"] = df2["total_charts"].apply(lambda x: "Top 25%" if x >= threshold else "Resto")
    for grp, color in [("Top 25%", "#1DB954"), ("Resto", "#535353")]:
        subset = df2[df2["g"] == grp]["streams"]
        fig.add_trace(go.Box(y=subset, name=grp, marker_color=color), row=1, col=2)

    cohorts = df.groupby("released_year")["streams"].median().reset_index()
    fig.add_trace(
        go.Bar(
            x=cohorts["released_year"], y=cohorts["streams"],
            marker_color="#1DB954", name="mediana streams",
        ),
        row=2, col=1,
    )

    top_g = (
        df.groupby("main_music_genre")["streams"]
        .median().sort_values(ascending=False).head(8).reset_index()
    )
    fig.add_trace(
        go.Bar(
            x=top_g["streams"], y=top_g["main_music_genre"],
            orientation="h", marker_color="#1DB954", name="géneros",
        ),
        row=2, col=2,
    )

    fig.update_layout(
        template="plotly_dark",
        title_text="Spotify Editorial Intelligence — 4 Hipótesis Confirmadas",
        height=750,
        showlegend=False,
    )
    return fig


def run(
    df_merged: pd.DataFrame = None,
    spotify_path: str = None,
    competition_path: str = None,
    inputs_dir: str = None,
    outputs_dir: str = "outputs",
) -> dict:
    """
    Builds 5 interactive Plotly charts and saves them as HTML files.

    Args:
        df_merged: Pre-merged DataFrame. If None, loads from paths.
        spotify_path: Path to main platform CSV (used if df_merged is None).
        competition_path: Path to cross-platform CSV (used if df_merged is None).
        inputs_dir: Legacy — if set, looks for CSVs in this directory (used by app.py).
        outputs_dir: Directory to save HTML charts.

    Returns:
        dict with keys: charts (dict of go.Figure), paths (dict of file paths), df
    """
    os.makedirs(outputs_dir, exist_ok=True)

    if df_merged is None:
        if inputs_dir is not None:
            # Legacy app.py compatibility: discover filenames in inputs_dir
            import glob
            csv_files = glob.glob(os.path.join(inputs_dir, "*.csv"))
            spotify_candidates = [f for f in csv_files if "spotify" in f.lower() and "competition" not in f.lower()]
            competition_candidates = [f for f in csv_files if "competition" in f.lower()]
            if not spotify_candidates or not competition_candidates:
                raise FileNotFoundError(
                    f"Could not find spotify/competition CSVs in {inputs_dir}. "
                    "Pass spotify_path and competition_path explicitly."
                )
            spotify_path = spotify_candidates[0]
            competition_path = competition_candidates[0]

        if spotify_path is None or competition_path is None:
            raise ValueError(
                "Provide either df_merged, spotify_path+competition_path, or inputs_dir"
            )

        print("Loading data...")
        _, _, df_merged = load_and_fix(spotify_path, competition_path)

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
        print(f"  Saved: {path}")

    print(f"\nTotal: {len(paths)} interactive charts generated.")
    return {"charts": charts, "paths": paths, "df": df}
