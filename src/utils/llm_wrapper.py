import os
from anthropic import Anthropic
from anthropic.types.message import Message
from openai import OpenAI
from openai.types.chat import ChatCompletion
from .read_config import read_config


def anthropic_chat(system_prompt: str, user_prompt: str) -> str:
    config: dict = read_config()
    api_key: str = config.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment or config")

    client: Anthropic = Anthropic(api_key=api_key)
    response: Message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.2,
    )
    return response.content[0].text


def openai_chat(system_prompt: str, user_prompt: str) -> str:
    config: dict = read_config()
    api_key: str = config.get("OPENAI_API_KEY")
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment or config")

    client: OpenAI = OpenAI(api_key=api_key)
    response: ChatCompletion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.2,
    )
    return response.choices[0].message.content
