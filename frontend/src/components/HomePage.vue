<template>
  <div class="home">
    <div class="home-card">
      <h1 class="home-title">HTML PPT 生成器</h1>
      <p class="home-desc">
        填写主题；提纲可完全手写（不需要 AI），也可留空由模型自行展开。需要时在草稿上点击「AI 辅助生成提纲」润色扩展。
      </p>

      <!-- Quick-start: inline topic chips -->
      <div class="quick-chips">
        <span class="quick-chips-label">快速开始：</span>
        <button
          v-for="qt in quickTopics"
          :key="qt.label"
          type="button"
          class="quick-chip"
          @click="applyQuickTopic(qt)"
        >{{ qt.icon }} {{ qt.label }}</button>
      </div>

      <div v-if="llmBanner" class="llm-banner">
        <span class="llm-banner-label">当前推理通道</span>
        <span class="llm-banner-val">{{ llmBanner.effective }}</span>
        <span v-if="llmBanner.fallback" class="llm-banner-warn">
          （已自动切换：{{ llmBanner.configured }} 未配置可用密钥）
        </span>
      </div>

      <div class="form-group">
        <label>选择模板风格</label>
        <div v-if="templateLoading" class="template-loading">加载模板中…</div>
        <div v-else class="template-grid">
          <button
            v-for="t in templates"
            :key="t.id"
            type="button"
            class="template-card"
            :class="{ active: selectedTemplate === t.id }"
            @click="selectedTemplate = t.id"
          >
            <div
              class="template-swatch"
              :style="swatchStyle(t)"
            >
              <div class="swatch-label">{{ t.name }}</div>
            </div>
          </button>
        </div>
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
        <span class="field-hint inline">建议 8～12 页；页数多不等于要多画图。</span>
      </div>

      <div class="form-group checkbox-row">
        <label class="checkbox-label">
          <input v-model="creativeMode" type="checkbox" />
          <span>创意模式（推荐）：版式与配色随主题发挥，少图标与套路模板</span>
        </label>
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

      <!-- Recent presentations: inline section -->
      <div v-if="recentPresentations.length" class="history-section">
        <div class="history-header">
          <span class="history-title-label">最近编辑</span>
          <button type="button" class="btn-clear-history" @click="clearHistory">清除全部</button>
        </div>
        <div class="history-list">
          <button
            v-for="p in recentPresentations"
            :key="p.id"
            type="button"
            class="history-item"
            @click="openPresentation(p.id)"
          >
            <span class="history-item-title">{{ p.title }}</span>
            <span class="history-meta">{{ p.slides_count }} 页 · {{ formatDate(p.updated_at) }}</span>
            <span
              class="history-delete"
              title="删除"
              @click.stop="deletePresentation(p.id)"
            >×</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePresentationStore } from '../stores/presentation'
import { proposeOutline, proposeOutlineStream, getLLMStatus, listTemplates, listPresentations as listPresentationsApi, deletePresentation as deletePresentationApi } from '../api'

const store = usePresentationStore()

const topic = ref('')
const outlineDraft = ref('')
const pageCount = ref(8)
const creativeMode = ref(true)
const outlineBusy = ref(false)
const pptBusy = ref(false)
const errorMsg = ref('')
const visibleSteps = ref([])
const llmEffective = ref('')
const llmConfigured = ref('')
const llmFallback = ref(false)

const templates = ref([])
const templateLoading = ref(false)
const selectedTemplate = ref('')

function swatchStyle(t) {
  const p = t.palette
  if (!p) return { background: '#f3f2f1' }
  return {
    background: `linear-gradient(135deg, ${p.primary} 0%, ${p.primary} 40%, ${p.accent} 60%, ${p.bg || '#fff'} 100%)`,
  }
}

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
    await store.generate(topic.value.trim(), outline || '', pageCount.value, creativeMode.value, selectedTemplate.value || undefined)
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
  // Fire all API calls in parallel — no waterfall waits
  loadLlmStatus()
  loadTemplates()
  loadRecentPresentations()
})

// Also run template + history in parallel on mount via Promise.allSettled
// (the individual functions already handle errors internally, so this is just
//  for ensuring they don't block each other)

const quickTopics = [
  { icon: '📊', label: '工作汇报', topic: '季度工作汇报与下季度计划', outline: '1. 本季度核心成果\n2. 关键数据指标\n3. 挑战与应对\n4. 下季度目标与计划' },
  { icon: '🚀', label: '产品路演', topic: '新产品发布与市场策略', outline: '1. 市场背景与用户痛点\n2. 产品核心亮点\n3. 竞品分析\n4. 商业模式与定价\n5. 上线路线图' },
  { icon: '📚', label: '教学课件', topic: '教学课件：课程核心知识点讲解', outline: '1. 课程导入与学习目标\n2. 核心概念解析\n3. 案例分析\n4. 课堂练习\n5. 总结与课后任务' },
  { icon: '💡', label: '技术分享', topic: '技术架构演进与实践分享', outline: '1. 背景与动机\n2. 旧架构痛点\n3. 新架构设计\n4. 落地过程与踩坑\n5. 成果与后续规划' },
  { icon: '📈', label: '数据分析', topic: '业务数据分析报告与洞察', outline: '1. 数据概览\n2. 核心指标趋势\n3. 用户行为分析\n4. 问题诊断\n5. 优化建议' },
  { icon: '🎯', label: '项目提案', topic: '项目立项提案与可行性分析', outline: '1. 项目背景\n2. 目标与范围\n3. 技术方案\n4. 资源与时间规划\n5. 风险评估' },
]

const recentPresentations = ref([])

function applyQuickTopic(qt) {
  topic.value = qt.topic
  outlineDraft.value = qt.outline || ''
  errorMsg.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function loadRecentPresentations() {
  try {
    const { data } = await listPresentationsApi()
    recentPresentations.value = (data || []).slice(0, 8)
  } catch {
    recentPresentations.value = []
  }
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH} 小时前`
  const diffD = Math.floor(diffH / 24)
  if (diffD < 7) return `${diffD} 天前`
  return `${d.getMonth() + 1}/${d.getDate()}`
}

async function openPresentation(id) {
  try {
    const { data } = await store.loadFromServerById(id)
    if (!data) return
  } catch {
    // fallback: set localStorage and reload
    localStorage.setItem('html-ppt-last-id', id)
    window.location.reload()
  }
}

async function deletePresentation(id) {
  try {
    await deletePresentationApi(id)
    recentPresentations.value = recentPresentations.value.filter(p => p.id !== id)
  } catch {
    // ignore
  }
}

async function clearHistory() {
  for (const p of recentPresentations.value) {
    try { await deletePresentationApi(p.id) } catch { /* skip */ }
  }
  recentPresentations.value = []
}

async function loadTemplates() {
  templateLoading.value = true
  try {
    const { data } = await listTemplates()
    templates.value = data
    if (data.length && !selectedTemplate.value) {
      selectedTemplate.value = data[0].id
    }
  } catch {
    templates.value = []
  } finally {
    templateLoading.value = false
  }
}
</script>

<style scoped>
.home {
  height: 100vh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 24px 12px;
  background: linear-gradient(135deg, #f3f2f1 0%, #edebe9 45%, #e1dfdd 100%);
  overflow-y: auto;
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
  margin-bottom: 12px;
  font-size: 13px;
  line-height: 1.55;
}
/* Quick chips */
.quick-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 18px;
}
.quick-chips-label {
  font-size: 12px;
  font-weight: 600;
  color: #605e5c;
}
.quick-chip {
  padding: 4px 12px;
  border: 1px solid #d2d0ce;
  border-radius: 14px;
  background: #faf9f8;
  font-size: 12px;
  font-weight: 500;
  color: #323130;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  white-space: nowrap;
}
.quick-chip:hover {
  border-color: #0078d4;
  background: #f0f8ff;
  color: #0078d4;
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
.checkbox-row {
  margin-bottom: 14px;
}
.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 13px;
  color: #323130;
  line-height: 1.45;
  cursor: pointer;
  font-weight: 500;
}
.checkbox-label input {
  margin-top: 3px;
  flex-shrink: 0;
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
.template-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 6px;
}
.template-card {
  display: block;
  padding: 0;
  border: 2px solid #edebe9;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  overflow: hidden;
}
.template-card:hover {
  border-color: #b3b0ad;
}
.template-card.active {
  border-color: #d83b01;
  box-shadow: 0 0 0 1px rgba(216, 59, 1, 0.2);
}
.template-swatch {
  width: 100%;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.swatch-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  text-shadow: 0 1px 3px rgba(0,0,0,0.4);
  padding: 4px 10px;
  border-radius: 3px;
  background: rgba(0,0,0,0.2);
  white-space: nowrap;
}
.template-loading {
  font-size: 12px;
  color: #605e5c;
  padding: 12px 0;
}

/* History section (inline) */
.history-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #edebe9;
}
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.history-title-label {
  font-size: 13px;
  font-weight: 700;
  color: #323130;
}
.btn-clear-history {
  font-size: 11px;
  color: #605e5c;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 2px;
}
.btn-clear-history:hover {
  background: #f3f2f1;
  color: #d83b01;
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #edebe9;
  border-radius: 3px;
  background: #faf9f8;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}
.history-item:hover {
  border-color: #b3b0ad;
  background: #fff;
}
.history-item-title {
  flex: 1;
  font-size: 12px;
  font-weight: 600;
  color: #323130;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-meta {
  font-size: 11px;
  color: #605e5c;
  flex-shrink: 0;
  white-space: nowrap;
}
.history-delete {
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 14px;
  color: #605e5c;
  background: transparent;
  flex-shrink: 0;
}
.history-delete:hover {
  background: #edebe9;
  color: #d83b01;
}
</style>
