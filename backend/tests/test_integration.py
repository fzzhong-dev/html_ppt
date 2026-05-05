"""Integration test: generate → modify → verify slides exist."""
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.services.ppt_service import PPTService


@pytest.fixture
def mock_llm():
    gen_response = json.dumps({"slides": [
        {"subtitle_top": "AI", "title": "人工智能", "subtitle": "未来已来", "author": "张三", "date": "2026"},
        {"section_title": "目录", "toc_1": "简介", "toc_2": "技术", "toc_3": "应用", "toc_4": "展望"},
        {"header_title": "简介", "title": "什么是AI", "body": "<p>AI是人工智能</p>"},
        {"header_title": "展望", "title": "AI未来", "body": "<p>AI将改变世界</p>"},
        {"thanks": "谢谢", "message": "感谢", "contact": "test"},
    ]})
    modify_response = '<!DOCTYPE html><html><body><h1 data-editable="title">修改后的标题</h1></body></html>'

    with patch("app.services.ppt_service.call_llm_json", new_callable=AsyncMock, return_value=json.loads(gen_response)):
        with patch("app.services.ppt_service.call_llm", new_callable=AsyncMock, return_value=modify_response):
            yield


@pytest.mark.asyncio
async def test_full_workflow(mock_llm):
    service = PPTService()

    # Step 1: Generate
    pres = await service.generate_with_ai("人工智能", "business-blue")
    assert pres.title == "人工智能"
    assert len(pres.slides) == 5
    cover = pres.slides[0]
    assert "人工智能" in cover.html_content

    # Step 2: Modify a slide
    modified = await service.modify_slide(
        pres.id, pres.slides[0].id,
        "把标题改成'AI革命'",
        [],
    )
    assert modified is not None
    assert modified.id == pres.slides[0].id
    assert "修改后的标题" in modified.html_content

    # Step 3: Verify persistence
    found = service.get_presentation(pres.id)
    assert found is not None
    assert found.slides[0].html_content == modified.html_content
