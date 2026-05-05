import asyncio
import logging
import re
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Optional

from app.models import Presentation, Slide
from app.services.llm_errors import format_llm_error
from app.services.llm_service import call_llm_json, call_llm, call_llm_stream
from app.services.slide_html import finalize_slide_html, minimal_slide, SLIDE_PLACEHOLDER_HINT
from app.services.layout_prompts import LAYOUT_ENHANCEMENT, MODIFY_LAYOUT_GUIDE

logger = logging.getLogger(__name__)


def _extract_slide_html_from_dict(item: dict) -> str | None:
    """LLM JSON may use html / html_content / slide_html; keep in sync with generate_with_ai."""
    for key in ("html", "html_content", "slide_html"):
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _slide_label_from_dict(item: dict, fallback: str) -> str:
    for key in ("label", "title"):
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return fallback


class PPTService:
    def __init__(self):
        self.presentations: dict[str, Presentation] = {}

    def create_presentation(self, title: str, template_id: str = "generated") -> Presentation:
        presentation = Presentation(
            id=str(uuid.uuid4()),
            title=title,
            template_id=template_id or "generated",
            slides=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.presentations[presentation.id] = presentation
        return presentation

    def get_presentation(self, presentation_id: str) -> Optional[Presentation]:
        return self.presentations.get(presentation_id)

    async def generate_with_ai(
        self,
        topic: str,
        outline: str | None = None,
        page_count: int = 8,
    ) -> Presentation:
        pc = max(4, min(int(page_count), 16))
        presentation = self.create_presentation(topic.strip()[:500], "generated")

        user_outline = (outline or "").strip()
        if user_outline:
            outline_part = (
                "\n【用户提纲】下列内容由用户提供，你必须严格遵循其章节、要点与语气来编排各页内容：\n"
                + user_outline
            )
        else:
            outline_part = "\n用户未提供提纲：请你自行拆解主题为完整叙事结构（封面→目录→层层展开的正文→致谢收尾）。"

        system_prompt = f"""你是资深演示文稿设计师兼前端工程师。根据主题与提纲，一次性生成恰好 {pc} 页「完整、独立」的 HTML 幻灯片。
输出必须是合法 JSON（不要 Markdown 代码围栏，不要解释文字）。

顶层格式：
{{"slides":[{{"label":"本页用途简述","html":"……"}}, …]}}

每一页的 html 字段必须是完整 HTML 文档（推荐包含 <!DOCTYPE html>、<html lang=\"zh-CN\">、<head>、<body>），并满足：
1. 画布固定为 1920×1080 CSS 像素：body 使用 width:1920px;height:1080px;margin:0;overflow:hidden;box-sizing:border-box;（可用 flex/grid 分区排版）。
2. 内容要充实：正文页需多段阐述、列表或小标题分区；至少 **两页正文** 必须包含 **数据可视化**，使用内联 SVG（柱状图 / 折线图 / 饼图 / 组合图均可），配有图标题、坐标轴或图例、简短解读文字。
3. 禁止外链脚本与 iframe；禁止使用依赖网络的图片 URL（可用渐变、几何图形、SVG、Unicode 图标）。
4. 配色专业协调，字体优先 \"Microsoft YaHei\",\"PingFang SC\",sans-serif；正文区域字号不宜过小（建议 ≥18px）。
5. 第一页为封面（主标题、副标题、演讲者/日期等企业信息）；第二页为目录；最后一页为致谢或展望；中间为递进正文。
6. JSON 字符串内的双引号必须转义（\\"），确保可被 json.loads 解析。

slides 数组长度必须恰好为 {pc}。

{LAYOUT_ENHANCEMENT}"""

        user_msg = f"主题：{topic.strip()}\n页数：{pc}" + outline_part

        result = await call_llm_json(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=16384,
        )

        payload = result.get("slides")
        slides_out: list[Slide] = []

        if isinstance(payload, list):
            for i, item in enumerate(payload[:pc]):
                if not isinstance(item, dict):
                    continue
                raw_html = _extract_slide_html_from_dict(item)
                label = _slide_label_from_dict(item, f"第 {len(slides_out) + 1} 页")
                if raw_html:
                    slides_out.append(
                        Slide(
                            id=str(uuid.uuid4()),
                            page_number=len(slides_out) + 1,
                            html_content=finalize_slide_html(raw_html),
                        )
                    )
                else:
                    slides_out.append(
                        Slide(
                            id=str(uuid.uuid4()),
                            page_number=len(slides_out) + 1,
                            html_content=minimal_slide(label),
                        )
                    )

        while len(slides_out) < pc:
            slides_out.append(
                Slide(
                    id=str(uuid.uuid4()),
                    page_number=len(slides_out) + 1,
                    html_content=minimal_slide(f"第 {len(slides_out) + 1} 页（待补充）"),
                )
            )

        presentation.slides = slides_out[:pc]
        for idx, s in enumerate(presentation.slides):
            s.page_number = idx + 1

        presentation.updated_at = datetime.now()
        return presentation

    async def propose_outline(self, topic: str, seed_outline: str | None = None) -> dict:
        """Optional AI-assisted Markdown outline."""
        system_prompt = """你是演示文稿策划助手。根据用户主题（以及用户可能提供的草稿提纲），输出精炼且可执行的提纲。
必须输出合法 JSON（不要 Markdown 代码围栏）。

格式：
{
  "steps": ["步骤1（简短）", "步骤2", "步骤3", "步骤4"],
  "outline": "Markdown 正文"
}

若用户已提供草稿提纲，请在保留其核心结构的前提下扩展润色；若无草稿，则从主题全新拟定。
outline 建议包含：封面信息要点、目录条目（与后续页数呼应）、各正文页要讲的核心论据及推荐的布局类型（如"数据图表"、"对比分栏"、"时间线"、"卡片网格"、"要点列表"）、结尾寄语。"""

        user_msg = f"主题：{topic.strip()}"
        if seed_outline and seed_outline.strip():
            user_msg += (
                "\n【用户已有草稿提纲】请在保留意图的前提下完善为正式 Markdown：\n"
                + seed_outline.strip()
            )

        result = await call_llm_json(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=4096,
        )

        steps = result.get("steps")
        outline = result.get("outline")
        if not isinstance(steps, list):
            steps = []
        steps = [str(s).strip() for s in steps if str(s).strip()]
        if not isinstance(outline, str):
            outline = ""

        return {"steps": steps[:8], "outline": outline.strip()}

    async def modify_slide(
        self,
        presentation_id: str,
        slide_id: str,
        instruction: str,
        chat_history: list[dict],
    ) -> Optional[Slide]:
        presentation = self.get_presentation(presentation_id)
        if not presentation:
            return None
        slide = next((s for s in presentation.slides if s.id == slide_id), None)
        if not slide:
            return None

        slide_index = presentation.slides.index(slide)
        total_slides = len(presentation.slides)

        system_prompt = f"""你是幻灯片 HTML 编辑专家。你正在编辑第 {slide_index + 1} 页（共 {total_slides} 页）。
按用户指令修改页面内容与样式；禁止引入外链脚本、iframe；不要在输出外附加说明文字。
完成后返回 **完整 HTML 文档**。

{MODIFY_LAYOUT_GUIDE}

当前 HTML：
{slide.html_content}"""

        messages = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": instruction}]

        new_html = await call_llm(messages, max_tokens=8192)

        new_html = new_html.strip()
        if new_html.startswith("```html"):
            new_html = new_html[7:]
        if new_html.startswith("```"):
            new_html = new_html[3:]
        if new_html.endswith("```"):
            new_html = new_html[:-3]
        new_html = new_html.strip()

        slide.html_content = finalize_slide_html(new_html)
        presentation.updated_at = datetime.now()
        return slide

    def delete_slide_by_id(self, presentation_id: str, slide_id: str) -> bool:
        presentation = self.get_presentation(presentation_id)
        if not presentation or len(presentation.slides) <= 1:
            return False
        idx = next(
            (i for i, s in enumerate(presentation.slides) if s.id == slide_id),
            None,
        )
        if idx is None:
            return False
        presentation.slides.pop(idx)
        for i, s in enumerate(presentation.slides):
            s.page_number = i + 1
        presentation.updated_at = datetime.now()
        return True

    def update_slide_html(self, presentation_id: str, slide_id: str, html_content: str) -> Optional[Slide]:
        """Persist manual edits from the web editor (no LLM)."""
        presentation = self.get_presentation(presentation_id)
        if not presentation:
            return None
        slide = next((s for s in presentation.slides if s.id == slide_id), None)
        if not slide:
            return None
        slide.html_content = finalize_slide_html(html_content)
        presentation.updated_at = datetime.now()
        return slide

    def insert_slide_html(self, presentation_id: str, html_content: str, after_index: Optional[int]) -> Optional[Slide]:
        """Append or insert a slide with fixed HTML (blank template, etc.)."""
        presentation = self.get_presentation(presentation_id)
        if not presentation:
            return None
        slide = Slide(
            id=str(uuid.uuid4()),
            page_number=0,
            html_content=finalize_slide_html(html_content),
            editable_regions={},
        )
        if after_index is None:
            presentation.slides.append(slide)
        else:
            pos = min(max(after_index + 1, 0), len(presentation.slides))
            presentation.slides.insert(pos, slide)
        for idx, s in enumerate(presentation.slides):
            s.page_number = idx + 1
        presentation.updated_at = datetime.now()
        return slide

    # ---- Streaming (slide-by-slide) generation ----

    async def generate_slides_streaming(
        self,
        topic: str,
        outline: str | None = None,
        page_count: int = 8,
    ) -> AsyncGenerator[dict, None]:
        """Generate slides one at a time, yielding each as it completes."""
        pc = max(4, min(int(page_count), 16))
        plan = await self._generate_slide_plan(topic, outline, pc)

        BATCH_SIZE = 2
        for batch_start in range(0, len(plan), BATCH_SIZE):
            batch = plan[batch_start : batch_start + BATCH_SIZE]
            tasks: dict[asyncio.Task, int] = {}
            for i, spec in enumerate(batch, start=batch_start):
                tasks[
                    asyncio.create_task(
                        self._generate_single_slide(topic, spec, i, pc, plan)
                    )
                ] = i

            buffer: dict[int, object] = {}
            next_idx = batch_start

            while tasks:
                done, _ = await asyncio.wait(tasks.keys(), return_when=asyncio.FIRST_COMPLETED)
                for t in done:
                    slide_index = tasks.pop(t)
                    exc = t.exception()
                    if exc is not None:
                        buffer[slide_index] = exc
                    else:
                        buffer[slide_index] = t.result()

                while next_idx in buffer:
                    result = buffer.pop(next_idx)
                    if isinstance(result, Exception):
                        yield {
                            "page_number": next_idx + 1,
                            "label": f"第 {next_idx + 1} 页",
                            "html_content": minimal_slide(
                                f"第 {next_idx + 1} 页 · 任务中断",
                                subtitle=SLIDE_PLACEHOLDER_HINT,
                            ),
                        }
                    else:
                        yield result
                    next_idx += 1

    async def _generate_slide_plan(
        self, topic: str, outline: str | None, pc: int
    ) -> list[dict]:
        user_outline = (outline or "").strip()
        outline_part = ""
        if user_outline:
            outline_part = "\n用户提纲：\n" + user_outline

        system_prompt = f"""为演示文稿「{topic}」规划恰好 {pc} 页幻灯片结构。
输出合法 JSON（不要围栏）：
{{"plan":[{{"page":1,"label":"封面","content_brief":"简要描述本页内容"}}, ...]}}

规则：第1页封面，第2页目录，最后一页致谢/展望，中间为递进正文。
每页 content_brief 应包含推荐的布局类型（如"数据图表"、"对比分栏"、"时间线"、"卡片网格"、"要点列表"）。"""

        try:
            result = await call_llm_json(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"主题：{topic}" + outline_part},
                ],
                max_tokens=2048,
            )
            plan = result.get("plan", [])
            if isinstance(plan, list) and len(plan) >= pc:
                return plan[:pc]
        except Exception:
            pass

        return [{"page": i + 1, "label": f"第 {i + 1} 页", "content_brief": ""} for i in range(pc)]

    async def _generate_single_slide(
        self,
        topic: str,
        spec: dict,
        index: int,
        total: int,
        plan: list[dict],
    ) -> dict:
        other_slides_summary = "\n".join(
            f"  第{s['page']}页: {s['label']}" for s in plan if s["page"] != index + 1
        )

        system_prompt = f"""你是资深演示文稿设计师兼前端工程师。生成「恰好 1 页」完整独立的 HTML 幻灯片。

当前是第 {index + 1} 页（共 {total} 页），用途：{spec['label']}。
内容要点：{spec.get('content_brief', '根据主题展开')}

完整幻灯片结构：
{other_slides_summary}

输出合法 JSON（不要 Markdown 围栏，不要解释）。
顶层必须是单页对象：{{"label":"本页用途","html":"完整HTML文档"}}；
也可用字段名 "html_content" 代替 "html"。不要把单页包进 slides 数组（若误包数组，仅取第一页）。

HTML 要求：
1. body 使用 width:1920px;height:1080px;margin:0;overflow:hidden;box-sizing:border-box;
2. 内容充实：正文页需多段阐述、列表或小标题分区
3. 禁止外链脚本与 iframe；禁止网络图片 URL（可用渐变、SVG、Unicode 图标）
4. 配色专业协调，字体 "Microsoft YaHei","PingFang SC",sans-serif；字号 >= 18px
5. JSON 内双引号必须转义

{LAYOUT_ENHANCEMENT}"""

        try:
            result = await call_llm_json(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"主题：{topic}\n请生成第 {index + 1} 页幻灯片。"},
                ],
                max_tokens=8192,
            )
            item: dict = result if isinstance(result, dict) else {}
            slides_wrapped = item.get("slides")
            if isinstance(slides_wrapped, list) and slides_wrapped:
                first = slides_wrapped[0]
                if isinstance(first, dict):
                    item = first
            raw_html = _extract_slide_html_from_dict(item) or ""
            label = _slide_label_from_dict(item, spec["label"])
            if raw_html:
                html_content = finalize_slide_html(raw_html)
            else:
                logger.warning(
                    "slide %s empty html after parse (label=%r)",
                    index + 1,
                    label,
                )
                html_content = minimal_slide(
                    "未生成有效页面内容",
                    subtitle=(
                        f"模型 JSON 中缺少 html / html_content / slide_html，或正文被截断。"
                        f"解析标题：{label}。"
                        f"{SLIDE_PLACEHOLDER_HINT}"
                    ),
                )
            return {
                "page_number": index + 1,
                "label": label,
                "html_content": html_content,
            }
        except Exception:
            logger.warning(
                "slide %s generation failed (label=%r)",
                index + 1,
                spec.get("label"),
                exc_info=True,
            )
            return {
                "page_number": index + 1,
                "label": spec["label"],
                "html_content": minimal_slide(
                    "本页自动生成失败",
                    subtitle=(
                        f"原计划版块：{spec['label']}。"
                        f"{SLIDE_PLACEHOLDER_HINT}"
                    ),
                ),
            }

    # ---- Streaming outline ----

    async def propose_outline_stream(
        self, topic: str, seed_outline: str | None = None
    ) -> AsyncGenerator[dict, None]:
        """Stream outline generation. Yields {"type": "step", "text": "..."} and finally {"type": "outline", "text": "..."}."""
        system_prompt = """你是演示文稿策划助手。根据用户主题（以及用户可能提供的草稿提纲），输出提纲。

输出格式（严格遵守）：

第一部分：策划步骤，每行一条，格式为 N. 内容（N 从 1 开始递增），共 4-8 条。
第二部分：在步骤结束后单独一行输出 ---OUTLINE---
第三部分：Markdown 格式的完整提纲正文。

示例：
1. 明确核心论点
2. 梳理数据支撑
3. 规划叙事逻辑
4. 确定视觉风格
---OUTLINE---
# 演示文稿提纲

## 一、背景与挑战
...

若用户已提供草稿提纲，请在保留其核心结构的前提下扩展润色；若无草稿，则从主题全新拟定。
提纲建议包含：封面信息要点、目录条目（与后续页数呼应）、各正文页要讲的核心论据及推荐的布局类型（如"数据图表"、"对比分栏"、"时间线"、"卡片网格"、"要点列表"）、结尾寄语。"""

        user_msg = f"主题：{topic.strip()}"
        if seed_outline and seed_outline.strip():
            user_msg += (
                "\n【用户已有草稿提纲】请在保留意图的前提下完善为正式 Markdown：\n"
                + seed_outline.strip()
            )

        buffer = ""
        in_outline = False
        outline_text = ""
        seen_steps = set()

        try:
            async for chunk in call_llm_stream(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=4096,
            ):
                buffer += chunk

                if not in_outline:
                    marker_pos = buffer.find("---OUTLINE---")
                    if marker_pos != -1:
                        step_section = buffer[:marker_pos]
                        for line in step_section.split("\n"):
                            line = line.strip()
                            if not line:
                                continue
                            m = re.match(r"^(\d+)\.\s*(.+)$", line)
                            if m:
                                step_text = m.group(2).strip()
                                step_key = f"{m.group(1)}:{step_text}"
                                if step_key not in seen_steps:
                                    seen_steps.add(step_key)
                                    yield {"type": "step", "text": step_text}

                        in_outline = True
                        outline_text = buffer[marker_pos + len("---OUTLINE---"):].lstrip("\n")
                        if outline_text.strip():
                            yield {"type": "outline_chunk", "text": outline_text}
                    else:
                        lines = buffer.split("\n")
                        buffer = lines[-1]
                        for line in lines[:-1]:
                            line = line.strip()
                            if not line:
                                continue
                            m = re.match(r"^(\d+)\.\s*(.+)$", line)
                            if m:
                                step_text = m.group(2).strip()
                                step_key = f"{m.group(1)}:{step_text}"
                                if step_key not in seen_steps:
                                    seen_steps.add(step_key)
                                    yield {"type": "step", "text": step_text}
                else:
                    outline_text += chunk
                    if outline_text.strip():
                        yield {"type": "outline_chunk", "text": outline_text}

            if not in_outline and buffer.strip():
                for line in buffer.split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    m = re.match(r"^(\d+)\.\s*(.+)$", line)
                    if m:
                        step_text = m.group(2).strip()
                        step_key = f"{m.group(1)}:{step_text}"
                        if step_key not in seen_steps:
                            seen_steps.add(step_key)
                            yield {"type": "step", "text": step_text}

            yield {"type": "done", "outline": outline_text.strip()}
        except Exception as e:
            logger.warning("propose_outline_stream failed", exc_info=True)
            yield {"type": "error", "message": format_llm_error(e)}
