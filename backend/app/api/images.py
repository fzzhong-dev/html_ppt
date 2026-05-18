"""Image search and proxy endpoints."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.services.image_service import search_images, proxy_image

router = APIRouter()


@router.get("/search")
async def image_search(
    q: str = Query(..., min_length=1, description="Search keywords"),
    page: int = Query(1, ge=1, le=50),
):
    """Search Pexels/Unsplash for landscape images."""
    return await search_images(q, page)


@router.get("/proxy")
async def image_proxy(
    url: str = Query(..., description="Pexels/Unsplash image URL to proxy"),
):
    """Proxy an external image so slides can embed it without CORS issues."""
    try:
        content, content_type, filename = await proxy_image(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to download image")

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )
