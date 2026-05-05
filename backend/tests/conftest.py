import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


def _fake_full_html(body_text: str) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"/></head>"
        f"<body><p>{body_text}</p></body></html>"
    )


async def _call_llm_json_side_effect(messages: list[dict], provider_id=None, **kwargs):
    sys_content = messages[0]["content"]
    if "演示文稿策划助手" in sys_content:
        return {
            "steps": ["理解主题要点", "规划叙事结构", "对齐页码节奏", "输出 Markdown"],
            "outline": "## 提纲\n- 封面\n",
        }
    if "资深演示文稿设计师" in sys_content:
        pc = 8
        import re

        m = re.search(r"恰好 (\d+) 页", sys_content)
        if m:
            pc = max(4, min(int(m.group(1)), 16))
        slides = []
        for i in range(pc):
            slides.append(
                {
                    "label": f"第{i + 1}页",
                    "html": _fake_full_html(f"SLIDE{i + 1}"),
                }
            )
        return {"slides": slides}
    return {"slides": []}


@pytest.fixture
def client():
    with patch("app.services.ppt_service.call_llm_json", new_callable=AsyncMock, side_effect=_call_llm_json_side_effect):
        with patch("app.services.ppt_service.call_llm", new_callable=AsyncMock, return_value="<html><body>x</body></html>"):
            yield TestClient(app)
