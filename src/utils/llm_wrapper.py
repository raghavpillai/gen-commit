from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from .config import read_config


def chat(
    system_prompt: str,
    user_prompt: str,
    response_model: BaseModel,
) -> BaseModel:
    provider_params, request_params = _get_params()

    client: OpenAI = OpenAI(**provider_params)
    response: ChatCompletion = client.chat.completions.parse(
        **request_params,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0,
        response_format=response_model,
    )
    return response.choices[0].message.parsed


def _get_params() -> tuple[dict, dict]:
    config: dict = read_config()
    model: str = config.get("MODEL")
    if not model:
        raise ValueError("MODEL not found in config")

    provider, model_name = model.lower().split(":", 1)

    provider_params: dict = {}
    request_params: dict = {}

    if provider == "openai":
        api_key: str = config.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        provider_params["api_key"] = api_key
    elif provider == "anthropic":
        api_key: str = config.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        provider_params["api_key"] = api_key
        provider_params["base_url"] = "https://api.anthropic.com/v1/"
    elif provider == "ollama":
        api_key: str = config.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        provider_params["api_key"] = api_key
        provider_params["base_url"] = (
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    else:
        raise ValueError(f"Invalid provider: {provider}")

    reasoning_models: list[str] = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]
    if model_name in reasoning_models:
        request_params["reasoning_effort"] = "none"

    request_params["model"] = model_name

    return provider_params, request_params
