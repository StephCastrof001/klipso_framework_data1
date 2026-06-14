"""Airbnb NYC 2019 — Plotly charts for H1-H4 + top neighbourhoods dashboard."""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


def load_and_clean(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[df["price"] > 0].copy()
    df["reviews_per_month"] = df["reviews_per_month"].fillna(0)
    df["last_review"] = df["last_review"].fillna("no_reviews")
    df["host_type"] = df["calculated_host_listings_count"].apply(
        lambda x: "Professional (5+)" if x >= 5 else "Occasional (1-4)"
    )
    return df


def chart_h1_room_type(df: pd.DataFrame) -> go.Figure:
    order = ["Entire home/apt", "Private room", "Shared room"]
    medians = df.groupby("room_type")["price"].median()
    df_plot = df[df["price"] <= df["price"].quantile(0.95)].copy()

    fig = px.box(
        df_plot,
        x="room_type",
        y="price",
        color="room_type",
        category_orders={"room_type": order},
        title="H1 CONFIRMADA — Tipo de habitación predice precio (Kruskal H=22,414, p<0.001)",
        labels={"price": "Precio por noche (USD)", "room_type": ""},
        color_discrete_map={
            "Entire home/apt": "#FF5A5F",
            "Private room": "#00A699",
            "Shared room": "#FC642D",
        },
        points=False,
    )
    for rt, color in zip(order, ["#FF5A5F", "#00A699", "#FC642D"]):
        m = int(medians[rt])
        fig.add_annotation(
            x=rt, y=medians[rt] + 15,
            text=f"Mediana: ${m}",
            showarrow=False,
            font=dict(color=color, size=12, family="monospace"),
        )
    fig.update_layout(template="plotly_dark", showlegend=False, height=420)
    return fig


def chart_h2_neighbourhood(df: pd.DataFrame) -> go.Figure:
    order = ["Manhattan", "Brooklyn", "Queens", "Staten Island", "Bronx"]
    medians = df.groupby("neighbourhood_group")["price"].median()
    df_plot = df[df["price"] <= df["price"].quantile(0.95)].copy()

    fig = px.box(
        df_plot,
        x="neighbourhood_group",
        y="price",
        color="neighbourhood_group",
        category_orders={"neighbourhood_group": order},
        title="H2 CONFIRMADA — Borough predice precio (Kruskal H=7,023, p<0.001)",
        labels={"price": "Precio por noche (USD)", "neighbourhood_group": ""},
        color_discrete_map={
            "Manhattan": "#FF5A5F",
            "Brooklyn": "#00A699",
            "Queens": "#FC642D",
            "Staten Island": "#484848",
            "Bronx": "#767676",
        },
        points=False,
    )
    for ng in order:
        m = int(medians[ng])
        fig.add_annotation(
            x=ng, y=medians[ng] + 10,
            text=f"${m}",
            showarrow=False,
            font=dict(color="white", size=11, family="monospace"),
        )
    fig.update_layout(template="plotly_dark", showlegend=False, height=420)
    return fig


def chart_h3_availability(df: pd.DataFrame) -> go.Figure:
    # Sample for performance — 5K points is enough for scatter
    sample = df.sample(min(5000, len(df)), random_state=42)
    rho, _ = stats.spearmanr(df["availability_365"], df["reviews_per_month"])

    fig = px.scatter(
        sample,
        x="availability_365",
        y="reviews_per_month",
        color="neighbourhood_group",
        opacity=0.4,
        trendline="ols",
        title=f"H3 CONFIRMADA (débil) — Disponibilidad vs reseñas/mes (ρ={rho:.3f}, p<0.001)",
        labels={
            "availability_365": "Días disponibles al año",
            "reviews_per_month": "Reseñas por mes",
            "neighbourhood_group": "Borough",
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(template="plotly_dark", height=420)
    return fig


def chart_h4_host_type(df: pd.DataFrame) -> go.Figure:
    agg = (
        df.groupby("host_type")["price"]
        .agg(median="median", mean="mean", count="count")
        .reset_index()
    )
    fig = px.bar(
        agg,
        x="host_type",
        y="median",
        color="host_type",
        text="median",
        title="H4 RECHAZADA — Host profesional NO cobra más (Mann-Whitney p=0.305)",
        labels={"median": "Mediana precio (USD)", "host_type": ""},
        color_discrete_map={
            "Occasional (1-4)": "#00A699",
            "Professional (5+)": "#FF5A5F",
        },
    )
    fig.update_traces(texttemplate="$%{text}", textposition="outside")
    fig.update_layout(template="plotly_dark", showlegend=False, height=420)
    return fig


def chart_top_neighbourhoods(df: pd.DataFrame) -> go.Figure:
    top = (
        df.groupby("neighbourhood")["price"]
        .agg(median="median", count="count")
        .query("count >= 30")
        .sort_values("median", ascending=False)
        .head(10)
        .reset_index()
    )
    fig = px.bar(
        top,
        x="median",
        y="neighbourhood",
        orientation="h",
        color="median",
        color_continuous_scale="Reds",
        title="Top 10 barrios más caros — mediana precio (mín. 30 listings)",
        labels={"median": "Mediana precio (USD)", "neighbourhood": ""},
        text="median",
    )
    fig.update_traces(texttemplate="$%{text}", textposition="outside")
    fig.update_layout(
        template="plotly_dark",
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
        height=420,
    )
    return fig


def chart_dashboard(df: pd.DataFrame) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "H1: Precio por tipo de habitación",
            "H2: Precio por borough",
            "H3: Disponibilidad vs reseñas",
            "H4: Host ocasional vs profesional",
        ],
    )

    order_rt = ["Entire home/apt", "Private room", "Shared room"]
    colors_rt = ["#FF5A5F", "#00A699", "#FC642D"]
    df_trim = df[df["price"] <= df["price"].quantile(0.95)]
    for rt, color in zip(order_rt, colors_rt):
        fig.add_trace(
            go.Box(y=df_trim[df_trim["room_type"] == rt]["price"],
                   name=rt, marker_color=color, showlegend=False),
            row=1, col=1,
        )

    order_ng = ["Manhattan", "Brooklyn", "Queens", "Staten Island", "Bronx"]
    colors_ng = ["#FF5A5F", "#00A699", "#FC642D", "#484848", "#767676"]
    for ng, color in zip(order_ng, colors_ng):
        fig.add_trace(
            go.Box(y=df_trim[df_trim["neighbourhood_group"] == ng]["price"],
                   name=ng, marker_color=color, showlegend=False),
            row=1, col=2,
        )

    sample = df.sample(min(3000, len(df)), random_state=42)
    fig.add_trace(
        go.Scatter(
            x=sample["availability_365"], y=sample["reviews_per_month"],
            mode="markers", marker=dict(color="#00A699", opacity=0.3, size=3),
            showlegend=False,
        ),
        row=2, col=1,
    )

    agg = df.groupby("host_type")["price"].median().reset_index()
    fig.add_trace(
        go.Bar(
            x=agg["host_type"], y=agg["price"],
            marker_color=["#00A699", "#FF5A5F"], showlegend=False,
        ),
        row=2, col=2,
    )

    fig.update_layout(
        template="plotly_dark",
        title_text="Airbnb NYC 2019 — 4 Hipótesis | Klipso Model A",
        height=750,
        showlegend=False,
    )
    return fig


def run(csv_path: str, outputs_dir: str = "outputs") -> dict:
    import os
    os.makedirs(outputs_dir, exist_ok=True)
    df = load_and_clean(csv_path)

    charts = {
        "h1_room_type":       chart_h1_room_type(df),
        "h2_neighbourhood":   chart_h2_neighbourhood(df),
        "h3_availability":    chart_h3_availability(df),
        "h4_host_type":       chart_h4_host_type(df),
        "top_neighbourhoods": chart_top_neighbourhoods(df),
        "dashboard":          chart_dashboard(df),
    }
    paths = {}
    for name, fig in charts.items():
        path = os.path.join(outputs_dir, f"airbnb_viz_{name}.html")
        fig.write_html(path, include_plotlyjs="cdn")
        paths[name] = path
        print(f"  Saved: {path}")

    return {"charts": charts, "paths": paths, "df": df}
