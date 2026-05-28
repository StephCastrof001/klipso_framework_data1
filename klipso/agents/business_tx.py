"""Agent 4 — Business Translation: statistical findings → editorial criteria (LLM only agent)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from langchain_core.messages import HumanMessage

from klipso.llm.provider import get_llm


def _build_brief_prompt(recon_summary: str, eda_summary: str, hypothesis_summary: str) -> str:
    return f"""You are a Senior Data Analyst on Spotify's Editorial Strategy team.
Transform the statistical analysis into concrete criteria that editors can apply TODAY.

RULES:
- No statistical jargon — explain as if talking to an A&R executive, not a mathematician
- Each criterion must be verifiable: "if X exceeds Y" or "if the song is in Z platforms"
- Maximum 5 editorial criteria ranked by impact
- Include "Warning Signals" section with 2-3 red flags
- Close with a process recommendation for the team

INPUT DATA:

=== DATA AUDIT ===
{recon_summary}

=== EXPLORATORY ANALYSIS ===
{eda_summary}

=== HYPOTHESIS TESTING ===
{hypothesis_summary}

RESPONSE FORMAT (in Spanish):
## Brief Editorial: Señales de Éxito Cross-Platform

### Criterios de Inclusión en Playlist
1. [concrete verifiable signal]
2. ...
3. ...
4. ...
5. ...

### Señales de Alerta
- [red flag 1]
- [red flag 2]

### Recomendación de Proceso
[1 paragraph with specific action for the editorial team]
"""


def run_business_tx(
    recon_result: dict = None,
    eda_result: dict = None,
    hypothesis_result: dict = None,
    outputs_dir: str = "outputs",
    llm=None,
) -> str:
    """
    Translates statistical findings into actionable editorial criteria using an LLM.

    This is the only agent in Model A that uses an LLM for reasoning.
    All other agents (recon, eda, hypothesis) are deterministic.

    Args:
        recon_result: Output dict from run_recon().
        eda_result: Output dict from run_eda().
        hypothesis_result: Output dict from run_hypothesis().
        outputs_dir: Directory to save editorial_brief.md.
        llm: Optional pre-built LangChain LLM. Uses "sonnet" task by default.

    Returns:
        str: The full editorial brief in Markdown.
    """
    recon_summary = (
        recon_result.get("llm_summary", "Not available") if recon_result else "Not available"
    )
    eda_summary = (
        eda_result.get("llm_interpretation", "Not available") if eda_result else "Not available"
    )

    if hypothesis_result:
        h_lines = []
        for key in ["h1", "h2", "h3", "h4"]:
            h = hypothesis_result.get(key, {})
            h_lines.append(
                f"{h.get('hypothesis', key)}: {h.get('verdict', 'N/A')} — {h.get('statement', '')}"
            )
        h_lines.append("\nInterpretación: " + hypothesis_result.get("llm_interpretation", "N/A"))
        hypothesis_summary = "\n".join(h_lines)
    else:
        hypothesis_summary = "Not available"

    prompt = _build_brief_prompt(recon_summary, eda_summary, hypothesis_summary)

    if llm is None:
        llm = get_llm(task="sonnet")

    response = llm.invoke([HumanMessage(content=prompt)])
    brief = response.content

    Path(outputs_dir).mkdir(exist_ok=True)
    brief_path = Path(outputs_dir) / "editorial_brief.md"
    brief_path.write_text(brief, encoding="utf-8")

    print("\n=== BRIEF EDITORIAL ===")
    print(brief)
    print(f"\nSaved to: {brief_path}")

    return brief
