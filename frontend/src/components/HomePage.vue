<template>
  <div class="home">
    <div class="home-card">
      <h1 class="home-title">HTML PPT 生成器</h1>
      <p class="home-desc">输入主题，AI 自动生成精美演示文稿</p>

      <div class="form-group">
        <label>主题</label>
        <input v-model="topic" placeholder="例如：人工智能的未来发展" @keyup.enter="handleGenerate" />
      </div>

      <div class="form-group">
        <label>大纲（可选）</label>
        <textarea v-model="outline" placeholder="输入你的大纲，每行一个要点..." rows="4"></textarea>
      </div>

      <div class="form-group">
        <label>模板</label>
        <select v-model="templateId">
          <option value="business-blue">商务蓝</option>
        </select>
      </div>

      <button class="btn-primary" @click="handleGenerate" :disabled="!topic || loading">
        {{ loading ? '生成中...' : '生成 PPT' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePresentationStore } from '../stores/presentation'

const store = usePresentationStore()
const topic = ref('')
const outline = ref('')
const templateId = ref('business-blue')
const loading = ref(false)

async function handleGenerate() {
  if (!topic.value) return
  loading.value = true
  try {
    await store.generate(topic.value, outline.value, templateId.value)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%);
}
.home-card {
  background: white;
  border-radius: 16px;
  padding: 48px;
  width: 500px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}
.home-title {
  font-size: 28px;
  color: #0d47a1;
  margin-bottom: 8px;
}
.home-desc {
  color: #666;
  margin-bottom: 32px;
  font-size: 14px;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}
.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #1565c0;
}
.btn-primary {
  width: 100%;
  padding: 12px;
  background: #1565c0;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover { background: #0d47a1; }
.btn-primary:disabled { background: #90caf9; cursor: not-allowed; }
</style>
