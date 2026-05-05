"""Shared httpx settings for OpenAI-compatible SDKs (OpenAI, DeepSeek, etc.)."""

from __future__ import annotations

import httpx

from app.config import settings


def build_openai_async_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(
            settings.llm_http_timeout_seconds,
            connect=settings.llm_connect_timeout_seconds,
        ),
        trust_env=settings.llm_trust_env_proxy,
    )
