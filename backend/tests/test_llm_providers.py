import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.llm.base import LLMProvider, get_provider


def test_get_provider_openai():
    provider = get_provider("openai")
    assert isinstance(provider, LLMProvider)
    assert provider.provider_id == "openai"


def test_get_provider_claude():
    provider = get_provider("claude")
    assert provider.provider_id == "claude"


def test_get_provider_zhipu():
    provider = get_provider("zhipu")
    assert provider.provider_id == "zhipu"


def test_get_provider_qwen():
    provider = get_provider("qwen")
    assert provider.provider_id == "qwen"


def test_get_provider_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("unknown_provider")


def test_list_providers():
    from app.llm.base import list_providers
    providers = list_providers()
    ids = [p["id"] for p in providers]
    assert "openai" in ids
    assert "claude" in ids
    assert "zhipu" in ids
    assert "qwen" in ids


@pytest.mark.asyncio
async def test_openai_chat():
    with patch("app.llm.openai_provider.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        from app.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key="test-key")
        result = await provider.chat([{"role": "user", "content": "Hello"}])
        assert result == "Hello response"
