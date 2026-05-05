<template>
  <header class="ppt-chrome">
    <div class="ppt-titlebar">
      <div class="ppt-title-left">
        <div class="ppt-qat" role="toolbar" aria-label="快速访问工具栏">
          <button
            type="button"
            class="ppt-qat-btn"
            @click="$emit('undo')"
            :disabled="!canUndo"
            title="撤销"
          >
            ↶
          </button>
          <button
            type="button"
            class="ppt-qat-btn"
            @click="$emit('redo')"
            :disabled="!canRedo"
            title="重做"
          >
            ↷
          </button>
          <button type="button" class="ppt-qat-btn ppt-qat-btn-dim" disabled title="保存（占位）">
            保存
          </button>
        </div>
        <button type="button" class="ppt-app-btn" title="应用程序菜单（占位）" @click="activeTab = 'file'">
          <span class="ppt-app-grid" aria-hidden="true" />
          <span class="visually-hidden">应用程序菜单</span>
        </button>
      </div>
      <div class="ppt-doc-name" :title="documentTitle">{{ documentTitle }}</div>
      <div class="ppt-title-actions">
        <button type="button" class="ppt-primary" @click="$emit('export')" :disabled="exporting">
          {{ exporting ? '导出中…' : '导出 PPTX' }}
        </button>
        <button type="button" class="ppt-tbtn-strong" @click="$emit('fullscreen')">幻灯片放映</button>
        <button type="button" class="ppt-tbtn" @click="$emit('back-home')">关闭</button>
      </div>
    </div>

    <div class="ppt-ribbon-wrap">
      <div class="ppt-tabs-row">
        <nav class="ppt-tabs" aria-label="功能区选项卡">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            class="ppt-tab"
            :class="{ 'ppt-tab-active': activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>
        <button
          type="button"
          class="ppt-ribbon-toggle"
          :title="ribbonCollapsed ? '展开功能区' : '折叠功能区'"
          :aria-expanded="!ribbonCollapsed"
          @click="ribbonCollapsed = !ribbonCollapsed"
        >
          <span class="ppt-chevron" :class="{ 'ppt-chevron-up': !ribbonCollapsed }">⌄</span>
        </button>
      </div>

      <div v-show="!ribbonCollapsed" class="ppt-ribbon-panels">
        <!-- 文件（占位） -->
        <div v-show="activeTab === 'file'" class="ppt-ribbon-panel">
          <div class="ppt-group ppt-group-wide">
            <div class="ppt-group-body ppt-group-hint-wrap">
              <span class="ppt-hint">
                以下为占位入口；本项目仍以浏览器内编辑为主，后续可扩展导入/另存为等。
              </span>
            </div>
            <span class="ppt-group-cap">文件</span>
          </div>
          <div class="ppt-vsep" />
          <div class="ppt-group">
            <div class="ppt-group-body ppt-group-row">
              <button type="button" class="ppt-rbtn ppt-rbtn-sm-flat" disabled title="占位">新建</button>
              <button type="button" class="ppt-rbtn ppt-rbtn-sm-flat" disabled title="占位">打开</button>
              <button type="button" class="ppt-rbtn ppt-rbtn-sm-flat" @click="$emit('export')" :disabled="exporting">
                {{ exporting ? '导出…' : '导出' }}
              </button>
            </div>
            <span class="ppt-group-cap">操作</span>
          </div>
        </div>

        <!-- 开始 -->
        <div v-show="activeTab === 'home'" class="ppt-ribbon-panel">
          <div class="ppt-group">
            <div class="ppt-group-body">
              <button type="button" class="ppt-rbtn" @click="$emit('add-slide')" :disabled="loading">
                AI 新建页
              </button>
              <button type="button" class="ppt-rbtn" @click="$emit('copy-slide')" :disabled="loading">复制</button>
              <button type="button" class="ppt-rbtn" @click="$emit('delete-slide')" :disabled="loading || slideCount <= 1">
                删除
              </button>
            </div>
            <span class="ppt-group-cap">幻灯片</span>
          </div>
          <div class="ppt-vsep" />
          <div class="ppt-group ppt-group-wide">
            <div class="ppt-group-body ppt-group-hint-wrap">
              <span class="ppt-hint">
                中间预览区可切换「预览 / 可视化 / HTML代码」直接改页面；右侧助手仍可用作批量改写。
              </span>
            </div>
            <span class="ppt-group-cap">编辑</span>
          </div>
          <div class="ppt-vsep" />
          <div class="ppt-group">
            <div class="ppt-group-body">
              <button type="button" class="ppt-rbtn" @click="$emit('insert-image')" :disabled="loading">
                图片(AI)
              </button>
              <button type="button" class="ppt-rbtn" @click="$emit('insert-chart')" :disabled="loading">
                图表(AI)
              </button>
              <button type="button" class="ppt-rbtn" @click="$emit('insert-shape')" :disabled="loading">
                形状(AI)
              </button>
            </div>
            <span class="ppt-group-cap">插入(AI)</span>
          </div>
        </div>

        <!-- 插入 -->
        <div v-show="activeTab === 'insert'" class="ppt-ribbon-panel ppt-ribbon-stack">
          <div class="ppt-ribbon-row">
            <div class="ppt-group">
              <div class="ppt-group-body">
                <button type="button" class="ppt-rbtn ppt-rbtn-accent" @click="$emit('insert-blank')" :disabled="loading">
                  空白页
                </button>
                <button type="button" class="ppt-rbtn" @click="$emit('copy-slide')" :disabled="loading">复制</button>
                <button type="button" class="ppt-rbtn" @click="$emit('delete-slide')" :disabled="loading || slideCount <= 1">
                  删除
                </button>
              </div>
              <span class="ppt-group-cap">幻灯片</span>
            </div>
            <div class="ppt-vsep" />
            <div class="ppt-group ppt-group-lg">
              <div class="ppt-group-body ppt-group-wrap">
                <button type="button" class="ppt-rbtn" @click="$emit('insert-snippet', 'divider')">分隔线</button>
                <button type="button" class="ppt-rbtn" @click="$emit('insert-snippet', 'textCard')">文本块</button>
                <button type="button" class="ppt-rbtn" @click="$emit('insert-snippet', 'shapeSvg')">几何图形</button>
                <button type="button" class="ppt-rbtn" @click="$emit('insert-snippet', 'chartSvg')">示例图表</button>
                <button type="button" class="ppt-rbtn" @click="$emit('insert-snippet', 'imagePlaceholder')">
                  图片占位
                </button>
              </div>
              <span class="ppt-group-cap">页面元素（追加到当前页底部）</span>
            </div>
          </div>
          <div class="ppt-ribbon-row ppt-ribbon-row--layouts">
            <span class="ppt-inline-cap">版式模板（替换当前页正文，可先应用配色）</span>
            <div class="ppt-layout-btns">
              <button type="button" class="ppt-rbtn ppt-rbtn-sm" @click="$emit('insert-layout', 'cover')">封面</button>
              <button type="button" class="ppt-rbtn ppt-rbtn-sm" @click="$emit('insert-layout', 'toc')">目录</button>
              <button type="button" class="ppt-rbtn ppt-rbtn-sm" @click="$emit('insert-layout', 'section')">章节分隔</button>
              <button type="button" class="ppt-rbtn ppt-rbtn-sm" @click="$emit('insert-layout', 'content')">正文双栏</button>
              <button type="button" class="ppt-rbtn ppt-rbtn-sm" @click="$emit('insert-layout', 'summary')">结尾回顾</button>
            </div>
          </div>
        </div>

        <!-- 设计 -->
        <div v-show="activeTab === 'design'" class="ppt-ribbon-panel ppt-ribbon-stack">
          <div class="ppt-palette-row">
            <span class="ppt-inline-cap">主题配色（写入 CSS 变量 --ppt-primary … --ppt-bg）</span>
            <div class="ppt-palette-strip">
              <button
                v-for="p in designPalettes"
                :key="p.id"
                type="button"
                class="ppt-pchip"
                :title="p.name"
                @click="$emit('apply-palette', p.id)"
              >
                <span class="ppt-pchip-swatch" :style="paletteSwatchStyle(p)" />
                <span class="ppt-pchip-label">{{ p.name }}</span>
              </button>
            </div>
          </div>
          <div class="ppt-ribbon-row ppt-align-end">
            <div class="ppt-group ppt-group-design">
              <div class="ppt-group-body ppt-group-row">
                <label class="ppt-color-label">
                  页面背景色
                  <input v-model="designColor" type="color" class="ppt-color-input" title="选择背景色" />
                </label>
                <button type="button" class="ppt-rbtn ppt-rbtn-go" @click="applyBg">应用到当前页</button>
              </div>
              <span class="ppt-group-cap">自定义背景</span>
            </div>
            <div class="ppt-vsep" />
            <div class="ppt-group">
              <div class="ppt-group-body">
                <button type="button" class="ppt-rbtn ppt-rbtn-outline" @click="$emit('insert-page-badge')">
                  插入页码角标
                </button>
              </div>
              <span class="ppt-group-cap">页码</span>
            </div>
          </div>
          <p class="ppt-design-footnote">
            配色参考 pptx-generator 主题契约；版式参考封面 / 目录 / 章节 / 正文 / 结尾五类结构。页码为右下角圆形角标（当前页序号）。
          </p>
        </div>

        <!-- 切换 -->
        <div v-show="activeTab === 'transition'" class="ppt-ribbon-panel">
          <div class="ppt-group">
            <div class="ppt-group-body ppt-group-row">
              <label class="ppt-select-label">
                翻页动画（预览）
                <select class="ppt-select" :value="slideTransition" @change="onTransitionChange">
                  <option value="ppt-none">无</option>
                  <option value="ppt-fade">淡入淡出</option>
                  <option value="ppt-slide">轻微滑动</option>
                </select>
              </label>
            </div>
            <span class="ppt-group-cap">切换</span>
          </div>
          <div class="ppt-vsep" />
          <div class="ppt-group ppt-group-wide">
            <div class="ppt-group-body ppt-group-hint-wrap">
              <span class="ppt-hint">仅影响本编辑器内切换幻灯片时的过渡；导出 PPTX 为静态截图不含动画。</span>
            </div>
            <span class="ppt-group-cap">说明</span>
          </div>
        </div>

        <!-- 视图 -->
        <div v-show="activeTab === 'view'" class="ppt-ribbon-panel">
          <div class="ppt-group">
            <div class="ppt-group-body">
              <button type="button" class="ppt-rbtn" title="适应窗口" @click="$emit('zoom-fit')">适应窗口</button>
              <button type="button" class="ppt-rbtn" title="实际大小 100%" @click="$emit('zoom-percent', 100)">
                实际大小
              </button>
            </div>
            <span class="ppt-group-cap">显示</span>
          </div>
          <div class="ppt-vsep" />
          <div class="ppt-group">
            <div class="ppt-group-body">
              <button type="button" class="ppt-rbtn ppt-rbtn-accent" @click="$emit('fullscreen')">幻灯片放映</button>
            </div>
            <span class="ppt-group-cap">放映</span>
          </div>
          <div class="ppt-vsep" />
          <div class="ppt-group ppt-group-wide">
            <div class="ppt-group-body ppt-group-hint-wrap">
              <span class="ppt-hint">缩放也可使用底部状态栏；备注面板仍为占位功能。</span>
            </div>
            <span class="ppt-group-cap">说明</span>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
import { DESIGN_PALETTES } from '../utils/designPalettes'

const designPalettes = DESIGN_PALETTES

function paletteSwatchStyle(p) {
  return {
    background: `linear-gradient(135deg, ${p.primary} 0%, ${p.accent} 45%, ${p.bg} 100%)`,
  }
}

defineProps({
  exporting: Boolean,
  canUndo: Boolean,
  canRedo: Boolean,
  loading: Boolean,
  slideCount: { type: Number, default: 0 },
  documentTitle: { type: String, default: '演示文稿' },
  slideTransition: { type: String, default: 'ppt-fade' },
})

const emit = defineEmits([
  'export',
  'fullscreen',
  'back-home',
  'undo',
  'redo',
  'add-slide',
  'copy-slide',
  'delete-slide',
  'insert-image',
  'insert-chart',
  'insert-shape',
  'insert-blank',
  'insert-snippet',
  'design-bg',
  'transition-change',
  'apply-palette',
  'insert-layout',
  'insert-page-badge',
  'zoom-fit',
  'zoom-percent',
])

const tabs = [
  { id: 'file', label: '文件' },
  { id: 'home', label: '开始' },
  { id: 'insert', label: '插入' },
  { id: 'design', label: '设计' },
  { id: 'transition', label: '切换' },
  { id: 'view', label: '视图' },
]

const activeTab = ref('home')
const ribbonCollapsed = ref(false)
const designColor = ref('#ffffff')

function applyBg() {
  emit('design-bg', designColor.value)
}

function onTransitionChange(e) {
  emit('transition-change', e.target.value)
}
</script>

<style scoped>
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.ppt-chrome {
  flex-shrink: 0;
  background: var(--oo-chrome-bg, #fff);
  border-bottom: 1px solid var(--oo-border, #edebe9);
  box-shadow: var(--oo-shadow-chrome, 0 1px 0 rgba(0, 0, 0, 0.04));
}
.ppt-titlebar {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 40px;
  padding: 0 12px 0 10px;
  background: var(--oo-chrome-bg, #fff);
  border-bottom: 1px solid var(--oo-border, #edebe9);
}
.ppt-title-left {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.ppt-qat {
  display: flex;
  align-items: center;
  gap: 2px;
  padding-right: 6px;
  border-right: 1px solid var(--oo-border, #edebe9);
}
.ppt-qat-btn {
  width: 28px;
  height: 26px;
  padding: 0;
  border-radius: 2px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--oo-text, #323130);
  font-size: 15px;
  line-height: 1;
  cursor: pointer;
}
.ppt-qat-btn:hover:not(:disabled) {
  background: var(--oo-qat-hover, #f3f2f1);
  border-color: var(--oo-border, #edebe9);
}
.ppt-qat-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}
.ppt-qat-btn-dim {
  opacity: 0.55;
  font-size: 11px;
  width: auto;
  min-width: 44px;
  padding: 0 8px;
}
.ppt-app-btn {
  width: 36px;
  height: 28px;
  padding: 0;
  border-radius: 2px;
  border: 1px solid transparent;
  background: var(--oo-app-btn-bg, #f3f2f1);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.ppt-app-btn:hover {
  background: var(--oo-app-btn-hover, #edebe9);
  border-color: var(--oo-border-strong, #d2d0ce);
}
.ppt-app-grid {
  width: 14px;
  height: 14px;
  background:
    linear-gradient(var(--oo-text-secondary, #605e5c), var(--oo-text-secondary, #605e5c)) 0 0 / 6px 6px no-repeat,
    linear-gradient(var(--oo-text-secondary, #605e5c), var(--oo-text-secondary, #605e5c)) 8px 0 / 6px 6px no-repeat,
    linear-gradient(var(--oo-text-secondary, #605e5c), var(--oo-text-secondary, #605e5c)) 0 8px / 6px 6px no-repeat,
    linear-gradient(var(--oo-text-secondary, #605e5c), var(--oo-text-secondary, #605e5c)) 8px 8px / 6px 6px no-repeat;
  opacity: 0.9;
}
.ppt-doc-name {
  flex: 1;
  min-width: 0;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: var(--oo-text, #323130);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ppt-title-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.ppt-tbtn {
  height: 28px;
  padding: 0 10px;
  border-radius: 2px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--oo-text, #323130);
  font-size: 12px;
  cursor: pointer;
}
.ppt-tbtn:hover {
  background: var(--oo-chrome-muted-hover, #edebe9);
  border-color: var(--oo-border, #edebe9);
}
.ppt-tbtn-strong {
  height: 28px;
  padding: 0 12px;
  border-radius: 2px;
  border: 1px solid var(--oo-border-strong, #c8c6c4);
  background: var(--oo-chrome-bg, #fff);
  color: var(--oo-text, #323130);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.ppt-tbtn-strong:hover {
  background: var(--oo-chrome-muted-hover, #f3f2f1);
}
.ppt-primary {
  height: 28px;
  padding: 0 14px;
  border-radius: 2px;
  border: 1px solid var(--oo-primary-green, #107c10);
  background: var(--oo-primary-green, #107c10);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.ppt-primary:hover:not(:disabled) {
  filter: brightness(1.05);
}
.ppt-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.ppt-ribbon-wrap {
  background: var(--oo-ribbon-tab-strip-bg, #f3f2f1);
}
.ppt-tabs-row {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--oo-border-tabs, #d2d0ce);
  background: var(--oo-ribbon-tab-strip-bg, #f3f2f1);
}
.ppt-tabs {
  display: flex;
  align-items: stretch;
  gap: 0;
  flex: 1;
  min-width: 0;
  padding: 0 4px 0 8px;
}
.ppt-ribbon-toggle {
  flex-shrink: 0;
  width: 32px;
  border: none;
  border-left: 1px solid var(--oo-border-tabs, #d2d0ce);
  background: var(--oo-ribbon-tab-strip-bg, #f3f2f1);
  cursor: pointer;
  color: var(--oo-text-secondary, #605e5c);
  font-size: 14px;
}
.ppt-ribbon-toggle:hover {
  background: var(--oo-chrome-muted-hover, #edebe9);
}
.ppt-chevron {
  display: inline-block;
  transition: transform 0.15s ease;
  transform: rotate(0deg);
}
.ppt-chevron-up {
  transform: rotate(180deg);
}
.ppt-tab {
  padding: 8px 14px 10px;
  border: none;
  background: transparent;
  font-size: 12px;
  font-weight: 600;
  color: var(--oo-text-secondary, #605e5c);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -1px;
}
.ppt-tab:hover {
  color: var(--oo-text, #323130);
}
.ppt-tab-active {
  background: var(--oo-ribbon-panel-bg, #fff);
  color: var(--oo-accent-orange, #d83b01);
  border-bottom-color: var(--oo-accent-orange, #d83b01);
}
.ppt-ribbon-panels {
  background: var(--oo-ribbon-panel-bg, #fff);
}
.ppt-ribbon-panel {
  display: flex;
  align-items: stretch;
  gap: 0;
  min-height: 72px;
  padding: 6px 12px 4px;
  background: var(--oo-ribbon-panel-bg, #fff);
  border-bottom: 1px solid var(--oo-border, #edebe9);
}
.ppt-group {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  padding: 0 10px 4px;
  min-width: 0;
}
.ppt-group-lg {
  flex: 1;
}
.ppt-group-body {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}
.ppt-group-wrap {
  flex-wrap: wrap;
  justify-content: flex-start;
}
.ppt-group-row {
  gap: 14px;
}
.ppt-group-cap {
  margin-top: 2px;
  font-size: 11px;
  color: var(--oo-text-secondary, #605e5c);
  white-space: nowrap;
}
.ppt-rbtn {
  height: 52px;
  min-width: 56px;
  padding: 6px 8px;
  border-radius: 2px;
  border: 1px solid transparent;
  background: transparent;
  font-size: 11px;
  line-height: 1.2;
  color: var(--oo-text, #323130);
  cursor: pointer;
}
.ppt-rbtn:hover:not(:disabled) {
  background: var(--oo-chrome-muted-hover, #edebe9);
  border-color: var(--oo-border-strong, #d2d0ce);
}
.ppt-rbtn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.ppt-rbtn-accent {
  border-color: rgba(216, 59, 1, 0.35);
  background: #fff8f4;
}
.ppt-rbtn-go {
  height: 36px;
  min-width: 120px;
  background: var(--oo-text, #323130);
  color: #fff;
  border-radius: 2px;
  font-weight: 600;
}
.ppt-rbtn-go:hover {
  background: #201f1e;
}
.ppt-rbtn-sm-flat {
  height: 40px !important;
  min-width: 72px !important;
}
.ppt-vsep {
  width: 1px;
  align-self: stretch;
  background: var(--oo-border, #edebe9);
  margin: 4px 6px;
}
.ppt-group-wide {
  flex: 1;
  min-width: 140px;
  max-width: 420px;
}
.ppt-group-design {
  align-items: flex-start;
}
.ppt-group-hint-wrap {
  align-items: flex-start !important;
  justify-content: center;
  min-height: 52px;
  padding: 6px 8px !important;
}
.ppt-hint {
  font-size: 11px;
  color: var(--oo-text-secondary, #605e5c);
  line-height: 1.4;
  text-align: left;
}
.ppt-color-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--oo-text, #323130);
}
.ppt-color-input {
  width: 44px;
  height: 32px;
  padding: 0;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  border-radius: 2px;
  cursor: pointer;
}
.ppt-select-label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--oo-text, #323130);
}
.ppt-select {
  min-width: 140px;
  height: 32px;
  padding: 0 8px;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  border-radius: 2px;
  font-size: 12px;
  background: var(--oo-chrome-bg, #fff);
}

.ppt-ribbon-stack {
  flex-direction: column;
  align-items: stretch;
  gap: 10px;
  min-height: auto;
  padding-bottom: 10px;
}
.ppt-ribbon-row {
  display: flex;
  align-items: stretch;
  flex-wrap: wrap;
  gap: 0;
}
.ppt-ribbon-row--layouts {
  align-items: center;
  gap: 12px;
  padding-top: 4px;
  border-top: 1px solid var(--oo-border, #edebe9);
}
.ppt-align-end {
  align-items: flex-end;
}
.ppt-inline-cap {
  font-size: 11px;
  font-weight: 700;
  color: var(--oo-text-secondary, #605e5c);
  width: 100%;
  margin-bottom: 4px;
}
.ppt-layout-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
.ppt-rbtn-sm {
  height: 40px !important;
  min-width: 72px !important;
  font-size: 11px;
}
.ppt-palette-row {
  width: 100%;
}
.ppt-palette-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.ppt-pchip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  border-radius: 6px;
  background: var(--oo-chrome-bg, #fff);
  cursor: pointer;
  font-size: 11px;
  color: var(--oo-text, #323130);
}
.ppt-pchip:hover {
  border-color: var(--oo-accent-orange, #d83b01);
  background: #fff8f4;
}
.ppt-pchip-swatch {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
}
.ppt-pchip-label {
  font-weight: 600;
  white-space: nowrap;
}
.ppt-rbtn-outline {
  border: 1px solid var(--oo-accent-blue, #0078d4) !important;
  color: var(--oo-accent-blue, #0078d4) !important;
  height: 44px !important;
  min-width: 120px !important;
}
.ppt-rbtn-outline:hover:not(:disabled) {
  background: #f0f7fc !important;
}
.ppt-design-footnote {
  margin: 0;
  font-size: 10px;
  color: #8a8886;
  line-height: 1.45;
  max-width: 920px;
}
</style>
