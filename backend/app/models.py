from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Slide(BaseModel):
    id: str
    page_number: int
    html_content: str
    editable_regions: dict = {}


class Presentation(BaseModel):
    id: str
    title: str
    template_id: str
    theme: str = "default"
    slides: list[Slide] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class GenerateRequest(BaseModel):
    topic: str
    outline: Optional[str] = None
    template_id: Optional[str] = None
    page_count: int = 5


class ModifyRequest(BaseModel):
    presentation_id: str
    slide_id: Optional[str] = None
    instruction: str
    chat_history: list[dict] = []


class ExportRequest(BaseModel):
    presentation_id: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    provider: Optional[str] = None
    stream: bool = False


class ProviderInfo(BaseModel):
    id: str
    name: str
    available: bool


class SwitchProviderRequest(BaseModel):
    provider: str
