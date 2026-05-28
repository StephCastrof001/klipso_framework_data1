# Metodología: Tres Modelos de Análisis con IA

## Contexto

Dataset: 839 canciones Spotify cross-platform (Spotify, Apple, Deezer, Shazam).
Pregunta central: ¿Qué hace que una canción triunfe en múltiples plataformas?

Construimos **tres modelos** con distintos niveles de sofisticación técnica y filosófica.
Cada uno responde la misma pregunta con una arquitectura diferente.

---

## Modelo A — Determinístico

**Filosofía:** "Primero entiende el dato. Luego involucra la IA."

El análisis estadístico no necesita LLM. Pandas, scipy y plotly son herramientas
determinísticas, reproducibles y gratuitas. El LLM aparece solo al final,
para traducir números a lenguaje editorial.

**Stack:**
- pandas + scipy (limpieza, hipótesis)
- Plotly (visualización interactiva)
- Streamlit (presentación narrativa)
- LLM (solo Agente 4: brief editorial)

**Flujo:**
```
CSV inputs → limpieza → EDA → hipótesis → visualizaciones → brief (LLM)
```

**Sin checkpoints humanos.** Corre batch, entrega resultado.

**Archivos:**
- `agents/01_data_recon.py` — schema, nulls, JOIN issues
- `agents/02_eda_auto.py` — correlaciones, estadísticas
- `agents/03_hypothesis.py` — H1-H4 con scipy
- `agents/04_business_tx.py` — brief editorial (LLM)
- `agents/05_viz.py` — 5 gráficos interactivos plotly
- `run_pipeline.py` — orquestador
- `app.py` — Streamlit con narrativa

**Lección clave:** Usar LLM para todo es un error de arquitectura.
Un data analyst sabe cuándo NO usar IA.

---

## Modelo A.1 — Determinístico Enriquecido (post-benchmark)

**Filosofía:** "Un buen analista itera. El primer análisis es el punto de partida, no el destino."

Después de comparar Modelo A contra el benchmark (Nayankoli/Spotify-Streamed-Songs-
y Power BI ref), se identificaron 4 gaps concretos. A.1 los cubre sin cambiar la arquitectura.

**Qué agrega sobre A:**
- KPIs con mediana (más honesto para distribución sesgada)
- Audio DNA: JOIN enriquecido con features de audio (bpm, energy, danceability, etc.)
- H5: correlación audio features vs streams
- Visualización de distribución (histogram + IQR)
- Outliers explícitos en scatter H1

**Stack:** idéntico al Modelo A. Solo datos y visualizaciones cambian.

**Archivos nuevos:**
- `agents/05a_enrich.py` — JOIN con dataset Nayankoli por track_name + artist
- `agents/06_viz_a1.py` — gráficos adicionales (distribución, H5, outliers marcados)
- `app_a1.py` — Streamlit app A.1 con KPIs actualizados + secciones nuevas

**Lección clave:** La iteración basada en benchmark es metodología CRISP-DM real.
No es rehacer el trabajo — es demostrar que sabés leer los gaps de tu propio análisis.

---

## Modelo B — Human-in-the-Loop (HITL)

**Filosofía:** "El análisis de datos requiere juicio humano en el medio, no solo al final."

El flujo no es lineal. En cada paso clave, el PM revisa, valida y redirige
antes de continuar. LangGraph `interrupt()` pausa la ejecución y espera aprobación.

**Stack:**
- LangGraph con `interrupt()` nodes
- MemorySaver (checkpointer)
- pandas + plotly (ejecución determinística)
- LLM (genera código, interpreta resultados)
- Streamlit con steps aprobables

**Flujo:**
```
PM define pregunta
    ↓
Agente: EDA + limpieza
    ↓
[PAUSA] → PM revisa → aprueba o redirige
    ↓
Agente: hipótesis según dirección del PM
    ↓
[PAUSA] → PM valida hallazgos
    ↓
Agente: visualizaciones
    ↓
[PAUSA] → PM aprueba o pide refinamiento
    ↓
Brief final
```

**Referencia de arquitectura:** `refs/ai-data-science-team/`
(Business Science — LangGraph HITL pattern con `node_func_human_review`)

**Lección clave:** El LLM genera el código Python. Pandas lo ejecuta.
El LLM nunca toca los datos directamente — es planner, no executor.

---

## Modelo C — RAG + Memoria + Self-Improvement

**Filosofía:** "Un analista senior aprende de otros analistas y de sus propios errores."

El modelo más sofisticado. Antes de analizar, **recolecta contexto externo**:
análisis de otros data scientists sobre el mismo dominio (música, streaming,
editorial). Ese contexto enriquece cada paso del análisis.

Además, los agentes tienen **memoria entre sí**: si un agente falla o produce
un resultado cuestionable, ese error se registra y los agentes posteriores
lo tienen en cuenta. El sistema **se mejora a sí mismo** en cada iteración.

**Stack:**
- RAG: Firecrawl (scraping de análisis externos) + vector store (ChromaDB/FAISS)
- Memoria: Mem0 o LangGraph MemorySaver persistente
- Self-improvement: Reflexion loop — agente revisa su propio output
- LangGraph multi-agente con estado compartido
- Streamlit con contexto enriquecido visible

**Flujo:**
```
1. RESEARCHER — scraping con Firecrawl:
   busca análisis de Spotify editorial, patrones de éxito musical,
   casos de estudio de playlisting. Los indexa en vector store.

2. CONTEXT LOADER — carga mejores prácticas:
   recupera chunks relevantes del vector store como contexto
   para los agentes de análisis.

3. ANALYST — EDA + hipótesis con contexto enriquecido:
   sus prompts incluyen: "según el análisis de X analistas,
   la señal clave es Y. ¿Confirma o contradice tu dataset?"

4. REFLEXION — self-review:
   el agente evalúa su propio output contra criterios de calidad.
   Si detecta inconsistencias, re-ejecuta con prompt refinado.

5. MEMORY WRITER — guarda aprendizajes:
   qué hipótesis falló, qué visualización confundió, qué insight
   fue validado por el PM. Disponible en próximas sesiones.

6. BRIEF FINAL — con contexto acumulado:
   recomendaciones editoriales respaldadas por el análisis propio
   + best practices externas + memoria de iteraciones anteriores.
```

**Componentes técnicos clave:**
- `Reflexion pattern` (Shinn et al. 2023): agente evalúa + critica + refina
- `RAG con dominio específico`: no Wikipedia general, sino análisis de música/streaming
- `Mem0 + LangGraph`: memoria episódica (qué pasó en sesiones anteriores)
- `Circuit breaker`: máx 3 intentos de refinamiento por hipótesis

**Lección clave:** La diferencia entre un análisis mediocre y uno excelente
no es el modelo LLM — es la calidad del contexto que recibe.

---

## Comparación de los tres modelos

| Dimensión | Modelo A | Modelo B | Modelo C |
|---|---|---|---|
| **Costo por run** | ~$0.05 | ~$0.10 | ~$0.50 |
| **Tiempo** | 1-2 min | 5-15 min | 15-30 min |
| **Control humano** | Solo al final | En cada paso | Continuo |
| **Aprendizaje** | Ninguno | En sesión | Entre sesiones |
| **Contexto externo** | No | No | Sí (RAG) |
| **Reproducibilidad** | Alta | Media | Media-baja |
| **Complejidad técnica** | Baja | Media | Alta |

---

## Por qué tres modelos

Este proyecto no busca demostrar que "la IA hace análisis".
Busca demostrar que **saber cuándo y cómo usar IA** es la habilidad real.

Un PM técnico entiende los tradeoffs y elige el modelo correcto
según el contexto: velocidad, costo, control, y calidad del insight.

---

*Proyecto: klipso_data_1 | GitHub: StephCastrof001/klipso_data_1*
