# Gaps de los modelos — auditoría honesta

> Estado al 2026-05-28. Cada gap detectado al correr pruebas reales (Spotify, Airbnb).

---

## Gap transversal #1 — Agentes hardcoded a Spotify (CRÍTICO)

`klipso/agents/*.py` tiene **98 referencias** hardcoded a columnas Spotify
(`streams`, `track_id`, `in_spotify_playlists`, `main_music_genre`).

**Cómo se detectó:** al correr Airbnb tuve que escribir `models/model_a/airbnb/viz_airbnb.py`
desde cero — 0% de reuso del paquete. El framework se bypasseó a sí mismo.

**Contradice:** el README dice "Framework is dataset-agnostic". Falso hoy.

**Fix propuesto:** config-driven. Cada dataset define `dataset.yaml` (target, categóricas,
numéricas, tests). Los agentes leen la config, no hardcodean columnas. Spotify y Airbnb
usarían los MISMOS agentes.

---

## Gap transversal #2 — Spotify y Airbnb divergen sin contrato común

- Spotify: `klipso/agents/` (paquete) + `agents/*.py` (CLI)
- Airbnb: `models/model_a/airbnb/viz_airbnb.py` (script suelto, otra forma)

Dos casos, dos arquitecturas. `klipso_data_2` sería una tercera. El fix de #1 resuelve esto.

---

## Gap transversal #3 — Sin tests

`tests/` no existe. CLAUDE.md exige smoke tests antes de commit. La verificación fue manual.
"Ver gaps al correr pruebas" (objetivo del proyecto) requiere pruebas repetibles automáticas.

---

## Gaps por modelo

### Modelo A — Determinístico (implementado)

| Gap | Impacto | Estado |
|---|---|---|
| Hipótesis fijas H1-H4 (Spotify) | No generaliza a otro dataset sin reescribir | 🔴 ligado a #1 |
| Sin ML — solo correlaciones | No predice ("¿supera 300M?"), solo describe | 🟡 vs business-science |
| Sin feature engineering | Usa columnas crudas, no deriva variables | 🟡 |
| Media vs mediana | A.1 lo corrige pero A.1 no está construido | 🟢 spec existe |

### Modelo A.1 — Enriquecido (solo spec)

| Gap | Impacto | Estado |
|---|---|---|
| No construido | Audio DNA, H5, outliers viz pendientes | 📋 spec en methodology.md |

### Modelo B — HITL (borrador, no refinado)

| Gap | Impacto | Estado |
|---|---|---|
| 3 interrupts puede ser fricción alta | PM se cansa de aprobar | ⚠️ decidir 2 vs 3 |
| Feedback como texto, no estado estructurado | Difícil de auditar/medir | ⚠️ refinar |
| No usa los 3 patrones HITL diferenciados | Todos los checkpoints iguales | ⚠️ refinar |
| Corre solo sobre Spotify (agentes hardcoded) | Mismo #1 | 🔴 |

### Modelo C — Contexto+Eval+Memoria (solo propuesta)

| Gap | Impacto | Estado |
|---|---|---|
| No construido | — | 📋 propuesta |
| Riesgo auto-aprobación (juez = analista) | Eval sesgado | ⚠️ usar juez distinto |
| Memoria por-dataset vs global sin decidir | Spotify enseña a Airbnb? | ⚠️ decidir |

---

## Comparación con benchmark (business-science/ai-data-science-team)

| Dimensión | business-science | klipso | Gap |
|---|---|---|---|
| Agnóstico al dataset | ✅ | ❌ (#1) | klipso pierde |
| ML modeling (H2O+MLflow) | ✅ | ❌ | klipso pierde |
| HITL `human_review_node` | ✅ ejemplos | ⚠️ borrador | empatado |
| pip installable | ✅ | ✅ (ya refactorizado) | empatado |
| Filosofía A/B/C comparada | ❌ | ✅ | **klipso gana** |
| Narrativa PM (6 bloques) | ❌ | ✅ | **klipso gana** |
| Eval/self-improvement | ❌ | 📋 (Model C) | klipso gana si construye C |

---

## Prioridad de fixes (alineada al objetivo "laboratorio de metodología")

1. 🟢 **Commit Airbnb** — no perder trabajo (rápido)
2. 🔴 **Fix #1 config-driven** — desbloquea "reusable", arregla #1+#2
3. 🟡 **Tests** (#3) — smoke test corre A sobre Spotify+Airbnb, detecta gaps auto
4. 🔴 **Refinar + construir Model B** — core de "demostrar A/B/C"
5. 🔴 **Construir Model C** — core de "demostrar A/B/C"
6. 🎯 **Tabla comparativa A/B/C ejecutada** — el deliverable que prueba la tesis
