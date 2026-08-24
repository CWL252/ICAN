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
const loading = ref(false)
const isRegister = ref(false)

const message = ref('')
const messageType = ref('success')

function switchMode() {
  isRegister.value = !isRegister.value

  message.value = ''
  username.value = ''
  password.value = ''
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
  const { token, user } = await register({
    username: username.value,
    email: email.value,
    password: password.value
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