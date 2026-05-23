"""Generate 12 template variants from business-blue base template.

Usage: python scripts/generate_templates.py
"""

import json
import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
BASE_DIR = TEMPLATES_DIR / "business-blue"

# Color mapping: business-blue colors → semantic names
# We replace these colors in all template HTML files
BUSINESS_BLUE_COLORS = {
    # Dark background gradients (cover, ending)
    "#0a1628": "bg_dark_1",
    "#0d2b5e": "bg_dark_2",
    # Primary brand colors
    "#1a3a6b": "primary",
    "#2a5aa0": "primary_light",
    # Accent / highlight
    "#4a90d9": "accent",
    # Borders and separators
    "#e8edf3": "border_light",
    "#f0f3f7": "border_light",
    # Light backgrounds
    "#f0f4f8": "surface",
    # Text colors
    "#333333": "text",
    "#444444": "text",
    "#2c3e50": "text_dark",
    # Image placeholder
    "#b0c4de": "placeholder_border",
    "#7a9cc6": "placeholder_text",
}

TEMPLATES = {
    "tech-gradient": {
        "name": "科技紫",
        "bg_dark_1": "#0a0514", "bg_dark_2": "#1a0a33",
        "primary": "#4a1d6e", "primary_light": "#7c3aed",
        "accent": "#a78bfa", "border_light": "#2e1f47",
        "surface": "#1e1033", "text": "#e2d9f3",
        "text_dark": "#c4b5e3", "placeholder_border": "#5b3a8a",
        "placeholder_text": "#8b6cc0",
    },
    "minimal-white": {
        "name": "极简白",
        "bg_dark_1": "#f9fafb", "bg_dark_2": "#f3f4f6",
        "primary": "#111827", "primary_light": "#374151",
        "accent": "#6b7280", "border_light": "#e5e7eb",
        "surface": "#f9fafb", "text": "#374151",
        "text_dark": "#111827", "placeholder_border": "#d1d5db",
        "placeholder_text": "#9ca3af",
    },
    "dark-pro": {
        "name": "深色专业",
        "bg_dark_1": "#030712", "bg_dark_2": "#111827",
        "primary": "#1f2937", "primary_light": "#374151",
        "accent": "#f97316", "border_light": "#1f2937",
        "surface": "#111827", "text": "#e5e7eb",
        "text_dark": "#d1d5db", "placeholder_border": "#4b5563",
        "placeholder_text": "#6b7280",
    },
    "nature-green": {
        "name": "自然绿",
        "bg_dark_1": "#022c22", "bg_dark_2": "#064e3b",
        "primary": "#065f46", "primary_light": "#047857",
        "accent": "#34d399", "border_light": "#d1fae5",
        "surface": "#ecfdf5", "text": "#374151",
        "text_dark": "#065f46", "placeholder_border": "#6ee7b7",
        "placeholder_text": "#34d399",
    },
    "warm-orange": {
        "name": "暖橙活力",
        "bg_dark_1": "#1c0a00", "bg_dark_2": "#431407",
        "primary": "#7c2d12", "primary_light": "#c2410c",
        "accent": "#fb923c", "border_light": "#fed7aa",
        "surface": "#fff7ed", "text": "#431407",
        "text_dark": "#7c2d12", "placeholder_border": "#fdba74",
        "placeholder_text": "#ea580c",
    },
    "elegant-purple": {
        "name": "优雅紫",
        "bg_dark_1": "#1a0533", "bg_dark_2": "#3b0764",
        "primary": "#4a1d6e", "primary_light": "#7e22ce",
        "accent": "#c084fc", "border_light": "#e9d5ff",
        "surface": "#faf5ff", "text": "#3b0764",
        "text_dark": "#581c87", "placeholder_border": "#d8b4fe",
        "placeholder_text": "#a855f7",
    },
    "academic-navy": {
        "name": "学术深蓝",
        "bg_dark_1": "#0c1929", "bg_dark_2": "#1e3a5f",
        "primary": "#1e3a5f", "primary_light": "#2d5a8e",
        "accent": "#c9a84c", "border_light": "#d4dde8",
        "surface": "#f0f4f8", "text": "#2c3e50",
        "text_dark": "#1e3a5f", "placeholder_border": "#8faabe",
        "placeholder_text": "#5a7d9a",
    },
    "creative-pink": {
        "name": "创意粉",
        "bg_dark_1": "#1a0214", "bg_dark_2": "#4a0e32",
        "primary": "#831843", "primary_light": "#be185d",
        "accent": "#f472b6", "border_light": "#fbcfe8",
        "surface": "#fdf2f8", "text": "#4a0e32",
        "text_dark": "#831843", "placeholder_border": "#f9a8d4",
        "placeholder_text": "#ec4899",
    },
    "vintage-paper": {
        "name": "复古纸",
        "bg_dark_1": "#3b2a1a", "bg_dark_2": "#5c3d24",
        "primary": "#44342a", "primary_light": "#6b4c38",
        "accent": "#d97706", "border_light": "#e8d5b7",
        "surface": "#fef3c7", "text": "#44342a",
        "text_dark": "#5c3d24", "placeholder_border": "#d4a574",
        "placeholder_text": "#b45309",
    },
    "fresh-cyan": {
        "name": "清新青",
        "bg_dark_1": "#021a19", "bg_dark_2": "#064e49",
        "primary": "#134e4a", "primary_light": "#0f766e",
        "accent": "#2dd4bf", "border_light": "#ccfbf1",
        "surface": "#f0fdfa", "text": "#134e4a",
        "text_dark": "#0f766e", "placeholder_border": "#5eead4",
        "placeholder_text": "#14b8a6",
    },
    "bold-red": {
        "name": "大胆红",
        "bg_dark_1": "#1a0505", "bg_dark_2": "#450a0a",
        "primary": "#7f1d1d", "primary_light": "#b91c1c",
        "accent": "#f87171", "border_light": "#fecaca",
        "surface": "#fef2f2", "text": "#450a0a",
        "text_dark": "#7f1d1d", "placeholder_border": "#fca5a5",
        "placeholder_text": "#dc2626",
    },
}


def generate_template(template_id: str, colors: dict) -> None:
    """Generate a template variant by replacing colors in business-blue templates."""
    out_dir = TEMPLATES_DIR / template_id
    out_dir.mkdir(parents=True, exist_ok=True)

    for html_file in BASE_DIR.glob("*.html"):
        content = html_file.read_text(encoding="utf-8")

        # Replace colors in CSS (case-insensitive hex matching)
        for old_color, placeholder in BUSINESS_BLUE_COLORS.items():
            if placeholder in colors:
                # Match both lowercase and uppercase hex colors
                content = re.sub(
                    re.escape(old_color),
                    colors[placeholder],
                    content,
                    flags=re.IGNORECASE,
                )

        # Also handle gradient stops that use the primary colors
        # e.g., "linear-gradient(90deg, #1a3a6b, #2a5aa0, #4a90d9)"
        # These should already be handled by the color replacement above

        out_file = out_dir / html_file.name
        out_file.write_text(content, encoding="utf-8")
        print(f"  Generated: {out_file.relative_to(TEMPLATES_DIR.parent)}")

    # Write theme.json with the palette for backend consumption
    theme_data = {
        "palette": {
            "primary": colors.get("primary", "#1a365d"),
            "secondary": colors.get("text", "#4a5568"),
            "accent": colors.get("accent", "#3182ce"),
            "accent_light": colors.get("border_light", "#ebf8ff"),
            "bg": colors.get("surface", "#ffffff"),
            "surface": colors.get("surface", "#f7fafc"),
            "border": colors.get("border_light", "#e2e8f0"),
        },
    }
    theme_file = out_dir / "theme.json"
    theme_file.write_text(json.dumps(theme_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Generated: {theme_file.relative_to(TEMPLATES_DIR.parent)}")


def main():
    print("Generating template variants from business-blue...")
    print(f"Templates directory: {TEMPLATES_DIR}")
    print(f"Base template: {BASE_DIR}")
    print()

    if not BASE_DIR.exists():
        print("ERROR: business-blue template not found!")
        return

    for template_id, colors in TEMPLATES.items():
        print(f"Generating '{colors['name']}' ({template_id})...")
        generate_template(template_id, colors)

    # Also write theme.json for business-blue base template
    bb_theme = {
        "palette": {
            "primary": "#1a3a6b",
            "secondary": "#333333",
            "accent": "#4a90d9",
            "accent_light": "#e8edf3",
            "bg": "#f0f4f8",
            "surface": "#f0f4f8",
            "border": "#e8edf3",
        },
    }
    bb_file = BASE_DIR / "theme.json"
    bb_file.write_text(json.dumps(bb_theme, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Generated: {bb_file.relative_to(TEMPLATES_DIR.parent)}")

    print()
    total = 1 + len(TEMPLATES)  # business-blue + new ones
    print(f"Done! {total} templates now available in {TEMPLATES_DIR}")


if __name__ == "__main__":
    main()
