from zhipuai import ZhipuAI
from app.llm.base import LLMProvider


class ZhipuProvider(LLMProvider):
    provider_id = "zhipu"
    provider_name = "智谱AI"

    def __init__(self, api_key: str, model: str = "glm-4"):
        self.client = ZhipuAI(api_key=api_key)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
        )
        if stream:
            return response
        return response.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.client.api_key)
