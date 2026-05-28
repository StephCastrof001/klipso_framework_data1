import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse

load_dotenv()

SONNET = "anthropic.claude-sonnet-4-5-20251001-v1:0"

def get_llm(model: str = SONNET) -> ChatBedrockConverse:
    api_key = os.getenv("BEDROCK_API_KEY")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    if not api_key or api_key.startswith("<"):
        raise ValueError(
            "BEDROCK_API_KEY no configurado. Crea un .env con la key de Bedrock Console → API Keys."
        )
    return ChatBedrockConverse(
        model=model,
        api_key=api_key,
        region_name=region,
    )
