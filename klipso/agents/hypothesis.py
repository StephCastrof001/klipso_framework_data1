"""Agent 3 — Hypothesis Testing: statistical tests, dataset-agnostic.

En vez de hipótesis hardcodeadas (Spotify), auto-genera hipótesis desde las
correlaciones más fuertes del dataset y las prueba con significancia. Mantiene
el rigor (Pearson + Spearman + p-value) y el insight firma: media vs mediana
en distribuciones sesgadas.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from scipy import stats
from langchain_core.messages import HumanMessage

from klipso.llm.provider import get_llm
from klipso.utils.profiler import build_profile


def _verdict(r: float, p: float) -> str:
    if p < 0.05 and abs(r) > 0.3:
        return "CONFIRMADA"
    if p < 0.05:
        return "DÉBIL"
    return "RECHAZADA"


def _test_correlation_hypotheses(df: pd.DataFrame, top_corrs: list[dict]) -> list[dict]:
    """Cada correlación fuerte = una hipótesis testeada con Pearson + Spearman."""
    results = []
    for i, c in enumerate(top_corrs, 1):
        a, b = c["a"], c["b"]
        mask = df[[a, b]].dropna()
        if len(mask) < 10:
            continue
        r, p = stats.pearsonr(mask[a], mask[b])
        rho, p_s = stats.spearmanr(mask[a], mask[b])
        results.append({
            "hypothesis": f"H{i}",
            "statement": f"{a} se relaciona con {b}",
            "pearson_r": round(float(r), 3),
            "pearson_p": round(float(p), 4),
            "spearman_rho": round(float(rho), 3),
            "spearman_p": round(float(p_s), 4),
            "n": int(len(mask)),
            "verdict": _verdict(r, p),
        })
    return results


def _detect_skew_warnings(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict]:
    """Detecta columnas donde la media engaña por skew (insight firma del framework)."""
    warnings = []
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) < 10:
            continue
        skew = float(s.skew())
        if abs(skew) > 1.0:  # distribución muy sesgada
            warnings.append({
                "column": col,
                "skew": round(skew, 2),
                "mean": round(float(s.mean()), 2),
                "median": round(float(s.median()), 2),
                "note": "media inflada por outliers — usar mediana como KPI",
            })
    return warnings


def _build_hypothesis_text(results: list, skew_warnings: list) -> str:
    lines = ["=== HYPOTHESIS TESTING REPORT (agnostic) ===\n"]
    for h in results:
        lines.append(f"--- {h['hypothesis']}: {h['statement']} ---")
        lines.append(f"  Verdict: {h['verdict']}")
        lines.append(f"  Pearson r={h['pearson_r']} (p={h['pearson_p']}), "
                     f"Spearman rho={h['spearman_rho']} (p={h['spearman_p']}), n={h['n']}")
        lines.append("")
    if skew_warnings:
        lines.append("--- SKEW WARNINGS (media vs mediana) ---")
        for w in skew_warnings:
            lines.append(f"  {w['column']}: skew={w['skew']}, mean={w['mean']} vs median={w['median']} — {w['note']}")
    return "\n".join(lines)


def run_hypothesis(
    spotify_path: str = None,
    competition_path: str = None,
    df_merged: pd.DataFrame = None,
    llm=None,
) -> dict:
    """Prueba hipótesis auto-generadas desde las correlaciones del dataset."""
    if df_merged is None:
        if spotify_path is None:
            raise ValueError("df_merged o spotify_path requerido")
        if competition_path and competition_path != spotify_path:
            try:
                from klipso.utils.data_cleaning import load_and_fix
                _, _, df_merged = load_and_fix(spotify_path, competition_path)
            except Exception:
                df_merged = pd.read_csv(spotify_path)
        else:
            df_merged = pd.read_csv(spotify_path)

    profile = build_profile(df_merged)
    numeric_cols = profile["types"]["numeric"]

    hypotheses = _test_correlation_hypotheses(df_merged, profile["top_correlations"])
    skew_warnings = _detect_skew_warnings(df_merged, numeric_cols)

    hypothesis_text = _build_hypothesis_text(hypotheses, skew_warnings)
    print(hypothesis_text)

    if llm is None:
        llm = get_llm()

    prompt = f"""Eres analista de datos senior. Estas hipótesis se auto-generaron
de las correlaciones más fuertes del dataset y se probaron con significancia.
Responde en español:
1. ¿Qué hipótesis tiene la evidencia más fuerte? ¿Qué implica?
2. ¿Algún resultado contra-intuitivo? (ej. correlación esperada que resultó nula)
3. ¿Las advertencias de skew importan? ¿Dónde la media engañaría?
4. Las 3 señales estadísticas más accionables del dataset

RESULTADOS:
{hypothesis_text}
"""
    response = llm.invoke([HumanMessage(content=prompt)])
    print("\n=== INTERPRETACIÓN (LLM) ===")
    print(response.content)

    return {
        "hypotheses": hypotheses,
        "skew_warnings": skew_warnings,
        "n_confirmed": sum(1 for h in hypotheses if h["verdict"] == "CONFIRMADA"),
        "n_tested": len(hypotheses),
        "llm_interpretation": response.content,
    }
