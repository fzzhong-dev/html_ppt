import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  generatePPT,
  generatePPTStream,
  modifySlide,
  exportPPTX,
  patchSlideHtml,
  insertSlide as insertSlideApi,
  deleteSlideApi,
  savePresentation,
  getPresentation,
} from '../api'

const MAX_HISTORY = 50
const LAST_ID_KEY = 'html-ppt-last-id'

export const usePresentationStore = defineStore('presentation', () => {
  const presentation = ref(null)
  const restoring = ref(true) // true until first restore attempt finishes
  const currentSlideIndex = ref(0)
  const chatHistory = ref([])
  const loading = ref(false)
  const generationProgress = ref({ current: 0, total: 0 })

  // undo/redo: store snapshots of the slides array
  const undoStack = ref([])
  const redoStack = ref([])

  // Auto-save
  const dirty = ref(false)
  let _saveTimer = null
  const AUTOSAVE_INTERVAL = 30_000

  function markDirty() {
    if (!presentation.value) return
    dirty.value = true
    if (!_saveTimer) {
      _saveTimer = setInterval(_autoSave, AUTOSAVE_INTERVAL)
    }
  }

  async function _autoSave() {
    if (!dirty.value || !presentation.value) return
    try {
      await savePresentation(presentation.value.id)
      dirty.value = false
    } catch (e) {
      console.error('auto-save failed', e)
    }
  }

  function stopAutoSave() {
    if (_saveTimer) {
      clearInterval(_saveTimer)
      _saveTimer = null
    }
  }

  function _snapshot() {
    if (!presentation.value) return
    undoStack.value.push(JSON.parse(JSON.stringify(presentation.value.slides)))
    if (undoStack.value.length > MAX_HISTORY) {
      undoStack.value.shift()
    }
    redoStack.value = []
  }

  const canUndo = computed(() => undoStack.value.length > 0)
  const canRedo = computed(() => redoStack.value.length > 0)

  function undo() {
    if (!canUndo.value || !presentation.value) return
    redoStack.value.push(JSON.parse(JSON.stringify(presentation.value.slides)))
    presentation.value.slides = undoStack.value.pop()
    if (currentSlideIndex.value >= presentation.value.slides.length) {
      currentSlideIndex.value = Math.max(0, presentation.value.slides.length - 1)
    }
    _renumber()
    markDirty()
  }

  function redo() {
    if (!canRedo.value || !presentation.value) return
    undoStack.value.push(JSON.parse(JSON.stringify(presentation.value.slides)))
    presentation.value.slides = redoStack.value.pop()
    if (currentSlideIndex.value >= presentation.value.slides.length) {
      currentSlideIndex.value = Math.max(0, presentation.value.slides.length - 1)
    }
    _renumber()
    markDirty()
  }

  function _renumber() {
    presentation.value.slides.forEach((s, i) => {
      s.page_number = i + 1
    })
  }

  const currentSlide = computed(() => {
    if (!presentation.value || !presentation.value.slides.length) return null
    return presentation.value.slides[currentSlideIndex.value]
  })

  const slideCount = computed(() => presentation.value?.slides.length || 0)

  async function patchCurrentSlideHtml(html) {
    if (!presentation.value || !currentSlide.value) return
    _snapshot()
    const sid = currentSlide.value.id
    const idx = currentSlideIndex.value
    presentation.value.slides[idx].html_content = html
    markDirty()
    try {
      await patchSlideHtml(presentation.value.id, sid, html)
      dirty.value = false
    } catch (e) {
      console.error(e)
    }
  }

  function applyHtmlTransform(transformFn) {
    const slide = currentSlide.value
    if (!slide || !presentation.value || typeof transformFn !== 'function') return
    const next = transformFn(slide.html_content)
    if (typeof next === 'string' && next !== slide.html_content) {
      patchCurrentSlideHtml(next)
    }
  }

  async function addBlankSlide() {
    if (!presentation.value) return
    const blank = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920"/><style>html,body{margin:0;padding:0;}body{width:1920px;height:1080px;box-sizing:border-box;background:#ffffff;font-family:"Microsoft YaHei","PingFang SC",sans-serif;}</style></head><body><p style="margin:56px;font-size:28px;color:#323130;">空白页 — 可在上方切换「可视化」或「HTML代码」编辑。</p></body></html>`
    _snapshot()
    try {
      const { data } = await insertSlideApi(presentation.value.id, {
        html_content: blank,
        after_index: currentSlideIndex.value,
      })
      presentation.value.slides.splice(currentSlideIndex.value + 1, 0, data)
      _renumber()
      currentSlideIndex.value++
    } catch (e) {
      console.error(e)
    }
  }

  async function generate(topic, outline, pageCount = 8, creativeMode = true, templateId) {
    loading.value = true
    generationProgress.value = { current: 0, total: pageCount }

    try {
      const response = await generatePPTStream(topic, outline, pageCount, creativeMode, templateId)
      if (!response.ok) {
        const fallback = await generatePPT(topic, outline, pageCount, creativeMode, templateId)
        presentation.value = fallback.data
        currentSlideIndex.value = 0
        chatHistory.value = []
        undoStack.value = []
        redoStack.value = []
        localStorage.setItem(LAST_ID_KEY, fallback.data.id)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))

          if (data.type === 'error') {
            throw new Error(data.message || '生成演示文稿失败')
          }
          if (data.type === 'meta') {
            presentation.value = {
              id: data.presentation_id,
              title: data.title,
              template_id: 'generated',
              theme: 'default',
              slides: [],
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }
            localStorage.setItem(LAST_ID_KEY, data.presentation_id)
            currentSlideIndex.value = 0
            chatHistory.value = []
            undoStack.value = []
            redoStack.value = []
            generationProgress.value.total = data.total
          } else if (data.type === 'slide') {
            presentation.value.slides.push(data.slide)
            generationProgress.value.current = presentation.value.slides.length
            currentSlideIndex.value = presentation.value.slides.length - 1
          } else if (data.type === 'done') {
            // generation complete
          }
        }
      }
    } finally {
      loading.value = false
      generationProgress.value = { current: 0, total: 0 }
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
      _snapshot()
      const idx = presentation.value.slides.findIndex(s => s.id === data.id)
      if (idx !== -1) {
        presentation.value.slides[idx] = data
      }
      chatHistory.value.push({
        role: 'assistant',
        content: `已按指令修改第 ${idx + 1} 页：「${instruction.slice(0, 30)}${instruction.length > 30 ? '…' : ''}」`,
      })
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

  function reorderSlides(from, to) {
    if (!presentation.value || from === to) return
    _snapshot()
    const slides = presentation.value.slides
    const [moved] = slides.splice(from, 1)
    slides.splice(to, 0, moved)
    _renumber()
    // Keep current slide selected
    const curId = currentSlide.value?.id
    if (curId) {
      const newIdx = slides.findIndex(s => s.id === curId)
      if (newIdx >= 0) currentSlideIndex.value = newIdx
    }
    markDirty()
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

  async function copySlide() {
    if (!currentSlide.value || !presentation.value) return
    _snapshot()
    try {
      const { data } = await insertSlideApi(presentation.value.id, {
        html_content: currentSlide.value.html_content,
        after_index: currentSlideIndex.value,
      })
      presentation.value.slides.splice(currentSlideIndex.value + 1, 0, data)
      _renumber()
      currentSlideIndex.value++
    } catch (e) {
      console.error(e)
    }
  }

  async function deleteSlide() {
    if (!presentation.value || slideCount.value <= 1) return
    _snapshot()
    const sid = currentSlide.value.id
    const idx = currentSlideIndex.value
    try {
      await deleteSlideApi(presentation.value.id, sid)
      presentation.value.slides.splice(idx, 1)
      _renumber()
      if (currentSlideIndex.value >= slideCount.value) {
        currentSlideIndex.value = Math.max(0, slideCount.value - 1)
      }
    } catch (e) {
      console.error(e)
    }
  }

  async function addSlide() {
    if (!presentation.value) return
    loading.value = true
    const slidesArr = presentation.value.slides
    const context = slidesArr
      .map((s, i) => `第${i + 1}页: ${i === 0 ? '封面' : i === slidesArr.length - 1 ? '结尾' : '正文'}`)
      .join('\n')
    const insertAfter = currentSlideIndex.value
    const instruction = `这是新建的一页幻灯片（当前只有占位符）。请替换为本页完整 HTML 文档（1920×1080 画布），内容与演示文稿「${presentation.value.title}」主题一致，风格与相邻页面协调。不要引用其它页的 DOM，只输出这一页的完整 HTML。`
    const systemMsg = `当前演示文稿共 ${slideCount.value} 页（插入占位后的索引：新页在第 ${insertAfter + 2} 页）。上下文：\n${context}`
    const placeholder = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/><style>html,body{margin:0;}body{width:1920px;height:1080px;box-sizing:border-box;background:#faf9f8;font-family:"Microsoft YaHei","PingFang SC",sans-serif;display:flex;align-items:center;justify-content:center;color:#605e5c;font-size:26px;}</style></head><body><span>正在生成新页…</span></body></html>`
    chatHistory.value.push({ role: 'user', content: instruction })
    try {
      _snapshot()
      const { data: newSlide } = await insertSlideApi(presentation.value.id, {
        html_content: placeholder,
        after_index: insertAfter,
      })
      presentation.value.slides.splice(insertAfter + 1, 0, newSlide)
      _renumber()
      currentSlideIndex.value = insertAfter + 1

      const { data } = await modifySlide(
        presentation.value.id,
        newSlide.id,
        instruction,
        [{ role: 'system', content: systemMsg }],
      )
      const idx = presentation.value.slides.findIndex((s) => s.id === newSlide.id)
      if (idx !== -1) {
        presentation.value.slides[idx] = data
      }
      chatHistory.value.push({ role: 'assistant', content: '已添加新幻灯片' })
    } finally {
      loading.value = false
    }
  }

  async function loadFromServer() {
    const lastId = localStorage.getItem(LAST_ID_KEY)
    if (!lastId) {
      restoring.value = false
      return false
    }
    try {
      const { data } = await getPresentation(lastId)
      if (data && data.slides?.length) {
        presentation.value = data
        currentSlideIndex.value = 0
        chatHistory.value = []
        undoStack.value = []
        redoStack.value = []
        restoring.value = false
        return true
      }
    } catch {
      // presentation no longer exists on server
    }
    localStorage.removeItem(LAST_ID_KEY)
    restoring.value = false
    return false
  }

  function reset() {
    stopAutoSave()
    dirty.value = false
    restoring.value = false
    localStorage.removeItem(LAST_ID_KEY)
    presentation.value = null
    currentSlideIndex.value = 0
    chatHistory.value = []
    undoStack.value = []
    redoStack.value = []
  }

  async function loadFromServerById(id) {
    try {
      const { data } = await getPresentation(id)
      if (data && data.slides?.length) {
        presentation.value = data
        currentSlideIndex.value = 0
        chatHistory.value = []
        undoStack.value = []
        redoStack.value = []
        localStorage.setItem(LAST_ID_KEY, id)
        restoring.value = false
        return data
      }
    } catch {
      // presentation no longer exists
    }
    return null
  }

  return {
    presentation, currentSlideIndex, chatHistory, loading, generationProgress, restoring,
    currentSlide, slideCount,
    canUndo, canRedo, dirty,
    generate, modify, exportToPPTX, selectSlide, nextSlide, prevSlide,
    undo, redo, copySlide, deleteSlide, addSlide, addBlankSlide, reorderSlides, reset,
    loadFromServer, loadFromServerById,
    patchCurrentSlideHtml,
    applyHtmlTransform,
  }
})
