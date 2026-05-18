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
  word-break:break-word;
  overflow-wrap:anywhere;
  font-family:"Microsoft YaHei","PingFang SC","Segoe UI",sans-serif;
}
*,*::before,*::after{box-sizing:border-box;}
</style>"""


def sanitize_slide_document(html: str) -> str:
    t = (html or "").strip()
    if not t:
        return t
    while re.search(r"(?is)<script\b[^>]*>.*?</script>", t):
        t = re.sub(r"(?is)<script\b[^>]*>.*?</script>", "", t)
    t = re.sub(r"(?is)<script\b[^>]*(?<!/)>", "", t)
    t = re.sub(r"(?is)<iframe[^>]*>.*?</iframe>", "", t)
    t = re.sub(r"(?is)<meta[^>]*http-equiv\s*=\s*[\"']?refresh[^>]*>", "", t)
    t = re.sub(
        r'(?i)\bon[a-z]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)',
        "",
        t,
    )
    t = re.sub(r'(?is)\b(href|src)\s*=\s*"\s*javascript:[^"]*"', r'\1=""', t)
    t = re.sub(r"(?is)\b(href|src)\s*=\s*'\s*javascript:[^']*'", r"\1=''", t)
    # Allow local proxy image URLs, strip external image URLs
    t = _strip_external_images(t)
    return t.strip()


# Allowed image src patterns (local proxy + data URIs + inline SVG)
_ALLOWED_IMG_PREFIXES = (
    "/api/images/proxy",
    "data:",
    "blob:",
)


def _strip_external_images(html: str) -> str:
    """Remove external image URLs but keep local proxy, data URIs, and inline SVG."""

    def _check_src(match):
        value = match.group(1)
        if not value:
            return match.group(0)

        for prefix in _ALLOWED_IMG_PREFIXES:
            if value.startswith(prefix):
                return match.group(0)

        if not value.startswith(("http://", "https://", "//")):
            return match.group(0)

        return f'src="{match.group(0)[match.group(0).index(value) - 1]}"'.replace(
            f'src="{match.group(0)[match.group(0).index(value) - 1]}"',
            'src=""',
        )

    # Double-quoted src="..."
    def _check_dq(m):
        val = m.group(1)
        for p in _ALLOWED_IMG_PREFIXES:
            if val.startswith(p):
                return m.group(0)
        if not val.startswith(("http://", "https://", "//")):
            return m.group(0)
        return 'src=""'

    # Single-quoted src='...'
    def _check_sq(m):
        val = m.group(1)
        for p in _ALLOWED_IMG_PREFIXES:
            if val.startswith(p):
                return m.group(0)
        if not val.startswith(("http://", "https://", "//")):
            return m.group(0)
        return "src=''"

    html = re.sub(r'src\s*=\s*"([^"]*)"', _check_dq, html, flags=re.IGNORECASE)
    html = re.sub(r"src\s*=\s*'([^']*)'", _check_sq, html, flags=re.IGNORECASE)
    return html


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
