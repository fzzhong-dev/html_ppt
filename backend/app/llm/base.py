from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMProvider(ABC):
    provider_id: str = ""
    provider_name: str = ""

    @abstractmethod
    async def chat(self, messages: list[dict], stream: bool = False) -> str | AsyncGenerator[str, None]:
        pass

    def is_available(self) -> bool:
        return False


def get_provider(provider_id: str) -> LLMProvider:
    from app.llm.openai_provider import OpenAIProvider
    from app.llm.claude_provider import ClaudeProvider
    from app.llm.zhipu_provider import ZhipuProvider
    from app.llm.qwen_provider import QwenProvider
    from app.config import settings

    providers = {
        "openai": lambda: OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        ),
        "claude": lambda: ClaudeProvider(
            api_key=settings.claude_api_key,
            model=settings.claude_model,
        ),
        "zhipu": lambda: ZhipuProvider(
            api_key=settings.zhipu_api_key,
            model=settings.zhipu_model,
        ),
        "qwen": lambda: QwenProvider(
            api_key=settings.qwen_api_key,
            model=settings.qwen_model,
        ),
    }
    if provider_id not in providers:
        raise ValueError(f"Unknown provider: {provider_id}")
    return providers[provider_id]()


def list_providers() -> list[dict]:
    result = []
    for pid in ["openai", "claude", "zhipu", "qwen"]:
        try:
            p = get_provider(pid)
            result.append({"id": pid, "name": p.provider_name, "available": p.is_available()})
        except Exception:
            result.append({"id": pid, "name": pid, "available": False})
    return result
