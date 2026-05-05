import pytest

from app.services.llm_service import parse_llm_json_text


def test_parse_plain_json():
    assert parse_llm_json_text('  {"a": 1}  ') == {"a": 1}


def test_parse_fence_json():
    body = '```json\n{"label":"x","html":"<p>hi</p>"}\n```'
    r = parse_llm_json_text(body)
    assert r["label"] == "x"


def test_parse_leading_prose():
    body = '以下为输出：\n{"plan":[{"page":1}]}\n'
    assert parse_llm_json_text(body)["plan"][0]["page"] == 1


def test_parse_empty_raises():
    with pytest.raises(ValueError, match="为空"):
        parse_llm_json_text("")
    with pytest.raises(ValueError, match="为空"):
        parse_llm_json_text("   ")
