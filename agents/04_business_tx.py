"""Agente 4 — Business Translation: hallazgos estadísticos → criterios editoriales."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from langchain_core.messages import HumanMessage

sys.path.insert(0, str(Path(__file__).parent))
from setup_llm import get_llm

OUTPUTS_DIR = Path(__file__).parent.parent / "outputs"


def _build_brief_prompt(recon_summary: str, eda_summary: str, hypothesis_summary: str) -> str:
    return f"""Eres Senior Data Analyst del equipo de Estrategia Editorial de Spotify.
Transforma el análisis estadístico en criterios concretos que los editores puedan aplicar HOY.

REGLAS:
- Sin jerga estadística — habla como si le explicaras a un A&R executive, no a un matemático
- Cada criterio debe ser verificable: "si X supera Y" o "si la canción está en Z plataformas"
- Máximo 5 criterios editoriales rankeados por impacto
- Incluir sección "Señales de Alerta" con 2-3 red flags
- Cerrar con recomendación de proceso para el equipo

DATOS DE ENTRADA:

=== AUDITORÍA DE DATOS ===
{recon_summary}

=== ANÁLISIS EXPLORATORIO ===
{eda_summary}

=== TESTING DE HIPÓTESIS ===
{hypothesis_summary}

FORMATO DE RESPUESTA (en español):
## Brief Editorial: Señales de Éxito Cross-Platform

### Criterios de Inclusión en Playlist
1. [señal concreta verificable]
2. ...
3. ...
4. ...
5. ...

### Señales de Alerta
- [red flag 1]
- [red flag 2]

### Recomendación de Proceso
[1 párrafo con acción específica para el equipo editorial]
"""


def run_business_tx(
    recon_result: dict = None,
    eda_result: dict = None,
    hypothesis_result: dict = None,
) -> str:
    recon_summary = (
        recon_result.get("llm_summary", "No disponible") if recon_result else "No disponible"
    )
    eda_summary = (
        eda_result.get("llm_interpretation", "No disponible") if eda_result else "No disponible"
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
        hypothesis_summary = "No disponible"

    prompt = _build_brief_prompt(recon_summary, eda_summary, hypothesis_summary)

    # Siempre el mejor modelo para el brief editorial final
    llm = get_llm(task="sonnet")
    response = llm.invoke([HumanMessage(content=prompt)])
    brief = response.content

    OUTPUTS_DIR.mkdir(exist_ok=True)
    brief_path = OUTPUTS_DIR / "editorial_brief.md"
    brief_path.write_text(brief, encoding="utf-8")

    print("\n=== BRIEF EDITORIAL ===")
    print(brief)
    print(f"\nGuardado en: {brief_path}")

    return brief


if __name__ == "__main__":
    print("Agente 4 standalone — usando datos de ejemplo para test")
    run_business_tx(
        recon_result={
            "llm_summary": "streams como object con comas, JOIN roto por track_id inconsistente (int vs string). 114 tracks sin match entre plataformas."
        },
        eda_result={
            "llm_interpretation": "Fuerte correlación playlists-streams. Pop y urbano dominan géneros. Distribución de streams muy sesgada (long tail)."
        },
        hypothesis_result={
            "h1": {"hypothesis": "H1", "verdict": "CONFIRMADA", "statement": "Más playlists cross-platform → más streams"},
            "h2": {"hypothesis": "H2", "verdict": "CONFIRMADA", "statement": "Charts múltiples → más streams"},
            "h3": {"hypothesis": "H3", "verdict": "PARCIAL", "statement": "Canciones recientes en playlists rápido → más streams"},
            "h4": {"hypothesis": "H4", "verdict": "RECHAZADA", "statement": "Género / país / colaboradores predicen streams"},
            "llm_interpretation": "H1 y H2 tienen evidencia sólida. El volumen cross-platform de playlists es el predictor más robusto.",
        },
    )
