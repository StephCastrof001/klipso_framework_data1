# Benchmark: Klipso vs SarangGami — Análisis Airbnb NYC 2019

> Mismo dataset. Dos metodologías. Resultados distintos.
> Escrito para PM no-técnico — sin jerga estadística.
> Referencia: https://github.com/SarangGami/Capstone-EDA-project-1-Airbnb-bookings-analysis

---

## La pregunta de negocio que ambos respondemos

**"¿Qué factores determinan el precio de un Airbnb en Nueva York?"**

Mismos 48,895 listings. Mismo dataset 2019. Mismas variables.
Pero llegamos a conclusiones distintas en puntos clave — y la razón es metodológica.

---

## Diferencia #1 — Describir vs Probar (la más importante)

### SarangGami
Usa visualizaciones para **describir patrones** que aparecen en el gráfico:
> "Manhattan is the most expensive place to stay in NYC"
> "Brooklyn comes second with cheaper prices"

Conclusión correcta — y el método funciona para cualquier ciudad, no solo NYC.
El patrón borough→precio es válido en Londres, Barcelona, Ciudad de México.
**El límite no es el hallazgo, es que se queda en descripción.**

### Klipso
Usa tests estadísticos para **probar que las diferencias son reales**, no ruido:
- Manhattan vs Bronx: p < 0.001 (Mann-Whitney)
- Resultado: **confirmado con evidencia**, no solo observado

**Para un PM esto importa porque:** una observación que "se ve en el gráfico" puede ser
coincidencia del dataset. Una prueba estadística dice "si tomáramos otros 48,000 listings
de cualquier ciudad con estructura borough/barrio, este patrón seguiría apareciendo con
alta probabilidad". La diferencia entre una anécdota y un hallazgo replicable.

---

## Diferencia #2 — Media vs Mediana (el número que miente)

### SarangGami
Reporta precio promedio (mean). No hay evidencia de que corrigieran el sesgo.

**Problema:** hay 1 listing a $10,000/noche en el dataset. Ese listing solo
infla el promedio de todo Manhattan. El promedio "miente" cuando hay outliers.

### Klipso
Detectó la distribución sesgada y usó **mediana** como KPI principal:

```
Media NYC:    $152.8  ← inflada por outliers extremos
Mediana NYC:  $106.0  ← lo que paga el 50% de los huéspedes realmente
```

**Para un PM:** si usas media para fijar precios o benchmarks, estás comparando
contra un número irreal. La mediana es el precio que encuentra un huésped típico.

---

## Diferencia #2.5 — Los outliers mueven la aguja (y eso importa)

Este hallazgo robustece el análisis de forma contraintuitiva.

Calculamos la correlación precio vs host_listings_count con tres versiones del dato:

| Dataset | Pearson r | Interpretación |
|---|---|---|
| Raw (todos los datos) | 0.057 | Correlación casi nula |
| Sin price=0 | 0.057 | Igual — los 11 casos no cambian nada |
| Sin outliers extremos (p99, price ≤ $799) | **0.151** | Sube casi 3× |
| SarangGami reportó | ~0.17 | Probablemente usaron algún recorte |

**Qué significa esto:** los 239 listings con precio >$1,000 (0.5% del dataset)
generan el 65% de la varianza en esa correlación. Un puñado de penthouses de
Tribeca a $10,000/noche está distorsionando la relación entre hosts profesionales
y precio para el 99.5% del mercado.

**La lección metodológica:** antes de reportar una correlación, hay que verificar
qué parte del dataset la está empujando. Si viene del 0.5% extremo, es un artefacto
del dataset de lujo, no una señal del mercado general.

**Esto suma al rigor de Klipso:** detectamos que aun con r=0.15 (recortado), el
test formal dice p=0.305 — no significativo. La correlación visible en el gráfico
no sobrevive al test de "¿es esto real o ruido?".

---

## Diferencia #3 — H4: el hallazgo que contradijimos

Este es el punto donde más divergemos.

### SarangGami reportó como hallazgo:
> "There is a weak positive correlation (0.17) between the price column and the
> calculated_host_listings_count column, which suggests that hosts with more
> listings tend to charge higher prices."

Traducción: hosts profesionales (más propiedades) cobran más.

### Klipso lo testeó formalmente y lo RECHAZÓ:

| | Hosts ocasionales (1-4 props) | Hosts profesionales (5+) |
|---|---|---|
| Precio mediano | $105 | $116 |
| ¿Diferencia real? | **NO** — p = 0.305 |

**p = 0.305 significa:** hay un 30% de probabilidad de que esa diferencia de $11
sea pura coincidencia del dataset. No es estadísticamente significativa.

**La razón de la divergencia:** SarangGami calculó la correlación en datos sin
cortar outliers. Con los top 1% de precios recortados, el r sube de 0.057 a 0.151 —
más cerca de su 0.17. Pero aun así: **0.17 es correlación débil y el test formal
dice que no es significativo.**

**Para un PM:** si tomáramos la conclusión de SarangGami, podríamos decir
"contrata un host profesional para tu propiedad, cobrará más". La evidencia dice
que eso no es verdad. El precio lo determina la ubicación y el tipo, no la
experiencia del anfitrión.

---

## Diferencia #4 — Limpieza de datos: visible vs invisible

### SarangGami
La limpieza existe (el análisis corre sin errores), pero **no está documentada**.
No se explica qué se hizo con los price=0, los min_nights=1250, los nulls de reviews.

### Klipso
Cada decisión de limpieza está documentada con 3 campos:
- **Problema:** qué encontré
- **Diagnóstico:** por qué ocurre (error vs señal de negocio)
- **Decisión:** qué hice y por qué

Ejemplo:
```
Problema:    reviews_per_month tiene 10,052 nulls (20.56%)
Diagnóstico: son listings nuevos sin reservas — no es error, es información
Decisión:    imputar 0 (correcto — ausencia de reseñas = 0 reseñas/mes)
             NO eliminar — perderíamos 20% del mercado nuevo
```

**Para un PM:** si no documentas las decisiones de limpieza, no puedes
reproducir el análisis, auditar el resultado, ni explicar a un stakeholder
por qué tomaste cierta decisión.

---

## Diferencia #5 — Profundidad de las recomendaciones

### SarangGami (conclusiones)
- "Manhattan and Brooklyn have highest demand — attractive for hosts to invest"
- "Consider investing in property near airports in Queens"
- "Short-term stays dominate — hosts should accommodate shorter stays"

Correcto pero **genérico**. Son observaciones que se derivan directamente de
ver el mapa de la ciudad — no requieren análisis de datos para llegar ahí.
Un agente inmobiliario sin dataset diría lo mismo basado en intuición.

### Klipso (criterios accionables)
- Entire home cobra **2.3× más** que habitación privada — sin importar el barrio
- H4 RECHAZADA: invertir en un host "profesional" NO garantiza precio premium
- Disponibilidad alta correlaciona con más reseñas (ρ=0.298) — señal de demanda
- Top 10 barrios más caros = Manhattan; Top 10 barrios con más demanda = Brooklyn/Harlem
  → **Tensión real:** caro ≠ popular. Tribeca ($295 mediana) no está en top-10 reseñas.

**Para un PM:** "invertir en Manhattan" es una observación. "Entire home en Brooklyn
con >200 días de disponibilidad tiene mayor probabilidad de alta demanda con precio
competitivo" es un criterio de decisión.

---

## Diferencia #6 — Framework reusable vs notebook único

### SarangGami
Jupyter notebook. Excelente análisis exploratorio. Pero si mañana llegan datos
de Airbnb Barcelona o 2024, hay que reescribir todo.

### Klipso
Framework con agentes independientes + paquete pip-installable:
```bash
python run_pipeline.py \
  --main-csv inputs/airbnb_barcelona.csv \
  --competition-csv inputs/... \
  --outputs-dir outputs/barcelona
```
El análisis corre sobre cualquier dataset compatible. La metodología es el activo,
no el análisis de un dataset específico.

**Para un PM:** Sarang hizo un análisis. Klipso construyó una herramienta que
puede hacer ese análisis. Son objetivos distintos y ambos son válidos.

---

## Tabla resumen — dónde coincidimos y dónde divergemos

| Dimensión | SarangGami | Klipso | Veredicto |
|---|---|---|---|
| Manhattan más caro | ✅ sí | ✅ sí (p<0.001) | **Coinciden** |
| Brooklyn 2do borough | ✅ sí | ✅ sí (p<0.001) | **Coinciden** |
| Room type predice precio | ✅ sí (visual) | ✅ sí (Kruskal H=22,414) | **Coinciden** |
| Host profesional = precio mayor | ✅ reportado (r=0.17) | ❌ RECHAZADO (p=0.305) | **Divergen** |
| KPI de precio | Mean $152 | Median $106 | **Divergen** |
| Queens alta demanda | ✅ sí | ✅ sí (reseñas) | **Coinciden** |
| Limpieza documentada | ❌ implícita | ✅ explícita con justificación | **Divergen** |
| Tests estadísticos | ❌ solo visual | ✅ Kruskal/Mann-Whitney/Spearman | **Divergen** |
| Framework reusable | ❌ notebook único | ✅ paquete Python | **Divergen** |

---

## ¿Cuál es "mejor"?

**Depende del objetivo.**

SarangGami hace **EDA exploratorio** de alta calidad — excelente para descubrir patrones
en un dataset nuevo, comunicar a stakeholders no técnicos con gráficos, presentar
en un portafolio de data analysis visual.

Klipso hace **análisis inferencial + framework** — correcto para tomar decisiones de negocio,
para auditar hallazgos, para repetir el análisis en nuevos datasets, para demostrar
que los patrones son reales y no artefactos del dataset.

El gap más importante de Klipso vs SarangGami **no es técnico — es narrativo**:
SarangGami tiene mejor storytelling visual en el notebook. Klipso tiene mejor
rigor metodológico pero la historia es más difícil de leer.

---

## Ruta de mejoras para Klipso Airbnb (priorizadas)

### Prioridad 1 — Corregir gaps metodológicos vs benchmark

| Gap | Qué falta | Esfuerzo |
|---|---|---|
| Sin análisis geoespacial | SarangGami muestra mapas de densidad por barrio. Klipso no tiene lat/long chart | Medio |
| Queens near airports | SarangGami identifica barrios aeropuerto como hidden gem. Klipso no los segmenta | Bajo |
| min_nights segmentation | 747 listings con >30 noches = mercado distinto. No analizamos por separado | Bajo |
| Correlación host_listings | SarangGami reporta r=0.17 como hallazgo. Klipso lo rechaza formalmente — documentar esto en dashboard como "lo que el análisis visual no captura" | Bajo |

### Prioridad 2 — Corregir gaps del framework (transversales)

| Gap | Descripción |
|---|---|
| Agentes hardcoded Spotify | 98 refs a columnas Spotify en klipso/agents/*.py — Airbnb tuvo que crear viz_airbnb.py separado |
| Config-driven | dataset.yaml por dataset — desbloquea reusabilidad real |
| Tests automáticos | smoke test corre Model A sobre Spotify + Airbnb, detecta regresiones |

### Prioridad 3 — Construir Model B y C

Ver `docs/model_b_proposal.md` y `docs/model_c_proposal.md` para specs completos.
Pendiente de refinar contra patrones de repos GitHub adicionales.

---

*Benchmark realizado: 2026-05-28 | Dataset: Airbnb NYC 2019 (48,895 listings)*
*Referencia: SarangGami/Capstone-EDA-project-1-Airbnb-bookings-analysis*
