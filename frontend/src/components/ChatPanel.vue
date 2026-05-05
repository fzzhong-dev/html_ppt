<template>
  <aside class="chat-panel" aria-label="右侧面板">
    <div class="oo-pane-tabs" role="tablist" aria-label="面板选项卡">
      <button type="button" class="oo-pane-tab oo-pane-tab-active" role="tab" aria-selected="true">
        AI 助手
      </button>
      <button type="button" class="oo-pane-tab" role="tab" aria-selected="false" disabled title="占位">
        备注
      </button>
    </div>
    <div class="chat-pane-head">
      <span class="chat-sub">自然语言改稿</span>
    </div>
    <div class="chat-messages" ref="messagesEl">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-msg"
        :class="msg.role"
      >
        {{ msg.content }}
      </div>
      <div v-if="loading" class="chat-msg assistant chat-loading">正在处理…</div>
    </div>
    <div class="chat-input">
      <input
        v-model="input"
        placeholder="输入修改指令，如：把标题改为蓝色、添加一个柱状图、调整字体大小…"
        @keyup.enter="handleSend"
        :disabled="loading"
      />
      <button type="button" @click="handleSend" :disabled="loading || !input">发送</button>
    </div>
    <div class="chat-hints">
      <button
        v-for="hint in quickHints"
        :key="hint"
        type="button"
        class="chat-hint-btn"
        @click="input = hint"
      >{{ hint }}</button>
    </div>
  </aside>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: Boolean,
})
const emit = defineEmits(['send'])

const input = ref('')
const messagesEl = ref(null)

const quickHints = [
  '把标题字体加大并居中',
  '添加一个柱状图展示数据',
  '把背景改为深蓝色渐变',
  '把正文改为两栏布局',
  '添加一个时间线',
]

function handleSend() {
  if (!input.value.trim() || props.loading) return
  emit('send', input.value.trim())
  input.value = ''
}

watch(() => props.messages.length, async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
})
</script>

<style scoped>
.chat-panel {
  width: 312px;
  display: flex;
  flex-direction: column;
  background: var(--oo-chrome-bg, #fff);
  border-left: 1px solid var(--oo-border, #edebe9);
  flex-shrink: 0;
  min-height: 0;
}
.oo-pane-tabs {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 0 8px;
  border-bottom: 1px solid var(--oo-border-tabs, #d2d0ce);
  background: var(--oo-ribbon-tab-strip-bg, #f3f2f1);
}
.oo-pane-tab {
  flex: 1;
  padding: 8px 10px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  background: transparent;
  font-size: 12px;
  font-weight: 600;
  color: var(--oo-text-secondary, #605e5c);
  cursor: pointer;
}
.oo-pane-tab:hover:not(:disabled) {
  color: var(--oo-text, #323130);
}
.oo-pane-tab-active {
  background: var(--oo-chrome-bg, #fff);
  color: var(--oo-accent-orange, #d83b01);
  border-bottom-color: var(--oo-accent-orange, #d83b01);
}
.oo-pane-tab:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.chat-pane-head {
  padding: 8px 14px 6px;
  border-bottom: 1px solid var(--oo-border, #edebe9);
  background: var(--oo-panel-header-bg, #faf9f8);
}
.chat-sub {
  font-size: 11px;
  color: var(--oo-text-secondary, #605e5c);
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--oo-chrome-bg, #fff);
}
.chat-msg {
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  max-width: 95%;
  word-break: break-word;
}
.chat-msg.user {
  background: #deecf9;
  border: 1px solid #c7e0f4;
  color: var(--oo-text, #323130);
  align-self: flex-end;
}
.chat-msg.assistant {
  background: var(--oo-chrome-muted, #f3f2f1);
  border: 1px solid var(--oo-border, #edebe9);
  color: var(--oo-text, #323130);
  align-self: flex-start;
}
.chat-loading {
  font-style: italic;
  color: var(--oo-text-secondary, #605e5c);
}
.chat-input {
  display: flex;
  padding: 10px;
  border-top: 1px solid var(--oo-border, #edebe9);
  gap: 8px;
  background: var(--oo-panel-header-bg, #faf9f8);
}
.chat-input input {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid #8a8886;
  border-radius: 2px;
  font-size: 12px;
  outline: none;
  font-family: inherit;
  background: var(--oo-chrome-bg, #fff);
  color: var(--oo-text, #323130);
}
.chat-input input:focus {
  border-color: var(--oo-accent-blue, #0078d4);
  box-shadow: 0 0 0 1px rgba(0, 120, 212, 0.35);
}
.chat-input button {
  background: var(--oo-accent-blue, #0078d4);
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 2px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
}
.chat-input button:hover:not(:disabled) {
  filter: brightness(1.05);
}
.chat-input button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.chat-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 6px 10px 10px;
  background: var(--oo-panel-header-bg, #faf9f8);
}
.chat-hint-btn {
  padding: 4px 8px;
  border: 1px solid var(--oo-border, #edebe9);
  border-radius: 2px;
  background: var(--oo-chrome-bg, #fff);
  color: var(--oo-text-secondary, #605e5c);
  font-size: 11px;
  cursor: pointer;
  white-space: nowrap;
}
.chat-hint-btn:hover {
  background: #deecf9;
  border-color: #c7e0f4;
  color: var(--oo-accent-blue, #0078d4);
}
</style>
