import { getToken } from '../lib/auth'
import { handleUnauthorized } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'

/**
 * 调用后端 MobileSAM 点击分割接口。
 * @param {{imageBase64: string, points: Array<{x:number,y:number,label:1|0}>, frameWidth?: number, frameHeight?: number}} params
 * @param {AbortSignal} [signal]
 * @returns {Promise<{polygon: number[][], mask_png?: string, device: string, elapsed_ms: number}>}
 */
export async function segmentFrame({ imageBase64, points, frameWidth, frameHeight }, signal) {
  const token = getToken()
  if (!token) {
    throw new Error('登录状态已失效，请重新登录')
  }

  const response = await fetch(`${API_BASE_URL}/api/segment`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      image: imageBase64,
      points,
      frame_width: frameWidth,
      frame_height: frameHeight,
    }),
    signal,
  })

  if (response.status === 401) {
    handleUnauthorized()
  }

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(payload?.detail || '分割请求失败')
  }

  return payload
}
