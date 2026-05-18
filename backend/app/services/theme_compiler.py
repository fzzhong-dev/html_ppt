"""Compile shared theme JSON → CSS stylesheet and assemble complete slide HTML."""

from __future__ import annotations

import re
from app.services.slide_html import _CANVAS_GUARD

# ---------------------------------------------------------------------------
# Default theme (fallback when LLM theme generation fails)
# ---------------------------------------------------------------------------

DEFAULT_THEME: dict = {
    "palette": {
        "primary": "#1a365d",
        "secondary": "#4a5568",
        "accent": "#3182ce",
        "accent_light": "#ebf8ff",
        "bg": "#ffffff",
        "surface": "#f7fafc",
        "border": "#e2e8f0",
    },
    "typography": {
        "heading_font": '"Microsoft YaHei","PingFang SC",sans-serif',
        "body_font": '"Microsoft YaHei","PingFang SC",sans-serif',
        "heading_weight": "700",
        "body_weight": "400",
    },
    "spacing": {
        "page_padding": "64px",
        "section_gap": "36px",
        "element_gap": "18px",
    },
}

# ---------------------------------------------------------------------------
# CSS template with placeholders
# ---------------------------------------------------------------------------

_CSS_TEMPLATE = """\
:root {{
  --ppt-primary: {primary};
  --ppt-secondary: {secondary};
  --ppt-accent: {accent};
  --ppt-accent-light: {accent_light};
  --ppt-bg: {bg};
  --ppt-surface: {surface};
  --ppt-border: {border};
  --ppt-heading-font: {heading_font};
  --ppt-body-font: {body_font};
  --ppt-heading-weight: {heading_weight};
  --ppt-body-weight: {body_weight};
  --ppt-page-padding: {page_padding};
  --ppt-section-gap: {section_gap};
  --ppt-element-gap: {element_gap};
}}
.ppt-page {{ width:100%; height:100%; box-sizing:border-box; padding:var(--ppt-page-padding); background:var(--ppt-bg); display:flex; flex-direction:column; position:relative; overflow:hidden; }}
.ppt-center {{ display:flex; align-items:center; justify-content:center; }}
.ppt-heading {{ font-family:var(--ppt-heading-font); font-weight:var(--ppt-heading-weight); color:var(--ppt-primary); margin:0; }}
.ppt-h1 {{ font-family:var(--ppt-heading-font); font-weight:var(--ppt-heading-weight); color:var(--ppt-primary); font-size:72px; line-height:1.1; margin:0; }}
.ppt-h2 {{ font-family:var(--ppt-heading-font); font-weight:var(--ppt-heading-weight); color:var(--ppt-primary); font-size:42px; line-height:1.2; margin:0; }}
.ppt-h3 {{ font-family:var(--ppt-heading-font); font-weight:var(--ppt-heading-weight); color:var(--ppt-primary); font-size:32px; line-height:1.3; margin:0; }}
.ppt-body {{ font-family:var(--ppt-body-font); font-weight:var(--ppt-body-weight); color:var(--ppt-secondary); font-size:24px; line-height:1.65; }}
.ppt-accent-text {{ color:var(--ppt-accent); }}
.ppt-surface {{ background:var(--ppt-surface); border-radius:12px; padding:24px; }}
.ppt-card {{ background:var(--ppt-surface); border-radius:12px; border:1px solid var(--ppt-border); padding:24px; }}
.ppt-accent-bar {{ width:120px; height:6px; background:var(--ppt-accent); border-radius:3px; }}
.ppt-divider {{ height:3px; background:linear-gradient(90deg,var(--ppt-accent),transparent); border-radius:2px; margin:var(--ppt-element-gap) 0; }}
.ppt-grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:var(--ppt-section-gap); }}
.ppt-grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:var(--ppt-section-gap); }}
.ppt-flex-row {{ display:flex; gap:var(--ppt-section-gap); }}
.ppt-flex-col {{ display:flex; flex-direction:column; gap:var(--ppt-element-gap); }}
.ppt-tag {{ display:inline-block; padding:6px 16px; border-radius:4px; font-size:18px; font-weight:600; background:var(--ppt-accent-light); color:var(--ppt-accent); }}
.ppt-badge {{ display:inline-block; padding:4px 12px; border-radius:999px; font-size:16px; background:var(--ppt-accent); color:#fff; }}
.ppt-cover-bg {{ position:absolute; inset:0; background:linear-gradient(135deg,var(--ppt-primary),var(--ppt-accent)); display:flex; flex-direction:column; align-items:center; justify-content:center; padding:var(--ppt-page-padding); }}
.ppt-cover-bg .ppt-h1 {{ color:#fff; text-align:center; }}
.ppt-cover-bg .ppt-h2 {{ color:rgba(255,255,255,0.85); text-align:center; }}
.ppt-cover-bg .ppt-body {{ color:rgba(255,255,255,0.75); text-align:center; }}
"""

# Summary of available classes for LLM prompt
THEME_CSS_CLASS_CATALOG = """\
可用 CSS 类（通过 class 属性使用）：
- 布局: .ppt-page .ppt-center .ppt-grid-2 .ppt-grid-3 .ppt-flex-row .ppt-flex-col
- 标题: .ppt-h1(72px) .ppt-h2(42px) .ppt-h3(32px) .ppt-heading(基础)
- 正文: .ppt-body .ppt-accent-text
- 卡片: .ppt-card(带边框) .ppt-surface(无边框)
- 装饰: .ppt-accent-bar .ppt-divider .ppt-tag .ppt-badge
- 封面: .ppt-cover-bg(全屏渐变背景，内部标题自动变白)
- CSS 变量: var(--ppt-primary) var(--ppt-secondary) var(--ppt-accent) var(--ppt-accent-light) var(--ppt-bg) var(--ppt-surface) var(--ppt-border)
"""


# ---------------------------------------------------------------------------
# compile_theme_to_css
# ---------------------------------------------------------------------------

def compile_theme_to_css(theme: dict) -> str:
    """Convert a theme JSON dict into a complete CSS stylesheet string."""
    palette = theme.get("palette", {})
    typo = theme.get("typography", {})
    spacing = theme.get("spacing", {})

    return _CSS_TEMPLATE.format(
        primary=palette.get("primary", "#1a365d"),
        secondary=palette.get("secondary", "#4a5568"),
        accent=palette.get("accent", "#3182ce"),
        accent_light=palette.get("accent_light", "#ebf8ff"),
        bg=palette.get("bg", "#ffffff"),
        surface=palette.get("surface", "#f7fafc"),
        border=palette.get("border", "#e2e8f0"),
        heading_font=typo.get("heading_font", '"Microsoft YaHei","PingFang SC",sans-serif'),
        body_font=typo.get("body_font", '"Microsoft YaHei","PingFang SC",sans-serif'),
        heading_weight=typo.get("heading_weight", "700"),
        body_weight=typo.get("body_weight", "400"),
        page_padding=spacing.get("page_padding", "64px"),
        section_gap=spacing.get("section_gap", "36px"),
        element_gap=spacing.get("element_gap", "18px"),
    )


# ---------------------------------------------------------------------------
# assemble_slide_html
# ---------------------------------------------------------------------------

def assemble_slide_html(body_fragment: str, theme_css: str) -> str:
    """Merge theme CSS + body fragment into a complete HTML document.

    The output is identical in structure to what finalize_slide_html() produces,
    so the frontend (iframe srcdoc) needs no changes.
    """
    clean = body_fragment.strip() if body_fragment else ""
    # Strip accidental <style> blocks the LLM might insert despite instructions
    clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
    # Also strip full-document wrappers if LLM wraps in html/head/body
    clean = re.sub(r"(?is)^.*<body[^>]*>", "", clean)
    clean = re.sub(r"(?is)</body>.*$", "", clean)
    clean = clean.strip()

    return (
        '<!DOCTYPE html>\n<html lang="zh-CN"><head>'
        '<meta charset="UTF-8"/><meta name="viewport" content="width=1920"/>'
        f'<style id="_ppt_theme">\n{theme_css}\n</style>\n'
        f"{_CANVAS_GUARD}</head><body>{clean}</body></html>"
    )
