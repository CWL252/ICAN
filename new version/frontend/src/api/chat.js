import { getToken } from '../lib/auth'
import { handleUnauthorized } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

export async function askDoubao(question, context = {}) {
  const token = getToken()
  if (!token) {
    throw new Error('登录状态已失效，请重新登录')
  }

  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      question,
      context,
    }),
  })

  if (response.status === 401) {
    handleUnauthorized()
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '智能问答请求失败')
  }

  return payload?.answer || ''
}
