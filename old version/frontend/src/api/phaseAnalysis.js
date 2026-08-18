const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

export async function createPhaseAnalysisJob(file, options = {}) {
  const sampleSeconds = options.sampleSeconds ?? 2
  const formData = new FormData()
  formData.append('file', file, file.name || 'video.mp4')

  const response = await fetch(`${API_BASE_URL}/api/phase/jobs?sample_seconds=${encodeURIComponent(sampleSeconds)}`, {
    method: 'POST',
    body: formData,
  })

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '关键步骤分析请求失败')
  }

  return payload
}

export async function getPhaseAnalysisJob(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/phase/jobs/${encodeURIComponent(jobId)}`)
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '关键步骤分析任务查询失败')
  }
  return payload
}
