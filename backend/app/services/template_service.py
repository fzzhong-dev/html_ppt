import json
from pathlib import Path
from typing import Optional
from app.config import settings


class TemplateService:
    def __init__(self):
        self.templates_dir = Path(settings.templates_dir)
        self._cache: list[dict] | None = None

    def list_templates(self) -> list[dict]:
        if self._cache is not None:
            return self._cache
        if not self.templates_dir.exists():
            self._cache = []
            return self._cache
        templates = []
        for d in sorted(self.templates_dir.iterdir()):
            if d.is_dir():
                palette = None
                theme_file = d / "theme.json"
                if theme_file.exists():
                    try:
                        theme_data = json.loads(theme_file.read_text(encoding="utf-8"))
                        palette = theme_data.get("palette")
                    except Exception:
                        pass
                templates.append({
                    "id": d.name,
                    "name": d.name.replace("-", " ").title(),
                    "slide_count": len(list(d.glob("*.html"))),
                    "palette": palette,
                })
        self._cache = templates
        return self._cache

    def get_template(self, template_id: str) -> Optional[dict]:
        template_dir = self.templates_dir / template_id
        if not template_dir.exists():
            return None
        slides = {}
        for f in sorted(template_dir.glob("*.html")):
            slides[f.stem] = {"file": str(f)}
        return {"id": template_id, "name": template_id.replace("-", " ").title(), "slides": slides}

    def get_slide_html(self, template_id: str, slide_type: str) -> Optional[str]:
        template_dir = self.templates_dir / template_id
        if not template_dir.exists():
            return None
        slide_file = template_dir / f"{slide_type}.html"
        if not slide_file.exists():
            return None
        return slide_file.read_text(encoding="utf-8")
