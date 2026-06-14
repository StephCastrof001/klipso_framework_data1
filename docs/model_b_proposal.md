# Propuesta — Modelo B: Human-in-the-Loop (HITL)

> Estado: **PROPUESTA — pendiente de refinar antes de construir**
> Fuentes: LangGraph docs (interrupt patterns), business-science `human_review_node`,
> Towards Data Science "LangGraph 201: Human Oversight to Deep Research Agent"

---

## El problema que resuelve

Modelo A corre batch: el agente decide qué hipótesis probar y entrega el resultado.
Problema: el agente puede ir en la dirección equivocada y nadie lo detiene hasta el final.

Modelo B inserta al PM **en el medio** del análisis, no solo al final.
El PM revisa, valida y redirige antes de que el agente continúe.

---

## Los 3 patrones HITL canónicos (LangGraph)

La investigación confirma que existen 3 formas de intervención humana. B debe usar las 3
según el checkpoint:

| Patrón | Qué hace | Dónde lo usamos en B |
|---|---|---|
| **Approve / Reject** | Humano aprueba o rechaza antes de una acción | Antes de visualizar (acción costosa) |
| **Edit state** | Humano modifica el estado propuesto por el agente | Después del EDA — PM ajusta qué hipótesis priorizar |
| **Review & redirect** | Humano revisa output y da dirección al siguiente paso | Después de hipótesis — PM valida hallazgos |

**Referencia:** el Deep Research Agent de TDS usa 2 nodos HITL: clarificar alcance (antes)
+ revisar borrador (después). B extiende esto a 3 checkpoints.

---

## Arquitectura propuesta

```
PM define pregunta
      ↓
  ┌────────┐
  │  EDA   │  (determinístico — pandas/scipy)
  └────────┘
      ↓
  [⏸ INTERRUPT 1 — Edit state]
  PM revisa correlaciones → ajusta qué hipótesis priorizar
      ↓
  ┌────────────┐
  │ HYPOTHESIS │  (dirigida por el ajuste del PM)
  └────────────┘
      ↓
  [⏸ INTERRUPT 2 — Review & redirect]
  PM valida veredictos → aprueba o pide re-test
      ↓
  ┌──────┐
  │ VIZ  │
  └──────┘
      ↓
  [⏸ INTERRUPT 3 — Approve / Reject]
  PM aprueba visuales o pide refinamiento
      ↓
  ┌───────┐
  │ BRIEF │  (incorpora TODAS las decisiones del PM)
  └───────┘
```

## Stack técnico

| Componente | Herramienta | Por qué |
|---|---|---|
| Orquestación | LangGraph `StateGraph` | Soporta pausas con estado persistente |
| Pausa | `interrupt()` | Pausa ejecución, espera input humano |
| Persistencia | `MemorySaver` (checkpointer) | Guarda estado entre pausas (thread_id) |
| Reanudación | `Command(resume=valor)` | Inyecta decisión del PM y continúa |
| Ejecución | pandas + scipy | El LLM NO toca datos — solo interpreta |
| UI | Streamlit con botones Aprobar/Redirigir | El PM interactúa sin código |

## Estado compartido (TypedDict)

```python
class AnalysisState(TypedDict, total=False):
    main_csv: str
    question: str
    df_merged: Any              # DataFrame en memoria entre nodos
    eda_corr: dict              # correlaciones para que el PM revise
    hypothesis_focus: str       # ← dirección del PM (Edit state)
    hypothesis_results: dict
    pm_hypothesis_feedback: str # ← validación del PM (Review)
    viz_paths: dict
    brief: str
    decision_log: list          # auditoría: toda decisión del PM, en orden
```

## La lección que demuestra B

**El LLM es planner, no executor.** El LLM genera la interpretación y propone dirección.
pandas/scipy ejecutan la matemática. El humano decide en cada bifurcación.

El `decision_log` es el deliverable que prueba la tesis: el brief final es trazable
a cada decisión humana. En A no hay decisiones que rastrear.

---

## Borrador existente

Ya hay un esqueleto en `models/model_b/` (`state.py`, `graph.py`, `app_b.py`).
**Es borrador** — implementa los 3 interrupts pero NO está refinado contra estos patrones.
Pendiente: validar que use Edit-state vs Review vs Approve correctamente por checkpoint.

## Decisiones pendientes (refinar antes de construir final)

1. ¿El PM puede **re-ejecutar** una hipótesis con otros parámetros, o solo aprobar/redirigir?
2. ¿El feedback del PM se inyecta como texto al prompt, o como cambio estructurado de estado?
3. ¿Cuántos checkpoints? 3 puede ser fricción alta — ¿colapsar a 2 (EDA + hallazgos)?
4. ¿Timeout en los interrupts o esperan indefinido?
