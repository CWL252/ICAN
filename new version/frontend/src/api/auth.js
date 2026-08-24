import {
  clearToken,
  getToken
} from '../lib/auth'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'http://127.0.0.1:8001'

export function handleUnauthorized() {
  clearToken()
  window.location.href = '/login'
}

export async function register({
  username,
  email,
  password,
  hospital,
  licenseFile
}) {
  // 二期:注册改 multipart(医院 + 医师资格证必填)。FormData 由浏览器
  // 自动携带 boundary,不能手动设 Content-Type。
  const form = new FormData()
  form.append('username', username)
  form.append('email', email)
  form.append('password', password)
  form.append('hospital', hospital)
  form.append('license_file', licenseFile)

  const response = await fetch(
    `${API_BASE_URL}/api/auth/register`,
    {
      method: 'POST',
      body: form
    }
  )

  const payload = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    throw new Error(
      payload?.detail || '注册失败，请稍后重试'
    )
  }

  return payload
}

// 医师资格证图片地址:<img> 无法带 Authorization 头,走 query token
export function licenseUrl() {
  const token = getToken()
  if (!token) return ''
  return `${API_BASE_URL}/api/auth/license?token=${encodeURIComponent(token)}`
}

// 修改个人资料(当前仅医院),返回更新后的 user
export async function updateProfile({ hospital }) {
  const token = getToken()

  const response = await fetch(
    `${API_BASE_URL}/api/auth/profile`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({ hospital })
    }
  )

  const payload = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    throw new Error(
      payload?.detail || '保存失败，请稍后重试'
    )
  }

  return payload
}

// 补传/更换医师资格证(个人主页"未上传资格证"入口),返回更新后的 user
export async function uploadLicense(file) {
  const token = getToken()
  const form = new FormData()
  form.append('license_file', file)

  const response = await fetch(
    `${API_BASE_URL}/api/auth/license`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      },
      body: form
    }
  )

  const payload = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    throw new Error(
      payload?.detail || '资格证上传失败，请稍后重试'
    )
  }

  return payload
}

export async function login({
  identifier,
  password
}) {
  const response = await fetch(
    `${API_BASE_URL}/api/auth/login`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        identifier,
        password
      })
    }
  )

  const payload = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    throw new Error(
      payload?.detail || '登录失败，请稍后重试'
    )
  }

  return payload
}

export async function logout() {
  const token = getToken()

  const response = await fetch(
    `${API_BASE_URL}/api/auth/logout`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )

  const payload = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    throw new Error(
      payload?.detail || '退出登录失败'
    )
  }

  return payload
}

export async function getMe() {
  const token = getToken()

  const response = await fetch(
    `${API_BASE_URL}/api/auth/me`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  )

  const payload = await response
    .json()
    .catch(() => null)

  if (!response.ok) {
    throw new Error(
      payload?.detail || '获取用户信息失败'
    )
  }

  return payload
}
