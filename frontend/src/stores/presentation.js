import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { generatePPT, modifySlide, exportPPTX } from '../api'

export const usePresentationStore = defineStore('presentation', () => {
  const presentation = ref(null)
  const currentSlideIndex = ref(0)
  const chatHistory = ref([])
  const loading = ref(false)

  const currentSlide = computed(() => {
    if (!presentation.value || !presentation.value.slides.length) return null
    return presentation.value.slides[currentSlideIndex.value]
  })

  const slideCount = computed(() => presentation.value?.slides.length || 0)

  async function generate(topic, outline, templateId) {
    loading.value = true
    try {
      const { data } = await generatePPT(topic, outline, templateId)
      presentation.value = data
      currentSlideIndex.value = 0
      chatHistory.value = []
    } finally {
      loading.value = false
    }
  }

  async function modify(instruction) {
    if (!currentSlide.value) return
    loading.value = true
    chatHistory.value.push({ role: 'user', content: instruction })
    try {
      const { data } = await modifySlide(
        presentation.value.id,
        currentSlide.value.id,
        instruction,
        chatHistory.value.slice(0, -1),
      )
      const idx = presentation.value.slides.findIndex(s => s.id === data.id)
      if (idx !== -1) {
        presentation.value.slides[idx] = data
      }
      chatHistory.value.push({ role: 'assistant', content: '已修改完成' })
    } finally {
      loading.value = false
    }
  }

  async function exportToPPTX() {
    if (!presentation.value) return
    const { data } = await exportPPTX(presentation.value.id)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `${presentation.value.title}.pptx`
    a.click()
    URL.revokeObjectURL(url)
  }

  function selectSlide(index) {
    currentSlideIndex.value = index
  }

  function nextSlide() {
    if (currentSlideIndex.value < slideCount.value - 1) {
      currentSlideIndex.value++
    }
  }

  function prevSlide() {
    if (currentSlideIndex.value > 0) {
      currentSlideIndex.value--
    }
  }

  return {
    presentation, currentSlideIndex, chatHistory, loading,
    currentSlide, slideCount,
    generate, modify, exportToPPTX, selectSlide, nextSlide, prevSlide,
  }
})
