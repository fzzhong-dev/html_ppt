from openai import AsyncOpenAI
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    provider_id = "openai"
    provider_name = "OpenAI"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
        )
        if stream:
            return response
        return response.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.client.api_key and self.client.api_key != "")
