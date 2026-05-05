"""Replace inner HTML for elements marked with data-editable=\"...\" (handles nested tags)."""

from __future__ import annotations

import re
from html import escape


_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


def replace_editable_region(html: str, key: str, replacement: str) -> str:
    esc_key = re.escape(key)
    open_re = re.compile(
        rf'<([a-zA-Z][\w:-]*)((?:\s[^>]*)?\sdata-editable="{esc_key}"(?:\s[^>]*)?)>',
        re.IGNORECASE,
    )
    m = open_re.search(html)
    if not m:
        return html

    tag = m.group(1).lower()
    inner_start = m.end()
    pos = inner_start
    depth = 1
    n = len(html)

    while pos < n and depth > 0:
        lt = html.find("<", pos)
        if lt == -1:
            return html

        if html.startswith("<!--", lt):
            ce = html.find("-->", lt + 4)
            if ce == -1:
                return html
            pos = ce + 3
            continue

        if html.startswith("</", lt):
            gt = html.find(">", lt)
            if gt == -1:
                return html
            inner = html[lt + 2 : gt].strip()
            close_name = inner.split()[0].lower().rstrip("/") if inner else ""
            if close_name == tag:
                depth -= 1
                if depth == 0:
                    return html[:inner_start] + replacement + html[gt + 1 :]
            pos = gt + 1
            continue

        gt = html.find(">", lt)
        if gt == -1:
            return html

        frag = html[lt + 1 : gt].strip()
        if frag.startswith("!") or frag.startswith("?"):
            pos = gt + 1
            continue

        name = frag.split()[0].lower().rstrip("/")
        is_void = name in _VOID_TAGS or frag.rstrip().endswith("/")
        if not is_void and name == tag:
            depth += 1
        pos = gt + 1

    return html


def normalize_plain_text(val: str) -> str:
    """Strip invisible chars / normalize NBSP so titles don't visually shift."""
    t = val.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    return t.strip()


def sanitize_body_html(fragment: str) -> str:
    """Strip harmful wrappers so injected HTML matches slide layout (fixes offset/weird blocks)."""
    t = fragment.strip()
    if not t:
        return "<p></p>"

    if t.startswith("```"):
        lines = t.split("\n")
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        while lines and lines[-1].strip().startswith("```"):
            lines.pop()
        t = "\n".join(lines).strip()

    t = re.sub(r"(?is)<script[^>]*>.*?</script>", "", t)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", "", t)

    if re.search(r"(?is)<body[^>]*>", t):
        m = re.search(r"(?is)<body[^>]*>(.*)</body>", t, re.DOTALL)
        if m:
            t = m.group(1).strip()
    if re.search(r"(?is)<html[^>]*>", t):
        m = re.search(r"(?is)<html[^>]*>(.*)</html>", t, re.DOTALL)
        if m:
            t = m.group(1).strip()

    t = t.strip()
    if "<" not in t:
        chunks = [p.strip() for p in re.split(r"\n\s*\n+", t) if p.strip()]
        if not chunks:
            return "<p></p>"
        return "".join(f"<p>{escape(p)}</p>" for p in chunks)

    return t


def apply_editable_fields(html: str, fields: dict, *, html_value_keys: frozenset[str]) -> str:
    out = html
    for raw_key, raw_val in fields.items():
        if raw_val is None:
            continue
        key = str(raw_key)
        marker = f'data-editable="{key}"'
        if marker not in out:
            continue
        val = raw_val if isinstance(raw_val, str) else str(raw_val)
        if key in html_value_keys:
            replacement = sanitize_body_html(val)
        else:
            replacement = escape(normalize_plain_text(val))
        out = replace_editable_region(out, key, replacement)
    return out
