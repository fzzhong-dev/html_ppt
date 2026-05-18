<template>
  <div class="editor">
    <!-- Fullscreen slideshow overlay -->
    <div
      v-if="slideshowActive"
      class="slideshow-overlay"
      @click="onSlideshowClick"
      @keydown.left="store.prevSlide"
      @keydown.right="store.nextSlide"
      @keydown.escape="exitSlideshow"
    >
      <div class="slideshow-stage" :style="slideshowStageStyle">
        <iframe
          :srcdoc="store.currentSlide?.html_content ?? ''"
          class="slideshow-iframe"
          sandbox="allow-scripts allow-same-origin"
        ></iframe>
      </div>
      <div class="slideshow-footer">
        <span>{{ store.currentSlideIndex + 1 }} / {{ store.slideCount }}</span>
        <span class="slideshow-hint">← → 翻页 · ESC 退出</span>
      </div>
    </div>

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
      @insert-image="showImageSearch = !showImageSearch"
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
        <ImageSearchPanel
          v-if="showImageSearch"
          @select="handleImageSelect"
          @close="showImageSearch = false"
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { usePresentationStore } from '../stores/presentation'
import Toolbar from './Toolbar.vue'
import SlideList from './SlideList.vue'
import SlidePreview from './SlidePreview.vue'
import ChatPanel from './ChatPanel.vue'
import EditorStatusBar from './EditorStatusBar.vue'
import ImageSearchPanel from './ImageSearchPanel.vue'
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
const showImageSearch = ref(false)

/** 'fit' | 'manual' — 与 SlidePreview、状态栏一致 */
const canvasZoomMode = ref('fit')
const canvasZoomPercent = ref(100)
const effectiveZoomPercent = ref(100)

// --- Fullscreen slideshow ---
const slideshowActive = ref(false)
const slideshowWinW = ref(window.innerWidth)
const slideshowWinH = ref(window.innerHeight)

const SLIDE_W = 1920
const SLIDE_H = 1080

const slideshowScale = computed(() => {
  const scaleX = slideshowWinW.value / SLIDE_W
  const scaleY = slideshowWinH.value / SLIDE_H
  return Math.min(scaleX, scaleY)
})

const slideshowStageStyle = computed(() => {
  const s = slideshowScale.value
  return {
    width: `${SLIDE_W * s}px`,
    height: `${SLIDE_H * s}px`,
    '--slideshow-s': s,
  }
})

function updateSlideshowSize() {
  slideshowWinW.value = window.innerWidth
  slideshowWinH.value = window.innerHeight
}

function handleFullscreen() {
  slideshowActive.value = true
  document.documentElement.requestFullscreen?.()
}

function exitSlideshow() {
  slideshowActive.value = false
  if (document.fullscreenElement) {
    document.exitFullscreen?.()
  }
}

function onSlideshowClick(e) {
  // Click left third → prev, right third → next, center → do nothing
  const x = e.clientX
  const third = window.innerWidth / 3
  if (x < third) {
    store.prevSlide()
  } else if (x > third * 2) {
    store.nextSlide()
  }
}

function onSlideshowKeydown(e) {
  if (!slideshowActive.value) return
  if (e.key === 'ArrowLeft') {
    store.prevSlide()
  } else if (e.key === 'ArrowRight') {
    store.nextSlide()
  } else if (e.key === 'Escape') {
    exitSlideshow()
  }
}

function onFullscreenChange() {
  if (!document.fullscreenElement && slideshowActive.value) {
    slideshowActive.value = false
  }
}

onMounted(() => {
  document.addEventListener('keydown', onSlideshowKeydown)
  document.addEventListener('fullscreenchange', onFullscreenChange)
  window.addEventListener('resize', updateSlideshowSize)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onSlideshowKeydown)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  window.removeEventListener('resize', updateSlideshowSize)
})

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

async function handleChatSend(message) {
  await store.modify(message)
}

function handleBackHome() {
  store.reset()
}

function handleInsert(instruction) {
  store.modify(instruction)
}

function handleImageSelect(img) {
  const proxyUrl = `/api/images/proxy?url=${encodeURIComponent(img.url)}`
  const imgHtml = `<img src="${proxyUrl}" alt="${img.alt}" style="width:100%;height:100%;object-fit:cover;border-radius:12px;" />`
  store.applyHtmlTransform((html) => injectBeforeClosingBody(html, imgHtml))
  showImageSearch.value = false
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

/* Fullscreen slideshow */
.slideshow-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: #000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.slideshow-stage {
  flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);
}
.slideshow-iframe {
  width: 1920px;
  height: 1080px;
  border: none;
  display: block;
  transform-origin: top left;
  transform: scale(var(--slideshow-s, 1));
}
.slideshow-footer {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 24px;
  align-items: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 500;
  pointer-events: none;
}
.slideshow-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
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
