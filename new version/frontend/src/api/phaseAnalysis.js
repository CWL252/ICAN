import { getToken } from '../lib/auth'
import { handleUnauthorized } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

export async function createPhaseAnalysisJob(file, options = {}) {
  const token = getToken()
  if (!token) {
    throw new Error('登录状态已失效，请重新登录')
  }

  const sampleSeconds = options.sampleSeconds ?? 2
  const formData = new FormData()
  formData.append('file', file, file.name || 'video.mp4')

  const response = await fetch(`${API_BASE_URL}/api/phase/jobs?sample_seconds=${encodeURIComponent(sampleSeconds)}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (response.status === 401) {
    handleUnauthorized()
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '关键步骤分析请求失败')
  }

  return payload
}

export async function getPhaseAnalysisJob(jobId) {
  const token = getToken()
  if (!token) {
    throw new Error('登录状态已失效，请重新登录')
  }

  const response = await fetch(`${API_BASE_URL}/api/phase/jobs/${encodeURIComponent(jobId)}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (response.status === 401) {
    handleUnauthorized()
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '关键步骤分析任务查询失败')
  }
  return payload
}

export async function savePhaseAnnotations(jobId, segments) {
  const token = getToken()
  if (!token) {
    throw new Error('登录状态已失效，请重新登录')
  }

  const response = await fetch(`${API_BASE_URL}/api/phase/jobs/${encodeURIComponent(jobId)}/annotations`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ segments }),
  })

  if (response.status === 401) {
    handleUnauthorized()
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '标注保存失败')
  }
  return payload
}
