import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import uuid
import streamlit as st
from langgraph.types import Command

from models.model_b.graph import build_graph

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
MAIN_CSV = os.path.join(ROOT, 'inputs', 'spotify', 'track_in_spotify_skill_academy.csv')
COMP_CSV = os.path.join(ROOT, 'inputs', 'spotify', 'track_in_competition _skill_academy.csv')

st.set_page_config(page_title="Klipso Model B — HITL", page_icon="🤝", layout="wide")

st.title("Model B — Human-in-the-Loop")
st.caption("El análisis pausa en cada paso. Tú (PM) revisas, apruebas o rediriges antes de continuar.")

# ── Session state ───────────────────────────────────────────────────────────
if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.state = None       # last returned state
    st.session_state.interrupt = None   # pending interrupt payload
    st.session_state.started = False
    st.session_state.done = False

graph = st.session_state.graph
config = {"configurable": {"thread_id": st.session_state.thread_id}}


def _extract_interrupt(result):
    """Pull the interrupt payload from a graph result, if any."""
    intr = result.get("__interrupt__")
    if not intr:
        return None
    item = intr[0] if isinstance(intr, (list, tuple)) else intr
    return getattr(item, "value", item)


# ── Sidebar: business question + start ──────────────────────────────────────
with st.sidebar:
    st.header("1. Define la pregunta")
    question = st.text_area(
        "Pregunta de negocio",
        value="¿Qué hace que una canción triunfe en múltiples plataformas?",
        height=100,
    )
    if st.button("▶ Iniciar análisis", type="primary", disabled=st.session_state.started):
        st.session_state.started = True
        with st.spinner("Corriendo EDA..."):
            result = graph.invoke(
                {
                    "main_csv": MAIN_CSV,
                    "competition_csv": COMP_CSV,
                    "question": question,
                    "decision_log": [],
                },
                config=config,
            )
        st.session_state.interrupt = _extract_interrupt(result)
        st.session_state.state = result
        st.rerun()

    if st.session_state.started and st.button("🔄 Reiniciar"):
        for k in ["graph", "thread_id", "state", "interrupt", "started", "done"]:
            st.session_state.pop(k, None)
        st.rerun()


# ── Main: checkpoint UI ─────────────────────────────────────────────────────
if not st.session_state.started:
    st.info("👈 Define la pregunta de negocio y presiona **Iniciar análisis**.")
    st.markdown("""
    ### Cómo funciona Model B

    A diferencia del Model A (corre todo de una), aquí el grafo **se pausa** en 3 checkpoints:

    1. **Después del EDA** → revisas correlaciones, decides qué hipótesis priorizar
    2. **Después de las hipótesis** → validas los hallazgos, puedes redirigir
    3. **Después de las visualizaciones** → apruebas o pides refinamiento

    Tu feedback en cada paso se inyecta al estado y moldea el brief final.
    LangGraph `interrupt()` persiste el estado entre pausas.
    """)

elif st.session_state.interrupt:
    payload = st.session_state.interrupt
    step = payload.get("step", "")

    st.subheader(f"⏸ Checkpoint: {payload.get('title', step)}")

    if step == "eda_review":
        st.markdown("**Correlaciones detectadas:**")
        st.json(payload.get("correlations", {}))
        with st.expander("Interpretación del EDA (LLM)", expanded=True):
            st.markdown(payload.get("summary", ""))

    elif step == "hypothesis_review":
        if payload.get("focus_requested"):
            st.info(f"Tu dirección previa: _{payload['focus_requested']}_")
        st.markdown("**Veredictos de hipótesis:**")
        cols = st.columns(4)
        for col, (h, v) in zip(cols, payload.get("verdicts", {}).items()):
            col.metric(h.upper(), v)
        with st.expander("Interpretación (LLM)", expanded=True):
            st.markdown(payload.get("interpretation", ""))

    elif step == "viz_review":
        st.markdown("**Visualizaciones generadas:**")
        for c in payload.get("charts", []):
            st.markdown(f"- `{c}`")

    st.divider()
    st.markdown(f"**{payload.get('prompt', '¿Continuar?')}**")

    feedback = st.text_input("Tu feedback / dirección (opcional)", key=f"fb_{step}")
    col_a, col_r = st.columns(2)

    def _resume(value):
        with st.spinner("Continuando..."):
            result = graph.invoke(Command(resume=value), config=config)
        st.session_state.interrupt = _extract_interrupt(result)
        st.session_state.state = result
        if not st.session_state.interrupt:
            st.session_state.done = True
        st.rerun()

    with col_a:
        if st.button("✅ Aprobar y continuar", type="primary"):
            _resume(feedback or "aprobado sin cambios")
    with col_r:
        if st.button("↪ Redirigir con mi feedback"):
            _resume(feedback or "redirigir (sin nota)")

    # Audit trail so far
    log = (st.session_state.state or {}).get("decision_log", [])
    if log:
        with st.expander("📋 Decisiones tomadas hasta ahora"):
            for d in log:
                st.markdown(f"- **{d['step']}** → _{d['pm_input']}_")

elif st.session_state.done:
    st.success("✅ Análisis completo — moldeado por tus decisiones")
    state = st.session_state.state

    st.subheader("Brief editorial final")
    st.markdown(state.get("brief", "(sin brief)"))

    st.divider()
    st.subheader("📋 Trazabilidad — tus decisiones moldearon este brief")
    for d in state.get("decision_log", []):
        st.markdown(f"**{d['step']}** → _{d['pm_input']}_")

    st.caption("Esto es lo que diferencia B de A: el output refleja tu juicio en cada paso.")
