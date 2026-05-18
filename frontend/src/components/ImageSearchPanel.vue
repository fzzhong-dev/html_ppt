<template>
  <div class="image-panel">
    <div class="image-panel-header">
      <span class="image-panel-title">图片搜索</span>
      <button type="button" class="image-panel-close" @click="$emit('close')">&times;</button>
    </div>
    <div class="image-search-bar">
      <input
        v-model="query"
        placeholder="搜索关键词，如：technology、nature、business…"
        @keyup.enter="handleSearch"
        :disabled="loading"
      />
      <button type="button" @click="handleSearch" :disabled="loading || !query.trim()">
        {{ loading ? '搜索中…' : '搜索' }}
      </button>
    </div>
    <p v-if="error" class="image-error">{{ error }}</p>
    <div v-if="images.length" class="image-grid">
      <div
        v-for="img in images"
        :key="img.id"
        class="image-item"
        @click="$emit('select', img)"
      >
        <img :src="img.preview" :alt="img.alt" loading="lazy" />
        <span class="image-source">{{ img.source }} · {{ img.photographer }}</span>
      </div>
    </div>
    <div v-if="!loading && !images.length && searched" class="image-empty">
      未找到相关图片，请尝试其他关键词
    </div>
    <div v-if="!loading && !images.length && !searched" class="image-empty">
      输入关键词搜索配图，点击图片插入到当前幻灯片
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchImages } from '../api'

const emit = defineEmits(['select', 'close'])

const query = ref('')
const images = ref([])
const loading = ref(false)
const error = ref('')
const searched = ref(false)

async function handleSearch() {
  const q = query.value.trim()
  if (!q) return

  loading.value = true
  error.value = ''
  images.value = []

  try {
    const { data } = await searchImages(q)
    images.value = data.images || []
    searched.value = true
    if (!images.value.length && data.error) {
      error.value = data.error
    }
  } catch (e) {
    error.value =
      e?.response?.data?.detail?.toString?.() ||
      e?.message ||
      '图片搜索失败'
    searched.value = true
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.image-panel {
  width: 312px;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-left: 1px solid #edebe9;
  flex-shrink: 0;
  min-height: 0;
}
.image-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid #edebe9;
  background: #faf9f8;
}
.image-panel-title {
  font-size: 13px;
  font-weight: 700;
  color: #323130;
}
.image-panel-close {
  border: none;
  background: transparent;
  font-size: 18px;
  color: #605e5c;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
.image-panel-close:hover {
  color: #d83b01;
}
.image-search-bar {
  display: flex;
  padding: 10px;
  gap: 8px;
  border-bottom: 1px solid #edebe9;
}
.image-search-bar input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #8a8886;
  border-radius: 2px;
  font-size: 12px;
  outline: none;
  font-family: inherit;
}
.image-search-bar input:focus {
  border-color: #0078d4;
  box-shadow: 0 0 0 1px rgba(0, 120, 212, 0.35);
}
.image-search-bar button {
  background: #0078d4;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 2px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.image-search-bar button:hover:not(:disabled) {
  filter: brightness(1.05);
}
.image-search-bar button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.image-error {
  padding: 10px 12px;
  font-size: 12px;
  color: #d83b01;
  line-height: 1.4;
}
.image-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 10px;
  overflow-y: auto;
  flex: 1;
}
.image-item {
  cursor: pointer;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #edebe9;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.image-item:hover {
  border-color: #0078d4;
  box-shadow: 0 2px 8px rgba(0, 120, 212, 0.15);
}
.image-item img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
}
.image-source {
  display: block;
  padding: 4px 6px;
  font-size: 10px;
  color: #605e5c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.image-empty {
  padding: 24px 12px;
  text-align: center;
  font-size: 12px;
  color: #605e5c;
  line-height: 1.5;
}
</style>
