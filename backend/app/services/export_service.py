import json
import subprocess
import tempfile
from pathlib import Path
from pptx import Presentation as PptxPresentation
from pptx.util import Inches

from app.config import settings


class ExportService:
    def __init__(self):
        self.screenshot_script = Path(settings.screenshot_script)
        self.screenshots_dir = Path(settings.screenshots_dir)

    async def export_to_pptx(self, slides: list, title: str = "Presentation") -> str:
        if not slides:
            raise ValueError("No slides to export")

        slides_data = {
            "slides": [
                {"page_number": s.page_number, "html_content": s.html_content}
                for s in slides
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(slides_data, f, ensure_ascii=False)
            input_path = f.name

        output_dir = self.screenshots_dir / f"export_{id(slides)}"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ["node", str(self.screenshot_script), input_path, str(output_dir)],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Screenshot failed: {result.stderr}")

        screenshots = json.loads(result.stdout)

        pptx_path = str(self.screenshots_dir / f"{title}.pptx")
        self.create_pptx_from_slides(screenshots, title, pptx_path)

        Path(input_path).unlink(missing_ok=True)

        return pptx_path

    def create_pptx_from_slides(self, screenshots: list[dict], title: str, output_path: str = None) -> str:
        if not screenshots:
            raise ValueError("No screenshots to export")

        prs = PptxPresentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(5.63)

        blank_layout = prs.slide_layouts[6]

        for shot in screenshots:
            slide = prs.slides.add_slide(blank_layout)
            slide.shapes.add_picture(
                shot["path"],
                Inches(0), Inches(0),
                Inches(10), Inches(5.63),
            )

        if output_path is None:
            output_path = str(self.screenshots_dir / f"{title}.pptx")
        prs.save(output_path)
        return output_path
