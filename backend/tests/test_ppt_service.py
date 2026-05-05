import pytest
from unittest.mock import AsyncMock, patch
from app.services.ppt_service import PPTService


@pytest.fixture
def service():
    return PPTService()


def test_create_presentation(service):
    result = service.create_presentation("人工智能的未来", "business-blue")
    assert result.title == "人工智能的未来"
    assert result.template_id == "business-blue"
    assert len(result.slides) > 0
    assert result.slides[0].id


def test_get_presentation(service):
    created = service.create_presentation("测试主题", "business-blue")
    found = service.get_presentation(created.id)
    assert found is not None
    assert found.title == "测试主题"


def test_get_presentation_not_found(service):
    assert service.get_presentation("nonexistent") is None


@pytest.mark.asyncio
async def test_generate_slides_with_ai(service):
    with patch("app.services.ppt_service.call_llm_json", new_callable=AsyncMock) as mock_llm:
        import json
        mock_llm.return_value = json.loads('{"slides": [{"title": "AI简介", "body": "人工智能是..."}]}')
        result = await service.generate_with_ai("人工智能", "business-blue")
        assert result is not None
        assert result.title == "人工智能"
