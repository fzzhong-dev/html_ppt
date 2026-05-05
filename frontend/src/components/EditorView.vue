<template>
  <div class="editor">
    <Toolbar
      :exporting="exporting"
      @export="handleExport"
      @fullscreen="handleFullscreen"
    />
    <div class="editor-body">
      <SlideList
        :slides="store.presentation?.slides || []"
        :currentIndex="store.currentSlideIndex"
        @select="store.selectSlide"
      />
      <SlidePreview
        :slide="store.currentSlide"
        :current="store.currentSlideIndex"
        :total="store.slideCount"
        @prev="store.prevSlide"
        @next="store.nextSlide"
      />
      <ChatPanel
        :messages="store.chatHistory"
        :loading="store.loading"
        @send="handleChatSend"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePresentationStore } from '../stores/presentation'
import Toolbar from './Toolbar.vue'
import SlideList from './SlideList.vue'
import SlidePreview from './SlidePreview.vue'
import ChatPanel from './ChatPanel.vue'

const store = usePresentationStore()
const exporting = ref(false)

async function handleExport() {
  exporting.value = true
  try {
    await store.exportToPPTX()
  } finally {
    exporting.value = false
  }
}

function handleFullscreen() {
  const iframe = document.querySelector('.preview-iframe')
  if (iframe?.requestFullscreen) {
    iframe.requestFullscreen()
  }
}

async function handleChatSend(message) {
  await store.modify(message)
}
</script>

<style scoped>
.editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
