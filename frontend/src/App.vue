<template>
  <div v-if="store.restoring" class="app-restoring">
    <div class="app-restoring-spinner"></div>
    <span>正在恢复…</span>
  </div>
  <template v-else>
    <HomePage v-if="!store.presentation" />
    <EditorView v-else />
  </template>
</template>

<script setup>
import { watchEffect, onMounted } from 'vue'
import { usePresentationStore } from './stores/presentation'
import HomePage from './components/HomePage.vue'
import EditorView from './components/EditorView.vue'

const store = usePresentationStore()

onMounted(() => {
  store.loadFromServer()
})

watchEffect(() => {
  document.getElementById('app')?.classList.toggle('app--editor', !!store.presentation)
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }
.app-restoring {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #f3f2f1;
  color: #605e5c;
  font-size: 13px;
}
.app-restoring-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #edebe9;
  border-top-color: #0078d4;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
