<template>
  <div class="chat-panel">
    <div class="chat-header">AI 对话</div>
    <div class="chat-messages" ref="messagesEl">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="chat-msg"
        :class="msg.role"
      >
        {{ msg.content }}
      </div>
      <div v-if="loading" class="chat-msg assistant">思考中...</div>
    </div>
    <div class="chat-input">
      <input
        v-model="input"
        placeholder="输入修改指令..."
        @keyup.enter="handleSend"
        :disabled="loading"
      />
      <button @click="handleSend" :disabled="loading || !input">发送</button>
    </div>
  </div>
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
  width: 300px;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  border-left: 1px solid #e0e0e0;
  flex-shrink: 0;
}
.chat-header {
  background: #4CAF50;
  color: white;
  padding: 10px 16px;
  font-weight: 600;
  font-size: 14px;
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.chat-msg {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-width: 90%;
  word-break: break-word;
}
.chat-msg.user {
  background: #e3f2fd;
  align-self: flex-end;
  text-align: right;
}
.chat-msg.assistant {
  background: #f0f0f0;
  align-self: flex-start;
}
.chat-input {
  display: flex;
  padding: 8px;
  border-top: 1px solid #e0e0e0;
  gap: 6px;
}
.chat-input input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
}
.chat-input input:focus { border-color: #4CAF50; }
.chat-input button {
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.chat-input button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
