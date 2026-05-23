<template>
  <div class="preview-area">
    <div v-if="slide" class="preview-toolbar">
      <div class="preview-mode-btns" role="tablist" aria-label="编辑模式">
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'preview'"
          class="mode-btn"
          :class="{ active: mode === 'preview' }"
          @click="mode = 'preview'"
        >
          预览
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'visual'"
          class="mode-btn"
          :class="{ active: mode === 'visual' }"
          title="在页面中直接点击、打字修改（完成后请点「保存」）"
          @click="mode = 'visual'"
        >
          可视化
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'code'"
          class="mode-btn"
          :class="{ active: mode === 'code' }"
          @click="switchToCode"
        >
          HTML 代码
        </button>
      </div>
      <div v-if="mode === 'visual'" class="preview-toolbar-right">
        <div class="fmt-bar">
          <button type="button" class="fmt-btn" title="加粗 (Ctrl+B)" @click="fmtCmd('bold')"><b>B</b></button>
          <button type="button" class="fmt-btn" title="斜体 (Ctrl+I)" @click="fmtCmd('italic')"><i>I</i></button>
          <button type="button" class="fmt-btn" title="下划线 (Ctrl+U)" @click="fmtCmd('underline')"><u>U</u></button>
          <button type="button" class="fmt-btn" title="删除线" @click="fmtCmd('strikeThrough')"><s>S</s></button>
          <span class="fmt-sep"></span>
          <button type="button" class="fmt-btn" title="上标" @click="fmtCmd('superscript')">X²</button>
          <button type="button" class="fmt-btn" title="下标" @click="fmtCmd('subscript')">X₂</button>
          <span class="fmt-sep"></span>
          <button type="button" class="fmt-btn" title="无序列表" @click="fmtCmd('insertUnorderedList')">&#8226; 列表</button>
          <button type="button" class="fmt-btn" title="有序列表" @click="fmtCmd('insertOrderedList')">1. 列表</button>
          <span class="fmt-sep"></span>
          <button type="button" class="fmt-btn" title="左对齐" @click="fmtCmd('justifyLeft')">≡←</button>
          <button type="button" class="fmt-btn" title="居中" @click="fmtCmd('justifyCenter')">≡↔</button>
          <button type="button" class="fmt-btn" title="右对齐" @click="fmtCmd('justifyRight')">≡→</button>
          <span class="fmt-sep"></span>
          <select class="fmt-select" title="字体" @change="fmtFont($event.target.value)">
            <option value="">字体</option>
            <option value="Microsoft YaHei">微软雅黑</option>
            <option value="SimHei">黑体</option>
            <option value="SimSun">宋体</option>
            <option value="KaiTi">楷体</option>
            <option value="Arial">Arial</option>
            <option value="Georgia">Georgia</option>
          </select>
          <select class="fmt-select" title="字号" @change="fmtSize($event.target.value)">
            <option value="">字号</option>
            <option value="1">小</option>
            <option value="3">标准</option>
            <option value="5">大</option>
            <option value="7">超大</option>
          </select>
          <label class="fmt-color-wrap" title="文字颜色">
            <span class="fmt-color-icon">A</span>
            <input type="color" class="fmt-color" value="#323130" @input="fmtColor($event.target.value)" />
          </label>
          <label class="fmt-color-wrap" title="高亮颜色">
            <span class="fmt-color-icon fmt-highlight-icon">&#9673;</span>
            <input type="color" class="fmt-color" value="#ffeb3b" @input="fmtHighlight($event.target.value)" />
          </label>
          <span class="fmt-sep"></span>
          <button type="button" class="fmt-btn" title="减少缩进" @click="fmtCmd('outdent')">←→</button>
          <button type="button" class="fmt-btn" title="增加缩进" @click="fmtCmd('indent')">→←</button>
          <button type="button" class="fmt-btn fmt-btn-danger" title="清除格式" @click="fmtCmd('removeFormat')">清除</button>
        </div>
        <button type="button" class="btn-save-visual" @click="saveVisual">保存可视化修改</button>
      </div>
      <div v-if="mode === 'code'" class="preview-toolbar-right">
        <button type="button" class="btn-apply-code" @click="applyCode">应用 HTML</button>
      </div>
    </div>

    <div class="preview-container" ref="containerRef">
      <template v-if="slide">
        <div v-show="mode === 'code'" class="code-panel">
          <textarea
            v-model="codeHtml"
            class="code-editor"
            spellcheck="false"
            autocomplete="off"
            autocorrect="off"
            autocapitalize="off"
          />
        </div>
        <div v-show="mode !== 'code'" class="preview-stage-wrap">
          <div class="preview-stage" :style="stageStyle">
            <div class="preview-wrapper" :style="wrapperStyle">
              <iframe
                ref="iframeRef"
                :srcdoc="iframeSrc"
                class="preview-iframe preview-iframe-main"
                sandbox="allow-scripts allow-same-origin"
                title="幻灯片预览"
                @load="onIframeLoad"
              ></iframe>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="preview-empty">{{ emptyHint }}</div>
    </div>
    <div v-if="slide" class="preview-nav">
      <button type="button" @click="$emit('prev')" :disabled="!canPrev">上一页</button>
      <span class="preview-nav-meta">{{ current + 1 }} / {{ total }}</span>
      <button type="button" @click="$emit('next')" :disabled="!canNext">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  slide: Object,
  current: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  awaitingSlides: { type: Boolean, default: false },
  /** 'fit'：适应窗口；'manual'：使用 zoomPercent */
  zoomMode: { type: String, default: 'fit' },
  zoomPercent: { type: Number, default: 100 },
})
const emit = defineEmits(['prev', 'next', 'update-html', 'effective-zoom'])

const emptyHint = computed(() => {
  if (props.awaitingSlides) return '正在生成首张幻灯片…'
  if (!props.slide && props.total === 0) return '暂无幻灯片'
  return '选择一张幻灯片'
})

const mode = ref('preview')
const iframeRef = ref(null)
const codeHtml = ref('')
const iframeSrc = ref('')
const containerRef = ref(null)
const fitScale = ref(1)

const SLIDE_W = 1920
const SLIDE_H = 1080

const canPrev = computed(() => props.current > 0)
const canNext = computed(() => props.current < props.total - 1)

const effectiveScale = computed(() => {
  if (props.zoomMode === 'manual') {
    const p = Math.min(400, Math.max(25, props.zoomPercent))
    return p / 100
  }
  return fitScale.value
})

const stageStyle = computed(() => ({
  width: `${SLIDE_W * effectiveScale.value}px`,
  height: `${SLIDE_H * effectiveScale.value}px`,
  overflow: 'hidden',
  borderRadius: '2px',
  boxShadow: '0 2px 10px rgba(0, 0, 0, 0.14), 0 0 1px rgba(0, 0, 0, 0.18)',
  flexShrink: 0,
}))

const wrapperStyle = computed(() => ({
  width: `${SLIDE_W}px`,
  height: `${SLIDE_H}px`,
  transform: `scale(${effectiveScale.value})`,
  transformOrigin: 'top left',
}))

function updateFitScale() {
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const padding = 36
  const availW = Math.max(0, rect.width - padding)
  const availH = Math.max(0, rect.height - padding - 44)
  if (availW <= 0 || availH <= 0) {
    fitScale.value = 0.05
    return
  }
  const scaleX = availW / SLIDE_W
  const scaleY = availH / SLIDE_H
  fitScale.value = Math.min(scaleX, scaleY, 1)
}

function syncIframeFromSlide() {
  iframeSrc.value = props.slide?.html_content ?? ''
}

function applyDesignMode(on) {
  const doc = iframeRef.value?.contentDocument
  if (!doc) return
  doc.designMode = on ? 'on' : 'off'
}

function serializeIframe() {
  const doc = iframeRef.value?.contentDocument
  if (!doc?.documentElement) return ''
  const dt = doc.doctype ? `<!DOCTYPE ${doc.doctype.name}>\n` : '<!DOCTYPE html>\n'
  return dt + doc.documentElement.outerHTML
}

function onIframeLoad() {
  nextTick(() => {
    if (mode.value === 'visual') {
      applyDesignMode(true)
    } else {
      applyDesignMode(false)
    }
    updateFitScale()
    requestAnimationFrame(updateFitScale)
  })
}

watch(
  () => props.slide?.id,
  () => {
    codeHtml.value = props.slide?.html_content ?? ''
    syncIframeFromSlide()
    if (mode.value === 'visual') {
      nextTick(() => applyDesignMode(true))
    }
  },
  { immediate: true },
)

watch(
  () => props.slide?.html_content,
  (h) => {
    if (!props.slide) return
    if (mode.value === 'visual') return
    codeHtml.value = h ?? ''
    syncIframeFromSlide()
  },
)

watch(mode, async (m) => {
  await nextTick()
  if (m === 'visual') {
    syncIframeFromSlide()
    await nextTick()
    applyDesignMode(true)
  } else if (m === 'preview') {
    syncIframeFromSlide()
    await nextTick()
    applyDesignMode(false)
  }
  updateFitScale()
})

function switchToCode() {
  if (mode.value === 'visual') {
    const live = serializeIframe()
    if (live) codeHtml.value = live
  }
  mode.value = 'code'
}

function saveVisual() {
  const html = serializeIframe()
  if (html) emit('update-html', html)
}

function fmtCmd(cmd) {
  iframeRef.value?.contentDocument?.execCommand(cmd, false, null)
}

function fmtSize(size) {
  if (!size) return
  iframeRef.value?.contentDocument?.execCommand('fontSize', false, size)
}

function fmtColor(color) {
  iframeRef.value?.contentDocument?.execCommand('foreColor', false, color)
}

function fmtFont(font) {
  if (!font) return
  iframeRef.value?.contentDocument?.execCommand('fontName', false, font)
}

function fmtHighlight(color) {
  iframeRef.value?.contentDocument?.execCommand('hiliteColor', false, color)
}

function applyCode() {
  emit('update-html', codeHtml.value)
  mode.value = 'preview'
}

let resizeObserver = null

watch(
  effectiveScale,
  (s) => {
    emit('effective-zoom', Math.round(s * 100))
  },
  { immediate: true },
)

watch(
  () => [props.zoomMode, props.zoomPercent],
  () => {
    nextTick(() => {
      updateFitScale()
      requestAnimationFrame(updateFitScale)
    })
  },
)

onMounted(() => {
  nextTick(() => {
    updateFitScale()
    requestAnimationFrame(updateFitScale)
  })
  if (containerRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => updateFitScale())
    resizeObserver.observe(containerRef.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

watch(
  () => [props.slide?.id, props.slide?.html_content],
  () => {
    nextTick(() => {
      updateFitScale()
      requestAnimationFrame(updateFitScale)
    })
  },
)
</script>

<style scoped>
.preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  background: var(--oo-workspace-bg, #e7e6e6);
  padding: 10px 18px 14px;
}
.preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.preview-mode-btns {
  display: flex;
  gap: 4px;
}
.mode-btn {
  padding: 6px 14px;
  border-radius: 2px;
  border: 1px solid #d2d0ce;
  background: #fff;
  font-size: 12px;
  font-weight: 600;
  color: #323130;
  cursor: pointer;
}
.mode-btn:hover {
  background: #f3f2f1;
}
.mode-btn.active {
  border-color: #d83b01;
  color: #d83b01;
  background: #fff8f4;
}
.preview-toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.visual-hint {
  font-size: 11px;
  color: #605e5c;
  max-width: 420px;
  line-height: 1.35;
}
.fmt-bar {
  display: flex;
  align-items: center;
  gap: 3px;
  background: #faf9f8;
  border: 1px solid #d2d0ce;
  border-radius: 3px;
  padding: 3px 6px;
}
.fmt-btn {
  width: 28px;
  height: 26px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  color: #323130;
  border-radius: 2px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.fmt-btn:hover {
  background: #e1dfdd;
}
.fmt-sep {
  width: 1px;
  height: 18px;
  background: #d2d0ce;
  margin: 0 2px;
}
.fmt-select {
  height: 26px;
  border: 1px solid #c8c6c4;
  border-radius: 2px;
  font-size: 11px;
  padding: 0 4px;
  background: #fff;
  color: #323130;
  cursor: pointer;
}
.fmt-color {
  width: 26px;
  height: 26px;
  border: 1px solid #c8c6c4;
  border-radius: 2px;
  padding: 2px;
  cursor: pointer;
  background: #fff;
}
.fmt-color-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.fmt-color-wrap .fmt-color {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}
.fmt-color-icon {
  width: 28px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #c8c6c4;
  border-radius: 2px;
  background: #fff;
  font-size: 14px;
  font-weight: 700;
  color: #323130;
  pointer-events: none;
}
.fmt-highlight-icon {
  font-size: 16px;
  font-weight: 400;
}
.fmt-btn-danger {
  color: #d83b01;
  font-weight: 600;
  font-size: 11px;
}
.btn-save-visual,
.btn-apply-code {
  padding: 7px 14px;
  border-radius: 2px;
  border: 1px solid #107c10;
  background: #107c10;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.btn-save-visual:hover,
.btn-apply-code:hover {
  filter: brightness(1.06);
}
.preview-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  overflow: hidden;
  min-height: 0;
}
.preview-stage-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  min-height: 0;
}
.code-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #3c3c3c;
}
.code-editor {
  flex: 1;
  width: 100%;
  min-height: 200px;
  padding: 14px 16px;
  border: none;
  resize: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  line-height: 1.45;
  color: #d4d4d4;
  background: #1e1e1e;
  box-sizing: border-box;
}
.code-editor:focus {
  outline: 2px solid #0078d4;
  outline-offset: -2px;
}
.preview-stage {
  background: #fff;
  border-radius: 2px;
}
.preview-wrapper {
  overflow: hidden;
  background: white;
}
.preview-iframe {
  width: 1920px;
  height: 1080px;
  border: none;
  display: block;
}
.preview-empty {
  color: #64748b;
  font-size: 15px;
  font-weight: 500;
  text-align: center;
  padding: 40px;
}
.preview-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 12px 8px 4px;
  flex-shrink: 0;
}
.preview-nav button {
  padding: 6px 16px;
  border: 1px solid #8a8886;
  background: #fff;
  border-radius: 2px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  color: #323130;
  transition: background 0.12s, border-color 0.12s;
}
.preview-nav button:hover:not(:disabled) {
  background: #f3f2f1;
  border-color: #605e5c;
}
.preview-nav button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.preview-nav-meta {
  font-size: 12px;
  font-weight: 600;
  color: #605e5c;
  min-width: 5rem;
  text-align: center;
}
</style>
