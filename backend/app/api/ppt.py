from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate():
    return {"message": "not implemented"}


@router.post("/modify")
async def modify():
    return {"message": "not implemented"}


@router.post("/export")
async def export():
    return {"message": "not implemented"}


@router.get("/{presentation_id}")
async def get_presentation(presentation_id: str):
    return {"message": "not implemented"}


@router.get("/{presentation_id}/slides/{slide_number}")
async def get_slide(presentation_id: str, slide_number: int):
    return {"message": "not implemented"}
