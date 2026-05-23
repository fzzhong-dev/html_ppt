# 五大核心功能优化实施计划

## Context

当前产品与市面 AI PPT 产品（Gamma、讯飞智文、百度文库）差距明显。按优先级实施 5 件事：
1. 10-20 个高质量模板 + 模板选择 UI
2. 持久化存储 + 自动保存
3. 可编辑 PPTX 导出（原生文本框）
4. "重新生成"按钮 + 风格选择器
5. 拖拽排序 + 幻灯片浏览视图

---

## P0：模板库 + 模板选择 UI

### 后端：新建 12 个模板

在 `templates/` 目录下新增 12 个主题模板（每个含 cover.html, toc.html, content-text.html, content-image-text.html, ending.html）：

| 模板 ID | 风格 | 配色 |
|---------|------|------|
| business-blue | 商务蓝 | 深蓝+白 |
| tech-gradient | 科技渐变 | 深紫+蓝渐变 |
| minimal-white | 极简白 | 黑+白+灰 |
| dark-pro | 深色专业 | 深灰+橙accent |
| nature-green | 自然绿 | 绿+米白 |
| warm-orange | 暖橙活力 | 橙+深棕 |
| elegant-purple | 优雅紫 | 紫+淡金 |
| academic-navy | 学术深蓝 | 海军蓝+金 |
| creative-pink | 创意粉 | 粉+深灰 |
| vintage-paper | 复古纸 | 米黄+深棕 |
| fresh-cyan | 清新青 | 青+白 |
| bold-red | 大胆红 | 红+黑 |

每个模板的 HTML 复用 business-blue 的结构，只改配色和装饰元素。新建文件：
- `templates/{id}/cover.html`
- `templates/{id}/toc.html`
- `templates/{id}/content-text.html`
- `templates/{id}/content-image-text.html`
- `templates/{id}/ending.html`

### 后端：模板缩略图

在 `backend/app/api/templates.py` 添加缩略图生成：每个模板返回 `cover.html` 的 base64 缩略图（在首次请求时通过 Puppeteer 截图并缓存）。

简化方案：直接在模板目录放一个 `thumbnail.png`（用脚本批量生成），`list_templates()` 返回缩略图 URL。

**更实际的方案**：在 `list_templates()` 返回时直接读取 cover.html 的内容，前端用 iframe 渲染缩略图（复用现有 SlideThumbnail 组件的模式）。

### 后端：修改模板 API

**文件：`backend/app/services/template_service.py`**
- `list_templates()` 增加 `cover_html` 字段（读取 cover.html 内容）

**文件：`backend/app/api/templates.py`**
- `GET /templates/` 返回含 cover_html 的列表

### 前端：首页添加模板选择器

**文件：`frontend/src/components/HomePage.vue`**

在主题输入框之前，添加模板选择区域：
```
[模板选择] ← 可视化网格，3列4行
┌──────┐ ┌──────┐ ┌──────┐
│ 商务蓝 │ │科技渐变│ │极简白 │
│ [缩略] │ │ [缩略] │ │ [缩略] │
└──────┘ └──────┘ └──────┘
┌──────┐ ┌──────┐ ┌──────┐
│ ...   │ │ ...   │ │ ...   │
```

- 选中模板高亮（橙色边框，复用现有 `--oo-accent-orange`）
- 默认选中"商务蓝"
- 点击模板 → 设置 `selectedTemplate` ref
- 不选模板则默认使用 AI 自由生成（当前行为）

**文件：`frontend/src/api/index.js`**
- 已有 `listTemplates()` 和 `getTemplate()`，无需修改

### 前端 → 后端：传递模板 ID

**文件：`frontend/src/stores/presentation.js`**
- `generate()` 方法添加 `templateId` 参数

**文件：`frontend/src/api/index.js`**
- `generatePPTStream()` 和 `generatePPT()` 添加 `template_id` 参数

**文件：`backend/app/models.py`**
- `GenerateRequest` 已有 `template_id: Optional[str] = None`

**文件：`backend/app/services/ppt_service.py`**
- `generate_slides_streaming()` 和 `generate_with_ai()` 接收 `template_id`
- 如果指定了模板：用模板 HTML 作为各页基础，LLM 只填充内容
- 如果未指定：当前行为（纯 AI 生成）

### 关键文件

| 文件 | 变更 |
|------|------|
| `templates/{12个目录}/*.html` | **新建** 12×5=60 个模板 HTML |
| `backend/app/services/template_service.py` | 修改 list_templates 返回 cover_html |
| `frontend/src/components/HomePage.vue` | 添加模板选择网格 UI |
| `frontend/src/stores/presentation.js` | generate() 传递 templateId |
| `backend/app/services/ppt_service.py` | 支持基于模板生成 |

---

## P0：持久化存储 + 自动保存

### 方案：SQLite + aiosqlite（零配置，无需外部数据库）

### 后端：添加依赖

**文件：`backend/requirements.txt`**
- 添加 `aiosqlite>=0.20.0`

### 后端：新建数据库模块

**新建：`backend/app/services/db.py`**

```python
# SQLite 数据库管理
# 表: presentations (id, title, template_id, theme, theme_data JSON, created_at, updated_at)
# 表: slides (id, presentation_id, page_number, html_content, editable_regions JSON)
# 启动时自动创建表
```

### 后端：修改 PPTService

**文件：`backend/app/services/ppt_service.py`**
- `create_presentation()` → 同时写入 DB
- `get_presentation()` → 先查内存，再查 DB
- `update_slide_html()` → 更新内存 + DB
- `delete_slide_by_id()` → 删除内存 + DB
- `insert_slide_html()` → 插入内存 + DB
- `generate_slides_streaming()` yield 后写入 DB

添加 `save_presentation()` 和 `_persist_slide()` 内部方法。

### 前端：自动保存

**文件：`frontend/src/stores/presentation.js`**
- 在 `patchCurrentSlideHtml()` 后自动 debounce 保存
- 添加 `autoSaveTimer` 和 `savePresentation()` 方法
- 在 `onMounted` 时启动自动保存定时器（每 30 秒检查是否有未保存变更）

### 关键文件

| 文件 | 变更 |
|------|------|
| `backend/app/services/db.py` | **新建** SQLite 持久化 |
| `backend/requirements.txt` | 添加 aiosqlite |
| `backend/app/services/ppt_service.py` | 所有写入操作同步到 DB |
| `frontend/src/stores/presentation.js` | 添加自动保存 |

---

## P1：可编辑 PPTX 导出

### 方案：HTML 内容解析 + python-pptx 原生对象

### 后端：新建 HTML 解析器

**新建：`backend/app/services/html_to_pptx.py`**

解析 HTML 幻灯片内容，提取结构化数据：
1. 用 BeautifulSoup 解析 HTML
2. 提取背景色/渐变（从 body 或 .ppt-page 的 style）
3. 提取标题（h1/h2/h3 → 文本框）
4. 提取正文段落（p → 文本框）
5. 提取列表项（li → 文本框）
6. 提取内联 SVG → 导出为图片或跳过
7. 返回结构化 slide_elements 列表

### 后端：修改导出服务

**文件：`backend/app/services/export_service.py`**

新增方法 `export_to_pptx_native()`:
1. 对每张幻灯片调用 HTML 解析器
2. 创建 python-pptx Presentation
3. 对每张幻灯片：
   - 设置背景色（如 HTML 有背景）
   - 添加标题文本框（映射字体/颜色/大小）
   - 添加正文文本框
   - 复杂布局 fallback 到截图
4. 保存 PPTX

策略：
- 简单页面（标题+正文）→ 原生文本框
- 复杂页面（SVG图表、复杂CSS布局）→ 截图 fallback
- 提供两个导出按钮："导出(可编辑)" 和 "导出(高清截图)"

### 后端依赖

**文件：`backend/requirements.txt`**
- 添加 `beautifulsoup4>=4.12`

### 关键文件

| 文件 | 变更 |
|------|------|
| `backend/app/services/html_to_pptx.py` | **新建** HTML 解析为 PPTX 原生对象 |
| `backend/app/services/export_service.py` | 添加原生导出方法 |
| `backend/requirements.txt` | 添加 beautifulsoup4 |

---

## P1："重新生成"按钮 + 风格选择器

### 前端：重新生成当前页

**文件：`frontend/src/components/Toolbar.vue`**
- 在"开始"选项卡的"幻灯片"组添加"重新生成"按钮
- 触发时调用 store 的 `regenerateSlide()` 方法

**文件：`frontend/src/stores/presentation.js`**
- 新增 `regenerateSlide()` 方法：
  1. 保存当前快照（undo）
  2. 调用 `/api/ppt/modify`，指令为"重新生成本页内容，保持相同主题和风格"
  3. 或调用专门的 regenerate API endpoint

### 后端：重新生成 API

**文件：`backend/app/api/ppt.py`**
- 新增 `POST /api/ppt/{id}/slides/{number}/regenerate`
- 读取当前幻灯片的主题信息（从 theme_data 或相邻页推断）
- 调用 LLM 重新生成该页 body fragment
- 用相同 theme_css 拼装

### 前端：风格选择器

**文件：`frontend/src/components/HomePage.vue`**
- 在模板选择器下方添加"生成风格"选择器：
  ```
  ○ 创意模式（当前默认）
  ○ 商务专业
  ○ 学术严谨
  ○ 极简设计
  ○ 活泼创意
  ```
- 替换当前的 checkbox "创意模式"
- 传给后端 `style` 参数

### 后端：风格参数

**文件：`backend/app/models.py`**
- `GenerateRequest` 添加 `style: Optional[str] = "creative"`

**文件：`backend/app/services/ppt_service.py`**
- `_generate_theme()` 接收 style 参数，在 prompt 中加入风格描述
- `_generate_single_slide_fragment()` 同理

### 关键文件

| 文件 | 变更 |
|------|------|
| `frontend/src/components/Toolbar.vue` | 添加"重新生成"按钮 |
| `frontend/src/stores/presentation.js` | 添加 regenerateSlide() |
| `frontend/src/components/HomePage.vue` | 风格选择器替代 checkbox |
| `backend/app/api/ppt.py` | 新增 regenerate endpoint |

---

## P2：拖拽排序 + 幻灯片浏览视图

### 前端：安装拖拽库

**安装：** `npm install vuedraggable@next`（Vue 3 兼容的 SortableJS 封装）

### 前端：SlideList 支持拖拽

**文件：`frontend/src/components/SlideList.vue`**
- 用 `<draggable>` 组件替换当前 `v-for` 的 `.slide-strip`
- `@end` 事件触发 `reorderSlides(oldIndex, newIndex)`
- 拖拽手柄：整个卡片可拖拽

### 前端：Store 添加排序方法

**文件：`frontend/src/stores/presentation.js`**
- 新增 `reorderSlides(oldIndex, newIndex)` 方法：
  1. 保存快照（undo）
  2. `array.splice` 移动元素
  3. `_renumber()` 重排页码
  4. 调用后端同步

### 后端：排序 API

**文件：`backend/app/api/ppt.py`**
- 新增 `PUT /api/ppt/{id}/slides/reorder`
- body: `{ "order": ["slide-id-3", "slide-id-1", "slide-id-2"] }`

### 前端：幻灯片浏览视图

**文件：`frontend/src/components/EditorView.vue`**
- 在"视图"选项卡添加"浏览视图"按钮
- 浏览视图：隐藏编辑区和聊天面板，显示所有幻灯片的网格布局
- 每个缩略图可点击进入编辑

**新建：`frontend/src/components/SlideGridView.vue`**
- 网格展示所有幻灯片（4列）
- 支持拖拽排序（复用 vuedraggable）
- 双击进入编辑
- 右键菜单（删除、复制）

### 关键文件

| 文件 | 变更 |
|------|------|
| `frontend/package.json` | 添加 vuedraggable@next |
| `frontend/src/components/SlideList.vue` | 用 draggable 替换 v-for |
| `frontend/src/stores/presentation.js` | 添加 reorderSlides() |
| `frontend/src/components/SlideGridView.vue` | **新建** 网格浏览视图 |

---

## 实施顺序

1. **P0-模板库** — 新建模板文件 → 修改 template_service → 首页 UI → 传递 template_id 到后端
2. **P0-持久化** — 新建 db.py → 修改 ppt_service → 前端自动保存
3. **P1-可编辑导出** — 新建 html_to_pptx.py → 修改 export_service → 添加导出按钮
4. **P1-重新生成+风格** — 后端 regenerate API → 前端按钮 → 首页风格选择器
5. **P2-拖拽排序** — 安装 vuedraggable → 修改 SlideList → 新建 SlideGridView

## 验证方案

1. 模板库：首页看到 13 个模板缩略图，选择后生成对应风格 PPT
2. 持久化：生成 PPT → 重启后端 → 刷新页面 → 演示文稿仍在
3. 导出：导出 PPTX → 用 PowerPoint 打开 → 文字可编辑
4. 重新生成：编辑器中点"重新生成" → 当前页内容刷新，风格保持
5. 拖拽：拖动缩略图改变顺序 → 页码正确更新
