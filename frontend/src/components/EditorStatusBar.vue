<template>
  <footer class="oo-statusbar" role="status" aria-label="状态栏">
    <div class="oo-status-left">
      <span class="oo-status-label">
        幻灯片 {{ displayIndex }} / {{ displayTotal }}
      </span>
      <span class="oo-status-sep" aria-hidden="true" />
      <span class="oo-status-placeholder" title="占位">拼写检查：关闭</span>
    </div>
    <div class="oo-status-right">
      <div class="oo-zoom" role="group" aria-label="缩放">
        <button
          type="button"
          class="oo-zoom-btn"
          title="缩小"
          :disabled="!canZoomOut"
          @click="$emit('zoom-out')"
        >
          −
        </button>
        <select
          class="oo-zoom-select"
          :value="selectValue"
          aria-label="缩放比例"
          @change="onSelectChange"
        >
          <option value="fit">{{ fitOptionLabel }}</option>
          <option v-for="z in zoomSteps" :key="z" :value="String(z)">{{ z }}%</option>
        </select>
        <button
          type="button"
          class="oo-zoom-btn"
          title="放大"
          :disabled="!canZoomIn"
          @click="$emit('zoom-in')"
        >
          +
        </button>
      </div>
      <span class="oo-zoom-readout" title="当前画布缩放">{{ effectiveZoom }}%</span>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentIndex: { type: Number, default: 0 },
  slideCount: { type: Number, default: 0 },
  /** 'fit' | fixed percents when manual */
  zoomMode: { type: String, default: 'fit' },
  zoomPercent: { type: Number, default: 100 },
  /** Actual rendered scale ×100, for readout */
  effectiveZoom: { type: Number, default: 100 },
})

const emit = defineEmits(['zoom-out', 'zoom-in', 'zoom-fit', 'zoom-percent'])

const zoomSteps = [50, 75, 100, 125, 150, 200]

const displayIndex = computed(() =>
  props.slideCount <= 0 ? 0 : Math.min(props.currentIndex + 1, props.slideCount),
)
const displayTotal = computed(() => props.slideCount)

const fitOptionLabel = computed(() => {
  if (props.zoomMode === 'fit') {
    return `适应窗口 (${props.effectiveZoom}%)`
  }
  return '适应窗口'
})

const selectValue = computed(() =>
  props.zoomMode === 'fit' ? 'fit' : String(props.zoomPercent),
)

const canZoomOut = computed(() => props.effectiveZoom > 25)
const canZoomIn = computed(() => props.effectiveZoom < 400)

function onSelectChange(e) {
  const v = e.target.value
  if (v === 'fit') {
    emit('zoom-fit')
  } else {
    const n = Number(v)
    if (!Number.isNaN(n)) emit('zoom-percent', n)
  }
}
</script>

<style scoped>
.oo-statusbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: 26px;
  padding: 0 10px 0 12px;
  background: var(--oo-status-bg, #f3f2f1);
  border-top: 1px solid var(--oo-status-border, #d2d0ce);
  font-size: 11px;
  color: var(--oo-text-secondary, #605e5c);
}
.oo-status-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.oo-status-label {
  font-weight: 600;
  color: var(--oo-text, #323130);
  white-space: nowrap;
}
.oo-status-sep {
  width: 1px;
  height: 14px;
  background: var(--oo-border-strong, #d2d0ce);
}
.oo-status-placeholder {
  opacity: 0.85;
  white-space: nowrap;
}
.oo-status-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.oo-zoom {
  display: flex;
  align-items: center;
  gap: 4px;
}
.oo-zoom-btn {
  width: 22px;
  height: 20px;
  padding: 0;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  border-radius: 2px;
  background: var(--oo-chrome-bg, #fff);
  color: var(--oo-text, #323130);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}
.oo-zoom-btn:hover:not(:disabled) {
  background: var(--oo-chrome-muted-hover, #edebe9);
}
.oo-zoom-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.oo-zoom-select {
  height: 22px;
  min-width: 120px;
  padding: 0 6px;
  border: 1px solid var(--oo-border-strong, #d2d0ce);
  border-radius: 2px;
  font-size: 11px;
  background: var(--oo-chrome-bg, #fff);
  color: var(--oo-text, #323130);
}
.oo-zoom-readout {
  min-width: 2.5rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--oo-text-secondary, #605e5c);
}
</style>
