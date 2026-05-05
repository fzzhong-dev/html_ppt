from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def chat():
    return {"message": "not implemented"}


@router.get("/providers")
async def list_providers():
    return []


@router.put("/provider")
async def switch_provider():
    return {"message": "not implemented"}
