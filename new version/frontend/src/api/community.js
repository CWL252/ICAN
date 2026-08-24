import { getToken } from '../lib/auth'
import { handleUnauthorized } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

function ensureLogin() {
  const token = getToken()
  if (!token) {
    throw new Error('登录状态已失效，请重新登录')
  }
  return token
}

async function request(path, options = {}) {
  const token = ensureLogin()
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  })

  if (response.status === 401) {
    handleUnauthorized()
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '请求失败，请稍后重试')
  }
  return payload
}

function withBody(method, body) {
  return { method, body: JSON.stringify(body) }
}

// ---------------------------------------------------------------- projects

export function listProjects({ q = '', sort = 'newest', limit = 20, offset = 0, mine = false, authorId = null, category = '', subcategory = '' } = {}) {
  const params = new URLSearchParams({ q, sort, limit, offset })
  if (mine) params.set('mine', 'true')
  if (authorId != null) params.set('author_id', authorId)
  if (category) params.set('category', category)
  if (subcategory) params.set('subcategory', subcategory)
  return request(`/api/community/projects?${params.toString()}`)
}

export function listCategories() {
  return request('/api/community/categories')
}

export function getProject(projectId) {
  return request(`/api/community/projects/${encodeURIComponent(projectId)}`)
}

export function askProjectQuestion(projectId, question) {
  return request(
    `/api/community/projects/${encodeURIComponent(projectId)}/qa`,
    withBody('POST', { question })
  )
}

export function shareProject(data) {
  return request('/api/community/projects', withBody('POST', data))
}

export function updateProject(projectId, data) {
  return request(`/api/community/projects/${encodeURIComponent(projectId)}`, withBody('PUT', data))
}

export function deleteProject(projectId) {
  return request(`/api/community/projects/${encodeURIComponent(projectId)}`, { method: 'DELETE' })
}

// ---------------------------------------------------------------- posts

export function listPosts({ q = '', limit = 20, offset = 0, mine = false, authorId = null } = {}) {
  const params = new URLSearchParams({ q, limit, offset })
  if (mine) params.set('mine', 'true')
  if (authorId != null) params.set('author_id', authorId)
  return request(`/api/community/posts?${params.toString()}`)
}

export function getPost(postId) {
  return request(`/api/community/posts/${encodeURIComponent(postId)}`)
}

export function createPost(data) {
  return request('/api/community/posts', withBody('POST', data))
}

export function updatePost(postId, data) {
  return request(`/api/community/posts/${encodeURIComponent(postId)}`, withBody('PUT', data))
}

export function deletePost(postId) {
  return request(`/api/community/posts/${encodeURIComponent(postId)}`, { method: 'DELETE' })
}

// ---------------------------------------------------------------- comments

export function listComments(targetType, targetId) {
  const params = new URLSearchParams({ target_type: targetType, target_id: targetId })
  return request(`/api/community/comments?${params.toString()}`)
}

export function createComment(targetType, targetId, content, parentId = null) {
  return request(
    '/api/community/comments',
    withBody('POST', { target_type: targetType, target_id: targetId, content, parent_id: parentId })
  )
}

export function deleteComment(commentId) {
  return request(`/api/community/comments/${encodeURIComponent(commentId)}`, { method: 'DELETE' })
}

export function listMyComments() {
  return request('/api/community/comments?mine=true')
}

export function listMyFavorites() {
  return request('/api/community/me/favorites')
}

export function listMyLikes() {
  return request('/api/community/me/likes')
}

// ---------------------------------------------------------------- likes / favorites

export function setLike(targetType, targetId, liked) {
  const method = liked ? 'POST' : 'DELETE'
  return request(`/api/community/${targetType}s/${encodeURIComponent(targetId)}/like`, { method })
}

export function setFavorite(targetType, targetId, favorited) {
  const method = favorited ? 'POST' : 'DELETE'
  return request(`/api/community/${targetType}s/${encodeURIComponent(targetId)}/favorite`, { method })
}

// ---------------------------------------------------------------- shared videos

export function uploadProjectVideo(projectId, file, onProgress) {
  const token = ensureLogin()

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', `${API_BASE_URL}/api/community/projects/${encodeURIComponent(projectId)}/video`)
    xhr.setRequestHeader('Authorization', `Bearer ${token}`)

    if (typeof onProgress === 'function') {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress(Math.round((event.loaded / event.total) * 100))
        }
      }
    }

    xhr.onload = () => {
      let payload = null
      try {
        payload = JSON.parse(xhr.responseText)
      } catch {
        payload = null
      }
      if (xhr.status === 401) {
        handleUnauthorized()
        reject(new Error('登录状态已失效，请重新登录'))
        return
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(payload || {})
        return
      }
      // FastAPI 422 的 detail 是数组/对象，转成字符串会变成 [object Object]，统一兜底
      const detail = payload?.detail
      const message =
        typeof detail === 'string' ? detail : '视频上传失败，请检查文件格式后重试'
      reject(new Error(message))
    }
    xhr.onerror = () => reject(new Error('网络异常，视频上传失败'))

    // 必须用 FormData：直接 send(File) 不带 multipart boundary，后端解析不了会 422
    const form = new FormData()
    form.append('file', file)
    xhr.send(form)
  })
}

export function removeProjectVideo(projectId) {
  return request(`/api/community/projects/${encodeURIComponent(projectId)}/video`, { method: 'DELETE' })
}

export function projectVideoUrl(projectId) {
  const token = getToken()
  if (!token) return ''
  return `${API_BASE_URL}/api/community/projects/${encodeURIComponent(projectId)}/video?token=${encodeURIComponent(token)}`
}

// 视频附件下载：download=1 让浏览器保存文件而不是播放
export function projectVideoDownloadUrl(projectId) {
  const token = getToken()
  if (!token) return ''
  return `${API_BASE_URL}/api/community/projects/${encodeURIComponent(projectId)}/video?token=${encodeURIComponent(token)}&download=1`
}

// 下载整个项目：有视频时后端打包 ZIP(项目信息 JSON + 视频)，无视频返回 JSON
export async function downloadProjectExport(projectId) {
  const token = ensureLogin()
  const response = await fetch(
    `${API_BASE_URL}/api/community/projects/${encodeURIComponent(projectId)}/export`,
    { headers: { Authorization: `Bearer ${token}` } }
  )

  if (response.status === 401) {
    handleUnauthorized()
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.detail || '下载失败，请稍后重试')
  }

  const blob = await response.blob()
  const disposition = response.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^";]+)"?/)
  const filename = match ? match[1] : `project_${projectId}.zip`

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
  return filename
}

// ---------------------------------------------------------------- follows / feed

export function followUser(userId, following) {
  const method = following ? 'POST' : 'DELETE'
  return request(`/api/community/users/${encodeURIComponent(userId)}/follow`, { method })
}

export function getUserProfile(userId) {
  return request(`/api/community/users/${encodeURIComponent(userId)}/profile`)
}

export function getFeed(limit = 20) {
  return request(`/api/community/feed?limit=${limit}`)
}

export function listMyFollowing() {
  return request('/api/community/me/following')
}

export function listMyDownloads() {
  return request('/api/community/me/downloads')
}

export function deleteDownload(projectId) {
  return request(`/api/community/me/downloads/${encodeURIComponent(projectId)}`, {
    method: 'DELETE',
  })
}

// ---------------------------------------------------------------- feedback

export function submitFeedback(data) {
  return request('/api/community/feedback', withBody('POST', data))
}

export function listMyFeedback() {
  return request('/api/community/feedback')
}

export function deleteFeedback(feedbackId) {
  return request(`/api/community/feedback/${encodeURIComponent(feedbackId)}`, {
    method: 'DELETE',
  })
}
