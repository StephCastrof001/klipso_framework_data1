"""Agent 4 — Business Translation: statistical findings → editorial criteria (LLM only agent)."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from langchain_core.messages import HumanMessage

from klipso.llm.provider import get_llm


def _build_brief_prompt(recon_summary: str, eda_summary: str, hypothesis_summary: str) -> str:
    return f"""Eres un Analista de Datos Senior. Traduce el análisis estadístico
de un dataset (de cualquier dominio) en hallazgos concretos y accionables para
un stakeholder de negocio NO técnico.

REGLAS:
- Sin jerga estadística — explica como a un ejecutivo, no a un matemático
- Cada hallazgo verificable: "si X supera Y" o "cuando Z"
- Máximo 5 hallazgos rankeados por impacto
- Incluye sección "Señales de Alerta" con 2-3 red flags (ej. media que engaña por skew)
- Cierra con una recomendación de proceso o decisión

DATOS DE ENTRADA:

=== AUDITORÍA DE DATOS ===
{recon_summary}

=== ANÁLISIS EXPLORATORIO ===
{eda_summary}

=== PRUEBA DE HIPÓTESIS ===
{hypothesis_summary}

FORMATO DE RESPUESTA (en español):
## Brief: Hallazgos Clave del Dataset

### Hallazgos Accionables
1. [señal concreta verificable]
2. ...
3. ...

### Señales de Alerta
- [red flag 1]
- [red flag 2]

### Recomendación
[1 párrafo con acción/decisión específica]
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
        for h in hypothesis_result.get("hypotheses", []):
            h_lines.append(
                f"{h.get('hypothesis')}: {h.get('verdict', 'N/A')} — {h.get('statement', '')} "
                f"(r={h.get('pearson_r')}, p={h.get('pearson_p')})"
            )
        for w in hypothesis_result.get("skew_warnings", []):
            h_lines.append(f"SKEW: {w['column']} media={w['mean']} vs mediana={w['median']} — {w['note']}")
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
