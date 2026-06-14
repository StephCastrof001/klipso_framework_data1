# Propuesta — Modelo C: Contexto-de-otros-modelos + Evals + Memoria

> Estado: **PROPUESTA — pendiente de refinar antes de construir**
> Fuentes: Reflexion (Shinn et al. 2023), Voyager skill library, LLM-as-judge,
> arXiv 2405.06682 "Self-Reflection in LLM Agents", awesome-ai-agent-papers (VoltAgent)

---

## El reframe clave (vs el spec viejo de methodology.md)

El spec original decía: "RAG con Firecrawl scrapea análisis externos de la web".

**Tu input lo afina:** el contexto NO es scraping web automático. Es **análisis de OTROS
modelos que TÚ le das** (un análisis de GPT-4, uno de Claude, un PDF de benchmark, un
notebook de Kaggle top). Eso entra como contexto. Y un **evaluador** puntúa el output.

Esto es más fuerte porque:
- Control total sobre la calidad del contexto (no ruido de la web)
- Demuestra "ensemble de modelos" — C aprende de cómo otros modelos analizaron lo mismo
- Los evals dan una métrica objetiva de mejora

---

## Los 3 mecanismos que hacen a C "senior"

### 1. RAG de otros modelos (contexto que tú das)

```
context/                          ← TÚ dropeas aquí
  gpt4_analysis_spotify.md
  claude_analysis_spotify.md
  kaggle_top_notebook_insights.md
       ↓
  [indexado: embeddings OpenAI + cosine — sin FAISS, deps que ya hay]
       ↓
  ANALYST recibe: "GPT-4 concluyó que X es la señal clave.
                   Claude priorizó Y. ¿Tu dataset lo confirma o contradice?"
```

### 2. Eval con rubric (LLM-as-judge)

Después de cada análisis, un **evaluador** puntúa el output contra una rúbrica:

| Dimensión | Pregunta | Escala |
|---|---|---|
| Rigor estadístico | ¿Usó el test correcto para la distribución? | 0-10 |
| Accionable | ¿El insight se traduce a una decisión? | 0-10 |
| Honestidad | ¿Reportó limitaciones y outliers? | 0-10 |
| Consistencia con contexto | ¿Coincide/explica diferencia vs otros modelos? | 0-10 |

Si `score < umbral` → **Reflexion loop**: el agente critica su propio output y re-ejecuta
con un prompt refinado. Máximo 3 intentos (circuit breaker).

### 3. Memoria entre runs (3 tipos)

```
memory.json
  episodic:   "Run 3: H4 falló rubric por no reportar p-value"
  semantic:   "En datasets de streaming, la mediana > media (skew)"
  procedural: "Para distribución sesgada → Kruskal, no ANOVA"
```

La memoria persiste entre sesiones. Run N+1 arranca sabiendo qué falló en run N.

---

## Arquitectura propuesta

```
1. CONTEXT LOADER  → lee context/*.md (otros modelos) → indexa (embeddings+cosine)
                     → carga memory.json de runs anteriores
        ↓
2. ANALYST         → EDA + hipótesis CON contexto inyectado
                     "otros modelos dijeron X, tu memoria dice Y"
        ↓
3. EVALUATOR       → puntúa vs rubric (4 dimensiones)
                     score < umbral?  →┐
        ↓ (pasa)                       │ (falla)
        │                    ┌─────────┘
        │                    ↓
        │              REFLEXION → critica + refina prompt → vuelve a ANALYST
        │                    (máx 3 intentos)
        ↓
4. MEMORY WRITER   → guarda qué pasó rubric, qué falló → memory.json
        ↓
5. BRIEF FINAL     → respaldado por: análisis propio + otros modelos + memoria
```

## Stack técnico

| Componente | Herramienta | Nota |
|---|---|---|
| Embeddings | OpenAI `text-embedding-3-small` | ya tienes la key |
| Similaridad | numpy cosine | **sin FAISS** — pocos docs, no hace falta |
| Eval | LLM-as-judge (GPT-4o) | prompt con rúbrica estructurada |
| Reflexion | loop actor→evaluator→reflect | Shinn 2023 |
| Memoria | `memory.json` (3 tipos) | episódica/semántica/procedural |
| Orquestación | LangGraph con estado compartido | reusa patrón de B |

## Por qué NO FAISS / Mem0

Over-engineering. El contexto son ~3-10 documentos que tú das, no millones.
Embeddings OpenAI + cosine en numpy es suficiente y no agrega dependencias pesadas.
Mem0 sería útil con cientos de sesiones — para un portafolio, `memory.json` basta.

## La lección que demuestra C

**La diferencia entre análisis mediocre y excelente no es el modelo LLM — es la calidad
del contexto.** C recibe lo que otros modelos concluyeron + su propia memoria de errores,
y se auto-evalúa. Es el patrón de un analista senior: aprende de pares y de sus errores.

---

## Decisiones pendientes (refinar antes de construir)

1. **Formato del contexto:** ¿markdown libre, o JSON estructurado con campos fijos
   (modelo, conclusión, confianza)? JSON estructurado da mejor retrieval.
2. **Umbral del eval:** ¿score >= 7/10 pasa? ¿Promedio o mínimo por dimensión?
3. **Reflexion:** ¿re-ejecuta solo la hipótesis que falló, o todo el análisis?
4. **Memoria:** ¿se comparte entre datasets (Spotify enseña a Airbnb) o es por-dataset?
5. ¿El evaluador es el mismo modelo que el analista (auto-juez) o uno distinto
   (juez independiente)? Juez distinto reduce sesgo de auto-aprobación.
