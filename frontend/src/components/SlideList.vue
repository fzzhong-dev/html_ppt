<template>
  <aside class="slide-pane" aria-label="幻灯片缩略图">
    <div class="slide-pane-inner">
      <div class="slide-pane-label">幻灯片</div>
      <div class="slide-strip" ref="stripEl">
        <div
          v-for="(slide, index) in slides"
          :key="slide.id"
          class="slide-card-wrap"
          :class="{
            active: index === currentIndex,
            'drag-over-top': dragOverIndex === index && dropPosition === 'top',
            'drag-over-bottom': dragOverIndex === index && dropPosition === 'bottom',
          }"
          draggable="true"
          @dragstart="onDragStart(index, $event)"
          @dragover.prevent="onDragOver(index, $event)"
          @dragleave="onDragLeave"
          @drop="onDrop(index)"
          @dragend="onDragEnd"
        >
          <button
            type="button"
            class="slide-card"
            :class="{ active: index === currentIndex }"
            @click="$emit('select', index)"
          >
            <span class="slide-card-num">{{ index + 1 }}</span>
            <SlideThumbnail :html-content="slide.html_content || ''" />
          </button>
        </div>
      </div>
      <div class="slide-pane-footer">
        <button type="button" class="slide-new-slide" title="新建幻灯片（AI）" @click="$emit('add-slide')">
          <span class="slide-new-icon" aria-hidden="true">+</span>
          <span>新建幻灯片</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import SlideThumbnail from './SlideThumbnail.vue'

defineProps({
  slides: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: 0 },
})
const emit = defineEmits(['select', 'add-slide', 'reorder'])

const dragFromIndex = ref(null)
const dragOverIndex = ref(null)
const dropPosition = ref(null) // 'top' or 'bottom'

function onDragStart(index, e) {
  dragFromIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('text/plain', String(index))
}

function onDragOver(index, e) {
  if (dragFromIndex.value === null) return
  e.dataTransfer.dropEffect = 'move'
  const rect = e.currentTarget.getBoundingClientRect()
  const midY = rect.top + rect.height / 2
  dropPosition.value = e.clientY < midY ? 'top' : 'bottom'
  dragOverIndex.value = index
}

function onDragLeave() {
  dragOverIndex.value = null
  dropPosition.value = null
}

function onDrop(toIndex) {
  const from = dragFromIndex.value
  if (from === null || from === toIndex) {
    resetDrag()
    return
  }
  let insertAt = dropPosition.value === 'top' ? toIndex : toIndex + 1
  // Adjust if dragging down
  if (from < insertAt) insertAt--
  if (insertAt === from) {
    resetDrag()
    return
  }
  emit('reorder', { from, to: insertAt })
  resetDrag()
}

function onDragEnd() {
  resetDrag()
}

function resetDrag() {
  dragFromIndex.value = null
  dragOverIndex.value = null
  dropPosition.value = null
}
</script>

<style scoped>
.slide-pane {
  width: 248px;
  flex-shrink: 0;
  background: var(--oo-slide-pane-bg, #f3f2f1);
  border-right: 1px solid var(--oo-border, #edebe9);
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.slide-pane-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 10px 12px 12px;
}
.slide-pane-footer {
  flex-shrink: 0;
  padding-top: 10px;
  margin-top: 8px;
  border-top: 1px solid var(--oo-border, #edebe9);
}
.slide-new-slide {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 2px;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  background: var(--oo-chrome-bg, #fff);
  color: var(--oo-text, #323130);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.slide-new-slide:hover {
  background: var(--oo-chrome-muted-hover, #edebe9);
  border-color: var(--oo-accent-orange, #d83b01);
  color: var(--oo-accent-orange, #d83b01);
}
.slide-new-icon {
  display: inline-flex;
  width: 18px;
  height: 18px;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  font-size: 14px;
  line-height: 1;
  font-weight: 700;
}
.slide-pane-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--oo-text-secondary, #605e5c);
  letter-spacing: 0.02em;
  margin-bottom: 10px;
  padding-left: 2px;
}
.slide-strip {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-right: 4px;
}
.slide-strip::-webkit-scrollbar {
  width: 8px;
}
.slide-strip::-webkit-scrollbar-thumb {
  background: #c8c6c4;
  border-radius: 4px;
}

/* Card wrapper (drag target) */
.slide-card-wrap {
  position: relative;
  border-radius: 3px;
  transition: padding 0.15s ease;
}
.slide-card-wrap.drag-over-top {
  padding-top: 28px;
}
.slide-card-wrap.drag-over-top::before {
  content: '';
  position: absolute;
  top: 12px;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--oo-accent-orange, #d83b01);
  border-radius: 2px;
  z-index: 10;
}
.slide-card-wrap.drag-over-bottom {
  padding-bottom: 28px;
}
.slide-card-wrap.drag-over-bottom::after {
  content: '';
  position: absolute;
  bottom: 12px;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--oo-accent-orange, #d83b01);
  border-radius: 2px;
  z-index: 10;
}

.slide-card {
  position: relative;
  border: none;
  padding: 0;
  margin: 0;
  width: 100%;
  background: transparent;
  cursor: pointer;
  text-align: left;
  border-radius: 2px;
}
.slide-card:focus-visible {
  outline: 2px solid var(--oo-accent-orange, #d83b01);
  outline-offset: 2px;
}
.slide-card::after {
  content: '';
  display: block;
  position: absolute;
  inset: -2px;
  border-radius: 3px;
  pointer-events: none;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
.slide-card:hover::after {
  border-color: #b3b0ad;
}
.slide-card.active::after {
  border: 2px solid var(--oo-accent-orange, #d83b01);
  box-shadow: 0 0 0 1px rgba(216, 59, 1, 0.25), 0 2px 8px rgba(0, 0, 0, 0.08);
}
.slide-card-num {
  position: absolute;
  top: -2px;
  left: -2px;
  z-index: 2;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: #323130;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid #edebe9;
  border-radius: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}
.slide-card.active .slide-card-num {
  color: var(--oo-accent-orange, #d83b01);
  border-color: rgba(216, 59, 1, 0.35);
}
</style>
