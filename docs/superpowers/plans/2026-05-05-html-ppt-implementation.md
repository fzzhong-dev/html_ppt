# HTML_PPT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an HTML-based PPT generation and editing tool where users describe a topic in natural language, AI generates HTML slides rendered in an editor, users modify via chat, and export to PPTX.

**Architecture:** Vue 3 frontend with a three-panel editor layout (slide list, preview, chat). Python FastAPI backend orchestrates LLM calls for content generation/modification, Puppeteer for HTML-to-screenshot conversion, and python-pptx for PPTX assembly. Templates are pre-built HTML files with marked editable regions.

**Tech Stack:** Vue 3 + Vite + Pinia, Python 3.10+ / FastAPI, Puppeteer (Node.js), python-pptx, multiple LLM APIs (OpenAI / Claude / 智谱 / 通义)

---

## File Structure

```
HTML_PPT/
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/
│       │   └── index.js              # axios API 封装
│       ├── stores/
│       │   └── presentation.js       # Pinia 状态管理
│       └── components/
│           ├── HomePage.vue          # 首页（输入主题）
│           ├── EditorView.vue        # 编辑器主视图
│           ├── Toolbar.vue           # 工具栏
│           ├── SlideList.vue         # 左侧幻灯片列表
│           ├── SlidePreview.vue      # 中间预览区
│           └── ChatPanel.vue         # 右侧对话面板
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── config.py                # 配置管理
│   │   ├── models.py                # 数据模型
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── ppt.py               # PPT 相关路由
│   │   │   ├── templates.py         # 模板路由
│   │   │   └── llm.py               # LLM 路由
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ppt_service.py       # PPT 生成/修改
│   │   │   ├── template_service.py  # 模板加载
│   │   │   ├── export_service.py    # PPTX 导出
│   │   │   └── llm_service.py       # LLM 调用编排
│   │   └── llm/
│   │       ├── __init__.py
│   │       ├── base.py              # LLM 基类
│   │       ├── openai_provider.py
│   │       ├── claude_provider.py
│   │       ├── zhipu_provider.py
│   │       └── qwen_provider.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_models.py
│       ├── test_ppt_service.py
│       ├── test_template_service.py
│       ├── test_export_service.py
│       ├── test_llm_service.py
│       └── test_api.py
├── templates/
│   └── business-blue/
│       ├── cover.html
│       ├── toc.html
│       ├── content-text.html
│       ├── content-image-text.html
│       └── ending.html
├── scripts/
│   ├── screenshot.js                # Puppeteer 截图脚本
│   └── package.json
└── docs/
```

---

### Task 1: Project Scaffolding — Backend

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/models.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Create backend directory structure and requirements**

```txt
# backend/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-pptx==1.0.2
pydantic==2.9.0
httpx==0.27.2
python-dotenv==1.0.1
openai==1.47.0
anthropic==0.34.2
zhipuai==2.1.5
dashscope==1.20.14
pytest==8.3.3
pytest-asyncio==0.24.0
```

- [ ] **Step 2: Create config module**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "HTML_PPT"
    debug: bool = True

    # LLM settings
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

    # Paths
    templates_dir: str = str(Path(__file__).parent.parent.parent / "templates")
    screenshots_dir: str = str(Path(__file__).parent.parent / "screenshots")

    # Puppeteer
    screenshot_script: str = str(Path(__file__).parent.parent.parent / "scripts" / "screenshot.js")

    class Config:
        env_file = ".env"


settings = Settings()
```

更新 `requirements.txt`，添加：
```
pydantic-settings==2.5.2
```

- [ ] **Step 3: Create data models**

```python
# backend/app/models.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Slide(BaseModel):
    id: str
    page_number: int
    html_content: str
    editable_regions: dict = {}


class Presentation(BaseModel):
    id: str
    title: str
    template_id: str
    theme: str = "default"
    slides: list[Slide] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class GenerateRequest(BaseModel):
    topic: str
    outline: Optional[str] = None
    template_id: Optional[str] = None
    page_count: int = 5


class ModifyRequest(BaseModel):
    presentation_id: str
    slide_id: Optional[str] = None
    instruction: str
    chat_history: list[dict] = []


class ExportRequest(BaseModel):
    presentation_id: str


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    provider: Optional[str] = None
    stream: bool = False


class ProviderInfo(BaseModel):
    id: str
    name: str
    available: bool


class SwitchProviderRequest(BaseModel):
    provider: str
```

- [ ] **Step 4: Create FastAPI entry point**

```python
# backend/app/main.py
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

# Ensure screenshots directory exists
Path(settings.screenshots_dir).mkdir(parents=True, exist_ok=True)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


from app.api import ppt, templates, llm  # noqa: E402

app.include_router(ppt.router, prefix="/api/ppt", tags=["ppt"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
```

- [ ] **Step 5: Create API __init__ and placeholder routers**

```python
# backend/app/api/__init__.py
```

```python
# backend/app/api/ppt.py
from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate():
    return {"message": "not implemented"}


@router.post("/modify")
async def modify():
    return {"message": "not implemented"}


@router.post("/export")
async def export():
    return {"message": "not implemented"}


@router.get("/{presentation_id}")
async def get_presentation(presentation_id: str):
    return {"message": "not implemented"}


@router.get("/{presentation_id}/slides/{slide_number}")
async def get_slide(presentation_id: str, slide_number: int):
    return {"message": "not implemented"}
```

```python
# backend/app/api/templates.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_templates():
    return []


@router.get("/{template_id}")
async def get_template(template_id: str):
    return {"message": "not implemented"}
```

```python
# backend/app/api/llm.py
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
```

- [ ] **Step 6: Create test conftest and verify server starts**

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
```

```python
# backend/tests/test_api.py
def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 7: Run tests and verify**

Run: `cd backend && pip install -r requirements.txt && pytest tests/test_api.py -v`
Expected: 1 passed

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend with FastAPI, config, models, and placeholder routes"
```

---

### Task 2: HTML Template System

**Files:**
- Create: `templates/business-blue/cover.html`
- Create: `templates/business-blue/toc.html`
- Create: `templates/business-blue/content-text.html`
- Create: `templates/business-blue/content-image-text.html`
- Create: `templates/business-blue/ending.html`
- Create: `backend/app/services/template_service.py`
- Create: `backend/tests/test_template_service.py`

- [ ] **Step 1: Write template_service tests**

```python
# backend/tests/test_template_service.py
import pytest
from app.services.template_service import TemplateService


@pytest.fixture
def service():
    return TemplateService()


def test_list_templates_returns_at_least_one(service):
    templates = service.list_templates()
    assert len(templates) >= 1
    assert templates[0]["id"] == "business-blue"
    assert templates[0]["name"]


def test_get_template_returns_slide_types(service):
    template = service.get_template("business-blue")
    assert template is not None
    assert "cover" in template["slides"]
    assert "content-text" in template["slides"]


def test_get_template_not_found(service):
    template = service.get_template("nonexistent")
    assert template is None


def test_get_slide_html(service):
    html = service.get_slide_html("business-blue", "cover")
    assert html is not None
    assert "<!DOCTYPE" in html or "<html" in html
    assert "data-editable" in html


def test_get_slide_html_not_found(service):
    html = service.get_slide_html("business-blue", "nonexistent")
    assert html is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_template_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.template_service'`

- [ ] **Step 3: Create business-blue cover template**

```html
<!-- templates/business-blue/cover.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1920px; height: 1080px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: linear-gradient(135deg, #0d47a1 0%, #1565c0 50%, #1e88e5 100%);
    color: white;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    overflow: hidden; position: relative;
  }
  .decoration {
    position: absolute; top: -100px; right: -100px;
    width: 400px; height: 400px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
  }
  .decoration2 {
    position: absolute; bottom: -150px; left: -150px;
    width: 500px; height: 500px;
    border-radius: 50%;
    background: rgba(255,255,255,0.03);
  }
  .subtitle-top {
    font-size: 24px; letter-spacing: 8px;
    text-transform: uppercase; opacity: 0.8;
    margin-bottom: 30px;
  }
  .title {
    font-size: 72px; font-weight: bold;
    text-align: center; margin-bottom: 20px;
    line-height: 1.3;
  }
  .subtitle-bottom {
    font-size: 28px; opacity: 0.9;
    margin-top: 10px;
  }
  .divider {
    width: 120px; height: 3px;
    background: rgba(255,255,255,0.6);
    margin: 30px 0;
  }
  .author {
    font-size: 20px; opacity: 0.7;
    margin-top: 40px;
  }
  .date {
    font-size: 18px; opacity: 0.6;
    margin-top: 10px;
  }
</style>
</head>
<body>
  <div class="decoration"></div>
  <div class="decoration2"></div>
  <div class="subtitle-top" data-editable="subtitle_top">PRESENTATION</div>
  <h1 class="title" data-editable="title">演示文稿标题</h1>
  <div class="divider"></div>
  <p class="subtitle-bottom" data-editable="subtitle">副标题或简要说明</p>
  <p class="author" data-editable="author">演讲者姓名</p>
  <p class="date" data-editable="date">2026年5月</p>
</body>
</html>
```

- [ ] **Step 4: Create business-blue TOC template**

```html
<!-- templates/business-blue/toc.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1920px; height: 1080px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #ffffff; color: #333;
    display: flex; overflow: hidden;
  }
  .left-bar {
    width: 80px; height: 1080px;
    background: linear-gradient(180deg, #0d47a1, #1565c0);
  }
  .content {
    flex: 1; padding: 80px 100px;
    display: flex; flex-direction: column;
  }
  .section-title {
    font-size: 42px; font-weight: bold;
    color: #0d47a1;
    margin-bottom: 60px;
    padding-bottom: 20px;
    border-bottom: 3px solid #0d47a1;
  }
  .toc-item {
    display: flex; align-items: center;
    margin-bottom: 40px;
  }
  .toc-number {
    font-size: 48px; font-weight: bold;
    color: #1565c0; width: 80px;
    opacity: 0.6;
  }
  .toc-text {
    font-size: 32px; color: #333;
  }
</style>
</head>
<body>
  <div class="left-bar"></div>
  <div class="content">
    <h2 class="section-title" data-editable="section_title">目录</h2>
    <div class="toc-item">
      <span class="toc-number">01</span>
      <span class="toc-text" data-editable="toc_1">第一章节标题</span>
    </div>
    <div class="toc-item">
      <span class="toc-number">02</span>
      <span class="toc-text" data-editable="toc_2">第二章节标题</span>
    </div>
    <div class="toc-item">
      <span class="toc-number">03</span>
      <span class="toc-text" data-editable="toc_3">第三章节标题</span>
    </div>
    <div class="toc-item">
      <span class="toc-number">04</span>
      <span class="toc-text" data-editable="toc_4">第四章节标题</span>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 5: Create business-blue content-text template**

```html
<!-- templates/business-blue/content-text.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1920px; height: 1080px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #ffffff; color: #333;
    overflow: hidden;
  }
  .header {
    height: 100px;
    background: linear-gradient(90deg, #0d47a1, #1565c0);
    display: flex; align-items: center;
    padding: 0 80px;
  }
  .header-title {
    font-size: 32px; color: white; font-weight: bold;
  }
  .main {
    padding: 60px 80px;
    display: flex; flex-direction: column;
  }
  .page-title {
    font-size: 44px; font-weight: bold;
    color: #0d47a1;
    margin-bottom: 40px;
  }
  .page-body {
    font-size: 24px; line-height: 2;
    color: #444;
  }
  .page-body p { margin-bottom: 20px; }
  .highlight {
    color: #1565c0; font-weight: bold;
  }
</style>
</head>
<body>
  <div class="header">
    <span class="header-title" data-editable="header_title">章节标题</span>
  </div>
  <div class="main">
    <h2 class="page-title" data-editable="title">页面标题</h2>
    <div class="page-body" data-editable="body">
      <p>这里是正文内容，支持多段落文字。</p>
      <p>可以包含<span class="highlight">重点标注</span>的文字。</p>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 6: Create business-blue content-image-text template**

```html
<!-- templates/business-blue/content-image-text.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1920px; height: 1080px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #ffffff; color: #333;
    overflow: hidden;
  }
  .header {
    height: 100px;
    background: linear-gradient(90deg, #0d47a1, #1565c0);
    display: flex; align-items: center;
    padding: 0 80px;
  }
  .header-title {
    font-size: 32px; color: white; font-weight: bold;
  }
  .main {
    padding: 60px 80px;
    display: flex; gap: 60px;
  }
  .text-area {
    flex: 1;
  }
  .page-title {
    font-size: 40px; font-weight: bold;
    color: #0d47a1;
    margin-bottom: 30px;
  }
  .page-body {
    font-size: 22px; line-height: 1.9;
    color: #444;
  }
  .page-body p { margin-bottom: 15px; }
  .image-area {
    width: 500px;
    display: flex; align-items: center; justify-content: center;
  }
  .image-area img {
    max-width: 100%; max-height: 500px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
  }
  .image-placeholder {
    width: 100%; height: 400px;
    background: #e3f2fd;
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; color: #90caf9;
  }
</style>
</head>
<body>
  <div class="header">
    <span class="header-title" data-editable="header_title">章节标题</span>
  </div>
  <div class="main">
    <div class="text-area">
      <h2 class="page-title" data-editable="title">页面标题</h2>
      <div class="page-body" data-editable="body">
        <p>左侧是文字内容区域。</p>
        <p>右侧可以放置配图。</p>
      </div>
    </div>
    <div class="image-area">
      <div class="image-placeholder" data-editable="image">图片区域</div>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 7: Create business-blue ending template**

```html
<!-- templates/business-blue/ending.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1920">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    width: 1920px; height: 1080px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    background: linear-gradient(135deg, #0d47a1 0%, #1565c0 50%, #1e88e5 100%);
    color: white;
    display: flex; flex-direction: column;
    justify-content: center; align-items: center;
    overflow: hidden; position: relative;
  }
  .decoration {
    position: absolute; bottom: -80px; right: -80px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
  }
  .thanks {
    font-size: 80px; font-weight: bold;
    margin-bottom: 30px;
  }
  .message {
    font-size: 28px; opacity: 0.9;
  }
  .contact {
    font-size: 20px; opacity: 0.7;
    margin-top: 60px;
  }
</style>
</head>
<body>
  <div class="decoration"></div>
  <h1 class="thanks" data-editable="thanks">谢谢聆听</h1>
  <p class="message" data-editable="message">感谢您的宝贵时间</p>
  <p class="contact" data-editable="contact">联系方式：email@example.com</p>
</body>
</html>
```

- [ ] **Step 8: Implement template_service**

```python
# backend/app/services/__init__.py
```

```python
# backend/app/services/template_service.py
from pathlib import Path
from typing import Optional

from app.config import settings


class TemplateService:
    def __init__(self):
        self.templates_dir = Path(settings.templates_dir)

    def list_templates(self) -> list[dict]:
        if not self.templates_dir.exists():
            return []
        templates = []
        for d in sorted(self.templates_dir.iterdir()):
            if d.is_dir():
                templates.append({
                    "id": d.name,
                    "name": d.name.replace("-", " ").title(),
                    "slide_count": len(list(d.glob("*.html"))),
                })
        return templates

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
```

- [ ] **Step 9: Run tests and verify they pass**

Run: `cd backend && pytest tests/test_template_service.py -v`
Expected: 5 passed

- [ ] **Step 10: Commit**

```bash
git add templates/ backend/app/services/ backend/tests/test_template_service.py
git commit -m "feat: add business-blue HTML templates and template loading service"
```

---

### Task 3: LLM Provider Abstraction

**Files:**
- Create: `backend/app/llm/__init__.py`
- Create: `backend/app/llm/base.py`
- Create: `backend/app/llm/openai_provider.py`
- Create: `backend/app/llm/claude_provider.py`
- Create: `backend/app/llm/zhipu_provider.py`
- Create: `backend/app/llm/qwen_provider.py`
- Create: `backend/tests/test_llm_providers.py`

- [ ] **Step 1: Write LLM provider tests**

```python
# backend/tests/test_llm_providers.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.llm.base import LLMProvider, get_provider


def test_get_provider_openai():
    provider = get_provider("openai")
    assert isinstance(provider, LLMProvider)
    assert provider.provider_id == "openai"


def test_get_provider_claude():
    provider = get_provider("claude")
    assert provider.provider_id == "claude"


def test_get_provider_zhipu():
    provider = get_provider("zhipu")
    assert provider.provider_id == "zhipu"


def test_get_provider_qwen():
    provider = get_provider("qwen")
    assert provider.provider_id == "qwen"


def test_get_provider_unknown():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("unknown_provider")


def test_list_providers():
    from app.llm.base import list_providers
    providers = list_providers()
    ids = [p["id"] for p in providers]
    assert "openai" in ids
    assert "claude" in ids
    assert "zhipu" in ids
    assert "qwen" in ids


@pytest.mark.asyncio
async def test_openai_chat():
    with patch("app.llm.openai_provider.AsyncOpenAI") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello response"
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        from app.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key="test-key")
        result = await provider.chat([{"role": "user", "content": "Hello"}])
        assert result == "Hello response"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_llm_providers.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement LLM base module**

```python
# backend/app/llm/__init__.py
```

```python
# backend/app/llm/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class LLMProvider(ABC):
    provider_id: str = ""
    provider_name: str = ""

    @abstractmethod
    async def chat(self, messages: list[dict], stream: bool = False) -> str | AsyncGenerator[str, None]:
        pass

    def is_available(self) -> bool:
        return False


def get_provider(provider_id: str) -> LLMProvider:
    from app.llm.openai_provider import OpenAIProvider
    from app.llm.claude_provider import ClaudeProvider
    from app.llm.zhipu_provider import ZhipuProvider
    from app.llm.qwen_provider import QwenProvider
    from app.config import settings

    providers = {
        "openai": lambda: OpenAIProvider(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
        ),
        "claude": lambda: ClaudeProvider(
            api_key=settings.claude_api_key,
            model=settings.claude_model,
        ),
        "zhipu": lambda: ZhipuProvider(
            api_key=settings.zhipu_api_key,
            model=settings.zhipu_model,
        ),
        "qwen": lambda: QwenProvider(
            api_key=settings.qwen_api_key,
            model=settings.qwen_model,
        ),
    }
    if provider_id not in providers:
        raise ValueError(f"Unknown provider: {provider_id}")
    return providers[provider_id]()


def list_providers() -> list[dict]:
    result = []
    for pid in ["openai", "claude", "zhipu", "qwen"]:
        try:
            p = get_provider(pid)
            result.append({"id": pid, "name": p.provider_name, "available": p.is_available()})
        except Exception:
            result.append({"id": pid, "name": pid, "available": False})
    return result
```

- [ ] **Step 4: Implement OpenAI provider**

```python
# backend/app/llm/openai_provider.py
from openai import AsyncOpenAI
from app.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    provider_id = "openai"
    provider_name = "OpenAI"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
        )
        if stream:
            return response
        return response.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.client.api_key and self.client.api_key != "")
```

- [ ] **Step 5: Implement Claude provider**

```python
# backend/app/llm/claude_provider.py
from anthropic import AsyncAnthropic
from app.llm.base import LLMProvider


class ClaudeProvider(LLMProvider):
    provider_id = "claude"
    provider_name = "Claude"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        # Separate system message from conversation messages
        system_msg = ""
        chat_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                chat_msgs.append(m)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_msg if system_msg else None,
            messages=chat_msgs,
        )
        return response.content[0].text

    def is_available(self) -> bool:
        return bool(self.client.api_key)
```

- [ ] **Step 6: Implement Zhipu provider**

```python
# backend/app/llm/zhipu_provider.py
from zhipuai import ZhipuAI
from app.llm.base import LLMProvider


class ZhipuProvider(LLMProvider):
    provider_id = "zhipu"
    provider_name = "智谱AI"

    def __init__(self, api_key: str, model: str = "glm-4"):
        self.client = ZhipuAI(api_key=api_key)
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=stream,
        )
        if stream:
            return response
        return response.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.client.api_key)
```

- [ ] **Step 7: Implement Qwen provider**

```python
# backend/app/llm/qwen_provider.py
import dashscope
from app.llm.base import LLMProvider


class QwenProvider(LLMProvider):
    provider_id = "qwen"
    provider_name = "通义千问"

    def __init__(self, api_key: str, model: str = "qwen-max"):
        self.api_key = api_key
        self.model = model

    async def chat(self, messages: list[dict], stream: bool = False) -> str:
        dashscope.api_key = self.api_key
        response = dashscope.Generation.call(
            model=self.model,
            messages=messages,
            result_format="message",
            stream=stream,
        )
        if stream:
            return response
        return response.output.choices[0].message.content

    def is_available(self) -> bool:
        return bool(self.api_key)
```

- [ ] **Step 8: Run tests and verify**

Run: `cd backend && pytest tests/test_llm_providers.py -v`
Expected: 7 passed

- [ ] **Step 9: Commit**

```bash
git add backend/app/llm/ backend/tests/test_llm_providers.py
git commit -m "feat: add LLM provider abstraction with OpenAI, Claude, Zhipu, Qwen adapters"
```

---

### Task 4: PPT Generation & Modification Service

**Files:**
- Create: `backend/app/services/ppt_service.py`
- Create: `backend/app/services/llm_service.py`
- Create: `backend/tests/test_ppt_service.py`

- [ ] **Step 1: Write ppt_service tests**

```python
# backend/tests/test_ppt_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ppt_service import PPTService


@pytest.fixture
def service():
    return PPTService()


def test_create_presentation(service):
    result = service.create_presentation("人工智能的未来", "business-blue")
    assert result.title == "人工智能的未来"
    assert result.template_id == "business-blue"
    assert len(result.slides) > 0
    assert result.slides[0].id


def test_get_presentation(service):
    created = service.create_presentation("测试主题", "business-blue")
    found = service.get_presentation(created.id)
    assert found is not None
    assert found.title == "测试主题"


def test_get_presentation_not_found(service):
    assert service.get_presentation("nonexistent") is None


@pytest.mark.asyncio
async def test_generate_slides_with_ai(service):
    with patch("app.services.ppt_service.PPTService._call_llm", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '{"slides": [{"title": "AI简介", "body": "人工智能是..."}]}'
        result = await service.generate_with_ai("人工智能", "business-blue")
        assert result is not None
        assert result.title == "人工智能"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_ppt_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement LLM service**

```python
# backend/app/services/llm_service.py
import json
from app.llm.base import get_provider
from app.config import settings

_current_provider = settings.default_provider


def get_current_provider():
    return _current_provider


def set_current_provider(provider_id: str):
    global _current_provider
    _current_provider = provider_id


async def call_llm(messages: list[dict], provider_id: str = None) -> str:
    pid = provider_id or _current_provider
    provider = get_provider(pid)
    return await provider.chat(messages)


async def call_llm_json(messages: list[dict], provider_id: str = None) -> dict:
    response = await call_llm(messages, provider_id)
    # Extract JSON from response, handling markdown code blocks
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    return json.loads(text)
```

- [ ] **Step 4: Implement PPT service**

```python
# backend/app/services/ppt_service.py
import uuid
import json
from datetime import datetime
from typing import Optional

from app.models import Presentation, Slide
from app.services.template_service import TemplateService
from app.services.llm_service import call_llm_json


class PPTService:
    def __init__(self):
        self.presentations: dict[str, Presentation] = {}
        self.template_service = TemplateService()

    def create_presentation(self, title: str, template_id: str) -> Presentation:
        slide_types = ["cover", "toc", "content-text", "content-text", "ending"]
        slides = []
        for i, st in enumerate(slide_types):
            html = self.template_service.get_slide_html(template_id, st)
            if html:
                slides.append(Slide(
                    id=str(uuid.uuid4()),
                    page_number=i + 1,
                    html_content=html,
                ))
        presentation = Presentation(
            id=str(uuid.uuid4()),
            title=title,
            template_id=template_id,
            slides=slides,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.presentations[presentation.id] = presentation
        return presentation

    def get_presentation(self, presentation_id: str) -> Optional[Presentation]:
        return self.presentations.get(presentation_id)

    async def generate_with_ai(self, topic: str, template_id: str, outline: str = None) -> Presentation:
        presentation = self.create_presentation(topic, template_id)

        system_prompt = """你是一个PPT内容生成助手。用户给你一个主题，你需要生成PPT各页的内容。
以JSON格式返回，格式如下：
{
  "slides": [
    {"subtitle_top": "PRESENTATION", "title": "主标题", "subtitle": "副标题", "author": "演讲者", "date": "日期"},
    {"section_title": "目录", "toc_1": "章节1", "toc_2": "章节2", "toc_3": "章节3", "toc_4": "章节4"},
    {"header_title": "章节1", "title": "页面标题", "body": "<p>正文内容</p>"},
    {"header_title": "章节2", "title": "页面标题", "body": "<p>正文内容</p>"},
    {"thanks": "谢谢聆听", "message": "感谢您的宝贵时间", "contact": "联系方式"}
  ]
}
只返回JSON，不要其他文字。"""

        user_msg = f"主题：{topic}"
        if outline:
            user_msg += f"\n大纲：{outline}"
        user_msg += f"\n共{len(presentation.slides)}页"

        result = await call_llm_json([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ])

        if "slides" in result:
            for i, slide_data in enumerate(result["slides"]):
                if i < len(presentation.slides):
                    html = presentation.slides[i].html_content
                    for key, value in slide_data.items():
                        placeholder = f'data-editable="{key}"'
                        if placeholder in html:
                            # Find the content after data-editable and replace the text
                            import re
                            pattern = rf'(<[^>]+data-editable="{key}"[^>]*>)(.*?)(</)'
                            html = re.sub(pattern, rf'\g<1>{value}\g<3>', html, flags=re.DOTALL)
                    presentation.slides[i].html_content = html

        presentation.updated_at = datetime.now()
        return presentation

    async def modify_slide(self, presentation_id: str, slide_id: str, instruction: str, chat_history: list[dict]) -> Optional[Slide]:
        presentation = self.get_presentation(presentation_id)
        if not presentation:
            return None
        slide = next((s for s in presentation.slides if s.id == slide_id), None)
        if not slide:
            return None

        system_prompt = f"""你是一个PPT修改助手。用户会给你修改指令，你需要返回修改后的完整HTML。
规则：
1. 只修改 data-editable 区域的内容
2. 保持HTML结构不变
3. 只返回完整的HTML内容，不要其他文字

当前HTML：
{slide.html_content}"""

        messages = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": instruction}]

        from app.services.llm_service import call_llm
        new_html = await call_llm(messages)

        # Clean response
        new_html = new_html.strip()
        if new_html.startswith("```html"):
            new_html = new_html[7:]
        if new_html.startswith("```"):
            new_html = new_html[3:]
        if new_html.endswith("```"):
            new_html = new_html[:-3]
        new_html = new_html.strip()

        slide.html_content = new_html
        presentation.updated_at = datetime.now()
        return slide
```

- [ ] **Step 5: Run tests and verify**

Run: `cd backend && pytest tests/test_ppt_service.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ backend/tests/test_ppt_service.py
git commit -m "feat: add PPT generation and modification service with LLM integration"
```

---

### Task 5: Export Service — Puppeteer + python-pptx

**Files:**
- Create: `scripts/package.json`
- Create: `scripts/screenshot.js`
- Create: `backend/app/services/export_service.py`
- Create: `backend/tests/test_export_service.py`

- [ ] **Step 1: Create Puppeteer screenshot script**

```json
// scripts/package.json
{
  "name": "html-ppt-screenshot",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "puppeteer": "^23.6.0"
  }
}
```

```javascript
// scripts/screenshot.js
const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function screenshotSlides(inputPath, outputDir) {
  const data = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const results = [];
  for (const slide of data.slides) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
    await page.setContent(slide.html_content, { waitUntil: 'networkidle0' });

    const outputPath = path.join(outputDir, `slide_${slide.page_number}.png`);
    await page.screenshot({ path: outputPath, fullPage: false });
    results.push({ page_number: slide.page_number, path: outputPath });
    await page.close();
  }

  await browser.close();
  // Output results as JSON for the Python backend to read
  console.log(JSON.stringify(results));
}

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node screenshot.js <input.json> <output_dir>');
  process.exit(1);
}
screenshotSlides(args[0], args[1]).catch(e => { console.error(e); process.exit(1); });
```

- [ ] **Step 2: Install puppeteer**

Run: `cd scripts && npm install`
Expected: puppeteer installed, Chromium downloaded

- [ ] **Step 3: Write export service tests**

```python
# backend/tests/test_export_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.export_service import ExportService


@pytest.fixture
def service():
    return ExportService()


def test_create_pptx_empty_slides(service):
    """Test that export handles empty slide list without error."""
    from app.models import Presentation, Slide
    pres = Presentation(id="test", title="Test", template_id="business-blue", slides=[])
    with pytest.raises(ValueError):
        service.create_pptx_from_slides([], pres.title)
```

- [ ] **Step 4: Implement export service**

```python
# backend/app/services/export_service.py
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

    async def export_to_pptx(self, slides: list[dict], title: str = "Presentation") -> str:
        if not slides:
            raise ValueError("No slides to export")

        # Create temp file with slide HTML data
        slides_data = {
            "slides": [
                {"page_number": s.page_number, "html_content": s.html_content}
                for s in slides
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(slides_data, f, ensure_ascii=False)
            input_path = f.name

        # Create output directory for screenshots
        output_dir = self.screenshots_dir / f"export_{id(slides)}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run Puppeteer screenshot script
        result = subprocess.run(
            ["node", str(self.screenshot_script), input_path, str(output_dir)],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Screenshot failed: {result.stderr}")

        # Parse screenshot results
        screenshots = json.loads(result.stdout)

        # Generate PPTX
        pptx_path = str(self.screenshots_dir / f"{title}.pptx")
        self.create_pptx_from_slides(screenshots, title, pptx_path)

        # Cleanup temp files
        Path(input_path).unlink(missing_ok=True)

        return pptx_path

    def create_pptx_from_slides(self, screenshots: list[dict], title: str, output_path: str = None) -> str:
        if not screenshots:
            raise ValueError("No screenshots to export")

        prs = PptxPresentation()
        # Set slide dimensions to 16:9 (10" x 5.63")
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(5.63)

        blank_layout = prs.slide_layouts[6]  # Blank layout

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
```

- [ ] **Step 5: Run tests and verify**

Run: `cd backend && pytest tests/test_export_service.py -v`
Expected: 1 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/ backend/app/services/export_service.py backend/tests/test_export_service.py
git commit -m "feat: add Puppeteer screenshot script and PPTX export service"
```

---

### Task 6: Wire Up API Routes

**Files:**
- Modify: `backend/app/api/ppt.py`
- Modify: `backend/app/api/templates.py`
- Modify: `backend/app/api/llm.py`
- Create: `backend/tests/test_api_routes.py`

- [ ] **Step 1: Write API route tests**

```python
# backend/tests/test_api_routes.py
import pytest


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200


def test_list_templates(client):
    r = client.get("/api/templates/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_get_template(client):
    r = client.get("/api/templates/business-blue")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "business-blue"
    assert "cover" in data["slides"]


def test_generate_ppt(client):
    r = client.post("/api/ppt/generate", json={"topic": "测试主题"})
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "测试主题"
    assert len(data["slides"]) > 0
    return data["id"]


def test_get_presentation(client):
    # Generate first
    gen = client.post("/api/ppt/generate", json={"topic": "测试"})
    pres_id = gen.json()["id"]
    # Then get
    r = client.get(f"/api/ppt/{pres_id}")
    assert r.status_code == 200
    assert r.json()["id"] == pres_id


def test_get_presentation_not_found(client):
    r = client.get("/api/ppt/nonexistent")
    assert r.status_code == 404


def test_get_slide(client):
    gen = client.post("/api/ppt/generate", json={"topic": "测试"})
    data = gen.json()
    r = client.get(f"/api/ppt/{data['id']}/slides/1")
    assert r.status_code == 200
    assert "html_content" in r.json()


def test_list_llm_providers(client):
    r = client.get("/api/llm/providers")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_api_routes.py -v`
Expected: Multiple FAIL — routes return "not implemented"

- [ ] **Step 3: Implement ppt routes**

```python
# backend/app/api/ppt.py
from fastapi import APIRouter, HTTPResponse
from fastapi.responses import FileResponse

from app.models import GenerateRequest, ModifyRequest, ExportRequest
from app.services.ppt_service import PPTService
from app.services.export_service import ExportService

router = APIRouter()

ppt_service = PPTService()
export_service = ExportService()


@router.post("/generate")
async def generate(req: GenerateRequest):
    template_id = req.template_id or "business-blue"
    if req.outline:
        presentation = await ppt_service.generate_with_ai(req.topic, template_id, req.outline)
    else:
        presentation = await ppt_service.generate_with_ai(req.topic, template_id)
    return presentation.model_dump()


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
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Presentation not found")
    return pres.model_dump()


@router.get("/{presentation_id}/slides/{slide_number}")
async def get_slide(presentation_id: str, slide_number: int):
    pres = ppt_service.get_presentation(presentation_id)
    if not pres:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Presentation not found")
    for slide in pres.slides:
        if slide.page_number == slide_number:
            return slide.model_dump()
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Slide not found")
```

- [ ] **Step 4: Implement template routes**

```python
# backend/app/api/templates.py
from fastapi import APIRouter, HTTPException

from app.services.template_service import TemplateService

router = APIRouter()

template_service = TemplateService()


@router.get("/")
async def list_templates():
    return template_service.list_templates()


@router.get("/{template_id}")
async def get_template(template_id: str):
    template = template_service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template
```

- [ ] **Step 5: Implement LLM routes**

```python
# backend/app/api/llm.py
from fastapi import APIRouter

from app.llm.base import list_providers
from app.services.llm_service import get_current_provider, set_current_provider

router = APIRouter()


@router.get("/providers")
async def get_providers():
    return list_providers()


@router.put("/provider")
async def switch_provider(request: dict):
    provider_id = request.get("provider")
    if not provider_id:
        return {"error": "provider is required"}
    set_current_provider(provider_id)
    return {"current_provider": get_current_provider()}
```

- [ ] **Step 6: Add ppt_service fixture to conftest**

Update `backend/tests/conftest.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    # Mock LLM calls so tests don't require API keys
    mock_response = '{"slides": [{"subtitle_top": "TEST", "title": "测试标题", "subtitle": "测试副标题", "author": "测试", "date": "2026"}, {"section_title": "目录", "toc_1": "章节1", "toc_2": "章节2", "toc_3": "章节3", "toc_4": "章节4"}, {"header_title": "章节1", "title": "测试", "body": "<p>测试内容</p>"}, {"header_title": "章节2", "title": "测试", "body": "<p>测试内容</p>"}, {"thanks": "谢谢", "message": "感谢", "contact": "test@test.com"}]}'

    with patch("app.services.llm_service.call_llm_json", new_callable=AsyncMock, return_value=__import__('json').loads(mock_response)):
        with patch("app.services.llm_service.call_llm", new_callable=AsyncMock, return_value="<html>modified</html>"):
            yield TestClient(app)
```

- [ ] **Step 7: Run tests and verify**

Run: `cd backend && pytest tests/test_api_routes.py -v`
Expected: 7 passed

- [ ] **Step 8: Run all backend tests together**

Run: `cd backend && pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: wire up all API routes with mock LLM support for tests"
```

---

### Task 7: Frontend Scaffolding — Vue 3

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/api/index.js`
- Create: `frontend/src/stores/presentation.js`

- [ ] **Step 1: Initialize Vue project**

Run: `cd e:/caogao/HTML_PPT && npm create vite@latest frontend -- --template vue`

- [ ] **Step 2: Install dependencies**

Run: `cd frontend && npm install && npm install axios pinia vue-router@4`

- [ ] **Step 3: Configure Vite proxy for backend**

```javascript
// frontend/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: Create API module**

```javascript
// frontend/src/api/index.js
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const generatePPT = (topic, outline, templateId, pageCount) =>
  api.post('/ppt/generate', { topic, outline, template_id: templateId, page_count: pageCount })

export const modifySlide = (presentationId, slideId, instruction, chatHistory) =>
  api.post('/ppt/modify', { presentation_id: presentationId, slide_id: slideId, instruction, chat_history: chatHistory })

export const exportPPTX = (presentationId) =>
  api.post('/ppt/export', { presentation_id: presentationId }, { responseType: 'blob' })

export const getPresentation = (id) =>
  api.get(`/ppt/${id}`)

export const getSlide = (presentationId, slideNumber) =>
  api.get(`/ppt/${presentationId}/slides/${slideNumber}`)

export const listTemplates = () =>
  api.get('/templates/')

export const getTemplate = (id) =>
  api.get(`/templates/${id}`)

export const listProviders = () =>
  api.get('/llm/providers')

export const switchProvider = (provider) =>
  api.put('/llm/provider', { provider })
```

- [ ] **Step 5: Create Pinia store**

```javascript
// frontend/src/stores/presentation.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generatePPT, getPresentation, modifySlide, exportPPTX } from '../api'

export const usePresentationStore = defineStore('presentation', () => {
  const presentation = ref(null)
  const currentSlideIndex = ref(0)
  const chatHistory = ref([])
  const loading = ref(false)

  const currentSlide = computed(() => {
    if (!presentation.value || !presentation.value.slides.length) return null
    return presentation.value.slides[currentSlideIndex.value]
  })

  const slideCount = computed(() => presentation.value?.slides.length || 0)

  async function generate(topic, outline, templateId) {
    loading.value = true
    try {
      const { data } = await generatePPT(topic, outline, templateId)
      presentation.value = data
      currentSlideIndex.value = 0
      chatHistory.value = []
    } finally {
      loading.value = false
    }
  }

  async function modify(instruction) {
    if (!currentSlide.value) return
    loading.value = true
    chatHistory.value.push({ role: 'user', content: instruction })
    try {
      const { data } = await modifySlide(
        presentation.value.id,
        currentSlide.value.id,
        instruction,
        chatHistory.value.slice(0, -1),
      )
      // Update the slide HTML in the presentation
      const idx = presentation.value.slides.findIndex(s => s.id === data.id)
      if (idx !== -1) {
        presentation.value.slides[idx] = data
      }
      chatHistory.value.push({ role: 'assistant', content: '已修改完成' })
    } finally {
      loading.value = false
    }
  }

  async function exportToPPTX() {
    if (!presentation.value) return
    const { data } = await exportPPTX(presentation.value.id)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${presentation.value.title}.pptx`
    a.click()
    URL.revokeObjectURL(url)
  }

  function selectSlide(index) {
    currentSlideIndex.value = index
  }

  function nextSlide() {
    if (currentSlideIndex.value < slideCount.value - 1) {
      currentSlideIndex.value++
    }
  }

  function prevSlide() {
    if (currentSlideIndex.value > 0) {
      currentSlideIndex.value--
    }
  }

  return {
    presentation, currentSlideIndex, chatHistory, loading,
    currentSlide, slideCount,
    generate, modify, exportToPPTX, selectSlide, nextSlide, prevSlide,
  }
})
```

- [ ] **Step 6: Update main.js with Pinia**

```javascript
// frontend/src/main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

- [ ] **Step 7: Update App.vue with router placeholder**

```vue
<!-- frontend/src/App.vue -->
<template>
  <HomePage v-if="!store.presentation" />
  <EditorView v-else />
</template>

<script setup>
import { usePresentationStore } from './stores/presentation'
import HomePage from './components/HomePage.vue'
import EditorView from './components/EditorView.vue'

const store = usePresentationStore()
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }
</style>
```

- [ ] **Step 8: Verify frontend starts**

Run: `cd frontend && npm run dev`
Expected: Vite dev server running at http://localhost:3000 (will show errors for missing components — that's expected)

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold Vue 3 frontend with API module, Pinia store, and Vite config"
```

---

### Task 8: Frontend — HomePage Component

**Files:**
- Create: `frontend/src/components/HomePage.vue`

- [ ] **Step 1: Create HomePage component**

```vue
<!-- frontend/src/components/HomePage.vue -->
<template>
  <div class="home">
    <div class="home-card">
      <h1 class="home-title">HTML PPT 生成器</h1>
      <p class="home-desc">输入主题，AI 自动生成精美演示文稿</p>

      <div class="form-group">
        <label>主题</label>
        <input v-model="topic" placeholder="例如：人工智能的未来发展" @keyup.enter="handleGenerate" />
      </div>

      <div class="form-group">
        <label>大纲（可选）</label>
        <textarea v-model="outline" placeholder="输入你的大纲，每行一个要点..." rows="4"></textarea>
      </div>

      <div class="form-group">
        <label>模板</label>
        <select v-model="templateId">
          <option value="business-blue">商务蓝</option>
        </select>
      </div>

      <button class="btn-primary" @click="handleGenerate" :disabled="!topic || loading">
        {{ loading ? '生成中...' : '生成 PPT' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePresentationStore } from '../stores/presentation'

const store = usePresentationStore()
const topic = ref('')
const outline = ref('')
const templateId = ref('business-blue')
const loading = ref(false)

async function handleGenerate() {
  if (!topic.value) return
  loading.value = true
  try {
    await store.generate(topic.value, outline.value, templateId.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%);
}
.home-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  width: 500px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.home-title {
  font-size: 28px;
  color: #0d47a1;
  margin-bottom: 8px;
}
.home-desc {
  color: #666;
  margin-bottom: 32px;
  font-size: 14px;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}
.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #1565c0;
}
.btn-primary {
  width: 100%;
  padding: 12px;
  background: #1565c0;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover { background: #0d47a1; }
.btn-primary:disabled { background: #90caf9; cursor: not-allowed; }
</style>
```

- [ ] **Step 2: Verify homepage renders**

Run: `cd frontend && npm run dev`
Expected: Homepage at http://localhost:3000 shows form with topic input, outline textarea, template selector, and generate button

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/HomePage.vue
git commit -m "feat: add HomePage component with topic input form"
```

---

### Task 9: Frontend — EditorView with Toolbar, SlideList, SlidePreview, ChatPanel

**Files:**
- Create: `frontend/src/components/EditorView.vue`
- Create: `frontend/src/components/Toolbar.vue`
- Create: `frontend/src/components/SlideList.vue`
- Create: `frontend/src/components/SlidePreview.vue`
- Create: `frontend/src/components/ChatPanel.vue`

- [ ] **Step 1: Create Toolbar component**

```vue
<!-- frontend/src/components/Toolbar.vue -->
<template>
  <div class="toolbar">
    <div class="toolbar-group">
      <button @click="$emit('undo')" title="撤销">↩ 撤销</button>
      <button @click="$emit('redo')" title="重做">↪ 重做</button>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <button @click="$emit('add-slide')" title="添加页">＋ 添加页</button>
      <button @click="$emit('copy-slide')" title="复制页">📋 复制页</button>
      <button @click="$emit('delete-slide')" title="删除页">🗑 删除页</button>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <select v-model="currentTheme" @change="$emit('change-theme', currentTheme)">
        <option value="business-blue">🎨 商务蓝</option>
      </select>
      <select v-model="currentFont" @change="$emit('change-font', currentFont)">
        <option value="default">字体</option>
        <option value="yahei">微软雅黑</option>
        <option value="songti">宋体</option>
        <option value="heiti">黑体</option>
      </select>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <button @click="$emit('insert-image')" title="插入图片">🖼 图片</button>
      <button @click="$emit('insert-chart')" title="插入图表">📊 图表</button>
      <button @click="$emit('insert-shape')" title="插入形状">🔷 形状</button>
    </div>
    <div class="toolbar-spacer"></div>
    <div class="toolbar-group">
      <button class="btn-export" @click="$emit('export')" :disabled="exporting">
        📥 导出 PPTX
      </button>
      <button @click="$emit('fullscreen')" title="全屏演示">🖥 演示</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({ exporting: Boolean })
defineEmits(['undo', 'redo', 'add-slide', 'copy-slide', 'delete-slide', 'change-theme', 'change-font', 'insert-image', 'insert-chart', 'insert-shape', 'export', 'fullscreen'])

const currentTheme = ref('business-blue')
const currentFont = ref('default')
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  background: #37474f;
  color: #ccc;
  padding: 6px 12px;
  font-size: 13px;
  gap: 4px;
  flex-shrink: 0;
}
.toolbar-group { display: flex; gap: 4px; align-items: center; }
.toolbar-divider { width: 1px; height: 24px; background: #546e7a; margin: 0 8px; }
.toolbar-spacer { flex: 1; }
.toolbar button {
  background: #455a64;
  color: #ccc;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
}
.toolbar button:hover { background: #546e7a; }
.toolbar button:disabled { opacity: 0.5; cursor: not-allowed; }
.toolbar select {
  background: #455a64;
  color: #ccc;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.btn-export { background: #4CAF50 !important; color: white !important; font-weight: 600; }
.btn-export:hover { background: #388E3C !important; }
</style>
```

- [ ] **Step 2: Create SlideList component**

```vue
<!-- frontend/src/components/SlideList.vue -->
<template>
  <div class="slide-list">
    <div class="slide-list-header">幻灯片 ({{ slides.length }})</div>
    <div
      v-for="(slide, index) in slides"
      :key="slide.id"
      class="slide-thumb"
      :class="{ active: index === currentIndex }"
      @click="$emit('select', index)"
    >
      <div class="slide-thumb-inner">
        <span>{{ getPageLabel(index) }}</span>
      </div>
      <span class="slide-number">{{ index + 1 }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  slides: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: 0 },
})
defineEmits(['select'])

function getPageLabel(index) {
  const labels = ['封面页', '目录页']
  if (index >= labels.length && index < labels.length + 10) return `内容页 ${index - labels.length + 1}`
  if (index === labels.length + 10) return '结尾页'
  const total = index + 1
  return total <= 2 ? labels[index] : `第 ${total} 页`
}
</script>

<style scoped>
.slide-list {
  width: 180px;
  background: #2c2c2c;
  padding: 10px;
  overflow-y: auto;
  flex-shrink: 0;
}
.slide-list-header {
  color: #aaa;
  font-size: 12px;
  text-align: center;
  margin-bottom: 8px;
}
.slide-thumb {
  position: relative;
  margin-bottom: 8px;
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 4px;
  overflow: hidden;
}
.slide-thumb.active { border-color: #42a5f5; }
.slide-thumb-inner {
  background: #3c3c3c;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 11px;
}
.slide-number {
  position: absolute;
  bottom: 2px;
  right: 4px;
  font-size: 10px;
  color: #666;
}
</style>
```

- [ ] **Step 3: Create SlidePreview component**

```vue
<!-- frontend/src/components/SlidePreview.vue -->
<template>
  <div class="preview-area">
    <div class="preview-container">
      <iframe
        v-if="slide"
        :srcdoc="slide.html_content"
        class="preview-iframe"
        sandbox="allow-same-origin"
      ></iframe>
      <div v-else class="preview-empty">选择一张幻灯片</div>
    </div>
    <div class="preview-nav">
      <button @click="$emit('prev')" :disabled="!canPrev">上一页</button>
      <span>{{ current + 1 }} / {{ total }}</span>
      <button @click="$emit('next')" :disabled="!canNext">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  slide: Object,
  current: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
})
defineEmits(['prev', 'next'])

const canPrev = computed(() => props.current > 0)
const canNext = computed(() => props.current < props.total - 1)
</script>

<style scoped>
.preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #d0d0d0;
  padding: 16px;
}
.preview-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-iframe {
  width: 90%;
  aspect-ratio: 16/9;
  border: none;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
  border-radius: 4px;
  background: white;
}
.preview-empty {
  color: #999;
  font-size: 18px;
}
.preview-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 8px;
}
.preview-nav button {
  padding: 6px 16px;
  border: 1px solid #bbb;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.preview-nav button:disabled { opacity: 0.4; cursor: not-allowed; }
.preview-nav span { font-size: 13px; color: #666; }
</style>
```

- [ ] **Step 4: Create ChatPanel component**

```vue
<!-- frontend/src/components/ChatPanel.vue -->
<template>
  <div class="chat-panel">
    <div class="chat-header">AI 对话</div>
    <div class="chat-messages" ref="messagesEl">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-msg"
        :class="msg.role"
      >
        {{ msg.content }}
      </div>
      <div v-if="loading" class="chat-msg assistant">思考中...</div>
    </div>
    <div class="chat-input">
      <input
        v-model="input"
        placeholder="输入修改指令..."
        @keyup.enter="handleSend"
        :disabled="loading"
      />
      <button @click="handleSend" :disabled="loading || !input">发送</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: Boolean,
})
const emit = defineEmits(['send'])

const input = ref('')
const messagesEl = ref(null)

function handleSend() {
  if (!input.value.trim() || props.loading) return
  emit('send', input.value.trim())
  input.value = ''
}

watch(() => props.messages.length, async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
})
</script>

<style scoped>
.chat-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  border-left: 1px solid #e0e0e0;
  flex-shrink: 0;
}
.chat-header {
  background: #4CAF50;
  color: white;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 14px;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-msg {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-width: 90%;
  word-break: break-word;
}
.chat-msg.user {
  background: #e3f2fd;
  align-self: flex-end;
  text-align: right;
}
.chat-msg.assistant {
  background: #f0f0f0;
  align-self: flex-start;
}
.chat-input {
  display: flex;
  padding: 8px;
  border-top: 1px solid #e0e0e0;
  gap: 6px;
}
.chat-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
}
.chat-input input:focus { border-color: #4CAF50; }
.chat-input button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.chat-input button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
```

- [ ] **Step 5: Create EditorView component (assembles all)**

```vue
<!-- frontend/src/components/EditorView.vue -->
<template>
  <div class="editor">
    <Toolbar
      :exporting="exporting"
      @export="handleExport"
      @fullscreen="handleFullscreen"
    />
    <div class="editor-body">
      <SlideList
        :slides="store.presentation?.slides || []"
        :currentIndex="store.currentSlideIndex"
        @select="store.selectSlide"
      />
      <SlidePreview
        :slide="store.currentSlide"
        :current="store.currentSlideIndex"
        :total="store.slideCount"
        @prev="store.prevSlide"
        @next="store.nextSlide"
      />
      <ChatPanel
        :messages="store.chatHistory"
        :loading="store.loading"
        @send="handleChatSend"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePresentationStore } from '../stores/presentation'
import Toolbar from './Toolbar.vue'
import SlideList from './SlideList.vue'
import SlidePreview from './SlidePreview.vue'
import ChatPanel from './ChatPanel.vue'

const store = usePresentationStore()
const exporting = ref(false)

async function handleExport() {
  exporting.value = true
  try {
    await store.exportToPPTX()
  } finally {
    exporting.value = false
  }
}

function handleFullscreen() {
  const iframe = document.querySelector('.preview-iframe')
  if (iframe?.requestFullscreen) {
    iframe.requestFullscreen()
  }
}

async function handleChatSend(message) {
  await store.modify(message)
}
</script>

<style scoped>
.editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
```

- [ ] **Step 6: Verify full UI renders**

Run: `cd frontend && npm run dev`
Expected: Homepage at http://localhost:3000. Enter topic and generate (backend must be running). Editor shows three-panel layout with toolbar.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: add EditorView with Toolbar, SlideList, SlidePreview, ChatPanel components"
```

---

### Task 10: End-to-End Integration Test

**Files:**
- Create: `backend/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# backend/tests/test_integration.py
"""Integration test: generate → modify → verify slides exist."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.ppt_service import PPTService
import json


@pytest.fixture
def mock_llm():
    gen_response = json.dumps({"slides": [
        {"subtitle_top": "AI", "title": "人工智能", "subtitle": "未来已来", "author": "张三", "date": "2026"},
        {"section_title": "目录", "toc_1": "简介", "toc_2": "技术", "toc_3": "应用", "toc_4": "展望"},
        {"header_title": "简介", "title": "什么是AI", "body": "<p>AI是人工智能</p>"},
        {"header_title": "展望", "title": "AI未来", "body": "<p>AI将改变世界</p>"},
        {"thanks": "谢谢", "message": "感谢", "contact": "test"},
    ]})
    modify_response = '<!DOCTYPE html><html><body><h1 data-editable="title">修改后的标题</h1></body></html>'

    with patch("app.services.llm_service.call_llm_json", new_callable=AsyncMock, return_value=json.loads(gen_response)):
        with patch("app.services.llm_service.call_llm", new_callable=AsyncMock, return_value=modify_response):
            yield


@pytest.mark.asyncio
async def test_full_workflow(mock_llm):
    service = PPTService()

    # Step 1: Generate
    pres = await service.generate_with_ai("人工智能", "business-blue")
    assert pres.title == "人工智能"
    assert len(pres.slides) == 5
    cover = pres.slides[0]
    assert "人工智能" in cover.html_content

    # Step 2: Modify a slide
    modified = await service.modify_slide(
        pres.id, pres.slides[0].id,
        "把标题改成'AI革命'",
        [],
    )
    assert modified is not None
    assert modified.id == pres.slides[0].id
    # The modified HTML should contain the LLM's response
    assert "修改后的标题" in modified.html_content

    # Step 3: Verify persistence
    found = service.get_presentation(pres.id)
    assert found is not None
    assert found.slides[0].html_content == modified.html_content
```

- [ ] **Step 2: Run integration test**

Run: `cd backend && pytest tests/test_integration.py -v`
Expected: 1 passed

- [ ] **Step 3: Run all tests**

Run: `cd backend && pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_integration.py
git commit -m "test: add end-to-end integration test for generate → modify workflow"
```

---

## Self-Review Checklist

- **Spec coverage:** Each section in the design doc maps to a task:
  - System architecture → Tasks 1, 7 (scaffolding)
  - Frontend design (three-panel) → Task 9
  - HTML template system → Task 2
  - HTML→PPTX export → Task 5
  - API routes → Task 6
  - LLM integration → Task 3
  - PPT generation/modification → Task 4
  - HomePage → Task 8
  - Integration → Task 10
- **Placeholder scan:** No TBD/TODO found. All code blocks contain actual implementations.
- **Type consistency:** `Slide.id`, `Slide.html_content`, `Slide.page_number`, `Presentation.id` used consistently across all tasks.
