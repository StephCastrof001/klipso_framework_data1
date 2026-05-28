# Klipso Data Framework

> Un framework de análisis con IA que demuestra cuándo y cómo usar inteligencia artificial en cada paso del proceso.

La pregunta no es "¿cómo uso IA para analizar datos?"
La pregunta es **"¿cuándo tiene sentido usarla, cuándo no, y cómo cambia eso el resultado?"**

Este framework implementa tres enfoques filosóficamente distintos sobre el mismo dataset.
Cada uno responde la misma pregunta de negocio con una arquitectura diferente.

---

## Los tres enfoques

### Modelo A — Determinístico
*"Primero entiende el dato. Luego involucra la IA."*

El análisis estadístico no necesita LLM. pandas, scipy y plotly son herramientas
determinísticas, reproducibles y gratuitas. La IA aparece solo al final,
para traducir números a lenguaje editorial.

**Cuándo elegirlo:** velocidad, reproducibilidad, presupuesto bajo, dataset limpio.
**Lección:** usar LLM para todo es un error de arquitectura.

---

### Modelo B — Human-in-the-Loop (HITL)
*"El análisis de datos requiere juicio humano en el medio, no solo al final."*

El flujo no es lineal. En cada paso clave el PM revisa, valida y redirige
antes de continuar. LangGraph `interrupt()` pausa la ejecución y espera aprobación.
El LLM genera código Python. pandas lo ejecuta. El LLM nunca toca los datos directamente.

```
PM define pregunta
    ↓
Agente: EDA + limpieza
    ↓ [PAUSA] → PM revisa → aprueba o redirige
Agente: hipótesis según dirección del PM
    ↓ [PAUSA] → PM valida hallazgos
Agente: visualizaciones
    ↓ [PAUSA] → PM aprueba o pide refinamiento
Brief final
```

**Cuándo elegirlo:** análisis estratégico, cliente con criterio, cuando el error tiene costo alto.
**Lección:** el LLM es planner, no executor.

---

### Modelo C — RAG + Memoria + Self-Improvement
*"Un analista senior aprende de otros analistas y de sus propios errores."*

Antes de analizar, recolecta contexto externo: análisis de otros data scientists
sobre el mismo dominio. Ese contexto enriquece cada paso. Los agentes tienen
memoria entre sí. Si un agente falla, ese error se registra y los agentes
posteriores lo tienen en cuenta. El sistema se mejora a sí mismo en cada iteración.

```
RESEARCHER     → scraping con Firecrawl, indexa análisis externos en vector store
CONTEXT LOADER → recupera chunks relevantes como contexto para los agentes
ANALYST        → EDA con contexto enriquecido ("según X analistas, la señal es Y")
REFLEXION      → evalúa su propio output, re-ejecuta si detecta inconsistencias
MEMORY WRITER  → guarda qué hipótesis falló, qué insight fue validado
BRIEF FINAL    → respaldado por análisis propio + best practices externas + memoria
```

**Cuándo elegirlo:** análisis de alto impacto, dominio nuevo, necesitas contexto externo.
**Lección:** la diferencia entre análisis mediocre y excelente no es el modelo LLM — es la calidad del contexto.

---

## Comparación de enfoques

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

## Estructura del framework

```
klipso_framework_data1/
├── agents/
│   ├── setup_llm.py        ← abstracción LLM (openai | bedrock | cualquier provider)
│   ├── 01_data_recon.py    ← reconocimiento de datos (schema, nulls, JOIN issues)
│   ├── 02_eda_auto.py      ← EDA estadístico + correlaciones
│   ├── 03_hypothesis.py    ← prueba de hipótesis con scipy
│   ├── 04_business_tx.py   ← traducción editorial (único agente con LLM)
│   └── 05_viz.py           ← visualizaciones Plotly interactivas
├── models/
│   ├── model_a/            ← implementación Modelo A (determinístico)
│   ├── model_b/            ← implementación Modelo B (HITL - en desarrollo)
│   └── model_c/            ← implementación Modelo C (RAG+Mem - en desarrollo)
├── docs/
│   ├── methodology.md      ← spec completa de los 3 modelos
│   └── modelo_a_gaps.md    ← gaps identificados post-benchmark
├── inputs/                 ← tu data va aquí (en .gitignore)
├── outputs/                ← resultados generados (en .gitignore)
├── .env.example            ← variables requeridas
└── requirements.txt
```

---

## LLM provider — completamente desacoplado

Los agentes no saben qué proveedor usan. Solo llaman `get_llm()`.

```python
# .env — elige uno
LLM_PROVIDER=openai    # o: bedrock
```

Cambiar de proveedor = cambiar una línea en `.env`. El código no cambia.

---

## Cómo usar este framework con tu dataset

```bash
# 1. Clonar
git clone https://github.com/StephCastrof001/klipso_framework_data1.git
cd klipso_framework_data1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar proveedor LLM
cp .env.example .env
# editar .env con tu API key

# 4. Poner tu data en inputs/

# 5. Correr Modelo A
python agents/01_data_recon.py
python agents/02_eda_auto.py
python agents/03_hypothesis.py
python agents/04_business_tx.py
python agents/05_viz.py
```

---

## Casos de uso implementados

| Repo | Dataset | Modelos aplicados |
|---|---|---|
| [klipso_data_1](https://github.com/StephCastrof001/klipso_data_1) | Spotify Most Streamed 2023 | Modelo A ✅ · A.1 🔨 · B 📋 · C 📋 |
| klipso_data_2 | — | — |

---

*Framework: klipso_framework_data1 | Autor: StephCastrof001*
