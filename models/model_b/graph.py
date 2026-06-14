"""
Model B — Human-in-the-Loop analysis graph.

LangGraph StateGraph with interrupt() checkpoints. The graph pauses after each
analytical step and waits for PM input. The PM's feedback is injected into the
state and changes how the next node behaves.

Key contrast vs Model A:
  - Model A: the agent decides which hypotheses to test.
  - Model B: the PM directs the analysis at each checkpoint.

The LLM generates interpretations; pandas/scipy execute the math. The LLM never
touches the raw data directly — it is a planner, not an executor.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from klipso.agents.eda import run_eda
from klipso.agents.hypothesis import run_hypothesis
from klipso.agents.viz import run as run_viz
from klipso.agents.business_tx import run_business_tx

from models.model_b.state import AnalysisState


# ── Node 1: EDA + first checkpoint ──────────────────────────────────────────
def eda_node(state: AnalysisState) -> dict:
    """Run deterministic EDA, then pause for PM review."""
    eda = run_eda(
        spotify_path=state["main_csv"],
        competition_path=state["competition_csv"],
        outputs_dir="outputs/model_b",
    )
    corr = {
        "spotify_playlist_corr": eda.get("spotify_playlist_corr"),
        "merge_rows": eda.get("merge_rows"),
    }

    # PAUSE — PM reviews the EDA before any hypothesis is chosen.
    pm_feedback = interrupt({
        "step": "eda_review",
        "title": "Revisa el EDA",
        "summary": eda["llm_interpretation"],
        "correlations": corr,
        "prompt": "¿Qué hipótesis quieres priorizar? ¿Algo que redirigir?",
    })

    log = state.get("decision_log", [])
    log.append({"step": "eda_review", "pm_input": pm_feedback})

    return {
        "df_merged": eda["df_merged"],
        "eda_summary": eda["llm_interpretation"],
        "eda_corr": corr,
        "pm_eda_feedback": pm_feedback,
        "hypothesis_focus": pm_feedback,   # PM direction drives the next step
        "decision_log": log,
        "step": "eda_done",
    }


# ── Node 2: Hypotheses (PM-directed) + second checkpoint ────────────────────
def hypothesis_node(state: AnalysisState) -> dict:
    """Run hypothesis tests. PM's EDA feedback is available as direction."""
    hyp = run_hypothesis(df_merged=state["df_merged"])

    verdicts = {k: hyp[k]["verdict"] for k in ["h1", "h2", "h3", "h4"]}

    # PAUSE — PM validates findings, can redirect before visualization.
    pm_feedback = interrupt({
        "step": "hypothesis_review",
        "title": "Valida los hallazgos",
        "focus_requested": state.get("hypothesis_focus", ""),
        "verdicts": verdicts,
        "interpretation": hyp["llm_interpretation"],
        "prompt": "¿Los hallazgos son válidos? ¿Refinar algo antes de visualizar?",
    })

    log = state.get("decision_log", [])
    log.append({"step": "hypothesis_review", "pm_input": pm_feedback})

    return {
        "hypothesis_results": hyp,
        "pm_hypothesis_feedback": pm_feedback,
        "decision_log": log,
        "step": "hypothesis_done",
    }


# ── Node 3: Visualization + third checkpoint ────────────────────────────────
def viz_node(state: AnalysisState) -> dict:
    """Generate charts, then pause for PM approval/refinement."""
    viz = run_viz(df_merged=state["df_merged"], outputs_dir="outputs/model_b")

    pm_feedback = interrupt({
        "step": "viz_review",
        "title": "Aprueba las visualizaciones",
        "charts": list(viz["paths"].keys()),
        "prompt": "¿Aprobar las visualizaciones o pedir refinamiento?",
    })

    log = state.get("decision_log", [])
    log.append({"step": "viz_review", "pm_input": pm_feedback})

    return {
        "viz_paths": viz["paths"],
        "pm_viz_feedback": pm_feedback,
        "decision_log": log,
        "step": "viz_done",
    }


# ── Node 4: Brief (incorporates every PM decision) ──────────────────────────
def brief_node(state: AnalysisState) -> dict:
    """Final editorial brief that reflects all PM feedback gathered."""
    pm_context = "\n".join(
        f"- [{d['step']}] PM dijo: {d['pm_input']}"
        for d in state.get("decision_log", [])
    )

    eda_result = {
        "llm_interpretation": state.get("eda_summary", "")
        + f"\n\nDIRECCIÓN DEL PM:\n{pm_context}"
    }

    brief = run_business_tx(
        eda_result=eda_result,
        hypothesis_result=state.get("hypothesis_results"),
        outputs_dir="outputs/model_b",
    )
    return {"brief": brief, "step": "done"}


# ── Graph builder ───────────────────────────────────────────────────────────
def build_graph():
    """Compile the HITL graph with an in-memory checkpointer for interrupts."""
    g = StateGraph(AnalysisState)
    g.add_node("eda", eda_node)
    g.add_node("hypothesis", hypothesis_node)
    g.add_node("viz", viz_node)
    g.add_node("brief", brief_node)

    g.add_edge(START, "eda")
    g.add_edge("eda", "hypothesis")
    g.add_edge("hypothesis", "viz")
    g.add_edge("viz", "brief")
    g.add_edge("brief", END)

    return g.compile(checkpointer=MemorySaver())
