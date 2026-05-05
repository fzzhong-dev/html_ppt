from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_templates():
    return []


@router.get("/{template_id}")
async def get_template(template_id: str):
    return {"message": "not implemented"}
