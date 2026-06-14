import os
from dotenv import load_dotenv

load_dotenv()

MODELS_BEDROCK = {
    "sonnet":      "us.anthropic.claude-sonnet-4-6",
    "haiku":       "anthropic.claude-haiku-4-5-20251001-v1:0",
    "deepseek-r1": "us.deepseek.r1-v1:0",
    "deepseek-v3": "deepseek.v3.2",
    "llama4":      "meta.llama4-scout-17b-instruct-v1:0",
    "nova-lite":   "amazon.nova-lite-v1:0",
    "nova-pro":    "amazon.nova-pro-v1:0",
}

MODELS_OPENAI = {
    "sonnet":      "gpt-4o",
    "haiku":       "gpt-4o-mini",
    "deepseek-r1": "gpt-4o",
    "deepseek-v3": "gpt-4o-mini",
    "llama4":      "gpt-4o-mini",
    "nova-lite":   "gpt-4o-mini",
    "nova-pro":    "gpt-4o",
}

# Ollama local (gratis) — todos los tasks mapean al modelo coder del EC2.
# Usa el endpoint OpenAI-compatible de Ollama, así reusa langchain_openai.
MODELS_OLLAMA = {
    "sonnet":      "qwen35u-tools:9b",
    "haiku":       "qwen35u-tools:9b",
    "deepseek-r1": "qwen3-14b-32k:latest",
    "deepseek-v3": "qwen35u-tools:9b",
    "llama4":      "qwen35u-tools:9b",
    "nova-lite":   "qwen35u-tools:9b",
    "nova-pro":    "qwen3-14b-32k:latest",
}

DEFAULT = "sonnet"


def llm_intermediate_enabled() -> bool:
    """Experimento E-LLM-FINAL: si LLM_INTERMEDIATE=false, los agentes 1-3
    quedan determinísticos puros (sin llamada LLM). business_tx (Agente 4)
    siempre usa LLM. Default true = comportamiento A-v2 original."""
    return os.getenv("LLM_INTERMEDIATE", "true").strip().lower() not in ("false", "0", "no")


def get_llm(task: str = DEFAULT, temperature: float = 0.0):
    """
    Returns a LangChain chat model based on .env configuration.

    Provider selection order:
      LLM_PROVIDER=openai  → OpenAI (gpt-4o / gpt-4o-mini)
      LLM_PROVIDER=bedrock → Amazon Bedrock
      LLM_PROVIDER=ollama  → Ollama local (gratis, vía endpoint OpenAI-compatible)
      LLM_PROVIDER=auto    → OpenAI if OPENAI_API_KEY present, else Bedrock

    task: "sonnet" | "haiku" | "deepseek-r1" | "deepseek-v3" | "llama4" | "nova-lite" | "nova-pro"
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    bedrock_key = os.getenv("AWS_BEARER_TOKEN_BEDROCK") or os.getenv("BEDROCK_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "auto")

    # Ollama local — no toca la lógica OpenAI/Bedrock, solo agrega opción gratis.
    if provider == "ollama":
        from langchain_openai import ChatOpenAI
        model_name = MODELS_OLLAMA.get(task, MODELS_OLLAMA[DEFAULT])
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        print(f"[LLM] Ollama → {model_name} @ {base_url}")
        return ChatOpenAI(
            model=model_name,
            api_key="ollama",  # Ollama ignora la key pero langchain la exige
            base_url=base_url,
            temperature=temperature,
            max_tokens=2048,
        )

    use_openai = (
        provider == "openai"
        or (provider == "auto" and openai_key and not openai_key.startswith("<"))
    )

    if use_openai:
        if not openai_key or openai_key.startswith("<"):
            raise ValueError("OPENAI_API_KEY not configured in .env")
        from langchain_openai import ChatOpenAI
        model_name = MODELS_OPENAI.get(task, MODELS_OPENAI[DEFAULT])
        print(f"[LLM] OpenAI → {model_name}")
        return ChatOpenAI(
            model=model_name,
            api_key=openai_key,
            temperature=temperature,
            max_tokens=2048,
        )
    else:
        if not bedrock_key or bedrock_key.startswith("<"):
            raise ValueError("AWS_BEARER_TOKEN_BEDROCK not configured in .env")
        from langchain_aws import ChatBedrockConverse
        model_id = MODELS_BEDROCK.get(task, MODELS_BEDROCK[DEFAULT])
        region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        print(f"[LLM] Bedrock → {model_id}")
        return ChatBedrockConverse(
            model=model_id,
            api_key=bedrock_key,
            region_name=region,
            temperature=temperature,
            max_tokens=2048,
        )
