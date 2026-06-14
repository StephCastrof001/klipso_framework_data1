"""Shared state for the Model B (HITL) LangGraph workflow."""
from typing import TypedDict, Optional, Any


class AnalysisState(TypedDict, total=False):
    # --- Inputs ---
    main_csv: str
    competition_csv: str
    question: str               # business question the PM defines

    # --- Data flowing through the graph ---
    df_merged: Any              # pandas DataFrame (kept in-memory between nodes)
    eda_summary: str            # LLM interpretation of EDA
    eda_corr: dict              # correlation dict for PM to review

    # --- PM direction captured at interrupt checkpoints ---
    pm_eda_feedback: str        # PM's note after reviewing EDA
    hypothesis_focus: str       # which hypotheses the PM wants prioritized
    hypothesis_results: dict    # H1-H4 verdicts + stats
    pm_hypothesis_feedback: str # PM's validation/redirect after hypotheses
    viz_paths: dict             # generated chart paths
    pm_viz_feedback: str        # PM's approval/refinement on visuals

    # --- Final output ---
    brief: str                  # editorial brief, shaped by PM feedback

    # --- Control / audit trail ---
    step: str                   # current step name
    decision_log: list          # ordered record of every PM decision
