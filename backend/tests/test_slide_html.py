from app.services.slide_html import finalize_slide_html


def test_finalize_wraps_fragment():
    html = finalize_slide_html('<div class="x">hello</div>')
    assert "<html" in html.lower()
    assert "_ppt_canvas_guard" in html
    assert "hello" in html


def test_finalize_strips_script():
    bad = "<!DOCTYPE html><html><body><script>x</script><p>ok</p></body></html>"
    html = finalize_slide_html(bad)
    assert "<script" not in html.lower()
    assert "ok" in html
