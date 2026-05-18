# AI 智能演示文稿生成与编辑平台

## 项目概述

一个基于 AI 驱动的在线 PPT 生成与编辑平台。用户输入主题或大纲，系统调用大语言模型自动生成完整的 HTML 格式演示文稿，支持在线可视化编辑、AI 对话式修改，并可导出为标准 PPTX 文件。

**项目规模**：56 个源文件，约 6200 行代码

---

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         Vue 3 + Pinia + Vite + Axios             │
│     (首页 / 编辑器 / 幻灯片预览 / AI 对话)        │
└──────────────────────┬──────────────────────────┘
                       │ HTTP / SSE (Server-Sent Events)
┌──────────────────────▼──────────────────────────┐
│                   Backend                        │
│           FastAPI + Pydantic + Uvicorn           │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ API 路由  │  │ 业务服务层 │  │ LLM 服务层   │  │
│  └──────────┘  └───────────┘  └──────────────┘  │
│  ┌──────────────────────────────────────────┐    │
│  │    多 LLM Provider 适配层 (策略模式)      │    │
│  │  OpenAI / DeepSeek / 智谱 / 通义 / Claude │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                Export Pipeline                    │
│        Puppeteer 截图 + python-pptx 合成          │
└─────────────────────────────────────────────────┘
```

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.5 | 核心框架，Composition API + `<script setup>` |
| Pinia | 3.0 | 状态管理（幻灯片数据、撤销/重做栈、聊天记录） |
| Vue Router | 4.6 | 页面路由（首页 / 编辑器视图切换） |
| Axios | 1.16 | HTTP 请求 |
| Vite | 8.0 | 构建工具与开发服务器 |
| SSE (EventSource) | - | 流式数据传输，实时接收 AI 生成的幻灯片 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 后端开发语言 |
| FastAPI | 0.115 | Web 框架，提供 RESTful API |
| Pydantic | 2.9 | 数据校验与序列化模型 |
| Uvicorn | 0.30 | ASGI 服务器 |
| httpx | 0.27 | 异步 HTTP 客户端（调用 LLM API） |
| python-pptx | 1.0 | PPTX 文件生成 |
| Puppeteer | - | Node.js 无头浏览器，HTML 截图 |

### AI / LLM 集成

| Provider | 模型 | SDK |
|----------|------|-----|
| OpenAI | GPT-4o | openai 1.47 |
| DeepSeek | DeepSeek-chat | 自定义 HTTP 适配器 |
| 智谱 AI | GLM-4 | zhipuai 2.1 |
| 通义千问 | Qwen-max | dashscope 1.20 |
| Anthropic | Claude Sonnet | anthropic 0.34 |

---

## 核心功能模块

### 1. AI 演示文稿生成

**流程**：主题输入 → 大纲规划 → 主题风格生成 → 逐页幻灯片生成 → 渲染预览

- **大纲生成**：支持用户自定义大纲或 AI 自动规划，流式输出并逐步展示
- **主题风格**：LLM 生成 CSS 主题 JSON（配色、字体、间距），编译为 CSS 变量
- **幻灯片生成**：每页独立生成 HTML，基于 1920×1080 画布，内联 SVG 图表，无外部依赖
- **创意模式 / 保守模式**：两套 Prompt 策略，创意模式追求视觉多样性，保守模式偏重商务规范

### 2. 三栏式在线编辑器

- **左侧**：幻灯片缩略图列表，支持拖拽排序、增删复制
- **中间**：幻灯片预览区，支持三种模式切换
  - 预览模式：只读浏览
  - 可视化编辑模式：所见即所得，直接在 iframe 中编辑
  - 代码编辑模式：直接编辑 HTML 源码
- **右侧**：AI 对话面板，通过自然语言指令修改幻灯片内容与样式

### 3. AI 对话式修改

- 用户在对话面板输入修改指令（如"把第三页的背景改为蓝色"、"增加一页总结"）
- 系统将当前幻灯片 HTML、上下文信息、历史对话一同发送给 LLM
- LLM 返回修改后的 HTML 片段，前端自动更新渲染

### 4. 幻灯片放映

- 全屏演示模式，支持键盘导航（方向键翻页，ESC 退出）
- 缩放控制：适应屏幕 / 25%–400% 手动缩放
- 页面过渡动画（淡入淡出、滑动）

### 5. PPTX 导出

- **两阶段流水线**：
  1. Puppeteer 无头浏览器对每页 HTML 截图（1920×1080 @ 2x 分辨率）
  2. python-pptx 将截图组装为标准 .pptx 文件
- 每页幻灯片作为高清图片嵌入，确保导出效果与在线预览一致

### 6. 撤销/重做系统

- 基于 Pinia Store 的快照栈，支持最多 50 步历史记录
- 每次编辑、AI 修改、页面操作均自动保存快照

---

## 项目结构

```
HTML_PPT/
├── frontend/                     # 前端项目
│   └── src/
│       ├── components/           # Vue 组件
│       │   ├── HomePage.vue      # 首页（主题输入表单）
│       │   ├── EditorView.vue    # 编辑器主视图
│       │   ├── SlidePreview.vue  # 幻灯片预览（三模式）
│       │   ├── SlideThumbnail.vue # 缩略图组件
│       │   └── ChatPanel         # AI 对话面板
│       ├── stores/
│       │   └── presentation.js   # Pinia 状态管理（核心 Store）
│       ├── api/
│       │   └── index.js          # API 请求封装（含 SSE 流式）
│       └── utils/                # 工具函数
│
├── backend/                      # 后端项目
│   └── app/
│       ├── main.py               # FastAPI 入口
│       ├── config.py             # 环境配置（多 LLM Key 管理）
│       ├── models.py             # Pydantic 数据模型
│       ├── api/                  # API 路由层
│       │   ├── ppt.py            # PPT 相关接口
│       │   ├── templates.py      # 模板接口
│       │   └── llm.py            # LLM 状态接口
│       ├── services/             # 业务逻辑层
│       │   ├── ppt_service.py    # PPT 生成、修改、大纲
│       │   ├── llm_service.py    # LLM 调用与 Provider 降级
│       │   ├── export_service.py # 导出流水线
│       │   ├── theme_compiler.py # 主题 JSON → CSS 编译
│       │   ├── layout_prompts.py # Prompt 工程（创意/保守）
│       │   ├── slide_html.py     # HTML 生成与校验
│       │   └── editable_html.py  # 可编辑区域处理
│       ├── llm/                  # LLM Provider 适配层
│       │   ├── base.py           # 抽象基类
│       │   ├── openai_provider.py
│       │   ├── deepseek_provider.py
│       │   ├── claude_provider.py
│       │   ├── zhipu_provider.py
│       │   └── qwen_provider.py
│       └── tests/                # 18 个测试文件
│
├── templates/                    # HTML 幻灯片模板
│   └── business-blue/            # 商务蓝主题模板
└── scripts/                      # Puppeteer 截图脚本
```

---

## 关键技术实现

### 多 LLM Provider 策略模式

采用策略模式（Strategy Pattern）适配 5 家 LLM 供应商，统一抽象接口，支持运行时动态切换与自动降级：

```
用户请求 → LLMService.resolve_provider() → 检查首选 Provider
    ↓ 不可用
    自动降级：DeepSeek → OpenAI → 智谱 → 通义 → Claude
    ↓ 全部不可用
    返回错误提示
```

- 每个 Provider 继承 `BaseLLMProvider`，实现 `generate()` / `stream()` 方法
- 降级过程有日志记录，便于排查 API 额度/网络问题

### 流式生成架构（SSE）

- 后端通过 FastAPI 的 `StreamingResponse` 以 SSE 协议推送数据
- 前端使用 `EventSource` 接收，基于换行符的缓冲解析处理不完整数据包
- 大纲规划和幻灯片生成均支持流式输出，用户可实时看到生成进度

### Prompt 工程

两套 Prompt 策略应对不同场景：

| 策略 | 适用场景 | 特点 |
|------|----------|------|
| 创意模式 | 产品展示、创意提案 | 鼓励视觉多样性，允许突破模板限制 |
| 保守模式 | 商务汇报、正式场合 | 干净规范，偏重品牌一致性 |

Prompt 技术要点：
- 分阶段生成（主题风格 → 大纲 → 逐页内容），降低单次生成复杂度
- JSON Schema 约束输出格式，后端做容错解析（处理 Markdown 围栏、多余文本）
- 技术约束内嵌 Prompt（画布尺寸、禁止外部资源、内联 SVG 等）

### 主题编译器

LLM 输出的主题 JSON（配色、字体、间距）通过 `ThemeCompiler` 编译为 CSS 变量：

```json
{ "palette": { "primary": "#1a3a5c", "accent": "#e8b84b" }, ... }
```
↓ 编译为
```css
:root { --palette-primary: #1a3a5c; --palette-accent: #e8b84b; ... }
```

### 前端状态管理

核心 Store（`presentation.js`）管理：
- `slides[]`：幻灯片数组，每项包含 HTML 内容与可编辑区域
- `undoStack[]` / `redoStack[]`：快照式撤销/重做（上限 50 步）
- `chatHistory[]`：AI 对话记录（上限 50 条）
- `generationProgress`：生成进度状态

---

## API 接口设计

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/ppt/generate` | 生成完整演示文稿 |
| POST | `/api/ppt/generate/stream` | 流式生成（SSE） |
| POST | `/api/ppt/modify` | AI 修改指定幻灯片 |
| POST | `/api/ppt/outline` | 生成大纲 |
| POST | `/api/ppt/outline/stream` | 流式生成大纲（SSE） |
| POST | `/api/ppt/export` | 导出 PPTX |
| GET | `/api/ppt/{id}` | 获取演示文稿详情 |
| PUT | `/api/ppt/{id}/slides/{num}` | 更新幻灯片 HTML |
| GET | `/api/templates` | 获取模板列表 |
| GET | `/api/llm/providers` | 获取 LLM 供应商状态 |

---

## 可能的面试问题准备

### Q: 为什么选择 HTML 而不是直接生成 PPTX？

传统 PPTX 的布局能力有限，HTML+CSS 提供更强大的视觉表现力（渐变、动画、复杂布局）。用户在线编辑体验更好，最终导出时通过 Puppeteer 截图保证视觉一致性。

### Q: 多 LLM 降级策略是怎么设计的？

策略模式 + 责任链。`LLMService.resolve_provider()` 按优先级依次检查各 Provider 的 API Key 配置是否完整，返回第一个可用的。调用失败时自动切换到下一个 Provider，并记录日志。

### Q: 流式生成怎么实现的？

后端用 FastAPI 的 `StreamingResponse` 配合 `async generator`，前端用 `EventSource` 接收 SSE 事件。关键难点在于处理不完整的数据包——基于换行符做缓冲拼接，确保 JSON 完整后再解析。

### Q: 撤销/重做怎么实现的？

Pinia Store 维护两个栈：`undoStack` 和 `redoStack`。每次修改前将当前 `slides` 数组深拷贝推入 `undoStack`，撤销时从栈顶弹出恢复，同时将当前状态推入 `redoStack`。限制 50 步防止内存溢出。

### Q: Prompt 工程有哪些技巧？

1. **分阶段生成**：主题 → 大纲 → 逐页，降低单次 LLM 调用的复杂度和出错率
2. **技术约束内嵌**：画布尺寸、禁止外部资源等硬约束直接写入 Prompt
3. **JSON Schema 约束输出**：减少解析失败率，后端做容错处理
4. **双策略 Prompt**：创意/保守两套 Prompt，同一套代码适配不同场景

### Q: 前端架构有什么亮点？

1. **Pinia 集中状态管理**：幻灯片、聊天、撤销栈统一管理，组件间通信清晰
2. **iframe 沙箱渲染**：幻灯片在独立 iframe 中渲染，样式隔离，编辑不影响主界面
3. **三种编辑模式无缝切换**：预览/可视化/代码，共享同一份 HTML 数据源
4. **SSE 流式更新**：生成过程中逐页追加，用户体验流畅
