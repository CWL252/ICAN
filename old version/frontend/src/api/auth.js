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
  password
}) {
  const response = await fetch(
    `${API_BASE_URL}/api/auth/register`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username,
        email,
        password
      })
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
