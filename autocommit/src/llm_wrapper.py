import os
from anthropic import Anthropic
from openai import OpenAI

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY") or os.getenv(
    "ACOMMIT_ANTHROPIC_API_KEY"
)
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY") or os.getenv("ACOMMIT_OPENAI_API_KEY")


def anthropic_chat(system_prompt: str, user_prompt: str) -> str:
    client: Anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
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
    client: OpenAI = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
        temperature=0.2,
    )
    return response.choices[0].message.content
