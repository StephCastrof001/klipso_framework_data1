# Modelo A — Gaps identificados post-benchmark

## Fecha de revisión
2026-05-27

## Baseline (Modelo A — entregado)

Pipeline 4 agentes determinísticos + Agent 5 viz + Streamlit app.
Hipótesis H1-H4 confirmadas. Dataset cross-platform (839 tracks, 2 CSVs).

**Resultado:** 5 gráficos Plotly interactivos, brief editorial LLM, app.py en Streamlit.

---

## Gaps encontrados

### Gap 1 — Estadísticas de tendencia central
**Qué falta:** KPIs muestran solo la media (`mean`). El dataset de streams tiene distribución
altamente sesgada (algunos hits con miles de millones distorsionan la media).
**Referencia benchmark:** Nayankoli repo usa mediana como métrica principal para streams.
**Impacto:** La mediana es más honesta. 274M streams (mediana real) vs 514M (media inflada por outliers).
**Fix en A.1:** Agregar mediana al KPI de `app.py` + nota editorial sobre distribución sesgada.

### Gap 2 — Audio DNA (features de audio)
**Qué falta:** No tenemos BPM, danceability_%, energy_%, valence_%, acousticness_%, etc.
**Referencia benchmark:** Nayankoli CSV tiene 10 columnas de audio features + cover_url.
**Impacto:** No podemos responder H5: "¿El audio DNA predice popularidad?"
**Fix en A.1:** JOIN enriquecido entre nuestro dataset y Nayankoli CSV por `track_name + artist`.
Agrega H5 como hipótesis adicional: correlación bpm/energy/danceability vs streams.

### Gap 3 — Visualización de distribución
**Qué falta:** No hay histograma ni boxplot de la distribución de streams.
**Referencia benchmark:** Power BI ref (Spotify-Data-Analysis-using-Power-Bi) muestra
distribución completa con percentiles.
**Impacto:** El lector no ve el skew del dataset — puede malinterpretar los promedios.
**Fix en A.1:** Agregar chart de distribución de streams (histogram + IQR) en app.py.

### Gap 4 — Outlier explícito
**Qué falta:** Outliers no están identificados visualmente.
**Referencia benchmark:** Nayankoli hace outlier removal en ML pipeline.
**Impacto:** Correlaciones pueden estar infladas por mega-hits (Bad Bunny, Taylor Swift).
**Fix en A.1:** Scatter H1 con outliers marcados en color distinto. Recalcular r sin outliers.

---

## Lo que Modelo A tiene que ellos NO tienen

| Ventaja Modelo A | Por qué importa |
|---|---|
| Dataset de 2 CSVs con JOIN | Demuestra data engineering real |
| Análisis cross-platform (Apple + Deezer + Shazam) | Más completo que single-platform |
| main_music_genre + main_country | Permite H4 (género/país) |
| Streamlit app narrativa | Portfolio-ready vs Jupyter estático |
| Pipeline modular (5 agentes) | Arquitectura reutilizable |

---

## Decisión de diseño

Modelo A NO se modifica. Sus outputs (5 HTML + editorial_brief.md) quedan como están.
Modelo A.1 es una rama separada del análisis con los gaps cubiertos.
Ambos conviven en el portfolio como evidencia de iteración CRISP-DM.
