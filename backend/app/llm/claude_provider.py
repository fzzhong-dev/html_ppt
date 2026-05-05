from anthropic import AsyncAnthropic
from app.llm.base import LLMProvider


class ClaudeProvider(LLMProvider):
    provider_id = "claude"
    provider_name = "Claude"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        system_msg = ""
        chat_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                chat_msgs.append(m)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_msg if system_msg else None,
            messages=chat_msgs,
        )
        return response.content[0].text

    def is_available(self) -> bool:
        return bool(self.client.api_key)
