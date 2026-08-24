<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="brand">SurgReview</div>

      <h1>{{ isRegister ? '创建账户' : '欢迎回来' }}</h1>

      <p class="subtitle">
        {{
          isRegister
            ? '注册 SurgReview 本地账户'
            : '登录以继续使用智慧外科分析平台'
        }}
      </p>

      <form class="auth-form" @submit.prevent="handleSubmit">
        <template v-if="isRegister">
          <label for="username">用户名</label>

          <input
            id="username"
            v-model.trim="username"
            type="text"
            placeholder="请输入用户名"
            autocomplete="username"
            minlength="2"
            maxlength="30"
            required
          />
        </template>

        <label for="email">
          {{ isRegister ? '邮箱' : '用户名或邮箱' }}
        </label>

        <input
          id="email"
          v-model.trim="email"
          :type="isRegister ? 'email' : 'text'"
          :placeholder="
            isRegister ? '请输入邮箱' : '请输入用户名或邮箱'
          "
          autocomplete="email"
          required
        />

        <label for="password">
  密码
  <span
    v-if="isRegister"
    class="password-rule"
  >
    （至少 8 位）
  </span>
</label>

<input
  id="password"
  v-model="password"
  type="password"
  placeholder="请输入密码"
  :autocomplete="isRegister ? 'new-password' : 'current-password'"
  :minlength="isRegister ? 8 : undefined"
  required
/>

<p
  v-if="isRegister"
  class="password-hint"
>
  密码需至少 8 位，且同时包含字母和数字
</p>

        <template v-if="isRegister">
          <label for="hospital">医院 <span class="required-asterisk">*</span></label>

          <input
            id="hospital"
            v-model.trim="hospital"
            type="text"
            placeholder="请输入所在医院"
            maxlength="60"
            required
          />

          <label>医师资格证 <span class="required-asterisk">*</span></label>

          <button
            class="license-picker"
            type="button"
            @click="licenseInputRef?.click()"
          >
            <i class="fas fa-id-card mr-2"></i>
            {{ licenseFile ? '重新选择照片' : '上传资格证照片' }}
          </button>
          <input
            ref="licenseInputRef"
            type="file"
            accept=".jpg,.jpeg,.png,.webp"
            class="hidden"
            @change="onLicenseSelected"
          />

          <p v-if="licenseFile" class="license-file-name">
            <i class="fas fa-check-circle mr-1"></i>{{ licenseFile.name }}
          </p>

          <div v-if="licensePreviewUrl" class="license-preview">
            <img
              :src="licensePreviewUrl"
              alt="医师资格证预览"
            />
          </div>
        </template>

        <button
          class="submit-button"
          type="submit"
          :disabled="loading"
        >
          {{
            loading
              ? '请稍候...'
              : isRegister
                ? '注册'
                : '登录'
          }}
        </button>
      </form>

      <p
        v-if="message"
        :class="[
          'message',
          messageType === 'error'
            ? 'error-message'
            : 'success-message'
        ]"
      >
        {{ message }}
      </p>

      <div class="switch-area">
        <span>
          {{ isRegister ? '已经有账户？' : '还没有账户？' }}
        </span>

        <button
          class="switch-button"
          type="button"
          @click="switchMode"
        >
          {{ isRegister ? '返回登录' : '创建账户' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, register } from '../api/auth'
import {
  currentUser,
  setStoredUser,
  setToken
} from '../lib/auth'

const router = useRouter()

const username = ref('')
const email = ref('')
const password = ref('')
const hospital = ref('')
const licenseInputRef = ref(null)
const licenseFile = ref(null)
const licensePreviewUrl = ref('')
const loading = ref(false)
const isRegister = ref(false)

const message = ref('')
const messageType = ref('success')

const LICENSE_ALLOWED_EXTS = ['.jpg', '.jpeg', '.png', '.webp']
const LICENSE_MAX_BYTES = 5 * 1024 * 1024

function onLicenseSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  const suffix = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!LICENSE_ALLOWED_EXTS.includes(suffix)) {
    messageType.value = 'error'
    message.value = '资格证仅支持 jpg/jpeg/png/webp 格式'
    event.target.value = ''
    return
  }
  if (file.size > LICENSE_MAX_BYTES) {
    messageType.value = 'error'
    message.value = '资格证大小不能超过 5MB'
    event.target.value = ''
    return
  }

  if (licensePreviewUrl.value) {
    URL.revokeObjectURL(licensePreviewUrl.value)
  }
  licenseFile.value = file
  licensePreviewUrl.value = URL.createObjectURL(file)
  message.value = ''
}

function switchMode() {
  isRegister.value = !isRegister.value

  message.value = ''
  username.value = ''
  password.value = ''
  hospital.value = ''
  licenseFile.value = null
  if (licensePreviewUrl.value) {
    URL.revokeObjectURL(licensePreviewUrl.value)
  }
  licensePreviewUrl.value = ''
  if (licenseInputRef.value) {
    licenseInputRef.value.value = ''
  }
}

async function handleSubmit() {
  loading.value = true
  message.value = ''

  try {
    if (isRegister.value) {
      await handleRegister()
    } else {
      await handleLogin()
    }
  } catch (error) {
    console.error('认证失败：', error)

    messageType.value = 'error'
    message.value =
      error?.message || '操作失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!hospital.value) {
    throw new Error('请输入所在医院')
  }
  if (!licenseFile.value) {
    throw new Error('请上传医师资格证照片')
  }

  const { token, user } = await register({
    username: username.value,
    email: email.value,
    password: password.value,
    hospital: hospital.value,
    licenseFile: licenseFile.value
  })

  setToken(token)
  setStoredUser(user)
  currentUser.value = user

  messageType.value = 'success'
  message.value = '注册成功，账户已登录。'

  await router.replace({
    name: 'Home'
  })
}

async function handleLogin() {
  const { token, user } = await login({
    identifier: email.value,
    password: password.value
  })

  setToken(token)
  setStoredUser(user)
  currentUser.value = user

  await router.replace({
    name: 'Home'
  })
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(
      circle at 20% 20%,
      rgba(59, 130, 246, 0.12),
      transparent 35%
    ),
    radial-gradient(
      circle at 80% 80%,
      rgba(14, 165, 233, 0.1),
      transparent 35%
    ),
    #f8fafc;
}

.auth-card {
  width: 100%;
  max-width: 420px;
  padding: 42px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.1);
}

.brand {
  margin-bottom: 28px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #2563eb;
}

h1 {
  margin: 0;
  font-size: 30px;
  color: #0f172a;
}

.subtitle {
  margin: 12px 0 30px;
  line-height: 1.6;
  color: #64748b;
}

.auth-form {
  display: flex;
  flex-direction: column;
}

.auth-form label {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.auth-form input {
  width: 100%;
  box-sizing: border-box;
  margin-bottom: 20px;
  padding: 13px 14px;
  font-size: 15px;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.auth-form input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.required-asterisk {
  color: #dc2626;
}

.license-picker {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  padding: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #2563eb;
  background: #eff6ff;
  border: 1px dashed #93c5fd;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
}

.license-picker:hover {
  background: #dbeafe;
}

.license-file-name {
  margin: -12px 0 14px;
  font-size: 13px;
  color: #166534;
}

.license-preview {
  margin-bottom: 20px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.license-preview img {
  display: block;
  width: 100%;
  max-height: 180px;
  object-fit: cover;
}

.hidden {
  display: none;
}

.submit-button {
  margin-top: 6px;
  padding: 13px;
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
  background: #2563eb;
  border: none;
  border-radius: 10px;
  cursor: pointer;
}

.submit-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.message {
  margin-top: 20px;
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.5;
  border-radius: 8px;
}

.success-message {
  color: #166534;
  background: #f0fdf4;
}

.error-message {
  color: #b91c1c;
  background: #fef2f2;
}

.switch-area {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  margin-top: 26px;
  font-size: 14px;
  color: #64748b;
}

.switch-button {
  padding: 0;
  font: inherit;
  font-weight: 600;
  color: #2563eb;
  background: none;
  border: none;
  cursor: pointer;
}

.password-rule {
  font-weight: 400;
  color: #64748b;
}

.password-hint {
  margin: -12px 0 20px;
  font-size: 13px;
  color: #64748b;
}
</style>