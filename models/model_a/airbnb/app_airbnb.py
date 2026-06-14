import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import streamlit as st
import pandas as pd

from models.model_a.airbnb.viz_airbnb import load_and_clean, run as run_viz

st.set_page_config(
    page_title="Airbnb NYC — Klipso Model A",
    page_icon="🏠",
    layout="wide",
)

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'inputs', 'Airbnb', 'Airbnb NYC 2019.csv')
OUTPUTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'outputs', 'airbnb')

@st.cache_data
def load_data():
    return run_viz(csv_path=CSV_PATH, outputs_dir=OUTPUTS_DIR)

with st.spinner("Cargando datos y generando visualizaciones..."):
    result = load_data()

charts = result["charts"]
df     = result["df"]

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — PROBLEMA DE NEGOCIO
# ══════════════════════════════════════════════════════════════════════════
st.title("Airbnb NYC 2019 — Análisis de Factores de Precio")
st.markdown("### ¿Qué determina el precio de un Airbnb en Nueva York?")

st.markdown("""
Nueva York tiene **48,895 listings activos** en Airbnb (2019). Los anfitriones fijan precios sin datos —
por intuición, comparando manualmente con vecinos cercanos. El resultado: pricing inconsistente,
oportunidades perdidas de ingresos, y huéspedes que pagan de más (o de menos) por lo que reciben.

**Perspectiva anfitrión:** ¿Cómo fijar un precio competitivo para mi barrio y tipo de habitación?

**Perspectiva huésped:** ¿Dónde encuentro el mejor valor? ¿Qué borough ofrece más por mi dinero?

**Pregunta central del análisis:** ¿Qué variables tienen correlación estadísticamente significativa con el precio?
¿Cuáles son señales reales y cuáles son ruido?
""")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Listings totales", "48,895")
col2.metric("Boroughs analizados", "5")
col3.metric("Precio mediano NYC", "$106/noche")
col4.metric("Precio máximo", "$10,000/noche", delta="outlier extremo")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — EL ESTADO DEL DATO
# ══════════════════════════════════════════════════════════════════════════
st.subheader("El estado del dato — qué recibimos y qué encontramos roto")

st.markdown("""
El dataset llega como **una sola tabla** (a diferencia del caso Spotify, no hay JOIN entre tablas).
El Agente 1 auditó el schema completo antes de cualquier análisis.
""")

col_schema, col_issues = st.columns(2)

with col_schema:
    st.markdown("**Schema completo — 16 columnas, 48,895 filas:**")
    st.code("""id:                             int64
name:                           object  ← 16 nulls (0.03%)
host_id:                        int64
host_name:                      object  ← 21 nulls (0.04%)
neighbourhood_group:            object  ← 5 valores únicos
neighbourhood:                  object  ← 221 barrios
latitude / longitude:           float64 ← coordenadas válidas
room_type:                      object  ← 3 categorías
price:                          int64   ← PROBLEMA: 11 en $0
minimum_nights:                 int64   ← PROBLEMA: max=1,250
number_of_reviews:              int64   ← OK
last_review:                    object  ← 10,052 nulls (20.56%)
reviews_per_month:              float64 ← 10,052 nulls (20.56%)
calculated_host_listings_count: int64   ← OK
availability_365:               int64   ← OK""", language="text")

with col_issues:
    st.markdown("**Distribución del dataset:**")
    st.code("""ROOM TYPE
  Entire home/apt  25,409  (52.0%)
  Private room     22,326  (45.7%)
  Shared room       1,160  ( 2.4%)

BOROUGH
  Manhattan   21,661  (44.3%)
  Brooklyn    20,104  (41.1%)
  Queens       5,666  (11.6%)
  Bronx        1,091  ( 2.2%)
  Staten Island  373  ( 0.8%)

PRECIO
  mean:    $152.8  ← inflado por outliers
  median:  $106.0  ← KPI honesto
  p99:     $799    ← 99% de listings <= $799
  max:     $10,000 ← 1 penthaus extremo""", language="text")

st.markdown("---")
st.markdown("#### Decisiones de limpieza — documentadas con justificación")

# Decisión 1
with st.expander("🔴 Decisión 1 — price = $0: DROP (11 registros)", expanded=True):
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Problema detectado:**")
        st.code("(df.price == 0).sum()  →  11 registros", language="python")
        st.markdown("""
**Diagnóstico:** Listings a precio $0 no representan oferta real.
En Airbnb, un precio de $0 indica uno de tres escenarios:
- Error de entrada del anfitrión
- Listing inactivo/borrado que no fue eliminado del dataset
- Dato corrupto en la extracción

No existen alquileres gratuitos en NYC por Airbnb.
""")
    with col_r:
        st.markdown("**Acción aplicada:**")
        st.code("""df_clean = df[df['price'] > 0].copy()
# Antes: 48,895 filas
# Después: 48,884 filas
# Eliminados: 11 registros (-0.02%)""", language="python")
        st.success("Impacto mínimo: solo 11 filas. El análisis no se ve afectado.")

# Decisión 2
with st.expander("🟡 Decisión 2 — reviews_per_month + last_review: 10,052 nulls (20.56%)", expanded=True):
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Problema detectado:**")
        st.code("""df['reviews_per_month'].isnull().sum()  →  10,052
df['last_review'].isnull().sum()        →  10,052
# Exactamente los mismos registros""", language="python")
        st.markdown("""
**Diagnóstico:** Los 10,052 nulls corresponden exactamente a los mismos listings.
Un listing tiene `last_review=NULL` y `reviews_per_month=NULL` **solo cuando nunca
ha recibido una reserva** confirmada con reseña.

Esto NO es un error de datos — es información válida:
- Listings nuevos (recién publicados)
- Listings sin reservas en el período

Eliminar estos registros sesgaría el análisis hacia listings "ya establecidos",
perdiendo el 20% del mercado que incluye oferta nueva.
""")
    with col_r:
        st.markdown("**Acción aplicada:**")
        st.code("""# Imputación informada — no aleatoria
df_clean['reviews_per_month'] = (
    df_clean['reviews_per_month'].fillna(0)
)
df_clean['last_review'] = (
    df_clean['last_review'].fillna('no_reviews')
)
# Resultado: 0 nulls restantes
# Los 10,052 listings conservados con reviews_per_month=0""", language="python")
        st.info("Imputar 0 es correcto porque la ausencia de reseñas = 0 reseñas/mes, no un valor desconocido.")

# Decisión 3
with st.expander("🟡 Decisión 3 — minimum_nights extremos: max=1,250 noches (14 registros)", expanded=True):
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Problema detectado:**")
        st.code("""(df['minimum_nights'] > 365).sum()  →  14 registros
df['minimum_nights'].max()           →  1,250 noches
df['minimum_nights'].quantile(0.95)  →  30 noches
(df['minimum_nights'] > 90).sum()    →  197 registros""", language="python")
        st.markdown("""
**Diagnóstico:** Un minimum_nights de 1,250 equivale a 3.4 años mínimo.
Técnicamente no son alquileres temporales — son **arriendos anuales o de largo
plazo** donde el anfitrión usa la plataforma Airbnb como canal de distribución.

Eliminarlos sería incorrecto: son listings legítimos con estrategia diferente.
""")
    with col_r:
        st.markdown("**Acción aplicada:**")
        st.code("""# FLAG — no drop
# Se mantienen en el dataset pero se identifican
df_clean['is_long_term'] = (
    df_clean['minimum_nights'] > 30
)
# 747 listings identificados como arrendamiento largo
# Se excluyen del análisis de pricing a corto plazo
# pero se mantienen para análisis de disponibilidad""", language="python")
        st.warning("14 listings con >365 noches mínimas son outliers extremos. En análisis de precios se usa p95 como límite superior para visualizaciones.")

# Decisión 4
with st.expander("🟠 Decisión 4 — price outliers altos: max=$10,000/noche", expanded=True):
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Problema detectado:**")
        st.code("""(df['price'] > 1000).sum()  →  239 listings
(df['price'] > 2000).sum()  →  90 listings
df['price'].max()           →  $10,000/noche
df['price'].mean()          →  $152.8
df['price'].median()        →  $106.0
# Diferencia media/mediana: 44%""", language="python")
        st.markdown("""
**Diagnóstico:** En NYC existen penthouses, lofts en Tribeca y propiedades de
lujo con precios reales de $1,000–$10,000/noche. **No son errores** — son
el segmento premium del mercado. Eliminarlos distorsionaría el análisis
del mercado de lujo.

La diferencia del 44% entre media y mediana confirma una distribución
con cola derecha pronunciada (right-skewed).
""")
    with col_r:
        st.markdown("**Acción aplicada:**")
        st.code("""# MANTENER — cambiar métrica
# No se eliminan outliers de precio alto
# Se usa MEDIANA como KPI principal (no media)

# Referencia honesta:
#   mean   = $152.8  ← inflada por los 239 casos >$1,000
#   median = $106.0  ← representa al 50% del mercado real
#   p95    = $355    ← 95% de los listings

# En visualizaciones: recorte a p95 para legibilidad
df_viz = df_clean[df_clean['price'] <= 355]""", language="python")
        st.error("Usar media como KPI de precio en Airbnb es un error metodológico. La mediana es la métrica honesta para distribuciones sesgadas.")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — PIPELINE NARRATIVO
# ══════════════════════════════════════════════════════════════════════════
st.subheader("El pipeline — qué hizo cada agente y qué encontró")

with st.expander("Agente 1 — Data Recon: auditoría de schema y calidad", expanded=True):
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("**Qué hizo:**")
        st.markdown("""
- Cargó el CSV crudo (48,895 × 16)
- Inspeccionó tipos de datos columna por columna
- Calculó conteo y % de nulls por columna
- Analizó rangos (min/max) en variables numéricas
- Identificó inconsistencias lógicas (price=0, min_nights>365)
- Calculó distribución de valores únicos en categorías
- Generó reporte textual para el LLM
""")
        st.markdown("**Herramienta:** pandas puro — sin LLM, determinístico")
    with col_r:
        st.markdown("**Qué encontró:**")
        st.code("""CRÍTICO:
  price=0               11 registros → DROP
  min_nights max=1,250  14 registros → FLAG

IMPORTANTE:
  reviews_per_month   20.56% nulls → imputar 0
  last_review         20.56% nulls → imputar 'no_reviews'

MENOR:
  name nulls    16 registros (0.03%)
  host_name     21 registros (0.04%)

CONTEXTO:
  1 tabla (no JOIN)
  Dataset limpio salvo los 4 problemas anteriores
  Columnas lat/long presentes (potencial geoespacial)""", language="text")

with st.expander("Agente 2 — EDA: correlaciones y estadísticas descriptivas", expanded=True):
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("**Correlaciones Pearson/Spearman con precio:**")
        import pandas as pd
        corr_data = {
            "Variable": [
                "room_type (encoded)", "neighbourhood_group (encoded)",
                "availability_365", "calculated_host_listings_count",
                "minimum_nights", "number_of_reviews",
                "reviews_per_month"
            ],
            "Spearman ρ": ["~0.65*", "~0.42*", "0.086", "-0.106", "0.101", "-0.055", "-0.060"],
            "Señal": ["✅ Fuerte", "✅ Fuerte", "⚠️ Débil", "⚠️ Débil", "⚠️ Débil", "❌ Ruido", "❌ Ruido"],
        }
        st.dataframe(pd.DataFrame(corr_data), hide_index=True, use_container_width=True)
        st.caption("*Estimado por diferencia de medianas entre categorías.")
    with col_r:
        st.markdown("**Hallazgos clave del EDA:**")
        st.code("""DISTRIBUCIÓN DE PRECIO
  right-skewed (asimétrica derecha)
  mean=$152.8 vs median=$106.0
  → KPI: usar mediana, no media

TOP CORRELACIONES
  1. Tipo de habitación → precio (más fuerte)
  2. Borough → precio (segundo predictor)
  3. Disponibilidad → reseñas (débil, rho=0.298)
  4. Host profesional → precio (no significativo)

INSIGHT SORPRESIVO
  Barrios más CAROS ≠ barrios más DEMANDADOS
  Tribeca: $295 mediana pero no en top-10 reseñas
  Bedford-Stuyvesant: $65 mediana, #1 en reseñas
  → Volumen y precio van en direcciones opuestas""", language="text")

with st.expander("Agente 3 — Hipótesis: los 4 tests estadísticos", expanded=True):
    h_col1, h_col2 = st.columns(2)

    with h_col1:
        st.markdown("**H1 — Tipo habitación → precio**")
        st.code("""Test: Kruskal-Wallis (no paramétrico)
  Por qué: distribución sesgada, no normal
  H=22,414.84, p<0.001  ✅ CONFIRMADA

Medianas:
  Entire home/apt: $160/noche
  Private room:    $70/noche   (-56%)
  Shared room:     $45/noche   (-72%)

Interpretación: El tipo de habitación es
el predictor de precio más fuerte del dataset.
Una habitación entera cuesta 2.3× más que
una habitación privada.""", language="text")
        st.success("H1 CONFIRMADA — señal más fuerte")

        st.markdown("**H3 — Disponibilidad → demanda (reseñas)**")
        st.code("""Test: Spearman correlation
  availability_365 vs reviews_per_month
  ρ=0.298, p<0.001  ✅ CONFIRMADA (débil)

Interpretación: Listings más disponibles
tienden a tener más reseñas — señal de
mayor demanda o menor fricción de reserva.
Correlación débil: disponibilidad ≠ único
factor de demanda.""", language="text")
        st.warning("H3 CONFIRMADA pero señal débil (ρ=0.298)")

    with h_col2:
        st.markdown("**H2 — Borough → precio**")
        st.code("""Test: Kruskal-Wallis
  H=7,023.12, p<0.001  ✅ CONFIRMADA

  Manhattan vs Bronx (Mann-Whitney p<0.001)

Medianas por borough:
  Manhattan:     $150/noche
  Brooklyn:       $90/noche  (-40%)
  Queens:         $75/noche  (-50%)
  Staten Island:  $75/noche  (-50%)
  Bronx:          $65/noche  (-57%)

Interpretación: La ubicación importa, pero
no tanto como el tipo. Manhattan cobra 2.3×
más que el Bronx.""", language="text")
        st.success("H2 CONFIRMADA")

        st.markdown("**H4 — Host profesional → mayor precio**")
        st.code("""Test: Mann-Whitney U
  Ocasional (1-4 listings): $105 mediana
  Profesional (5+ listings): $116 mediana
  p=0.305  ❌ RECHAZADA

Interpretación: Ser anfitrión profesional
NO implica cobrar más. La diferencia de $11
no es estadísticamente significativa.
El precio lo determina la ubicación y el
tipo, no la experiencia del anfitrión.""", language="text")
        st.error("H4 RECHAZADA — p=0.305, no significativo")

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 4 — HALLAZGOS CON GRÁFICOS
# ══════════════════════════════════════════════════════════════════════════
st.subheader("Los hallazgos — con evidencia visual")

st.markdown("#### H1 — El tipo de habitación es el predictor más fuerte")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("Kruskal-Wallis H=**22,414**, p<0.001.")
    st.markdown("Toda habitación entera cuesta en promedio **2.3× más** que una habitación privada, independiente del barrio.")
    st.info("Para anfitriones: si tienes una propiedad entera, NO la alquiles por habitaciones — pierdes el 56% del ingreso potencial.")
with col_chart:
    st.plotly_chart(charts["h1_room_type"], use_container_width=True)

st.divider()

st.markdown("#### H2 — El borough determina el piso y techo de precio")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("Kruskal-Wallis H=**7,023**, p<0.001.")
    st.markdown("Manhattan cobra **$150** de mediana vs **$65** en el Bronx — una diferencia del 130%.")
    st.warning("Ojo: Brooklyn ($90) es casi competitivo con Queens ($75) y tiene más demanda (top en reseñas).")
with col_chart:
    st.plotly_chart(charts["h2_neighbourhood"], use_container_width=True)

st.divider()

st.markdown("#### H3 — Disponibilidad como señal de demanda (débil)")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("Spearman ρ = **0.298**, p<0.001.")
    st.markdown("Listings con más días disponibles al año tienden a tener más reseñas — proxy de ocupación real.")
    st.info("Señal débil: la disponibilidad explica solo una parte de la demanda. Otros factores (precio, ubicación, tipo) tienen más peso.")
with col_chart:
    st.plotly_chart(charts["h3_availability"], use_container_width=True)

st.divider()

st.markdown("#### H4 — Host profesional no es ventaja de precio")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("Mann-Whitney p = **0.305** — NO significativo.")
    st.markdown("Hosts con 5+ propiedades cobran **$116** de mediana vs **$105** de hosts ocasionales.")
    st.error("Diferencia de $11 no es estadísticamente significativa. Ser 'profesional' no justifica cobrar más.")
with col_chart:
    st.plotly_chart(charts["h4_host_type"], use_container_width=True)

st.divider()

st.markdown("#### Top 10 barrios más caros (mediana, mín. 30 listings)")
col_text, col_chart = st.columns([1, 2])
with col_text:
    st.markdown("Tribeca lidera con **$295/noche** de mediana.")
    st.markdown("Los 10 barrios más caros son exclusivamente Manhattan.")
    st.info("Contraste: los 10 barrios con más reseñas son Brooklyn/Harlem — donde el precio es accesible y el volumen es alto.")
with col_chart:
    st.plotly_chart(charts["top_neighbourhoods"], use_container_width=True)

st.divider()

st.subheader("Dashboard — 4 hipótesis en una pantalla")
st.plotly_chart(charts["dashboard"], use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — IMPACTO CUANTIFICADO
# ══════════════════════════════════════════════════════════════════════════
st.subheader("Impacto cuantificado — criterios accionables")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Para anfitriones — maximizar precio:**")
    st.markdown("- Habitación entera → +130% vs habitación privada")
    st.markdown("- Manhattan → +130% vs Bronx")
    st.markdown("- Tribeca/NoHo → mediana $250–295")
    st.markdown("- Tener 5+ propiedades NO justifica precio premium")

with col2:
    st.markdown("**Para huéspedes — mejor valor:**")
    st.markdown("- Brooklyn: 60% precio de Manhattan, alta demanda")
    st.markdown("- Bedford-Stuyvesant: #1 en reseñas, $65 mediana")
    st.markdown("- Habitación privada: 56% más barato que entera")
    st.markdown("- Más reseñas = más confiable (no más caro)")

with col3:
    st.markdown("**Señales de alerta:**")
    st.markdown("- price=0 → listing inactivo, ignorar")
    st.markdown("- min_nights>30 → no es alquiler turístico")
    st.markdown("- reviews=0 → nuevo o inactivo, precio sin validar mercado")
    st.markdown("- Media de precio ($153) miente — usar mediana ($106)")

st.markdown("---")
st.markdown("**Impacto medido:**")
impact_data = {
    "Factor": ["Tipo: Entera vs Privada", "Borough: Manhattan vs Bronx",
               "Disponibilidad vs reseñas", "Host profesional vs ocasional"],
    "Efecto": ["+130% precio (mediana $160 vs $70)", "+130% precio (mediana $150 vs $65)",
               "ρ=0.298 (débil pero significativo)", "NO significativo (p=0.305)"],
    "Veredicto": ["✅ CONFIRMADA", "✅ CONFIRMADA", "⚠️ DÉBIL", "❌ RECHAZADA"],
}
st.dataframe(pd.DataFrame(impact_data), hide_index=True, use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# BLOQUE 6 — STACK
# ══════════════════════════════════════════════════════════════════════════
with st.expander("Stack técnico — Modelo A (determinístico)"):
    st.markdown("""
| Capa | Herramienta | Función |
|---|---|---|
| Ingesta | `pandas.read_csv` | Carga del CSV crudo |
| Limpieza | `pandas` | DROP price=0, fillna reviews, flagging outliers |
| EDA | `pandas`, `scipy.stats` | Correlaciones Pearson + Spearman |
| Hipótesis | `scipy.stats.kruskal`, `mannwhitneyu`, `spearmanr` | Tests no paramétricos (distribución sesgada) |
| Visualización | `Plotly` | 6 gráficos interactivos |
| Narrativa | `OpenAI GPT-4o` vía LangChain | Solo brief editorial (Agente 4) |
| Dashboard | `Streamlit` | App narrativa 6 bloques |

**Por qué tests no paramétricos (Kruskal-Wallis, Mann-Whitney)?**

La distribución de precios es altamente asimétrica (right-skewed). Los tests paramétricos como ANOVA asumen normalidad.
Al usar Kruskal-Wallis y Mann-Whitney evitamos ese supuesto — los resultados son válidos incluso con la distribución real del precio.
""")

st.caption("Modelo A — determinístico | Dataset: Airbnb NYC 2019 | Klipso Framework v0.1.0")
