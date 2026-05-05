import pytest
from app.services.export_service import ExportService


@pytest.fixture
def service():
    return ExportService()


def test_create_pptx_empty_slides(service):
    with pytest.raises(ValueError):
        service.create_pptx_from_slides([], "Test")
