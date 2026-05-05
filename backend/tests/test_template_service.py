import pytest
from app.services.template_service import TemplateService


@pytest.fixture
def service():
    return TemplateService()


def test_list_templates_returns_at_least_one(service):
    templates = service.list_templates()
    assert len(templates) >= 1
    assert templates[0]["id"] == "business-blue"
    assert templates[0]["name"]


def test_get_template_returns_slide_types(service):
    template = service.get_template("business-blue")
    assert template is not None
    assert "cover" in template["slides"]
    assert "content-text" in template["slides"]


def test_get_template_not_found(service):
    template = service.get_template("nonexistent")
    assert template is None


def test_get_slide_html(service):
    html = service.get_slide_html("business-blue", "cover")
    assert html is not None
    assert "<!DOCTYPE" in html or "<html" in html
    assert "data-editable" in html


def test_get_slide_html_not_found(service):
    html = service.get_slide_html("business-blue", "nonexistent")
    assert html is None
