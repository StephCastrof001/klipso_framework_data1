"""Agente 1 — Data Recon: audita schema, tipos, nulls y JOIN issues."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
from pathlib import Path
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).parent))
from setup_llm import get_llm

SPOTIFY_PATH = Path(__file__).parent.parent / "inputs" / "track_in_spotify_skill_academy.csv"
COMPETITION_PATH = Path(__file__).parent.parent / "inputs" / "track_in_competition _skill_academy.csv"


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
        lines.append("Tipos de datos:")
        for col, dtype in audit["dtypes"].items():
            null_pct = audit["null_pct"][col]
            null_flag = f"  ← {null_pct}% nulls" if null_pct > 0 else ""
            lines.append(f"  {col}: {dtype}{null_flag}")
        lines.append("")

    # JOIN analysis
    lines.append("--- JOIN ANALYSIS (track_id) ---")
    lines.append(f"  spotify  track_id dtype: {spotify_audit['dtypes'].get('track_id', 'N/A')}")
    lines.append(f"  competition track_id dtype: {competition_audit['dtypes'].get('track_id', 'N/A')}")
    lines.append(f"  rows spotify: {spotify_audit['shape'][0]}")
    lines.append(f"  rows competition: {competition_audit['shape'][0]}")
    lines.append(f"  delta: {abs(spotify_audit['shape'][0] - competition_audit['shape'][0])} tracks sin match")

    return "\n".join(lines)


def run_recon(
    spotify_path: str = str(SPOTIFY_PATH),
    competition_path: str = str(COMPETITION_PATH),
) -> dict:
    df_spotify = pd.read_csv(spotify_path)
    df_competition = pd.read_csv(competition_path)

    spotify_audit = _audit_df(df_spotify, "track_in_spotify")
    competition_audit = _audit_df(df_competition, "track_in_competition")

    recon_text = _build_recon_text(spotify_audit, competition_audit)
    print(recon_text)

    llm = get_llm()
    prompt = f"""Eres analista de datos para el equipo editorial de Spotify.
Revisa este reporte técnico de calidad de datos y responde en español con:
1. Lista de problemas críticos que bloquean el análisis (máx 5 bullets)
2. Impacto de negocio de cada problema (1 línea por problema)
3. Recomendación de qué limpiar primero

REPORTE TÉCNICO:
{recon_text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    print("\n=== INTERPRETACIÓN EDITORIAL (LLM) ===")
    print(response.content)

    # JOIN warning
    spotify_id_type = str(df_spotify["track_id"].dtype)
    competition_id_type = str(df_competition["track_id"].dtype)
    join_warning = spotify_id_type != competition_id_type

    return {
        "schema_issues": {
            col: str(dtype)
            for col, dtype in df_spotify.dtypes.items()
            if dtype == "object" and col in ["streams", "in_deezer_playlists"]
        },
        "null_counts": spotify_audit["null_counts"],
        "join_warning": join_warning,
        "join_detail": f"spotify track_id={spotify_id_type}, competition track_id={competition_id_type}",
        "llm_summary": response.content,
    }


if __name__ == "__main__":
    results = run_recon()
    print("\n=== RESULTADO ESTRUCTURADO ===")
    for k, v in results.items():
        if k != "llm_summary":
            print(f"  {k}: {v}")
