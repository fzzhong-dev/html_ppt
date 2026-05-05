<template>
  <div class="toolbar">
    <div class="toolbar-group">
      <button @click="$emit('undo')" title="撤销">↩ 撤销</button>
      <button @click="$emit('redo')" title="重做">↪ 重做</button>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <button @click="$emit('add-slide')" title="添加页">＋ 添加页</button>
      <button @click="$emit('copy-slide')" title="复制页">📋 复制页</button>
      <button @click="$emit('delete-slide')" title="删除页">🗑 删除页</button>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <select v-model="currentTheme" @change="$emit('change-theme', currentTheme)">
        <option value="business-blue">🎨 商务蓝</option>
      </select>
      <select v-model="currentFont" @change="$emit('change-font', currentFont)">
        <option value="default">字体</option>
        <option value="yahei">微软雅黑</option>
        <option value="songti">宋体</option>
        <option value="heiti">黑体</option>
      </select>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <button @click="$emit('insert-image')" title="插入图片">🖼 图片</button>
      <button @click="$emit('insert-chart')" title="插入图表">📊 图表</button>
      <button @click="$emit('insert-shape')" title="插入形状">🔷 形状</button>
    </div>
    <div class="toolbar-spacer"></div>
    <div class="toolbar-group">
      <button class="btn-export" @click="$emit('export')" :disabled="exporting">
        📥 导出 PPTX
      </button>
      <button @click="$emit('fullscreen')" title="全屏演示">🖥 演示</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({ exporting: Boolean })
defineEmits(['undo', 'redo', 'add-slide', 'copy-slide', 'delete-slide', 'change-theme', 'change-font', 'insert-image', 'insert-chart', 'insert-shape', 'export', 'fullscreen'])

const currentTheme = ref('business-blue')
const currentFont = ref('default')
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  background: #37474f;
  color: #ccc;
  padding: 6px 12px;
  font-size: 13px;
  gap: 4px;
  flex-shrink: 0;
}
.toolbar-group { display: flex; gap: 4px; align-items: center; }
.toolbar-divider { width: 1px; height: 24px; background: #546e7a; margin: 0 8px; }
.toolbar-spacer { flex: 1; }
.toolbar button {
  background: #455a64;
  color: #ccc;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
}
.toolbar button:hover { background: #546e7a; }
.toolbar button:disabled { opacity: 0.5; cursor: not-allowed; }
.toolbar select {
  background: #455a64;
  color: #ccc;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.btn-export { background: #4CAF50 !important; color: white !important; font-weight: 600; }
.btn-export:hover { background: #388E3C !important; }
</style>
