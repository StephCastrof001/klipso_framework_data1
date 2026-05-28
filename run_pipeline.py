"""Pipeline completo — ejecuta los 4 agentes Spotify en secuencia."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import importlib.util
import time
from pathlib import Path

AGENTS_DIR = Path(__file__).parent / "agents"


def _load_agent(filename: str):
    """Carga un módulo con nombre numérico que Python no puede importar directamente."""
    path = AGENTS_DIR / filename
    spec = importlib.util.spec_from_file_location(filename.replace(".", "_"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_pipeline() -> dict:
    print("=" * 60)
    print("PIPELINE SPOTIFY EDITORIAL — INICIO")
    print("=" * 60)

    # --- Agente 1: Data Recon ---
    print("\n[1/4] DATA RECON")
    print("-" * 40)
    t0 = time.time()
    agent01 = _load_agent("01_data_recon.py")
    recon_result = agent01.run_recon()
    print(f"Agente 1 completado en {time.time() - t0:.1f}s")

    # --- Agente 2: EDA Auto ---
    print("\n[2/4] EDA AUTO")
    print("-" * 40)
    t0 = time.time()
    agent02 = _load_agent("02_eda_auto.py")
    eda_result = agent02.run_eda()
    print(f"Agente 2 completado en {time.time() - t0:.1f}s")

    # --- Agente 3: Hypothesis Testing (reutiliza df_merged del Agente 2) ---
    print("\n[3/4] HYPOTHESIS TESTING")
    print("-" * 40)
    t0 = time.time()
    agent03 = _load_agent("03_hypothesis.py")
    hypothesis_result = agent03.run_hypothesis(
        df_merged=eda_result.get("df_merged")  # evita re-leer y re-limpiar CSVs
    )
    print(f"Agente 3 completado en {time.time() - t0:.1f}s")

    # --- Agente 4: Business Translation ---
    print("\n[4/4] BUSINESS TRANSLATION")
    print("-" * 40)
    t0 = time.time()
    agent04 = _load_agent("04_business_tx.py")
    brief = agent04.run_business_tx(
        recon_result=recon_result,
        eda_result=eda_result,
        hypothesis_result=hypothesis_result,
    )
    print(f"Agente 4 completado en {time.time() - t0:.1f}s")

    # --- Resumen final ---
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETADO")
    print("=" * 60)

    veredictos = {
        key: hypothesis_result[key]["verdict"]
        for key in ["h1", "h2", "h3", "h4"]
    }
    print("\nVeredictos de hipótesis:")
    for h, v in veredictos.items():
        print(f"  {h.upper()}: {v}")

    outputs_dir = Path(__file__).parent / "outputs"
    print(f"\nOutputs generados en: {outputs_dir}")
    for f in outputs_dir.glob("*"):
        print(f"  {f.name}")

    return {
        "recon": recon_result,
        "eda": eda_result,
        "hypothesis": hypothesis_result,
        "brief": brief,
    }


if __name__ == "__main__":
    run_pipeline()
