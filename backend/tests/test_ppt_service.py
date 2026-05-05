import pytest
from unittest.mock import AsyncMock, patch
from app.services.ppt_service import PPTService


@pytest.fixture
def service():
    return PPTService()


def test_create_presentation(service):
    result = service.create_presentation("人工智能的未来", "generated")
    assert result.title == "人工智能的未来"
    assert result.template_id == "generated"
    assert len(result.slides) == 0
    assert result.id


def test_get_presentation(service):
    created = service.create_presentation("测试主题", "generated")
    found = service.get_presentation(created.id)
    assert found is not None
    assert found.title == "测试主题"


def test_get_presentation_not_found(service):
    assert service.get_presentation("nonexistent") is None


@pytest.mark.asyncio
async def test_generate_slides_with_ai(service):
    fake_slides = [
        {"label": "封面", "html": "<!DOCTYPE html><html><head></head><body><p>封面页内容</p></body></html>"},
        {"label": "目录", "html": "<!DOCTYPE html><html><head></head><body><p>目录页</p></body></html>"},
        {"label": "一", "html": "<!DOCTYPE html><html><head></head><body><p>第一段</p></body></html>"},
        {"label": "二", "html": "<!DOCTYPE html><html><head></head><body><p>第二段</p></body></html>"},
        {"label": "三", "html": "<!DOCTYPE html><html><head></head><body><p>第三段</p></body></html>"},
        {"label": "四", "html": "<!DOCTYPE html><html><head></head><body><p>第四段</p></body></html>"},
        {"label": "五", "html": "<!DOCTYPE html><html><head></head><body><p>第五段</p></body></html>"},
        {"label": "尾", "html": "<!DOCTYPE html><html><head></head><body><p>致谢</p></body></html>"},
    ]
    with patch("app.services.ppt_service.call_llm_json", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {"slides": fake_slides}
        result = await service.generate_with_ai("人工智能", "提纲要点", 8)
        assert result is not None
        assert result.title == "人工智能"
        assert len(result.slides) == 8
        assert "封面页内容" in result.slides[0].html_content
