from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.config import settings

app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.screenshots_dir).mkdir(parents=True, exist_ok=True)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


from app.api import ppt, templates, llm  # noqa: E402

app.include_router(ppt.router, prefix="/api/ppt", tags=["ppt"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
