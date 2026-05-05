from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models import GenerateRequest, ModifyRequest, ExportRequest
from app.services.ppt_service import PPTService
from app.services.export_service import ExportService

router = APIRouter()

ppt_service = PPTService()
export_service = ExportService()


@router.post("/generate")
async def generate(req: GenerateRequest):
    template_id = req.template_id or "business-blue"
    presentation = await ppt_service.generate_with_ai(req.topic, template_id, req.outline)
    return presentation.model_dump()


@router.post("/modify")
async def modify(req: ModifyRequest):
    slide = await ppt_service.modify_slide(
        req.presentation_id,
        req.slide_id,
        req.instruction,
        req.chat_history,
    )
    if not slide:
        return {"error": "Slide not found"}
    return slide.model_dump()


@router.post("/export")
async def export_pptx(req: ExportRequest):
    presentation = ppt_service.get_presentation(req.presentation_id)
    if not presentation:
        return {"error": "Presentation not found"}
    pptx_path = await export_service.export_to_pptx(presentation.slides, presentation.title)
    return FileResponse(pptx_path, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename=f"{presentation.title}.pptx")


@router.get("/{presentation_id}")
async def get_presentation(presentation_id: str):
    pres = ppt_service.get_presentation(presentation_id)
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return pres.model_dump()


@router.get("/{presentation_id}/slides/{slide_number}")
async def get_slide(presentation_id: str, slide_number: int):
    pres = ppt_service.get_presentation(presentation_id)
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")
    for slide in pres.slides:
        if slide.page_number == slide_number:
            return slide.model_dump()
    raise HTTPException(status_code=404, detail="Slide not found")
