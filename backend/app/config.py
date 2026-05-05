from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "HTML_PPT"
    debug: bool = True
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    zhipu_api_key: str = ""
    zhipu_base_url: str = ""
    zhipu_model: str = "glm-4"
    qwen_api_key: str = ""
    qwen_model: str = "qwen-max"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    default_provider: str = "openai"
    # OpenAI 兼容客户端（OpenAI / DeepSeek）共用：超时与是否读取系统代理 HTTP(S)_PROXY
    llm_http_timeout_seconds: float = 120.0
    llm_connect_timeout_seconds: float = 45.0
    llm_trust_env_proxy: bool = True
    templates_dir: str = str(Path(__file__).parent.parent.parent / "templates")
    screenshots_dir: str = str(Path(__file__).parent.parent / "screenshots")
    screenshot_script: str = str(Path(__file__).parent.parent.parent / "scripts" / "screenshot.js")


settings = Settings()
