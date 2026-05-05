from fastapi import APIRouter

from app.config import settings
from app.llm.base import list_providers as llm_list_providers
from app.services.llm_service import get_current_provider, resolve_provider_id, set_current_provider

router = APIRouter()


@router.get("/status")
async def llm_status():
    selected = get_current_provider()
    effective = resolve_provider_id(None)
    return {
        "configured_default": settings.default_provider,
        "selected_provider": selected,
        "effective_provider": effective,
        "auto_fallback_used": selected != effective,
        "providers": llm_list_providers(),
    }


@router.get("/providers")
async def get_providers():
    return llm_list_providers()


@router.put("/provider")
async def switch_provider(request: dict):
    provider_id = request.get("provider")
    if not provider_id:
        return {"error": "provider is required"}
    set_current_provider(provider_id)
    return {"current_provider": get_current_provider()}
