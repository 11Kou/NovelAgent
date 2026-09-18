const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const DEFAULT_TIMEOUT_MS = 90000

async function request(path, options = {}) {
  const { timeoutMs, ...fetchOptions } = options
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs || DEFAULT_TIMEOUT_MS)
  let response

  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(fetchOptions.headers || {})
      },
      ...fetchOptions,
      signal: fetchOptions.signal || controller.signal
    })
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('请求超时：模型生成可能耗时较久，请稍后重试。')
    }
    throw new Error(`无法连接后端 API（${API_BASE}），请确认 FastAPI 服务正在运行。`)
  } finally {
    window.clearTimeout(timeoutId)
  }

  const text = await response.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }

  if (!response.ok) {
    const message = formatErrorMessage(response.status, data, text)
    throw new Error(message)
  }

  return data
}

function formatErrorMessage(status, data, text) {
  const detail = data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join('；')
  }
  if (text && text.trim()) {
    return `请求失败：${status}，${text.slice(0, 300)}`
  }
  return `请求失败：${status}`
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
