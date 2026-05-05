import dashscope
from app.llm.base import LLMProvider


class QwenProvider(LLMProvider):
    provider_id = "qwen"
    provider_name = "通义千问"

    def __init__(self, api_key: str, model: str = "qwen-max"):
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        dashscope.api_key = self.api_key
        response = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            result_format="message",
            stream=stream,
        )
        if stream:
            return response
        return response.output.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.api_key)
