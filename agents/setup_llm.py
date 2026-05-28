import os
from dotenv import load_dotenv

load_dotenv()

# Model registry — Mayo 2026
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
    "sonnet":      "gpt-4o",          # equivalente a Claude Sonnet — razonamiento top
    "haiku":       "gpt-4o-mini",     # equivalente a Claude Haiku — barato
    "deepseek-r1": "gpt-4o",          # sin DeepSeek en OpenAI, usar 4o
    "deepseek-v3": "gpt-4o-mini",
    "llama4":      "gpt-4o-mini",
    "nova-lite":   "gpt-4o-mini",
    "nova-pro":    "gpt-4o",
}

DEFAULT = "sonnet"


def get_llm(task: str = DEFAULT, temperature: float = 0.0):
    """
    Detecta proveedor por variables de entorno:
      OPENAI_API_KEY  → usa OpenAI (gpt-4o / gpt-4o-mini)
      AWS_BEARER_TOKEN_BEDROCK → usa Amazon Bedrock

    task: "sonnet" | "haiku" | "deepseek-r1" | "deepseek-v3" | "llama4" | "nova-lite" | "nova-pro"
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    bedrock_key = os.getenv("AWS_BEARER_TOKEN_BEDROCK") or os.getenv("BEDROCK_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "auto")

    use_openai = (
        provider == "openai"
        or (provider == "auto" and openai_key and not openai_key.startswith("<"))
    )

    if use_openai:
        if not openai_key or openai_key.startswith("<"):
            raise ValueError("OPENAI_API_KEY no configurado en .env")
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
            raise ValueError("AWS_BEARER_TOKEN_BEDROCK no configurado en .env")
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
