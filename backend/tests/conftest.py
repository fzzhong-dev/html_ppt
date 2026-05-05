import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    mock_response = json.dumps({"slides": [
        {"subtitle_top": "TEST", "title": "测试标题", "subtitle": "测试副标题", "author": "测试", "date": "2026"},
        {"section_title": "目录", "toc_1": "章节1", "toc_2": "章节2", "toc_3": "章节3", "toc_4": "章节4"},
        {"header_title": "章节1", "title": "测试", "body": "<p>测试内容</p>"},
        {"header_title": "章节2", "title": "测试", "body": "<p>测试内容</p>"},
        {"thanks": "谢谢", "message": "感谢", "contact": "test@test.com"},
    ]})

    mock_return = json.loads(mock_response)
    with patch("app.services.ppt_service.call_llm_json", new_callable=AsyncMock, return_value=mock_return):
        with patch("app.services.ppt_service.call_llm", new_callable=AsyncMock, return_value="<html>modified</html>"):
            yield TestClient(app)
