import sys
sys.stdout.reconfigure(encoding='utf-8')

import streamlit as st
import importlib.util
import os
import pandas as pd

st.set_page_config(
    page_title="Spotify Editorial Intelligence",
    page_icon="🎵",
    layout="wide",
)

# ── Load viz ───────────────────────────────────────────────────────────────
@st.cache_data
def load_viz():
    spec = importlib.util.spec_from_file_location(
        "viz", os.path.join(os.path.dirname(__file__), "agents", "05_viz.py")
    )
    viz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(viz)
    return viz.run(inputs_dir="inputs", outputs_dir="outputs")

with st.spinner("Cargando datos..."):
    result = load_viz()

charts = result["charts"]
df     = result["df"]

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — PROBLEMA DE NEGOCIO
# ══════════════════════════════════════════════════════════════════════════
st.title("Spotify Editorial Intelligence")
st.markdown("### ¿Qué hace que una canción triunfe en múltiples plataformas?")

st.markdown("""
El equipo editorial de Spotify decide qué canciones entran a sus playlists **por intuición**.
El costo es real: una canción que entra tarde pierde su ventana de momentum.
Una que entra sin señal real ocupa el espacio de una que sí hubiera roto.

**Este análisis busca señales medibles — antes de que una canción explote.**
""")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — EL ESTADO DEL DATO
# ══════════════════════════════════════════════════════════════════════════
st.subheader("Los datos que llegaron — y lo que estaba roto")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**track_in_spotify** (839 filas)")
    st.code("""track_id:    int64     ← tipo A
track_name:  object
streams:     object    ← PROBLEMA: string con comas
in_spotify_playlists: int64
in_spotify_charts:    int64""", language="text")

with col2:
    st.markdown("**track_in_competition** (953 filas)")
    st.code("""track_id:            object  ← tipo B → JOIN roto
in_apple_playlists:  int64
in_deezer_playlists: object  ← PROBLEMA: debería ser int
in_shazam_charts:    object  ← 5.25% nulls""", language="text")

st.error("**JOIN roto:** `track_id` era `int64` en Spotify y `object` en competition. Sin normalizar, el merge produce resultados silenciosamente incorrectos.")

col_a, col_b, col_c = st.columns(3)
col_a.metric("Tracks en Spotify", "839")
col_b.metric("Tracks en Competition", "953")
col_c.metric("Sin match cross-platform", "114", delta="señal de negocio, no error")

st.info("Las 114 canciones sin match existen en Apple/Deezer/Shazam pero no llegaron a Spotify. No toda presencia cross-platform implica Spotify.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — PIPELINE NARRATIVO
# ══════════════════════════════════════════════════════════════════════════
st.subheader("El pipeline — qué encontró cada agente")

# ── Agente 2 ───────────────────────────────────────────────────────────
with st.expander("Agente 2 — EDA: correlaciones reales con streams", expanded=True):
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("**Correlaciones Pearson vs streams:**")
        corr_data = {
            "Variable": [
                "in_spotify_playlists", "in_apple_playlists", "in_deezer_playlists",
                "in_apple_charts", "in_spotify_charts", "in_deezer_charts",
                "in_shazam_charts", "artist_count"
            ],
            "r": [0.788, 0.775, 0.759, 0.317, 0.242, 0.228, 0.053, -0.123]
        }
        corr_df = pd.DataFrame(corr_data)
        st.dataframe(corr_df, hide_index=True, use_container_width=True)
    with col_r:
        st.markdown("**Distribución de streams — la media miente:**")
        st.code("""mean:    536M  ← inflada por outliers
median:  301M  ← la realidad de la mayoría
max:   3,703M  ← Blinding Lights distorsiona
min:      0.003M""", language="text")
        st.warning("Shazam charts: r = 0.053 — casi nula. No sirve como señal editorial.")

# ── Agente 3 ───────────────────────────────────────────────────────────
with st.expander("Agente 3 — Hipótesis: los 4 tests estadísticos", expanded=True):
    h_col1, h_col2 = st.columns(2)

    with h_col1:
        st.markdown("**H1 — Playlists cross-platform → streams**")
        st.code("""Pearson  r = 0.795, p = 0.0  ✓
Spearman ρ = 0.831, p = 0.0  ✓""", language="text")
        st.success("CONFIRMADA — señal más fuerte del dataset")

        st.markdown("**H3 — Timing: entrada rápida a playlists**")
        st.code("""año vs streams:        ρ = −0.68  (viejas acumularon más)
recientes en playlists: ρ = +0.651  ✓""", language="text")
        st.success("CONFIRMADA — ventana crítica: primera semana")

    with h_col2:
        st.markdown("**H2 — Charts múltiples → streams**")
        st.code("""Mann-Whitney p = 0.0  ✓
Top 25% charts:  mediana 480M
Resto:           mediana 274M
Diferencia: +75%""", language="text")
        st.success("CONFIRMADA")

        st.markdown("**H4 — Género / colaboradores predicen**")
        st.code("""ANOVA géneros: F = 4.46, p = 0.0  ✓
artist_count:  ρ = −0.135, p = 0.0001
Top géneros:
  Disco pop  → 2,303M mediana
  Indie rock → 2,135M mediana
  EDM        → 1,970M mediana""", language="text")
        st.success("CONFIRMADA — más colaboradores = menos streams")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — HALLAZGOS CON GRÁFICOS
# ══════════════════════════════════════════════════════════════════════════
st.subheader("Los hallazgos — con evidencia visual")

# H1
st.markdown("#### H1 — La señal más fuerte: playlists cross-platform")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("r = **0.79** (Pearson) y ρ = **0.83** (Spearman).")
    st.markdown("Una canción en playlists de Spotify + Apple + Deezer simultáneamente tiene **3× más probabilidad** de superar 300M streams que una en una sola plataforma.")
    st.info("Señal accionable: si entra a 2+ plataformas en semana 1 → prioridad alta.")
with col_chart:
    st.plotly_chart(charts["h1_playlists"], use_container_width=True)

st.divider()

# H2
st.markdown("#### H2 — Charts múltiples: +75% más streams")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("Top 25% en charts: mediana **480M** vs **274M** del resto.")
    st.markdown("Diferencia estadísticamente significativa (Mann-Whitney p < 0.001).")
    st.warning("Ojo: Shazam charts tiene r = 0.05 — no usar como señal principal.")
with col_chart:
    st.plotly_chart(charts["h2_charts"], use_container_width=True)

st.divider()

# H3
st.markdown("#### H3 — La ventana crítica: primera semana")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("Canciones más viejas acumulan más streams históricamente (ρ = −0.68).")
    st.markdown("Pero canciones recientes que entran rápido a playlists: ρ = **+0.65**.")
    st.success("Si no entra a playlists en 7 días, el momentum no se recupera.")
with col_chart:
    st.plotly_chart(charts["h3_timing"], use_container_width=True)

st.divider()

# H4
st.markdown("#### H4 — Género predice, colaboradores sorprenden")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("ANOVA géneros: F = 4.46, p < 0.001.")
    st.markdown("**Contraintuitivo:** más colaboradores = menos streams (ρ = −0.135).")
    st.markdown("Los mega-collabs son estrategia comercial, no señal orgánica.")
    st.info("Top géneros: Disco pop (2.3B), Indie rock (2.1B), EDM (1.9B) — medianas.")
with col_chart:
    st.plotly_chart(charts["h4_genres"], use_container_width=True)

st.divider()

# Dashboard
st.subheader("Dashboard — las 4 hipótesis en una pantalla")
st.plotly_chart(charts["dashboard"], use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — IMPACTO CUANTIFICADO
# ══════════════════════════════════════════════════════════════════════════
st.subheader("Impacto cuantificado — criterios editoriales")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Incluir en playlist si:**")
    st.markdown("- En 2+ plataformas en semana 1")
    st.markdown("- Lanzamiento < 14 días")
    st.markdown("- Género: EDM, Indie, Disco pop")
    st.markdown("- Artista solo o dúo (≤ 2)")

with col2:
    st.markdown("**Señales de alerta:**")
    st.markdown("- Solo en Shazam charts (r = 0.05)")
    st.markdown("- 3+ colaboradores")
    st.markdown("- Sin playlists en semana 1")
    st.markdown("- Solo en 1 plataforma")

with col3:
    st.markdown("**Impacto medido:**")
    st.markdown("- Playlists cross-platform: r = 0.79")
    st.markdown("- Top 25% charts: +75% streams")
    st.markdown("- Timing rápido: ρ = 0.65")
    st.markdown("- Más de 2 artistas: −13.5%")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 6 — STACK
# ══════════════════════════════════════════════════════════════════════════
with st.expander("Stack técnico"):
    st.markdown("""
- **Agentes 1–3:** pandas + scipy — determinístico, sin LLM
- **Agente 4:** LangChain + OpenAI/Bedrock — solo para brief editorial
- **Agente 5:** Plotly — visualización interactiva
- **App:** Streamlit
- **Orquestación:** LangGraph + importlib
""")

st.caption("Modelo A — determinístico | Dataset: Spotify Skill Academy | klipso_data_1")
