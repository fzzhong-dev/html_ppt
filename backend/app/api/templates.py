from fastapi import APIRouter, HTTPException

from app.services.template_service import TemplateService

router = APIRouter()

template_service = TemplateService()


@router.get("/")
async def list_templates():
    return template_service.list_templates()


@router.get("/{template_id}")
async def get_template(template_id: str):
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
