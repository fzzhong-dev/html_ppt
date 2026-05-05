import json
import logging
from collections.abc import AsyncGenerator

from app.config import settings
from app.llm.base import get_provider

logger = logging.getLogger(__name__)


def parse_llm_json_text(raw_text: str) -> dict:
    """Parse JSON from model output (strip BOM and markdown fences); allow prose before the first brace."""
    text = (raw_text or "").strip()
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff").strip()
    if not text:
        raise ValueError("模型返回为空，无法解析 JSON")

    if text.startswith("```"):
        lines = text.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        while lines and lines[-1].strip().startswith("```"):
            lines.pop()
        text = "\n".join(lines).strip()

    if not text:
        raise ValueError("模型返回为空（去除围栏后），无法解析 JSON")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except json.JSONDecodeError:
            logger.warning(
                "call_llm_json: brace-slice parse failed; preview=%r",
                snippet[:500],
            )

    logger.warning(
        "call_llm_json: invalid JSON; preview=%r",
        text[:800],
    )
    raise ValueError("模型返回的内容不是合法 JSON（可能超时、截断或未输出正文）")


_current_provider = settings.default_provider

_FALLBACK_ORDER = ("deepseek", "openai", "zhipu", "qwen", "claude")


def get_current_provider():
    return _current_provider


def set_current_provider(provider_id: str):
    global _current_provider
    _current_provider = provider_id


def _provider_available(provider_id: str) -> bool:
    try:
        return get_provider(provider_id).is_available()
    except Exception:
        return False


def resolve_provider_id(preferred: str | None = None) -> str:
    """Pick first provider that has credentials among preferred + fallbacks."""
    pid = preferred or _current_provider
    if _provider_available(pid):
        return pid
    tried = {pid}
    for alt in _FALLBACK_ORDER:
        if alt in tried:
            continue
        tried.add(alt)
        if _provider_available(alt):
            logger.warning(
                "LLM 提供商 %s 不可用，已自动切换到 %s（请在 .env 设置 DEFAULT_PROVIDER 或补齐密钥）",
                pid,
                alt,
            )
            return alt
    return pid


async def call_llm(messages: list[dict], provider_id: str = None, **kwargs) -> str:
    pid = resolve_provider_id(provider_id)
    provider = get_provider(pid)
    return await provider.chat(messages, **kwargs)


async def call_llm_json(messages: list[dict], provider_id: str = None, *, max_tokens: int | None = None) -> dict:
    kw = {}
    if max_tokens is not None:
        kw["max_tokens"] = max_tokens
    response = await call_llm(messages, provider_id, **kw)
    return parse_llm_json_text(response)


async def call_llm_stream(messages: list[dict], provider_id: str = None, **kwargs) -> AsyncGenerator[str, None]:
    """Stream LLM response as text chunks."""
    pid = resolve_provider_id(provider_id)
    provider = get_provider(pid)
    response = await provider.chat(messages, stream=True, **kwargs)

    # OpenAI-compatible (async): iterate with async for
    if hasattr(response, "__aiter__"):
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
        return

    # Sync iterator fallback (e.g. Zhipu)
    if hasattr(response, "__iter__"):
        for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content
        return

    # Unexpected: just yield the whole string
    yield str(response)
