<template>
  <div class="home">
    <div class="home-card wide">
      <h1 class="home-title">HTML PPT 生成器</h1>
      <p class="home-desc">
        填写主题；提纲可完全手写（不需要 AI），也可留空由模型自行展开。需要时在草稿上点击「AI 辅助生成提纲」润色扩展。
      </p>

      <div v-if="llmBanner" class="llm-banner">
        <span class="llm-banner-label">当前推理通道</span>
        <span class="llm-banner-val">{{ llmBanner.effective }}</span>
        <span v-if="llmBanner.fallback" class="llm-banner-warn">
          （已自动切换：{{ llmBanner.configured }} 未配置可用密钥）
        </span>
      </div>

      <div class="form-group">
        <label>主题（必填）</label>
        <input v-model="topic" placeholder="例如：企业数字化转型实践" />
      </div>

      <div class="form-group">
        <label>提纲（可选）</label>
        <p class="field-hint">
          支持 Markdown / 纯文本；若不填，模型会按主题自动搭建叙事结构。已写好提纲时无需再点 AI。
        </p>
        <textarea
          v-model="outlineDraft"
          rows="12"
          placeholder="例：&#10;1. 背景与挑战&#10;2. 目标与指标&#10;3. 实施路径 …"
        />
      </div>

      <div class="form-group inline-number">
        <label for="pc">幻灯片页数</label>
        <input
          id="pc"
          v-model.number="pageCount"
          type="number"
          min="4"
          max="16"
          class="num-input"
        />
        <span class="field-hint inline">建议 8～12 页以获得足够正文与图表空间。</span>
      </div>

      <div v-if="visibleSteps.length" class="steps-panel">
        <div class="steps-title">
          AI 提纲辅助 · 策划摘要
          <span v-if="outlineBusy" class="steps-loading">推理中…</span>
        </div>
        <ul class="steps-list">
          <li v-for="(s, i) in visibleSteps" :key="i" class="step-row done">
            <span class="step-idx">{{ i + 1 }}</span>
            <span>{{ s }}</span>
          </li>
          <li v-if="outlineBusy" class="step-row streaming">
            <span class="step-idx step-idx-pending">…</span>
            <span class="step-pending">正在生成下一条…</span>
          </li>
        </ul>
      </div>

      <div class="btn-row">
        <button
          type="button"
          class="btn-secondary"
          @click="handleAiAssist"
          :disabled="!topic.trim() || outlineBusy || pptBusy"
        >
          {{ outlineBusy ? '提纲推理中…' : 'AI 辅助生成提纲' }}
        </button>
        <button
          type="button"
          class="btn-primary btn-split"
          @click="handleGeneratePpt"
          :disabled="!topic.trim() || pptBusy || outlineBusy || invalidPageCount"
        >
          {{ pptBusy
            ? (progressTotal > 0
              ? `正在生成… ${progressCurrent}/${progressTotal}`
              : '正在准备…')
            : '生成幻灯片'
          }}
        </button>
      </div>

      <div v-if="pptBusy && progressTotal > 0" class="gen-progress">
        <div
          class="gen-progress-bar"
          :style="{ width: (progressCurrent / progressTotal * 100) + '%' }"
        ></div>
      </div>

      <p v-if="errorMsg" class="form-error">{{ errorMsg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePresentationStore } from '../stores/presentation'
import { proposeOutline, proposeOutlineStream, getLLMStatus } from '../api'

const store = usePresentationStore()

const topic = ref('')
const outlineDraft = ref('')
const pageCount = ref(8)
const outlineBusy = ref(false)
const pptBusy = ref(false)
const errorMsg = ref('')
const visibleSteps = ref([])
const llmEffective = ref('')
const llmConfigured = ref('')
const llmFallback = ref(false)

const invalidPageCount = computed(() => {
  const n = Number(pageCount.value)
  return !Number.isFinite(n) || n < 4 || n > 16
})

const progressCurrent = computed(() => store.generationProgress.current)
const progressTotal = computed(() => store.generationProgress.total)

const llmBanner = computed(() => {
  if (!llmEffective.value) return null
  return {
    effective: llmEffective.value,
    configured: llmConfigured.value,
    fallback: llmFallback.value,
  }
})

async function loadLlmStatus() {
  try {
    const { data } = await getLLMStatus()
    llmEffective.value = data.effective_provider || ''
    llmConfigured.value = data.configured_default || ''
    llmFallback.value = !!data.auto_fallback_used
  } catch {
    llmEffective.value = ''
  }
}

async function handleAiAssist() {
  errorMsg.value = ''
  if (!topic.value.trim()) return
  outlineBusy.value = true
  visibleSteps.value = []

  try {
    const response = await proposeOutlineStream(
      topic.value.trim(),
      outlineDraft.value.trim() || undefined,
    )

    if (!response.ok) {
      const fallback = await proposeOutline(topic.value.trim(), outlineDraft.value.trim() || undefined)
      const data = fallback.data
      for (const s of data.steps || []) {
        visibleSteps.value.push(s)
      }
      if (data.outline) outlineDraft.value = data.outline
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
        const evt = JSON.parse(line.slice(6))

        if (evt.type === 'error') {
          errorMsg.value = evt.message || '提纲生成出错'
          return
        }
        if (evt.type === 'step') {
          visibleSteps.value.push(evt.text)
        } else if (evt.type === 'outline_chunk') {
          outlineDraft.value = evt.text
        } else if (evt.type === 'done') {
          if (evt.outline) outlineDraft.value = evt.outline
        }
      }
    }
  } catch (e) {
    errorMsg.value =
      e?.response?.data?.detail?.toString?.() ||
      e?.message ||
      '提纲辅助失败，请检查模型密钥与网络。'
  } finally {
    outlineBusy.value = false
  }
}

function clampPageCount() {
  let n = Math.round(Number(pageCount.value))
  if (!Number.isFinite(n)) n = 8
  pageCount.value = Math.min(16, Math.max(4, n))
}

async function handleGeneratePpt() {
  errorMsg.value = ''
  clampPageCount()
  if (!topic.value.trim()) return
  pptBusy.value = true
  try {
    const outline = outlineDraft.value.trim()
    await store.generate(topic.value.trim(), outline || '', pageCount.value)
  } catch (e) {
    errorMsg.value =
      e?.response?.data?.detail?.toString?.() ||
      e?.message ||
      '生成失败，请稍后重试。'
  } finally {
    pptBusy.value = false
  }
}

onMounted(() => {
  loadLlmStatus()
})
</script>

<style scoped>
.home {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 12px;
  background: linear-gradient(135deg, #f3f2f1 0%, #edebe9 45%, #e1dfdd 100%);
}
.home-card {
  background: white;
  border-radius: 4px;
  padding: 36px 40px;
  width: min(760px, calc(100vw - 24px));
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08), 0 0 1px rgba(0, 0, 0, 0.08);
  border: 1px solid #edebe9;
}
.home-title {
  font-size: 22px;
  font-weight: 700;
  color: #323130;
  margin-bottom: 6px;
}
.home-desc {
  color: #605e5c;
  margin-bottom: 18px;
  font-size: 13px;
  line-height: 1.55;
}
.llm-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 10px;
  padding: 10px 12px;
  margin-bottom: 18px;
  font-size: 12px;
  background: #faf9f8;
  border: 1px solid #edebe9;
  border-radius: 2px;
}
.llm-banner-label {
  font-weight: 700;
  color: #605e5c;
}
.llm-banner-val {
  font-weight: 700;
  color: #0078d4;
}
.llm-banner-warn {
  color: #d83b01;
  flex-basis: 100%;
}
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #323130;
  margin-bottom: 6px;
}
.field-hint {
  margin: 0 0 8px;
  font-size: 12px;
  color: #605e5c;
  line-height: 1.45;
}
.field-hint.inline {
  margin: 0 0 0 12px;
  display: inline;
}
.inline-number {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.inline-number label {
  margin-bottom: 0;
}
.num-input {
  width: 72px;
  padding: 6px 8px;
  border: 1px solid #8a8886;
  border-radius: 2px;
  font-size: 14px;
}
.form-group input[type='text'],
.form-group textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #8a8886;
  border-radius: 2px;
  font-size: 14px;
  font-family: inherit;
  outline: none;
}
.form-group textarea {
  font-family: ui-monospace, Consolas, 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  line-height: 1.45;
  resize: vertical;
}
.form-group input:focus,
.form-group textarea:focus {
  border-color: #0078d4;
  box-shadow: 0 0 0 1px rgba(0, 120, 212, 0.35);
}
.btn-primary {
  padding: 10px 14px;
  background: #0078d4;
  color: white;
  border: none;
  border-radius: 2px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn-primary:hover:not(:disabled) {
  filter: brightness(1.05);
}
.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.btn-secondary {
  padding: 10px 14px;
  background: #fff;
  color: #323130;
  border: 1px solid #8a8886;
  border-radius: 2px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.btn-secondary:hover:not(:disabled) {
  background: #f3f2f1;
}
.btn-secondary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 8px;
}
.btn-split {
  flex: 1;
  min-width: 200px;
}
.steps-panel {
  margin: 14px 0 18px;
  padding: 12px 14px;
  background: #faf9f8;
  border: 1px solid #edebe9;
  border-radius: 2px;
}
.steps-title {
  font-size: 11px;
  font-weight: 700;
  color: #605e5c;
  margin-bottom: 8px;
}
.steps-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.step-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  font-size: 13px;
  color: #323130;
  line-height: 1.45;
  padding: 6px 0;
  border-bottom: 1px solid #edebe9;
}
.step-row:last-child {
  border-bottom: none;
}
.step-idx {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #0078d4;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.step-idx-pending {
  background: #edebe9;
  color: #605e5c;
  animation: step-pulse 1.2s ease-in-out infinite;
}
.step-pending {
  color: #605e5c;
  font-style: italic;
}
.steps-loading {
  font-weight: 400;
  color: #0078d4;
  margin-left: 8px;
  font-size: 11px;
}
.streaming {
  border-bottom: none;
}
@keyframes step-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
.form-error {
  margin-top: 14px;
  font-size: 12px;
  color: #d83b01;
  line-height: 1.4;
}
.gen-progress {
  margin-top: 12px;
  height: 6px;
  background: #edebe9;
  border-radius: 3px;
  overflow: hidden;
}
.gen-progress-bar {
  height: 100%;
  background: #0078d4;
  border-radius: 3px;
  transition: width 0.3s ease;
}
</style>
