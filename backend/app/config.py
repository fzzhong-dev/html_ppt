from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "HTML_PPT"
    debug: bool = True
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    zhipu_api_key: str = ""
    zhipu_model: str = "glm-4"
    qwen_api_key: str = ""
    qwen_model: str = "qwen-max"
    default_provider: str = "openai"
    templates_dir: str = str(Path(__file__).parent.parent.parent / "templates")
    screenshots_dir: str = str(Path(__file__).parent.parent / "screenshots")
    screenshot_script: str = str(Path(__file__).parent.parent.parent / "scripts" / "screenshot.js")

    class Config:
        env_file = ".env"


settings = Settings()
