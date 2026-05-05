<template>
  <div class="editor">
    <Toolbar
      :exporting="exporting"
      :can-undo="store.canUndo"
      :can-redo="store.canRedo"
      :loading="store.loading"
      :slide-count="store.slideCount"
      :document-title="store.presentation?.title || '演示文稿'"
      :slide-transition="slideTransition"
      @export="handleExport"
      @fullscreen="handleFullscreen"
      @back-home="handleBackHome"
      @undo="store.undo"
      @redo="store.redo"
      @add-slide="store.addSlide"
      @copy-slide="store.copySlide"
      @delete-slide="store.deleteSlide"
      @insert-image="handleInsert('在这页中插入一张配图，风格与页面主题协调')"
      @insert-chart="handleInsert('在这页中添加一个数据图表（柱状图/折线图/饼图），使用内联SVG实现，配有标题和简短解读')"
      @insert-shape="handleInsert('在这页中添加装饰性形状元素（几何图形、分隔线、图标等），提升视觉效果')"
      @insert-blank="store.addBlankSlide"
      @insert-snippet="handleInsertSnippet"
      @design-bg="handleDesignBg"
      @transition-change="slideTransition = $event"
      @apply-palette="handleApplyPalette"
      @insert-layout="handleInsertLayout"
      @insert-page-badge="handleInsertPageBadge"
      @zoom-fit="setZoomFit"
      @zoom-percent="setZoomPercent"
    />
    <div class="editor-workspace">
      <div class="editor-body">
        <SlideList
          :slides="store.presentation?.slides || []"
          :currentIndex="store.currentSlideIndex"
          @select="store.selectSlide"
          @add-slide="store.addSlide"
        />
        <div class="editor-main">
          <Transition :name="slideTransition" mode="out-in">
            <SlidePreview
              :key="store.currentSlide?.id ?? '__empty__'"
              :slide="store.currentSlide"
              :current="store.currentSlideIndex"
              :total="store.slideCount"
              :awaiting-slides="store.loading && store.slideCount === 0"
              :zoom-mode="canvasZoomMode"
              :zoom-percent="canvasZoomPercent"
              @prev="store.prevSlide"
              @next="store.nextSlide"
              @update-html="store.patchCurrentSlideHtml($event)"
              @effective-zoom="onEffectiveZoom"
            />
          </Transition>
        </div>
        <ChatPanel
          :messages="store.chatHistory"
          :loading="store.loading"
          @send="handleChatSend"
        />
      </div>
      <EditorStatusBar
        :current-index="store.currentSlideIndex"
        :slide-count="store.slideCount"
        :zoom-mode="canvasZoomMode"
        :zoom-percent="canvasZoomPercent"
        :effective-zoom="effectiveZoomPercent"
        @zoom-fit="setZoomFit"
        @zoom-percent="setZoomPercent"
        @zoom-out="zoomOut"
        @zoom-in="zoomIn"
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
import EditorStatusBar from './EditorStatusBar.vue'
import { getPalette } from '../utils/designPalettes'
import { getLayoutBody } from '../utils/slideLayouts'
import {
  SNIPPETS,
  injectBeforeClosingBody,
  setBodyBackground,
  injectThemeTokens,
  replaceBodyInnerHtml,
  injectPageBadge,
} from '../utils/slideHtml'

const store = usePresentationStore()
const exporting = ref(false)
const slideTransition = ref('ppt-fade')
const activePaletteId = ref('luxury-muted')

/** 'fit' | 'manual' — 与 SlidePreview、状态栏一致 */
const canvasZoomMode = ref('fit')
const canvasZoomPercent = ref(100)
const effectiveZoomPercent = ref(100)

function onEffectiveZoom(z) {
  effectiveZoomPercent.value = z
}

function setZoomFit() {
  canvasZoomMode.value = 'fit'
}

function setZoomPercent(p) {
  canvasZoomMode.value = 'manual'
  canvasZoomPercent.value = Math.min(400, Math.max(25, Math.round(Number(p) || 100)))
}

function zoomOut() {
  canvasZoomMode.value = 'manual'
  canvasZoomPercent.value = Math.max(25, Math.round(effectiveZoomPercent.value - 10))
}

function zoomIn() {
  canvasZoomMode.value = 'manual'
  canvasZoomPercent.value = Math.min(400, Math.round(effectiveZoomPercent.value + 10))
}

function handleApplyPalette(id) {
  activePaletteId.value = id
  store.applyHtmlTransform((html) => injectThemeTokens(html, getPalette(id)))
}

function handleInsertLayout(key) {
  const pal = getPalette(activePaletteId.value)
  store.applyHtmlTransform((html) => {
    const themed = injectThemeTokens(html, pal)
    return replaceBodyInnerHtml(themed, getLayoutBody(key))
  })
}

function handleInsertPageBadge() {
  const pal = getPalette(activePaletteId.value)
  const n = store.currentSlideIndex + 1
  store.applyHtmlTransform((html) => injectPageBadge(html, n, pal))
}

async function handleExport() {
  exporting.value = true
  try {
    await store.exportToPPTX()
  } finally {
    exporting.value = false
  }
}

function handleFullscreen() {
  const iframe = document.querySelector('.preview-iframe-main')
  const wrap = document.querySelector('.preview-stage')
  const el = wrap || iframe
  if (el?.requestFullscreen) {
    el.requestFullscreen()
  }
}

async function handleChatSend(message) {
  await store.modify(message)
}

function handleBackHome() {
  store.reset()
}

function handleInsert(instruction) {
  store.modify(instruction)
}

function handleInsertSnippet(type) {
  const snippet = SNIPPETS[type]
  if (!snippet) return
  store.applyHtmlTransform((html) => injectBeforeClosingBody(html, snippet))
}

function handleDesignBg(color) {
  store.applyHtmlTransform((html) => setBodyBackground(html, color))
}
</script>

<style scoped>
.editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.editor-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  background: var(--oo-workspace-bg, #e7e6e6);
}
.editor-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* 翻页过渡（切换选项卡） */
.ppt-fade-enter-active,
.ppt-fade-leave-active {
  transition: opacity 0.22s ease;
}
.ppt-fade-enter-from,
.ppt-fade-leave-to {
  opacity: 0;
}

.ppt-slide-enter-active,
.ppt-slide-leave-active {
  transition:
    transform 0.26s ease,
    opacity 0.26s ease;
}
.ppt-slide-enter-from {
  transform: translateX(22px);
  opacity: 0;
}
.ppt-slide-leave-to {
  transform: translateX(-22px);
  opacity: 0;
}

.ppt-none-enter-active,
.ppt-none-leave-active {
  transition-duration: 0ms !important;
}
</style>
