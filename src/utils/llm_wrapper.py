import os

import instructor
from anthropic import Anthropic
from anthropic.types.message import Message
from openai import OpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from .config import read_config


def anthropic_chat(
    model: str, system_prompt: str, user_prompt: str, response_model: BaseModel
) -> BaseModel:
    config: dict = read_config()
    api_key: str = config.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment or config")

    client: Anthropic = instructor.from_anthropic(Anthropic(api_key=api_key))
    response: Message = client.messages.create(
        model=model,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0,
        response_model=response_model,
    )
    return response


def openai_chat(
    model: str, system_prompt: str, user_prompt: str, response_model: BaseModel
) -> BaseModel:
    config: dict = read_config()
    api_key: str = config.get("OPENAI_API_KEY")
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or config")

    client: OpenAI = instructor.from_openai(OpenAI(api_key=api_key))
    response: ChatCompletion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0,
        response_model=response_model,
    )
    return response
