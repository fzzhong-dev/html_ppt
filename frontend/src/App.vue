<template>
  <HomePage v-if="!store.presentation" />
  <EditorView v-else />
</template>

<script setup>
import { watchEffect } from 'vue'
import { usePresentationStore } from './stores/presentation'
import HomePage from './components/HomePage.vue'
import EditorView from './components/EditorView.vue'

const store = usePresentationStore()

watchEffect(() => {
  document.getElementById('app')?.classList.toggle('app--editor', !!store.presentation)
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body, #app { height: 100%; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }
</style>
