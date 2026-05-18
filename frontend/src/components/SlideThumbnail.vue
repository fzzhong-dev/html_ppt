<template>
  <div class="thumb-root" ref="rootRef">
    <div v-if="htmlContent" class="thumb-stage" :style="stageStyle">
      <div class="thumb-inner" :style="innerStyle">
        <iframe
          class="thumb-iframe"
          :srcdoc="htmlContent"
          sandbox="allow-scripts allow-same-origin"
          tabindex="-1"
          title=""
          @load="scheduleResize"
        />
      </div>
    </div>
    <div v-else class="thumb-placeholder">—</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  htmlContent: { type: String, default: '' },
})

const SLIDE_W = 1920
const SLIDE_H = 1080

const rootRef = ref(null)
const scale = ref(0.1)

function computeScale() {
  const el = rootRef.value
  if (!el) return
  const w = el.clientWidth
  if (w <= 0) return
  scale.value = Math.min(w / SLIDE_W, 1)
}

function scheduleResize() {
  nextTick(() => {
    computeScale()
    requestAnimationFrame(computeScale)
  })
}

const stageStyle = computed(() => ({
  width: `${SLIDE_W * scale.value}px`,
  height: `${SLIDE_H * scale.value}px`,
  overflow: 'hidden',
}))

const innerStyle = computed(() => ({
  width: `${SLIDE_W}px`,
  height: `${SLIDE_H}px`,
  transform: `scale(${scale.value})`,
  transformOrigin: 'top left',
}))

let ro = null

onMounted(() => {
  scheduleResize()
  if (rootRef.value && typeof ResizeObserver !== 'undefined') {
    ro = new ResizeObserver(scheduleResize)
    ro.observe(rootRef.value)
  }
})

onUnmounted(() => ro?.disconnect())
</script>

<style scoped>
.thumb-root {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #fff;
  border-radius: 2px;
  overflow: hidden;
}
.thumb-stage {
  pointer-events: none;
}
.thumb-inner {
  overflow: hidden;
  background: #fff;
}
.thumb-iframe {
  width: 1920px;
  height: 1080px;
  border: none;
  display: block;
}
.thumb-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c8c6c4;
  font-size: 14px;
  background: #faf9f8;
}
</style>
