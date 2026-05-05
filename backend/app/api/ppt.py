import json
import logging
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from app.models import (
    GenerateRequest,
    ModifyRequest,
    ExportRequest,
    OutlineProposalRequest,
    Slide,
    SlideHtmlPatchRequest,
    SlideInsertRequest,
    SlideDeleteRequest,
)
from app.services.llm_errors import format_llm_error
from app.services.export_service import ExportService
from app.services.ppt_service import PPTService

router = APIRouter()

ppt_service = PPTService()
export_service = ExportService()
logger = logging.getLogger(__name__)


@router.post("/outline")
async def propose_outline(req: OutlineProposalRequest):
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="topic is required")
    return await ppt_service.propose_outline(req.topic.strip(), req.seed_outline)


@router.post("/outline-stream")
async def propose_outline_stream(req: OutlineProposalRequest):
    if not req.topic or not req.topic.strip():
        raise HTTPException(status_code=400, detail="topic is required")

    async def event_generator():
        async for evt in ppt_service.propose_outline_stream(
            req.topic.strip(), req.seed_outline
        ):
            yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/generate")
async def generate(req: GenerateRequest):
    presentation = await ppt_service.generate_with_ai(
        req.topic.strip(),
        req.outline,
        req.page_count,
    )
    return presentation.model_dump()


@router.post("/generate-stream")
async def generate_stream(req: GenerateRequest):
    pc = max(4, min(int(req.page_count), 16))
    presentation = ppt_service.create_presentation(req.topic.strip()[:500], "generated")

    async def event_generator():
        meta = json.dumps({
            "type": "meta",
            "presentation_id": presentation.id,
            "title": presentation.title,
            "total": pc,
        })
        yield f"data: {meta}\n\n"

        try:
            async for slide_info in ppt_service.generate_slides_streaming(
                topic=req.topic.strip(),
                outline=req.outline,
                page_count=pc,
            ):
                slide_info["id"] = str(uuid.uuid4())
                slide_info["editable_regions"] = {}
                presentation.slides.append(Slide(**slide_info))
                evt = json.dumps({"type": "slide", "slide": slide_info})
                yield f"data: {evt}\n\n"

            done = json.dumps({"type": "done", "presentation_id": presentation.id})
            yield f"data: {done}\n\n"
        except Exception as e:
            logger.warning("generate_stream failed", exc_info=True)
            err_evt = json.dumps(
                {"type": "error", "message": format_llm_error(e)},
                ensure_ascii=False,
            )
            yield f"data: {err_evt}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.patch("/{presentation_id}/slide-html")
async def patch_slide_html(presentation_id: str, body: SlideHtmlPatchRequest):
    slide = ppt_service.update_slide_html(
        presentation_id, body.slide_id, body.html_content
    )
    if not slide:
        raise HTTPException(status_code=404, detail="Presentation or slide not found")
    return slide.model_dump()


@router.post("/{presentation_id}/slides")
async def insert_slide(presentation_id: str, body: SlideInsertRequest):
    slide = ppt_service.insert_slide_html(
        presentation_id, body.html_content, body.after_index
    )
    if not slide:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return slide.model_dump()


@router.post("/{presentation_id}/delete-slide")
async def delete_slide(presentation_id: str, body: SlideDeleteRequest):
    ok = ppt_service.delete_slide_by_id(presentation_id, body.slide_id)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete slide (not found or last remaining slide)",
        )
    return {"ok": True}


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
