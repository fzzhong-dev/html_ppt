"""Layout/design prompt fragments: technical constraints vs aesthetic guidance."""

# Hard limits: canvas, overflow, security — keep outputs usable and safe.
LAYOUT_TECH = """
## 技术边界（必须遵守）

### 画布与可读性
- 画布固定为 **1920×1080 CSS 像素**：body 使用 width:1920px;height:1080px;margin:0;overflow:hidden;box-sizing:border-box。
- 所有正文须在画布内完整可读：flex/grid 承载长文本的子容器请加 **min-width:0**（或合理 max-width）；必要时标题使用 **text-overflow:ellipsis**。
- 长单词、URL：容器侧使用 **overflow-wrap:anywhere** 或 **word-break:break-word**，避免横向撑破版面。
- 不要用巨幅偏移把主要内容挤出可视区；图表轴标签过长时请缩写或换行。

### 安全与资源
- **禁止**外链脚本、iframe、依赖网络的图片 URL。
- **配图**：若需配图，使用 `<img src="/api/images/proxy?url=编码后的图片地址" />` 格式（通过后端代理加载）；或使用内联 SVG、CSS 渐变、几何色块。
- 若页面需要数据图形，**仅使用内联 SVG**，禁止使用外部图表库或脚本驱动的图表。
"""

# Creative default: diversity, no emoji wallpaper, charts only when justified.
LAYOUT_CREATIVE = """
## 美学与多样性（大胆发挥，禁止「同一套淘宝模板」感）

### 版式反套路（最高优先级）
**禁止连续出现相同版式结构。** 以下每种模式在整个演示文稿中最多使用 2 次：
- ❌ 禁止默认套路：顶部标题 + 下方 3-4 个等宽圆角卡片 + 每个卡片内放图标+文字
- ❌ 禁止每页都用 flex 横排 2-3 列等分布局
- ❌ 禁止所有正文页都是「大标题 + 要点列表」的同一骨架

**推荐的高差异版式库（每页从中选不同的）：**
1. 全出血大图/渐变背景 + 居中大字核心论点（极简海报式）
2. 左右严格分栏（一侧色块/图案，一侧密集文字）
3. 上下分区（顶部宽色带标题 + 底部多段正文）
4. 杂志排版（多列不等宽，穿插引用块和侧边注）
5. 时间线/流程（纵向或横向带连接线的步骤展示）
6. 对照表/矩阵（用表格或网格做对比，无边框极简线条风格）
7. 数据焦点页（一个核心大数字 + 简短说明 + 小型 SVG 图表）
8. 引用块式（大面积留白 + 居中引用文字 + 署名线）
9. 卡片瀑布流（不等高、不等宽，错落排布）
10. 全文字排版（纯靠字重、字号层级和留白区分，零装饰元素）

每页必须声明自己用了哪种版式思路，避免无意识地重复。

### 气质与色彩
- **由主题自拟**调色与字体气质（科技 / 人文 / 童趣 / 高冷极简 / 复古印刷风等均可）；不必套用固定「企业五色盘」。
- 全稿可有统一的叙事气质，但**允许**章节之间有轻微的色相或密度变化，避免每张都像复制粘贴。

### 图标与符号
- **默认不要**在列表项、标题旁堆砌装饰性 Emoji 或 Unicode 符号。
- 若语义上确实需要（例如步骤序号、单一警示点），**少量**即可；**多数页面应为纯排版**（字重、间距、分割线、几何块面）。

### 数据图（SVG）
- **仅当本页确有数值、比例、趋势或结构化对比**时再画内联 SVG；样式自定（不必圆角柱、渐变填充或固定网格线样式）。
- 无合适数据时，用精炼文字、对照列表、引用块等完成叙事，**禁止无病呻吟式图表**。

### 内容充实度
- 每页正文内容必须充实：至少 2-3 段阐述或 5+ 个要点，不要只有标题 + 一句话。
- 文字密度与版式要匹配：极简版式页可以有少量精炼文字；但信息页必须有足够的文字量。
- 内容应具体、有数据支撑、有逻辑递进，避免空泛的套话。

### 收尾页
- 形式随主题而定（总结、CTA、讨论问题、延伸阅读等），避免程式化「感谢聆听」套话（除非场景确实适合）。
"""

# Conservative: tighter brand-friendly tone without mandating emoji or chart spam.
LAYOUT_CONSERVATIVE = """
## 美学（稳健模式）

### 整体
- 选择 **一套协调配色**，在全稿中保持一致或轻微渐变过渡；字体清晰可读。
- 层级分明：封面主标题醒目，正文段间距舒适；避免杂乱堆砌装饰。

### 图标与图表
- **少用**装饰性 Emoji；优先靠排版与色彩区分层次。
- **仅当**内容包含可量化对比或趋势时，使用内联 SVG 简化图表；否则用文字与列表即可。

### 版式
- 以清晰的信息传达为先：分栏、列表、适度留白；不必追求花哨特效。
"""

MODIFY_LAYOUT_GUIDE = """
## 编辑规范
1. 保持画布 1920×1080，body overflow:hidden；不要引入外链脚本、iframe、网络图片。
2. 尊重当前幻灯片已有的视觉气质与配色逻辑；用户未要求改版式或配色时，尽量只做针对性修改。
3. 字号与字重以可读为准，不必强行对齐某一固定 px 规范。
4. 可使用内联 SVG、CSS 渐变；不要为了装饰而堆砌 Emoji。
5. 仅修改用户要求的部分，其余结构与文案尽量保持不变。
6. 若用户要求补充数据对比且尚无图表，可用内联 SVG；否则优先用文字与排版解决。
7. 布局调整优先使用 flexbox/grid。
"""


def slide_layout_instructions(*, creative: bool = True) -> str:
    """Full layout block for slide generation: tech + aesthetic tier."""
    aesthetic = LAYOUT_CREATIVE if creative else LAYOUT_CONSERVATIVE
    return f"{LAYOUT_TECH}\n{aesthetic}"


# Backward compatibility for imports expecting a single constant name.
LAYOUT_ENHANCEMENT = slide_layout_instructions(creative=True)

# ---------------------------------------------------------------------------
# Shared-theme generation prompt (Phase 1 — tiny LLM call, ~200 tokens out)
# ---------------------------------------------------------------------------

THEME_GENERATION_PROMPT = """\
你是演示文稿视觉设计师。为主题选择一套协调的设计令牌。
输出合法 JSON（不要 Markdown 围栏，不要解释文字）。

格式：
{
  "palette": {
    "primary": "#...",
    "secondary": "#...",
    "accent": "#...",
    "accent_light": "#...",
    "bg": "#...",
    "surface": "#...",
    "border": "#..."
  },
  "typography": {
    "heading_font": "...",
    "body_font": "...",
    "heading_weight": "700",
    "body_weight": "400"
  },
  "spacing": {
    "page_padding": "64px",
    "section_gap": "36px",
    "element_gap": "18px"
  }
}

要求：
- 配色须服务于主题气质（科技 / 人文 / 商务 / 创意 等），可读优先。
- palette 共 7 个色值，全部为 hex 格式。
- typography 中 font 须包含中文回退（Microsoft YaHei / PingFang SC）。
- spacing 保持合理的 px 值。
- accent_light 应为 accent 的浅色版本（10-20% 不透明度效果）。
"""

# ---------------------------------------------------------------------------
# Slide body-fragment generation prompt (Phase 2 — ~500-800 tokens out)
# ---------------------------------------------------------------------------

SLIDE_FRAGMENT_PROMPT = """\
你是资深演示文稿设计师。生成「恰好 1 页」的幻灯片正文 HTML 片段。

当前是第 {index} 页（共 {total} 页），用途：{label}。
内容要点：{content_brief}

完整幻灯片结构：
{plan_summary}

本演示文稿已定义以下共享 CSS 类（通过 class 属性使用，禁止自定义 <style> 标签）：
{css_catalog}

{palette_instruction}

## 版式反套路规则（必须遵守）
**这一页的版式必须与同一演示文稿中的其他页面有明显的结构差异。**
- ❌ 禁止默认套路：顶部标题 + 下方 3-4 个等宽圆角卡片 + 每个卡片内放图标+文字
- ❌ 禁止所有正文页都用 flex 横排等分布局
- 从以下版式中选择一个与本页用途最匹配的（不要与相邻页重复）：
  A) 全出血背景 + 居中大字核心论点（极简海报）
  B) 左右严格分栏（一侧色块/图案，一侧文字）
  C) 上下分区（顶部色带标题 + 底部多段正文）
  D) 杂志排版（多列不等宽，穿插引用块）
  E) 时间线/流程（带连接线的步骤展示）
  F) 对照表/矩阵（表格或网格对比）
  G) 数据焦点（一个大数字 + SVG 图表 + 说明）
  H) 引用块式（大面积留白 + 居中引用 + 署名线）
  I) 卡片瀑布流（不等高、不等宽，错落排布）
  J) 全文字排版（纯靠字重、字号层级和留白区分，零装饰）

在 JSON 的 label 字段开头标注所选版式字母，如 "G) 数据分析"。

## 内容充实度
- 正文内容必须充实：至少 2-3 段阐述或 5+ 个要点
- 内容具体、有数据支撑、有逻辑递进，避免空泛套话
- 文字密度与版式匹配：极简版式页可以有精炼文字；信息页必须有足够文字量

输出合法 JSON（不要 Markdown 围栏，不要解释文字）。
顶层格式：{{"label":"版式字母) 本页用途简述","body":"...HTML body 片段..."}}

body 字段只需 <body> 标签内部的 HTML，不需要 <!DOCTYPE>、<html>、<head>、<style>。

HTML 要求：
1. 使用上述 ppt-* CSS 类进行排版；如需微调可用 inline style。
2. body 片段将渲染在 1920x1080 画布内，请确保内容不溢出。
3. 禁止外链脚本与 iframe；禁止直接使用外部图片 URL。
4. **配图**：若需图片装饰，可使用 `<img src="/api/images/proxy?url=ENCODED_URL" style="width:100%;height:100%;object-fit:cover;" />`（ENCODED_URL 为已编码的 Pexels/Unsplash 图片直链）；也可用 CSS 渐变、几何色块、内联 SVG。
5. 禁止 <style> 标签（所有样式通过共享 CSS 类 + inline style 实现）。
6. 配色与排版服务于主题；正文可读优先（字号不宜过小）；不要用装饰性 Emoji 铺满页面。
7. JSON 内双引号必须转义。
"""
