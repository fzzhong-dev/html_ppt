import dashscope
from app.llm.base import LLMProvider


class QwenProvider(LLMProvider):
    provider_id = "qwen"
    provider_name = "通义千问"

    def __init__(self, api_key: str, model: str = "qwen-max"):
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False, **kwargs) -> str:
        dashscope.api_key = self.api_key
        params = {
            "model": self.model,
            "messages": messages,
            "result_format": "message",
            "stream": stream,
        }
        mt = kwargs.get("max_tokens")
        if mt is not None:
            params["max_tokens"] = mt
        response = dashscope.Generation.call(**params)
        if stream:
            return response
        return response.output.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.api_key)
