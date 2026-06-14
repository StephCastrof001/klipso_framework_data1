# Modelo A — Versiones y Experimentos (método científico)

> No reemplazamos modelos: los versionamos y medimos. Cada cambio = una hipótesis
> con métrica. Si mejora, se queda. Si no, se documenta el por qué y se prueba otro.
> El código viejo NUNCA se pierde (git history + back-compat).

---

## Línea de versiones

| Versión | Qué es | Estado | Funciona en |
|---|---|---|---|
| **A-v1** Spotify-tuned | Agentes hardcodeados a columnas Spotify (streams, danceability, track_id). LLM en cada agente. | ✅ original | Spotify, Airbnb (benchmark hecho) |
| **A-v2** Agnóstico | profiler genérico + correlaciones auto + skew. Sin columnas hardcoded. | 🟡 en prueba | cualquier tabla (Iris ✅) |

A-v1 vive en git history (commits previos a `28408bb`). A-v2 es el HEAD actual.
El eda mantiene back-compat: devuelve keys viejas (`spotify_playlist_corr`, `merge_rows`)
Y nuevas (`top_correlations`, `column_types`) para no romper Model B.

---

## Experimento E-AGNOSTIC: ¿generalizar mejora?

**Hipótesis:** un pipeline agnóstico (A-v2) analiza correctamente CUALQUIER dataset
tabular, manteniendo el rigor estadístico de A-v1.

**Métrica de éxito:**
- ≥ 3 datasets distintos pasan los 4 agentes sin error
- Cada eval reproduce el answer key documentado del dataset
- Tiempo por dataset < 300s (no timeout)

**Resultados parciales (2026-06-14):**

| Dataset | Determinístico (stats) | LLM layer | vs answer key |
|---|---|---|---|
| Iris | ✅ petal_length↔petal_width r=0.963 | ✅ completó | ✅ MATCH (petal best discriminator) |
| Titanic | ✅ skew Fare=4.79, H7/H8 | 🔴 timeout 600s | pendiente (stats OK) |
| Spotify | ✅ recon reproduce findings | 🔴 timeout | pendiente (stats OK) |

**Hallazgo:** el motor estadístico agnóstico FUNCIONA (3/3 producen stats correctas).
El cuello es el LLM: A-v1 y A-v2 llaman al LLM en 3 agentes → timeout en datasets grandes.

**Sub-experimento E-LLM-FINAL:** ¿mover el LLM a solo el Agente 4 (como declara el
diseño "IA solo al final") arregla el timeout sin perder calidad?
- Hipótesis: 1 llamada LLM vs 3 → 3x más rápido, sin timeout, mismo eval
- Variable: flag `LLM_INTERMEDIATE=false` (recon/eda/hypothesis sin LLM)
- Métrica: status ok, tiempo < 300s, eval.json completo
- Estado: ✅ APLICADO Y MEDIDO (2026-06-14)

**Resultado E-LLM-FINAL — el árbitro (bench_runner) habló:**

Esta tabla mide SOLO lo que el experimento controla: velocidad y que el pipeline
cierre sin timeout. La comparación vs answer key es OTRA cosa (ver Adjudicación).

| Dataset | con-LLM (default) | sin-LLM-intermedio (flag) | corrió completo |
|---|---|---|---|
| Titanic | 🔴 timeout 600s | ✅ **218s exit 0** | ✅ eval.json + brief |
| Spotify | 🔴 timeout | (midiendo) | (pendiente) |

**Veredicto del experimento E-LLM-FINAL (solo velocidad/robustez):** confirmado.
600s timeout → 218s éxito, 2.75x más rápido, sin perder el eval. Cumple el diseño
"IA solo al final" + más barato (1 llamada vs 3).
DECISIÓN si Spotify confirma: `LLM_INTERMEDIATE=false` pasa a default.

> ⚠️ ESTO NO DICE que nuestro análisis sea CORRECTO — solo que corre rápido y sin error.

---

## Adjudicación: nosotros vs el answer key (PENDIENTE de revisar)

El answer key es un análisis HUMANO publicado — puede tener errores. Cuando nuestro
pipeline difiere del answer key, NO asumimos que nosotros acertamos ni que ellos sí.
Hay que adjudicar: revisar el cálculo de ambos y decidir quién está bien.

| Dataset | Nuestro hallazgo | Answer key (ref) | ¿Coincide? | Adjudicación |
|---|---|---|---|---|
| Titanic | Pclass↔Fare r=-0.549; skew Fare=4.79 | "clase importa; 1ra paga más" | aparente sí | pendiente revisar nº exacto |
| Spotify | (midiendo) | "danceability/speechiness corr NEG con streams" | ? | pendiente |

**Regla:** una coincidencia aparente NO cierra el caso. Adjudicar = comparar el número
real de ambos lados. Si difieren, investigar el cálculo (¿nosotros mal? ¿ellos mal?).
Esto se revisa luego — acá queda registrado como deuda de verificación.

---

## Decisión (cuándo cerrar el experimento)

```
SI E-LLM-FINAL pasa (3/3 ok, < 300s):
  → A-v2 agnóstico + LLM-al-final es la versión ganadora
  → reproduce answer keys → benchmark mostrable
SI falla:
  → documentar por qué, volver a A-v1 para Spotify, mantener v2 para tabular simple
```

---

## Inventario de modelos (no matar ninguno)

| Modelo | Código | Estado |
|---|---|---|
| A-v1 Spotify | git history | preservado |
| A-v2 Agnóstico | klipso/ HEAD | en prueba |
| Model A Airbnb app | models/model_a/airbnb/ | demo viz |
| **B** HITL | models/model_b/ (graph+state+app) | esqueleto LangGraph, sin probar |
| **C** RAG+Memoria | docs/model_c_proposal.md | propuesta, sin código |

Regla: cada modelo es un experimento válido. Se documenta, se mide, se decide.
Ninguno se borra — se versiona.
