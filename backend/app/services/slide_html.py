"""Normalize LLM-produced slide HTML so pages stay within a 1920×1080 canvas."""

from __future__ import annotations

import re
from html import escape

_CANVAS_GUARD = """<style id="_ppt_canvas_guard">
html,body{margin:0;padding:0;}
body{
  width:1920px!important;height:1080px!important;
  max-width:1920px!important;max-height:1080px!important;
  overflow:hidden!important;position:relative;
  box-sizing:border-box!important;
}
*,*::before,*::after{box-sizing:border-box;}
</style>"""


def sanitize_slide_document(html: str) -> str:
    t = (html or "").strip()
    if not t:
        return t
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", "", t)
    t = re.sub(r"(?is)<iframe[^>]*>.*?</iframe>", "", t)
    t = re.sub(r"(?is)<meta[^>]*http-equiv\s*=\s*[\"']?refresh[^>]*>", "", t)
    return t.strip()


def _inject_guard_into_document(html: str) -> str:
    if "_ppt_canvas_guard" in html:
        return html
    low = html.lower()
    if "</head>" in low:
        idx = low.index("</head>")
        return html[:idx] + _CANVAS_GUARD + html[idx:]
    if "<head>" in low:
        idx = low.index("<head>") + len("<head>")
        return html[:idx] + _CANVAS_GUARD + html[idx:]
    # malformed — wrap as fragment
    return wrap_body_fragment(html)


def wrap_body_fragment(fragment: str) -> str:
    frag = (fragment or "").strip()
    return (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\"><head>"
        '<meta charset="UTF-8"/><meta name="viewport" content="width=1920"/>'
        f"{_CANVAS_GUARD}</head><body>{frag}</body></html>"
    )


def finalize_slide_html(html: str) -> str:
    t = sanitize_slide_document(html)
    if not t:
        return minimal_slide("空白页")
    if "<html" not in t.lower():
        t = wrap_body_fragment(t)
    else:
        t = _inject_guard_into_document(t)
    return t


SLIDE_PLACEHOLDER_HINT = (
    "请在编辑器右侧对话中说明本页要讲的内容，以便重新生成该页 HTML。"
)


def minimal_slide(title: str, subtitle: str = "") -> str:
    title_esc = escape((title or "").strip() or "空白页")
    sub_t = (subtitle or "").strip()
    sub_html = ""
    if sub_t:
        sub_esc = escape(sub_t)
        sub_html = (
            f'<p style="margin:28px 0 0;font-size:22px;font-weight:400;color:#605e5c;'
            f'max-width:960px;line-height:1.6;text-align:center;">{sub_esc}</p>'
        )
    body = (
        f'<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;'
        f'width:100%;height:100%;background:#f5f5f5;padding:56px;box-sizing:border-box;">'
        f'<div style="font-size:38px;font-weight:700;color:#323130;text-align:center;line-height:1.3;">'
        f"{title_esc}</div>{sub_html}</div>"
    )
    return finalize_slide_html(body)
