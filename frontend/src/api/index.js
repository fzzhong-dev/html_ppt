import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const proposeOutline = (topic, seedOutline) =>
  api.post('/ppt/outline', {
    topic,
    ...(seedOutline ? { seed_outline: seedOutline } : {}),
  })

export function proposeOutlineStream(topic, seedOutline) {
  return fetch('/api/ppt/outline-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic,
      ...(seedOutline ? { seed_outline: seedOutline } : {}),
    }),
  })
}

export const getLLMStatus = () =>
  api.get('/llm/status')

export const generatePPT = (topic, outline, pageCount = 8, creativeMode = true) =>
  api.post('/ppt/generate', {
    topic,
    ...(outline?.trim() ? { outline: outline.trim() } : {}),
    page_count: pageCount,
    creative_mode: creativeMode,
  })

export function generatePPTStream(topic, outline, pageCount = 8, creativeMode = true) {
  return fetch('/api/ppt/generate-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic,
      ...(outline?.trim() ? { outline: outline.trim() } : {}),
      page_count: pageCount,
      creative_mode: creativeMode,
    }),
  })
}

export const modifySlide = (presentationId, slideId, instruction, chatHistory) =>
  api.post('/ppt/modify', { presentation_id: presentationId, slide_id: slideId, instruction, chat_history: chatHistory })

export const patchSlideHtml = (presentationId, slideId, htmlContent) =>
  api.patch(`/ppt/${presentationId}/slide-html`, { slide_id: slideId, html_content: htmlContent })

export const insertSlide = (presentationId, payload) =>
  api.post(`/ppt/${presentationId}/slides`, payload)

export const deleteSlideApi = (presentationId, slideId) =>
  api.post(`/ppt/${presentationId}/delete-slide`, { slide_id: slideId })

export const exportPPTX = (presentationId) =>
  api.post('/ppt/export', { presentation_id: presentationId }, { responseType: 'blob' })

export const getPresentation = (id) =>
  api.get(`/ppt/${id}`)

export const getSlide = (presentationId, slideNumber) =>
  api.get(`/ppt/${presentationId}/slides/${slideNumber}`)

export const listTemplates = () =>
  api.get('/templates/')

export const getTemplate = (id) =>
  api.get(`/templates/${id}`)

export const listProviders = () =>
  api.get('/llm/providers')

export const switchProvider = (provider) =>
  api.put('/llm/provider', { provider })

export const searchImages = (query, page = 1) =>
  api.get('/images/search', { params: { q: query, page } })
