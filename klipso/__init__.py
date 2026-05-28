"""
klipso — AI data analysis framework with three philosophical approaches.

Model A (Deterministic): pandas + scipy, LLM only for editorial brief
Model B (HITL): LangGraph interrupt() — PM reviews at each step
Model C (RAG + Memory): Firecrawl + Mem0 + Reflexion self-improvement

Quick start:
    from klipso.agents import run_recon, run_eda, run_hypothesis, run_business_tx, run_viz
    from klipso.llm import get_llm

    recon = run_recon(spotify_path="inputs/spotify.csv", competition_path="inputs/competition.csv")
    eda   = run_eda(spotify_path="inputs/spotify.csv", competition_path="inputs/competition.csv")
    hyp   = run_hypothesis(df_merged=eda["df_merged"])
    brief = run_business_tx(recon_result=recon, eda_result=eda, hypothesis_result=hyp)
"""

from klipso.llm.provider import get_llm
from klipso.agents import run_recon, run_eda, run_hypothesis, run_business_tx, run_viz

__version__ = "0.1.0"
__all__ = [
    "get_llm",
    "run_recon",
    "run_eda",
    "run_hypothesis",
    "run_business_tx",
    "run_viz",
]
