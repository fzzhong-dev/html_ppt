<template>
  <div class="slide-list">
    <div class="slide-list-header">幻灯片 ({{ slides.length }})</div>
    <div
      v-for="(slide, index) in slides"
      :key="slide.id"
      class="slide-thumb"
      :class="{ active: index === currentIndex }"
      @click="$emit('select', index)"
    >
      <div class="slide-thumb-inner">
        <span>{{ getPageLabel(index) }}</span>
      </div>
      <span class="slide-number">{{ index + 1 }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  slides: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: 0 },
})
defineEmits(['select'])

function getPageLabel(index) {
  const labels = ['封面页', '目录页']
  if (index >= labels.length && index < labels.length + 10) return `内容页 ${index - labels.length + 1}`
  if (index === labels.length + 10) return '结尾页'
  const total = index + 1
  return total <= 2 ? labels[index] : `第 ${total} 页`
}
</script>

<style scoped>
.slide-list {
  width: 180px;
  background: #2c2c2c;
  padding: 10px;
  overflow-y: auto;
  flex-shrink: 0;
}
.slide-list-header {
  color: #aaa;
  font-size: 12px;
  text-align: center;
  margin-bottom: 8px;
}
.slide-thumb {
  position: relative;
  margin-bottom: 8px;
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 4px;
  overflow: hidden;
}
.slide-thumb.active { border-color: #42a5f5; }
.slide-thumb-inner {
  background: #3c3c3c;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 11px;
}
.slide-number {
  position: absolute;
  bottom: 2px;
  right: 4px;
  font-size: 10px;
  color: #666;
}
</style>
