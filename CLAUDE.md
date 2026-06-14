# CLAUDE.md — klipso_framework_data1

Guía para Claude Code (y cualquier agente) al trabajar en este repo.
**Leé esto al inicio de cada sesión antes de tocar código.**

---

## Qué es este repo

Framework de análisis de datos con IA que implementa 3 enfoques filosóficamente
distintos sobre el mismo problema:

- **Modelo A — Determinístico:** pandas/scipy hacen la estadística; el LLM solo
  traduce a lenguaje de negocio al final. Rápido, reproducible, barato.
- **Modelo B — Human-in-the-Loop (HITL):** LangGraph `interrupt()` pausa en cada
  paso; el PM valida/redirige. El LLM planifica, pandas ejecuta.
- **Modelo C — RAG + Memoria + Self-Improvement:** researcher externo (Firecrawl),
  memoria entre agentes, reflexion. (Propuesta — sin código aún.)

El árbitro de calidad es `bench_runner.sh`: corre el pipeline sobre datasets con
answer key conocido y mide si los hallazgos reproducen la verdad documentada.

---

## Protocolo de Experimentos (Método Científico) — OBLIGATORIO

NUNCA reemplaces un modelo, pipeline o función en producción directamente.
SIEMPRE aplicá este flujo:

1. **HIPÓTESIS:** "Creo que X mejora porque Y"
2. **VERSIONAR:** `git branch exp/<nombre>` O flag en `.env`
3. **CONTROLAR:** una sola variable cambia por experimento
4. **MEDIR:** definir métrica ANTES de correr (DONE WHEN)
5. **DECIDIR:** si mejora → merge. Si no → documentá y descartá.

### Reglas
- El código viejo NUNCA se borra (git history lo preserva)
- Back-compat obligatorio si otros módulos dependen del output
- Los resultados van a `docs/VERSIONS_*.md` (registro permanente)
- "Suena mejor" NO es criterio. El `bench_runner` es el árbitro.
- Cada modelo (A/B/C, v1/v2) es un experimento válido — se versiona, no se mata.

---

## Estructura

```
klipso/agents/      Model A: data_recon, eda, hypothesis, business_tx
klipso/utils/       profiler.py (genérico), data_cleaning.py
klipso/llm/         provider.py (openai|bedrock|ollama|auto)
models/model_b/     Model B HITL: graph.py, state.py, app_b.py
docs/               VERSIONS_*.md (registro de experimentos), propuestas B/C
bench_queue/        datasets pendientes (drop .csv + .key.md)
bench_results/      evals acumulados (accumulated.jsonl) + por corrida
bench_runner.sh     árbitro 24/7 (cron)
bench_seed.sh       llena la cola con datasets curados
```

## LLM provider
- `.env`: `LLM_PROVIDER=ollama` para el 9B local gratis (EC2), `openai` para producción.
- No quemar la OpenAI key en experimentos — usar Ollama para medir.

## Cómo correr el pipeline
```bash
PYTHONPATH=. python3 run_pipeline.py --main-csv inputs/x.csv --competition-csv inputs/x.csv
# single-CSV: pasar el mismo archivo como main y competition
```

## DONE = verificado, no "código escrito"
- Un cambio cierra cuando `bench_runner` lo confirma con datos reales.
- Status QA/exit-0 mienten — el eval.json + answer key son la verdad.
