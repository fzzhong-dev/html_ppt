from openai import AsyncOpenAI
from app.llm.base import LLMProvider
from app.llm.openai_http import build_openai_async_http_client


class DeepseekProvider(LLMProvider):
    provider_id = "deepseek"
    provider_name = "DeepSeek"

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", model: str = "deepseek-chat"):
        self._http_client = build_openai_async_http_client()
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, http_client=self._http_client)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False, **kwargs) -> str:
        api_kwargs = {"model": self.model, "messages": messages, "stream": stream}
        mt = kwargs.get("max_tokens")
        if mt is not None:
            api_kwargs["max_tokens"] = mt
        response = await self.client.chat.completions.create(**api_kwargs)
        if stream:
            return response
        return response.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.client.api_key and self.client.api_key != "")
