import uuid
import re
from datetime import datetime
from typing import Optional

from app.models import Presentation, Slide
from app.services.template_service import TemplateService
from app.services.llm_service import call_llm_json, call_llm


class PPTService:
    def __init__(self):
        self.presentations: dict[str, Presentation] = {}
        self.template_service = TemplateService()

    def create_presentation(self, title: str, template_id: str) -> Presentation:
        slide_types = ["cover", "toc", "content-text", "content-text", "ending"]
        slides = []
        for i, st in enumerate(slide_types):
            html = self.template_service.get_slide_html(template_id, st)
            if html:
                slides.append(Slide(
                    id=str(uuid.uuid4()),
                    page_number=i + 1,
                    html_content=html,
                ))
        presentation = Presentation(
            id=str(uuid.uuid4()),
            title=title,
            template_id=template_id,
            slides=slides,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.presentations[presentation.id] = presentation
        return presentation

    def get_presentation(self, presentation_id: str) -> Optional[Presentation]:
        return self.presentations.get(presentation_id)

    async def generate_with_ai(self, topic: str, template_id: str, outline: str = None) -> Presentation:
        presentation = self.create_presentation(topic, template_id)

        system_prompt = """你是一个PPT内容生成助手。用户给你一个主题，你需要生成PPT各页的内容。
以JSON格式返回，格式如下：
{
  "slides": [
    {"subtitle_top": "PRESENTATION", "title": "主标题", "subtitle": "副标题", "author": "演讲者", "date": "日期"},
    {"section_title": "目录", "toc_1": "章节1", "toc_2": "章节2", "toc_3": "章节3", "toc_4": "章节4"},
    {"header_title": "章节1", "title": "页面标题", "body": "<p>正文内容</p>"},
    {"header_title": "章节2", "title": "页面标题", "body": "<p>正文内容</p>"},
    {"thanks": "谢谢聆听", "message": "感谢您的宝贵时间", "contact": "联系方式"}
  ]
}
只返回JSON，不要其他文字。"""

        user_msg = f"主题：{topic}"
        if outline:
            user_msg += f"\n大纲：{outline}"
        user_msg += f"\n共{len(presentation.slides)}页"

        result = await call_llm_json([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ])

        if "slides" in result:
            for i, slide_data in enumerate(result["slides"]):
                if i < len(presentation.slides):
                    html = presentation.slides[i].html_content
                    for key, value in slide_data.items():
                        placeholder = f'data-editable="{key}"'
                        if placeholder in html:
                            pattern = rf'(<[^>]+data-editable="{key}"[^>]*>)(.*?)(</)'
                            html = re.sub(pattern, rf'\g<1>{value}\g<3>', html, flags=re.DOTALL)
                    presentation.slides[i].html_content = html

        presentation.updated_at = datetime.now()
        return presentation

    async def modify_slide(self, presentation_id: str, slide_id: str, instruction: str, chat_history: list[dict]) -> Optional[Slide]:
        presentation = self.get_presentation(presentation_id)
        if not presentation:
            return None
        slide = next((s for s in presentation.slides if s.id == slide_id), None)
        if not slide:
            return None

        system_prompt = f"""你是一个PPT修改助手。用户会给你修改指令，你需要返回修改后的完整HTML。
规则：
1. 只修改 data-editable 区域的内容
2. 保持HTML结构不变
3. 只返回完整的HTML内容，不要其他文字

当前HTML：
{slide.html_content}"""

        messages = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": instruction}]

        new_html = await call_llm(messages)

        new_html = new_html.strip()
        if new_html.startswith("```html"):
            new_html = new_html[7:]
        if new_html.startswith("```"):
            new_html = new_html[3:]
        if new_html.endswith("```"):
            new_html = new_html[:-3]
        new_html = new_html.strip()

        slide.html_content = new_html
        presentation.updated_at = datetime.now()
        return slide
