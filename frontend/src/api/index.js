import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const generatePPT = (topic, outline, templateId, pageCount) =>
  api.post('/ppt/generate', { topic, outline, template_id: templateId, page_count: pageCount })

export const modifySlide = (presentationId, slideId, instruction, chatHistory) =>
  api.post('/ppt/modify', { presentation_id: presentationId, slide_id: slideId, instruction, chat_history: chatHistory })

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
