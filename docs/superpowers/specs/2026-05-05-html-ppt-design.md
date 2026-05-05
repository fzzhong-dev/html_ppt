# HTML_PPT 项目设计文档

## 概述

一个基于 HTML 的 PPT 生成与编辑工具。用户通过自然语言描述主题，AI 自动生成 HTML 幻灯片，用户在浏览器中以编辑器模式查看并通过对话修改内容，最终导出为 PPTX 文件。

**目标用户**：非技术人员（运营、销售等）
**核心价值**：比传统 PPT 工具更好看，比 AI PPT 工具更灵活可编辑

## 系统架构

```
用户浏览器 (Vue 前端)
    ↕ HTTP / WebSocket
Python 后端 (FastAPI)
    ↕ API 调用
┌─────────────┬──────────────┬──────────────┐
│ 大模型 API   │ Puppeteer    │ python-pptx  │
│ (多模型可切换)│ (HTML→截图)   │ (生成.pptx)  │
└─────────────┴──────────────┴──────────────┘
```

### 技术栈

- **前端**：Vue 3 + Vite
- **后端**：Python 3.10+ / FastAPI
- **AI**：支持多种大模型 API（ChatGPT / Claude / 智谱 / 通义千问等），可切换
- **HTML 渲染与截图**：Puppeteer（Node.js），后端通过子进程调用
- **PPTX 生成**：python-pptx

## 核心流程

```
1. 用户输入主题/大纲
2. AI 选择合适模板 + 生成幻灯片内容（HTML）
3. 前端渲染 HTML 幻灯片，以编辑器模式展示
4. 用户通过右侧对话面板发送修改指令
5. AI 解析指令，修改对应 HTML 内容
6. 前端实时刷新预览
7. 用户点击导出 → Puppeteer 逐页截图 → python-pptx 生成 .pptx
```

## 前端设计

### 布局结构（三栏）

```
┌──────────────────────────────────────────────────────┐
│ 工具栏：撤销/重做 | 页面管理 | 主题与样式 | 插入 | 导出  │
├──────┬─────────────────────────────┬─────────────────┤
│      │                             │                 │
│ 幻灯 │                             │    AI 对话      │
│ 片列 │     HTML 幻灯片预览区         │    面板         │
│ 表   │                             │                 │
│      │                             │                 │
├──────┴─────────────────────────────┴─────────────────┤
```

### 工具栏功能

| 分组 | 功能 |
|------|------|
| 撤销/重做 | 撤销、重做操作历史 |
| 页面管理 | 添加页、复制页、删除页、页面排序（拖拽） |
| 主题与样式 | 主题切换（商务蓝/简约绿/科技紫/中国红等）、配色方案、字体选择 |
| 插入元素 | 图片、图表、形状、图标 |
| 导出 | 导出 PPTX、全屏演示 |

### 右侧 AI 对话面板

- 聊天式界面，用户输入自然语言修改指令
- 支持的修改类型：修改文字内容、调整布局、更换配色/字体、添加/删除页面、插入图片/图表等
- AI 修改后自动刷新预览区

## HTML 模板系统

### 模板 + AI 变体策略

1. **预设模板库**：预先设计 5-10 套高质量 HTML 模板
   - 每套模板包含：封面页、目录页、内容页（多种布局）、结尾页
   - 模板使用标准 16:9 比例（1920×1080px）
   - 模板内定义可编辑区域（标题、正文、图片位等）

2. **AI 变体生成**：
   - AI 基于预设模板做变体：调整配色、字体、布局微调
   - 保持模板结构不变，只改变视觉风格
   - 确保生成结果视觉质量稳定

### 模板结构

每个模板是一个 HTML 文件，包含：
- CSS 样式（内联或 style 标签）
- 可编辑区域标记（data 属性，如 `data-editable="title"`, `data-editable="body"`）
- 固定布局结构

## HTML → PPTX 导出（截图嵌入法）

### 导出流程

```
1. 收集当前 PPT 所有页面的 HTML
2. 启动 Puppeteer，设置视口为 1920×1080
3. 逐页加载 HTML → 截图为 PNG（2x 分辨率，即 3840×2160，保证清晰度）
4. 使用 python-pptx 创建 PPTX：
   - 每页创建一个 slide
   - 将截图作为全尺寸图片填满幻灯片（10" × 5.63"，标准 16:9）
5. 返回 .pptx 文件供下载
```

### 限制

- 导出的 PPTX 中每页是一张图片，文字不可在 PowerPoint 中直接编辑
- 这是 MVP 的权衡：优先保证视觉还原度 100%
- 后续可迭代为混合方案（简单页面结构化转换，复杂页面截图）

## 后端 API 设计

### 主要接口

```
POST /api/ppt/generate          — 根据主题生成 PPT（返回幻灯片 HTML 列表）
POST /api/ppt/modify            — 根据对话指令修改指定页面的 HTML
POST /api/ppt/export            — 导出为 PPTX（触发截图 + 生成）
GET  /api/ppt/{id}              — 获取 PPT 信息
GET  /api/ppt/{id}/slides/{n}   — 获取指定页面的 HTML

GET  /api/templates             — 获取可用模板列表
GET  /api/templates/{id}        — 获取模板详情

POST /api/llm/chat              — 发送对话消息（流式返回）
GET  /api/llm/providers         — 获取可用的大模型列表
PUT  /api/llm/provider          — 切换当前使用的大模型
```

### 数据模型

```python
class Presentation:
    id: str
    title: str
    template_id: str
    theme: str                    # 当前主题/配色
    slides: list[Slide]
    created_at: datetime
    updated_at: datetime

class Slide:
    id: str
    page_number: int
    html_content: str             # 完整的 HTML 内容
    editable_regions: dict        # 可编辑区域映射
```

## 大模型集成

### 多模型适配

设计统一的 LLM 接口，各模型实现自己的适配器：

```python
class LLMProvider(ABC):
    async def chat(self, messages: list[dict], stream: bool = False) -> AsyncGenerator[str, None]

class OpenAIProvider(LLMProvider): ...
class ClaudeProvider(LLMProvider): ...
class ZhipuProvider(LLMProvider): ...
class QwenProvider(LLMProvider): ...
```

### Prompt 策略

AI 在生成和修改 HTML 时使用的 Prompt 策略：

1. **生成阶段**：提供模板结构 + 用户主题 → AI 填充内容（保持 HTML 结构不变）
2. **修改阶段**：提供当前 HTML + 用户修改指令 → AI 返回修改后的 HTML diff
3. **约束**：AI 只能修改可编辑区域的内容，不能破坏模板结构

## 目录结构

```
HTML_PPT/
├── frontend/                  # Vue 3 前端
│   ├── src/
│   │   ├── components/        # 组件
│   │   │   ├── Editor.vue     # 主编辑器（三栏布局）
│   │   │   ├── Toolbar.vue    # 工具栏
│   │   │   ├── SlideList.vue  # 左侧幻灯片列表
│   │   │   ├── Preview.vue    # 中间预览区
│   │   │   ├── ChatPanel.vue  # 右侧对话面板
│   │   │   └── ...
│   │   ├── stores/            # Pinia 状态管理
│   │   └── api/               # API 调用封装
│   └── ...
├── backend/                   # Python 后端
│   ├── app/
│   │   ├── main.py            # FastAPI 入口
│   │   ├── api/               # API 路由
│   │   ├── services/          # 业务逻辑
│   │   │   ├── ppt_service.py # PPT 生成/修改
│   │   │   ├── export_service.py  # PPTX 导出
│   │   │   └── llm_service.py # 大模型调用
│   │   ├── llm/               # 大模型适配器
│   │   │   ├── base.py
│   │   │   ├── openai_provider.py
│   │   │   ├── claude_provider.py
│   │   │   ├── zhipu_provider.py
│   │   │   └── qwen_provider.py
│   │   └── models/            # 数据模型
│   └── ...
├── templates/                 # HTML 模板库
│   ├── business-blue/
│   ├── minimal-green/
│   ├── tech-purple/
│   └── chinese-red/
├── scripts/                   # 工具脚本
│   └── screenshot.js          # Puppeteer 截图脚本
└── docs/                      # 文档
```

## MVP 范围

### 第一期（MVP）

- [x] 3-5 套预设模板（含封面、目录、内容、结尾页）
- [x] 输入主题生成完整 PPT
- [x] 编辑器模式展示（三栏布局）
- [x] AI 对话修改（文字内容、简单布局调整）
- [x] 导出 PPTX（截图嵌入法）
- [x] 支持至少 2 个大模型（如智谱 + ChatGPT）

### 后续迭代

- [ ] 更多模板（10+）
- [ ] 混合导出方案（简单页面结构化转换，可编辑文字）
- [ ] 插入图表功能
- [ ] 协作编辑
- [ ] 模板市场（用户自定义模板）
