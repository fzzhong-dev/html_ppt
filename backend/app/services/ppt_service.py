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
from app.services.layout_prompts import (
    slide_layout_instructions,
    MODIFY_LAYOUT_GUIDE,
    THEME_GENERATION_PROMPT,
    SLIDE_FRAGMENT_PROMPT,
)
from app.services.theme_compiler import (
    compile_theme_to_css,
    assemble_slide_html,
    DEFAULT_THEME,
    THEME_CSS_CLASS_CATALOG,
)

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
        *,
        creative_mode: bool = True,
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
            outline_part = (
                "\n用户未提供提纲：请你按主题自行拆解叙事结构：封面 → 目录 → 层层展开的正文 → **收尾页**；"
                "收尾语气与形式须匹配主题、受众与场景，勿套用固定演说结束语。"
            )

        system_prompt = f"""你是资深演示文稿设计师兼前端工程师。根据主题与提纲，一次性生成恰好 {pc} 页「完整、独立」的 HTML 幻灯片。
输出必须是合法 JSON（不要 Markdown 代码围栏，不要解释文字）。

顶层格式：
{{"slides":[{{"label":"本页用途简述","html":"……"}}, …]}}

每一页的 html 字段必须是完整 HTML 文档（推荐包含 <!DOCTYPE html>、<html lang=\"zh-CN\">、<head>、<body>），并满足：
1. 画布固定为 1920×1080 CSS 像素：body 使用 width:1920px;height:1080px;margin:0;overflow:hidden;box-sizing:border-box;（可用 flex/grid 分区排版）。
2. 内容要充实：正文页需多段阐述、列表或小标题分区。**数据可视化**：仅当某页确有数值、比例、趋势或结构化对比时再使用内联 SVG（柱状图、折线图、饼图等）；若无合适数据，用大段精炼文字、引用、时间线文字、对照表等完成叙事，禁止为凑页硬画图表。
3. 禁止外链脚本与 iframe；禁止使用依赖网络的图片 URL（可用 CSS 渐变、几何块面、内联 SVG）。
4. 配色与字体气质须服务于主题，可读优先；正文不宜过小（建议 ≥18px）。
5. 第一页为封面（主标题与主题一致，可含副标题、日期、署名等）；第二页为目录；最后一页为 **收尾页**，形式由主题决定（例如：要点回顾、行动呼吁、下一步计划、讨论议题、开放问答、数据结论重申、资源延伸阅读等）；勿千篇一律使用「感谢聆听」「谢谢观看」等套路话术，除非主题本身是面向听众的报告场景且用语贴切。中间为递进正文。
6. 各页之间版式与视觉应有差异，避免每张都是「图标列表 + 圆角卡片」的同一模板复制。
7. JSON 字符串内的双引号必须转义（\\"），确保可被 json.loads 解析。

slides 数组长度必须恰好为 {pc}。

{slide_layout_instructions(creative=creative_mode)}"""

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
outline 建议包含：封面信息要点、目录条目（与后续页数呼应）、各正文页的核心论据及 **视觉倾向（文字主导 / 数据图表页 / 图文混合 / 极简留白 / 强对比单页 等，按页任选其一；勿默认每页都要求图表）**、**最后一页的收尾意图**（须依主题拟定：总结、倡议、展望、讨论、问答引导等均可；不要默认写成演说致谢套话）。"""

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

    async def _generate_theme(self, topic: str, creative_mode: bool) -> dict:
        """Phase 1: generate a shared theme JSON (~200 tokens)."""
        try:
            result = await call_llm_json(
                [
                    {"role": "system", "content": THEME_GENERATION_PROMPT},
                    {"role": "user", "content": f"主题：{topic.strip()}"},
                ],
                max_tokens=512,
            )
            # Validate minimal structure
            if isinstance(result, dict) and "palette" in result:
                return result
        except Exception:
            logger.warning("theme generation failed, using default", exc_info=True)
        return DEFAULT_THEME

    async def generate_slides_streaming(
        self,
        topic: str,
        outline: str | None = None,
        page_count: int = 8,
        *,
        creative_mode: bool = True,
    ) -> AsyncGenerator[dict, None]:
        """Generate slides one at a time, yielding each immediately.

        Pipeline: theme+plan (parallel) → body fragments (serial, yield each).
        """
        pc = max(4, min(int(page_count), 16))

        # Phase 1+2: generate theme and plan in parallel
        theme_task = asyncio.create_task(self._generate_theme(topic, creative_mode))
        plan_task = asyncio.create_task(self._generate_slide_plan(topic, outline, pc))
        theme, plan = await asyncio.gather(theme_task, plan_task)
        theme_css = compile_theme_to_css(theme)

        # Phase 3: generate slides one by one, yield immediately
        for i, spec in enumerate(plan):
            try:
                result = await self._generate_single_slide_fragment(
                    topic, spec, i, pc, plan,
                    theme_css=theme_css,
                    creative_mode=creative_mode,
                )
                yield result
            except Exception:
                logger.warning("slide %s generation failed", i + 1, exc_info=True)
                yield {
                    "page_number": i + 1,
                    "label": spec.get("label", f"第 {i + 1} 页"),
                    "html_content": minimal_slide(
                        f"第 {i + 1} 页 · 生成失败",
                        subtitle=SLIDE_PLACEHOLDER_HINT,
                    ),
                }

    async def _generate_single_slide_fragment(
        self,
        topic: str,
        spec: dict,
        index: int,
        total: int,
        plan: list[dict],
        *,
        theme_css: str,
        creative_mode: bool = True,
    ) -> dict:
        """Phase 3: generate a body fragment using shared theme CSS classes."""
        other_slides_summary = "\n".join(
            f"  第{s['page']}页: {s['label']}" for s in plan if s["page"] != index + 1
        )

        system_prompt = SLIDE_FRAGMENT_PROMPT.format(
            index=index + 1,
            total=total,
            label=spec["label"],
            content_brief=spec.get("content_brief", "根据主题展开"),
            plan_summary=other_slides_summary,
            css_catalog=THEME_CSS_CLASS_CATALOG,
        )

        user_slide_msg = f"主题：{topic}\n请生成第 {index + 1} 页幻灯片。"
        max_slide_tokens = 4096
        last_exc: Exception | None = None
        parsed_label = spec["label"]

        for attempt in range(2):
            try:
                result = await call_llm_json(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_slide_msg},
                    ],
                    max_tokens=max_slide_tokens,
                )
                last_exc = None
                item: dict = result if isinstance(result, dict) else {}
                # Handle accidental wrapping in slides array
                slides_wrapped = item.get("slides")
                if isinstance(slides_wrapped, list) and slides_wrapped:
                    first = slides_wrapped[0]
                    if isinstance(first, dict):
                        item = first

                # Extract body fragment (prefer "body", fallback to html keys)
                body = item.get("body") or _extract_slide_html_from_dict(item) or ""
                parsed_label = _slide_label_from_dict(item, spec["label"])

                if body:
                    assembled = assemble_slide_html(body, theme_css)
                    return {
                        "page_number": index + 1,
                        "label": parsed_label,
                        "html_content": assembled,
                    }
                logger.warning(
                    "slide %s empty body after parse (attempt %s, label=%r)",
                    index + 1, attempt + 1, parsed_label,
                )
            except Exception as e:
                last_exc = e
                logger.warning(
                    "slide %s LLM error (attempt %s, label=%r)",
                    index + 1, attempt + 1, spec.get("label"), exc_info=True,
                )
            if attempt == 0:
                await asyncio.sleep(0.5)

        if last_exc is not None:
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

        return {
            "page_number": index + 1,
            "label": parsed_label,
            "html_content": minimal_slide(
                "未生成有效页面内容",
                subtitle=(
                    "模型 JSON 中缺少 body / html 字段，或正文被截断。"
                    f"解析标题：{parsed_label}。"
                    f"{SLIDE_PLACEHOLDER_HINT}"
                ),
            ),
        }

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

规则：第1页封面，第2页目录，最后一页为 **与主题匹配的收尾页**（总结、行动呼吁、Q&A、展望、讨论引导等皆可；勿硬性等同于「致谢」），中间为递进正文。
每页 content_brief 须简短；其中建议标注 **视觉倾向**：文字主导 / 数据图表（仅确有数据时） / 图文混合 / 极简留白 / 强对比单页 等之一，**不要**默认所有正文页都写「数据图表」。"""

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
        *,
        creative_mode: bool = True,
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
2. 内容充实：多段阐述、列表或小标题分区均可；本页视觉应与主题及相邻页有差异，避免复制「图标列表 + 圆角卡片」同一模板。
3. 禁止外链脚本与 iframe；禁止网络图片 URL（可用渐变、几何块面、内联 SVG）。
4. 配色与排版服务于主题；正文可读优先（字号不宜过小）；不要用装饰性 Emoji 铺满页面。
5. JSON 内双引号必须转义。

{slide_layout_instructions(creative=creative_mode)}"""

        user_slide_msg = f"主题：{topic}\n请生成第 {index + 1} 页幻灯片。"
        max_slide_tokens = 12288
        last_exc: Exception | None = None
        parsed_label = spec["label"]

        for attempt in range(2):
            try:
                result = await call_llm_json(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_slide_msg},
                    ],
                    max_tokens=max_slide_tokens,
                )
                last_exc = None
                item: dict = result if isinstance(result, dict) else {}
                slides_wrapped = item.get("slides")
                if isinstance(slides_wrapped, list) and slides_wrapped:
                    first = slides_wrapped[0]
                    if isinstance(first, dict):
                        item = first
                raw_html = _extract_slide_html_from_dict(item) or ""
                parsed_label = _slide_label_from_dict(item, spec["label"])
                if raw_html:
                    return {
                        "page_number": index + 1,
                        "label": parsed_label,
                        "html_content": finalize_slide_html(raw_html),
                    }
                logger.warning(
                    "slide %s empty html after parse (attempt %s, label=%r)",
                    index + 1,
                    attempt + 1,
                    parsed_label,
                )
            except Exception as e:
                last_exc = e
                logger.warning(
                    "slide %s LLM error (attempt %s, label=%r)",
                    index + 1,
                    attempt + 1,
                    spec.get("label"),
                    exc_info=True,
                )
            if attempt == 0:
                await asyncio.sleep(0.5)

        if last_exc is not None:
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

        return {
            "page_number": index + 1,
            "label": parsed_label,
            "html_content": minimal_slide(
                "未生成有效页面内容",
                subtitle=(
                    "模型 JSON 中缺少 html / html_content / slide_html，或正文被截断。"
                    f"解析标题：{parsed_label}。"
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
提纲建议包含：封面信息要点、目录条目（与后续页数呼应）、各正文页的核心论据及 **视觉倾向（文字主导 / 数据图表 / 混合 / 极简等；勿默认每页都画图）**、**最后一页的收尾意图**（依主题而定，避免默认致谢套话）。"""

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
