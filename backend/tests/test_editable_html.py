from app.services.editable_html import (
    apply_editable_fields,
    replace_editable_region,
    sanitize_body_html,
)


def test_replace_editable_simple():
    html = '<div class="t" data-editable="title">OLD</div>'
    out = replace_editable_region(html, "title", "NEW")
    assert "NEW" in out
    assert "OLD" not in out


def test_replace_editable_nested_inner_html():
    html = (
        '<div class="body-text" data-editable="body_text">'
        "<p>第一段</p><p>第二段</p>"
        "</div>"
    )
    replacement = "<p>替换A</p><p>替换B</p>"
    out = replace_editable_region(html, "body_text", replacement)
    assert "替换A" in out
    assert "第一段" not in out


def test_apply_editable_escapes_plain_text():
    html = '<span data-editable="title">X</span>'
    keys = frozenset({"body_text"})
    out = apply_editable_fields(html, {"title": "a<b>c"}, html_value_keys=keys)
    assert "a&lt;b&gt;c" in out


def test_sanitize_body_plain_becomes_paragraphs():
    out = sanitize_body_html("第一段\n\n第二段")
    assert "<p>" in out
    assert "第一段" in out
