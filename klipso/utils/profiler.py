"""Generic dataset profiler — dataset-agnostic.

Detecta tipos de columna y produce estadísticas sin asumir nombres de columna.
Reemplaza la lógica hardcodeada a Spotify (streams/genres/countries) por
detección dinámica. Mantiene el rigor: correlaciones, mediana, skew, significancia.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from scipy import stats


def detect_column_types(df: pd.DataFrame) -> dict:
    """Clasifica columnas en numeric / categorical / datetime sin hardcode.

    - numeric: dtype numérico con >2 valores únicos
    - categorical: object/category, o numérico con baja cardinalidad
    - datetime: dtype datetime o columnas parseables
    """
    numeric, categorical, datetime_cols = [], [], []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_datetime64_any_dtype(s):
            datetime_cols.append(col)
        elif pd.api.types.is_numeric_dtype(s):
            # numérico con muy baja cardinalidad → tratar como categórico (ej. binario)
            if s.nunique(dropna=True) <= 2:
                categorical.append(col)
            else:
                numeric.append(col)
        else:
            categorical.append(col)
    return {"numeric": numeric, "categorical": categorical, "datetime": datetime_cols}


def numeric_summary(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    """Describe numéricas + skew (clave para detectar media-mentirosa)."""
    if not numeric_cols:
        return pd.DataFrame()
    desc = df[numeric_cols].describe().T
    desc["median"] = df[numeric_cols].median()
    desc["skew"] = df[numeric_cols].skew()
    return desc.round(3)


def correlation_matrix(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    """Matriz de correlación Pearson entre numéricas."""
    if len(numeric_cols) < 2:
        return pd.DataFrame()
    return df[numeric_cols].corr(method="pearson").round(3)


def top_correlations(df: pd.DataFrame, numeric_cols: list[str], n: int = 8) -> list[dict]:
    """Top N pares de correlación más fuertes (|r|), con significancia.

    Retorna lista de dicts: {a, b, r, p, significant}. Esto reemplaza las
    hipótesis hardcodeadas — funciona con cualquier set de columnas numéricas.
    """
    results = []
    cols = [c for c in numeric_cols if df[c].notna().sum() > 10]
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a, b = cols[i], cols[j]
            mask = df[[a, b]].dropna()
            if len(mask) < 10:
                continue
            try:
                r, p = stats.pearsonr(mask[a], mask[b])
            except Exception:
                continue
            results.append({
                "a": a, "b": b,
                "r": round(float(r), 3),
                "p": round(float(p), 5),
                "significant": bool(p < 0.05),
                "n": int(len(mask)),
            })
    results.sort(key=lambda d: abs(d["r"]), reverse=True)
    return results[:n]


def categorical_summary(df: pd.DataFrame, categorical_cols: list[str], top: int = 5) -> dict:
    """Top valores por columna categórica (cardinalidad + distribución)."""
    out = {}
    for col in categorical_cols:
        vc = df[col].value_counts(dropna=True).head(top)
        out[col] = {
            "cardinality": int(df[col].nunique(dropna=True)),
            "top_values": {str(k): int(v) for k, v in vc.items()},
        }
    return out


def build_profile(df: pd.DataFrame) -> dict:
    """Perfil completo agnóstico de cualquier DataFrame."""
    types = detect_column_types(df)
    return {
        "shape": df.shape,
        "types": types,
        "null_pct": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
        "numeric_summary": numeric_summary(df, types["numeric"]),
        "correlations": correlation_matrix(df, types["numeric"]),
        "top_correlations": top_correlations(df, types["numeric"]),
        "categorical_summary": categorical_summary(df, types["categorical"]),
    }


def profile_to_text(profile: dict) -> str:
    """Reporte de texto legible del perfil (para prompts LLM + logs)."""
    lines = ["=== GENERIC DATA PROFILE ===\n"]
    lines.append(f"Shape: {profile['shape'][0]} rows x {profile['shape'][1]} cols")
    t = profile["types"]
    lines.append(f"Numeric: {t['numeric']}")
    lines.append(f"Categorical: {t['categorical']}")
    lines.append(f"Datetime: {t['datetime']}\n")

    nulls = {k: v for k, v in profile["null_pct"].items() if v > 0}
    if nulls:
        lines.append("--- Columns with nulls ---")
        for k, v in sorted(nulls.items(), key=lambda x: -x[1]):
            lines.append(f"  {k}: {v}%")
        lines.append("")

    if not profile["numeric_summary"].empty:
        lines.append("--- Numeric summary (median + skew) ---")
        lines.append(profile["numeric_summary"][["median", "mean", "std", "skew"]].to_string())
        lines.append("")

    if profile["top_correlations"]:
        lines.append("--- Top correlations (Pearson, p-value) ---")
        for c in profile["top_correlations"]:
            sig = "✓ sig" if c["significant"] else "  ns"
            lines.append(f"  {c['a']} ↔ {c['b']}: r={c['r']:+.3f} p={c['p']:.4f} [{sig}] n={c['n']}")
        lines.append("")

    if profile["categorical_summary"]:
        lines.append("--- Categorical columns ---")
        for col, info in profile["categorical_summary"].items():
            lines.append(f"  {col}: {info['cardinality']} unique, top={list(info['top_values'].keys())[:3]}")

    return "\n".join(lines)
