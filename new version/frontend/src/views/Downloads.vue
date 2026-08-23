<template>
  <div class="downloads-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <button class="btn-secondary mb-6" @click="router.push('/community')">
      <i class="fas fa-arrow-left mr-2"></i>返回社区
    </button>

    <h1 class="text-2xl font-bold text-gray-800 mb-2">
      <i class="fas fa-download mr-2 text-blue-600"></i>下载中心
    </h1>
    <p class="text-sm text-slate-400 mb-6">
      从开源社区下载过的项目都记录在这里，可以随时查看或重新下载。
    </p>

    <section class="bg-white rounded-lg shadow-md p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-xl"></i>
      </div>

      <div v-else-if="!items.length" class="py-10 text-center text-gray-500">
        <i class="fas fa-download text-3xl mb-3 text-blue-400"></i>
        <p>还没有下载过任何项目。</p>
        <router-link to="/community" class="btn-primary inline-block mt-4">
          <i class="fas fa-box-open mr-2"></i>去开源广场逛逛
        </router-link>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="item in items"
          :key="item.projectId"
          class="border border-slate-200 rounded-xl p-4 flex justify-between items-center gap-3 flex-wrap hover:bg-slate-50 transition-colors"
        >
          <div class="min-w-0 flex items-center gap-3">
            <div
              class="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 text-lg"
              :class="item.hasVideo ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'"
            >
              <i class="fas" :class="item.hasVideo ? 'fa-file-zipper' : 'fa-file-code'"></i>
            </div>
            <div class="min-w-0">
              <p class="font-semibold text-slate-800 truncate">
                {{ item.title }}
                <i v-if="item.hasVideo" class="fas fa-video ml-1 text-blue-500 text-xs" title="含共享视频"></i>
              </p>
              <p class="text-xs text-slate-400 mt-1 truncate">
                下载于 {{ formatDate(item.downloadedAt) }} ·
                <button
                  class="hover:text-blue-600 transition-colors"
                  @click="router.push(`/community/users/${item.author.id}`)"
                >
                  {{ item.author.username }}
                </button>
                <template v-if="item.hasVideo"> · {{ formatSize(item.videoSize) }}</template>
              </p>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0 flex-wrap">
            <span class="text-xs text-slate-400">
              <i class="fas fa-heart mr-0.5 text-rose-400"></i>{{ item.likeCount }}
              <i class="fas fa-star ml-2 mr-0.5 text-amber-400"></i>{{ item.favoriteCount }}
            </span>
            <button class="btn-secondary" @click="router.push(`/community/projects/${item.projectId}`)">
              <i class="fas fa-eye mr-1"></i>查看项目
            </button>
            <button
              class="btn-secondary"
              title="重新下载一份项目文件到电脑"
              :disabled="downloadingId === item.projectId"
              @click="reDownload(item)"
            >
              <i
                class="fas mr-1"
                :class="downloadingId === item.projectId ? 'fa-circle-notch fa-spin' : 'fa-download'"
              ></i>
              {{ downloadingId === item.projectId ? '下载中...' : '再次下载' }}
            </button>
            <button class="btn-danger" @click="removeItem(item)">
              <i class="fas fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteDownload, downloadProjectExport, listMyDownloads } from '../api/community'

const router = useRouter()

const items = ref([])
const loading = ref(true)
const downloadingId = ref(null)

const statusMessage = ref('')
const statusType = ref('success')
let statusTimer = null

function showStatus(message, type = 'success') {
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
  statusMessage.value = message
  statusType.value = type
  statusTimer = window.setTimeout(() => {
    statusMessage.value = ''
    statusTimer = null
  }, 2400)
}

function formatDate(raw) {
  if (!raw) return ''
  return String(raw).slice(0, 16).replace('T', ' ')
}

function formatSize(bytes) {
  if (!bytes || bytes <= 0) return ''
  if (bytes >= 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

async function reDownload(item) {
  downloadingId.value = item.projectId
  try {
    const filename = await downloadProjectExport(item.projectId)
    showStatus(
      filename.endsWith('.zip')
        ? '项目打包(含视频)已开始下载'
        : '项目数据已开始下载'
    )
  } catch (error) {
    showStatus(error.message || '下载失败，请稍后重试', 'error')
  } finally {
    downloadingId.value = null
  }
}

async function removeItem(item) {
  if (!window.confirm(`删除「${item.title}」的下载记录吗？已下载到电脑的文件不受影响。`)) return
  try {
    await deleteDownload(item.projectId)
    items.value = items.value.filter((entry) => entry.projectId !== item.projectId)
    showStatus('下载记录已删除')
  } catch (error) {
    showStatus(error.message || '删除失败，请稍后重试', 'error')
  }
}

onMounted(async () => {
  try {
    items.value = (await listMyDownloads()).items || []
  } catch (error) {
    showStatus(error.message || '加载下载记录失败', 'error')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
})
</script>

<style scoped>
.downloads-page {
  width: 100%;
  max-width: none;
}
.btn-danger {
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 700;
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-danger:hover {
  background: #fee2e2;
}
.top-toast {
  position: fixed;
  top: 84px;
  left: 50%;
  z-index: 9999;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  max-width: min(560px, calc(100vw - 32px));
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 800;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.22);
  transform: translateX(-50%);
}
.top-toast.success {
  background: #ecfdf3;
  color: #166534;
  border: 1px solid #bbf7d0;
}
.top-toast.error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}
</style>
