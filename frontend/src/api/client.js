const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  const text = await response.text()
  const data = text ? JSON.parse(text) : null

  if (!response.ok) {
    const message = data?.detail || `请求失败：${response.status}`
    throw new Error(message)
  }

  return data
}

export const api = {
  draftSettings(idea) {
    return request('/api/stories/draft-settings', {
      method: 'POST',
      body: JSON.stringify({ idea })
    })
  },
  createStory(settings) {
    return request('/api/stories', {
      method: 'POST',
      body: JSON.stringify({ settings })
    })
  },
  draftChapterEvent(storyId, payload) {
    return request(`/api/stories/${storyId}/chapter-events/draft`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },
  draftChapter(storyId, payload) {
    return request(`/api/stories/${storyId}/chapters/draft`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },
  confirmChapter(storyId, payload) {
    return request(`/api/stories/${storyId}/chapters`, {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },
  getMemory(storyId) {
    return request(`/api/stories/${storyId}/memory`)
  },
  correctMemory(storyId, payload) {
    return request(`/api/stories/${storyId}/memory/latest-state`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    })
  }
}

