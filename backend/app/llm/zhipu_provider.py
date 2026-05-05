from zhipuai import ZhipuAI
from app.llm.base import LLMProvider


class ZhipuProvider(LLMProvider):
    provider_id = "zhipu"
    provider_name = "智谱AI"

    def __init__(self, api_key: str, model: str = "glm-4", base_url: str | None = None):
        client_kw: dict = {"api_key": api_key}
        if base_url:
            client_kw["base_url"] = base_url
        self.client = ZhipuAI(**client_kw)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False, **kwargs) -> str:
        api_kwargs = {"model": self.model, "messages": messages, "stream": stream}
        mt = kwargs.get("max_tokens")
        if mt is not None:
            api_kwargs["max_tokens"] = mt
        response = self.client.chat.completions.create(**api_kwargs)
        if stream:
            return response
        return response.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.client.api_key)
