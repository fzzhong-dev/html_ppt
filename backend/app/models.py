from pydantic import BaseModel, Field
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
    theme_data: Optional[dict] = None
    slides: list[Slide] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class OutlineProposalRequest(BaseModel):
    topic: str
    seed_outline: Optional[str] = None


class OutlineProposalResponse(BaseModel):
    steps: list[str]
    outline: str


class GenerateRequest(BaseModel):
    topic: str
    outline: Optional[str] = None
    template_id: Optional[str] = None  # 已废弃，忽略
    page_count: int = Field(default=8, ge=4, le=16)
    creative_mode: bool = True


class ModifyRequest(BaseModel):
    presentation_id: str
    slide_id: Optional[str] = None
    instruction: str
    chat_history: list[dict] = []


class ExportRequest(BaseModel):
    presentation_id: str


class SlideHtmlPatchRequest(BaseModel):
    """Manual editor sync: replace one slide's HTML."""

    slide_id: str
    html_content: str


class SlideInsertRequest(BaseModel):
    """Insert a new slide with raw HTML (e.g. blank page)."""

    html_content: str
    after_index: Optional[int] = None  # insert after this index; None = append at end


class SlideDeleteRequest(BaseModel):
    slide_id: str


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
