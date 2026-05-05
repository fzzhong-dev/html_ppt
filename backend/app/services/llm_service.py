import json
from app.llm.base import get_provider
from app.config import settings

_current_provider = settings.default_provider


def get_current_provider():
    return _current_provider


def set_current_provider(provider_id: str):
    global _current_provider
    _current_provider = provider_id


async def call_llm(messages: list[dict], provider_id: str = None) -> str:
    pid = provider_id or _current_provider
    provider = get_provider(pid)
    return await provider.chat(messages)


async def call_llm_json(messages: list[dict], provider_id: str = None) -> dict:
    response = await call_llm(messages, provider_id)
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)
