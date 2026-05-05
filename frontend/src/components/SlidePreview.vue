<template>
  <div class="preview-area">
    <div class="preview-container">
      <iframe
        v-if="slide"
        :srcdoc="slide.html_content"
        class="preview-iframe"
        sandbox="allow-same-origin"
      ></iframe>
      <div v-else class="preview-empty">选择一张幻灯片</div>
    </div>
    <div class="preview-nav">
      <button @click="$emit('prev')" :disabled="!canPrev">上一页</button>
      <span>{{ current + 1 }} / {{ total }}</span>
      <button @click="$emit('next')" :disabled="!canNext">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  slide: Object,
  current: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
})
defineEmits(['prev', 'next'])

const canPrev = computed(() => props.current > 0)
const canNext = computed(() => props.current < props.total - 1)
</script>

<style scoped>
.preview-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #d0d0d0;
  padding: 16px;
}
.preview-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-iframe {
  width: 90%;
  aspect-ratio: 16/9;
  border: none;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
  border-radius: 4px;
  background: white;
}
.preview-empty {
  color: #999;
  font-size: 18px;
}
.preview-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 8px;
}
.preview-nav button {
  padding: 6px 16px;
  border: 1px solid #bbb;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.preview-nav button:disabled { opacity: 0.4; cursor: not-allowed; }
.preview-nav span { font-size: 13px; color: #666; }
</style>
