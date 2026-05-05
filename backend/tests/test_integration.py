"""Integration test: generate → modify → verify slides exist."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.ppt_service import PPTService


def _slide_html(text: str) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"/></head>"
        f"<body><p>{text}</p></body></html>"
    )


@pytest.fixture
def mock_llm():
    gen_slides = [
        {"label": "封面", "html": _slide_html("人工智能")},
        {"label": "目录", "html": _slide_html("目录")},
        {"label": "a", "html": _slide_html("正文1")},
        {"label": "b", "html": _slide_html("正文2")},
        {"label": "c", "html": _slide_html("正文3")},
        {"label": "d", "html": _slide_html("正文4")},
        {"label": "e", "html": _slide_html("正文5")},
        {"label": "尾", "html": _slide_html("谢谢")},
    ]
    modify_response = "<!DOCTYPE html><html><body><p>修改后的标题</p></body></html>"

    with patch("app.services.ppt_service.call_llm_json", new_callable=AsyncMock, return_value={"slides": gen_slides}):
        with patch("app.services.ppt_service.call_llm", new_callable=AsyncMock, return_value=modify_response):
            yield


@pytest.mark.asyncio
async def test_full_workflow(mock_llm):
    service = PPTService()

    pres = await service.generate_with_ai("人工智能", None, 8)
    assert pres.title == "人工智能"
    assert len(pres.slides) == 8
    cover = pres.slides[0]
    assert "人工智能" in cover.html_content

    modified = await service.modify_slide(
        pres.id,
        pres.slides[0].id,
        "把标题改成'AI革命'",
        [],
    )
    assert modified is not None
    assert modified.id == pres.slides[0].id
    assert "修改后的标题" in modified.html_content

    found = service.get_presentation(pres.id)
    assert found is not None
    assert found.slides[0].html_content == modified.html_content
