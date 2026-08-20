<template>
  <div class="min-h-screen flex flex-col">
    <nav
      v-if="showNavigation"
      class="bg-white shadow-sm py-4 sticky top-0 z-50"
    >
      <div
        class="app-shell px-4 sm:px-6 lg:px-8 flex justify-between items-center gap-4 flex-wrap"
      >
        <div class="flex items-center">
          <i
            class="fas fa-stethoscope text-2xl text-blue-600 mr-2"
          ></i>

          <div>
            <span class="text-xl font-bold text-gray-800">
              SurgReview
            </span>

            <p class="text-xs text-gray-500">
              交互式智慧外科平台——赋能外科质控、科研与培训
            </p>
          </div>
        </div>

        <div class="flex items-center gap-4 text-sm">
          <div class="flex items-center gap-2 text-gray-600">
            <i class="fas fa-circle-user text-blue-600"></i>

            <span>
              {{ currentUsername }}
            </span>
          </div>

          <router-link
            to="/home"
            class="btn-secondary"
          >
            <i class="fas fa-house mr-2"></i>
            首页
          </router-link>

          <button
            class="btn-secondary"
            type="button"
            :disabled="loggingOut"
            @click="handleLogout"
          >
            <i class="fas fa-right-from-bracket mr-2"></i>

            {{ loggingOut ? '正在退出...' : '退出登录' }}
          </button>
        </div>
      </div>
    </nav>

    <main class="flex-1">
      <router-view />
    </main>

    <footer
      v-if="showFooter"
      class="bg-gray-900 text-white py-6 mt-8"
    >
      <div
        class="app-shell px-4 sm:px-6 lg:px-8 text-center text-gray-400 text-sm"
      >
        © 2026 SurgReview. 专注于数据驱动的外科见解。
      </div>
    </footer>
  </div>
</template>

<script setup>
import {
  computed,
  onMounted,
  ref
} from 'vue'

import {
  useRoute,
  useRouter
} from 'vue-router'

import {
  getMe,
  logout
} from './api/auth'
import {
  clearToken,
  currentUser,
  getStoredUser,
  getToken
} from './lib/auth'

const route = useRoute()
const router = useRouter()

const loggingOut = ref(false)

const showNavigation = computed(() => {
  return ![
    'Splash',
    'Login'
  ].includes(route.name)
})

const showFooter = computed(() => {
  return ![
    'Splash',
    'Analysis',
    'Login'
  ].includes(route.name)
})

const currentUsername = computed(() => {
  return (
    currentUser.value?.username ||
    currentUser.value?.email ||
    getStoredUser()?.username ||
    '用户'
  )
})

async function loadCurrentUser() {
  if (!getToken()) {
    currentUser.value = null
    return
  }

  try {
    const me = await getMe()

    currentUser.value = me
  } catch (error) {
    console.error('获取用户信息失败：', error)

    clearToken()
    currentUser.value = null

    await router.replace({
      name: 'Login'
    })
  }
}

async function handleLogout() {
  loggingOut.value = true

  try {
    // Best effort: clear local state even if the API call fails.
    await logout()
  } catch (error) {
    console.error('退出登录失败：', error)
  } finally {
    clearToken()
    currentUser.value = null

    await router.replace({
      name: 'Login'
    })

    loggingOut.value = false
  }
}

onMounted(() => {
  loadCurrentUser()
})
</script>

<style scoped>
.app-shell {
  width: 100%;
  max-width: none;
}
</style>