---
title: HTML PPT Generator
emoji: 📊
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# HTML PPT Generator

输入主题，AI 自动生成专业演示文稿，支持实时编辑和导出 PPTX。

## 功能特性

- **AI 一键生成** — 输入主题，自动规划大纲并逐页生成专业 HTML 幻灯片，实时流式输出
- **多 LLM 支持** — DeepSeek、智谱 GLM、通义千问、OpenAI、Claude，可切换
- **流式生成进度** — 逐页生成并实时展示进度，无需等待全部完成
- **所见即所得编辑** — 内置富文本编辑器，可直接修改幻灯片内容和样式
- **AI 辅助修改** — 通过自然语言指令修改单页（如"添加柱状图"、"改为深蓝色渐变"）
- **在线图片搜索** — 集成 Pexels + Unsplash 图库，一键搜索插入配图
- **PPTX 导出** — 基于 Puppeteer 高清截图，导出标准 PowerPoint 文件
- **多主题配色** — AI 自动生成配色方案（科技蓝、商务绿、创意橙等），全篇风格统一
- **丰富布局** — 封面页、目录页、要点页、数据图表页、对比页、时间线页等多种版式
- **免费部署** — 支持部署到 Hugging Face Spaces（完全免费，无需服务器）

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Pinia + Vite |
| 后端 | FastAPI + Uvicorn |
| LLM | DeepSeek / 智谱 GLM / 通义千问 / OpenAI / Claude |
| 截图导出 | Puppeteer + Chromium |
| 图片搜索 | Pexels API + Unsplash API |
| 容器化 | Docker 多阶段构建 + Nginx 反代 |

## 快速开始

### 本地开发

**1. 克隆项目**

```bash
git clone https://github.com/your-username/html-ppt.git
cd html-ppt
```

**2. 启动后端**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

编辑 `backend/.env`，至少配置一个 LLM 密钥：

```ini
DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key
```

启动后端服务：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. 启动前端**

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用。

> 开发时前端 Vite 已配置 `/api` 代理到后端 8000 端口，无需额外配置。

### 配置说明

所有配置通过 `backend/.env` 文件或环境变量注入：

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `DEFAULT_PROVIDER` | LLM 提供商：`deepseek` / `zhipu` / `qwen` / `openai` / `claude` | 是 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 至少配一个 |
| `ZHIPU_API_KEY` | 智谱 AI 密钥 | 否 |
| `PEXELS_API_KEY` | Pexels 图片搜索密钥（[免费申请](https://www.pexels.com/api/)） | 否（推荐） |
| `UNSPLASH_ACCESS_KEY` | Unsplash 图片搜索密钥（[免费申请](https://unsplash.com/developers)） | 否 |

## 部署

### Hugging Face Spaces（免费，推荐）

无需服务器，一键部署到 HF Docker Space：

1. 在 [huggingface.co](https://huggingface.co) 创建 Docker Space
2. 推送代码到 Space 仓库
3. 在 Settings → Secrets 中配置 API 密钥
4. 自动构建启动，访问 `https://your-username-html-ppt.hf.space`

详细步骤见 [Hugging Face 部署指南](docs/deployment-huggingface.md)。

### 传统服务器

使用 Nginx + PM2/Systemd 部署，支持 HTTPS 和自定义域名。

详细步骤见 [服务器部署指南](docs/deployment-guide.md)。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ppt/outline-stream` | AI 生成大纲（SSE 流式） |
| POST | `/api/ppt/generate-stream` | AI 生成幻灯片（SSE 流式，逐页输出） |
| POST | `/api/ppt/generate` | AI 生成幻灯片（一次性返回） |
| POST | `/api/ppt/modify` | AI 修改指定幻灯片 |
| PATCH | `/api/ppt/{id}/slide-html` | 直接更新幻灯片 HTML |
| POST | `/api/ppt/{id}/slides` | 插入新幻灯片 |
| POST | `/api/ppt/{id}/delete-slide` | 删除幻灯片 |
| POST | `/api/ppt/export` | 导出 PPTX |
| GET | `/api/images/search` | 搜索图片 |
| GET | `/api/images/proxy` | 图片代理（绕过 CORS） |
| GET | `/api/llm/status` | 查看 LLM 配置状态 |
| GET | `/api/health` | 健康检查 |

## 项目结构

```
html-ppt/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI 路由（ppt, llm, images, templates）
│   │   ├── services/         # 业务逻辑（PPT 生成、LLM 调用、图片搜索）
│   │   ├── models.py         # 数据模型
│   │   ├── config.py         # 配置管理（pydantic-settings）
│   │   └── main.py           # FastAPI 入口
│   ├── screenshots/          # 截图临时目录
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # Vue 组件
│   │   │   ├── HomePage.vue        # 首页（主题输入）
│   │   │   ├── EditorView.vue      # 编辑器主界面
│   │   │   ├── ChatPanel.vue       # AI 修改面板
│   │   │   ├── ImageSearchPanel.vue # 图片搜索面板
│   │   │   ├── Toolbar.vue         # 工具栏
│   │   │   └── SlideList.vue       # 幻灯片缩略图列表
│   │   ├── stores/           # Pinia 状态管理
│   │   └── api/              # API 请求封装
│   └── package.json
├── scripts/
│   └── screenshot.js         # Puppeteer 截图脚本（用于 PPTX 导出）
├── templates/                # PPT 模板
├── deploy/
│   ├── nginx.conf            # 生产环境 Nginx 配置
│   └── start.sh              # Docker 容器启动脚本
├── docs/                     # 部署文档
├── Dockerfile                # 多阶段 Docker 构建
└── README.md
```

## License

MIT