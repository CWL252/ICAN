<template>
  <div class="project-detail-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <button class="btn-secondary mb-6" @click="router.back()">
      <i class="fas fa-arrow-left mr-2"></i>返回社区
    </button>

    <section v-if="loading" class="bg-white rounded-lg shadow-md p-10 text-center text-gray-400">
      <i class="fas fa-circle-notch fa-spin text-2xl"></i>
    </section>

    <div v-else-if="!project" class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
      <i class="fas fa-box-open text-3xl mb-3 text-blue-500"></i>
      <p>项目不存在或已被作者取消分享。</p>
      <router-link to="/community" class="btn-primary inline-block mt-4">
        <i class="fas fa-arrow-left mr-2"></i>返回社区
      </router-link>
    </div>

    <div v-else class="space-y-6">
      <!-- 头部 -->
      <section class="bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-start gap-4 flex-wrap">
          <div class="min-w-0">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">{{ project.title }}</h1>
            <div class="flex items-center gap-3 text-sm text-slate-500 flex-wrap">
              <span class="flex items-center gap-1">
                <i class="fas fa-circle-user text-blue-600"></i>
                <span class="font-semibold text-slate-700">{{ project.author.username }}</span>
              </span>
              <span>{{ formatDate(project.createdAt) }}</span>
              <span
                class="text-xs rounded-full px-3 py-1 bg-emerald-100 text-emerald-700"
              >
                {{ project.status || '分析完成' }}
              </span>
            </div>
          </div>
          <button
            v-if="!isSelf"
            class="btn-secondary"
            :class="isFollowing ? 'text-blue-600' : ''"
            @click="toggleFollow"
          >
            <i class="fas mr-2" :class="isFollowing ? 'fa-user-check' : 'fa-user-plus'"></i>
            {{ isFollowing ? '已关注' : '关注作者' }}
          </button>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-slate-600 mt-5">
          <div>
            <p class="text-slate-400">术式</p>
            <p class="font-medium">{{ project.procedure || '未填写' }}</p>
          </div>
          <div>
            <p class="text-slate-400">术者</p>
            <p class="font-medium">{{ project.surgeon || '未填写' }}</p>
          </div>
          <div>
            <p class="text-slate-400">科室</p>
            <p class="font-medium">{{ project.department || '未填写' }}</p>
          </div>
          <div>
            <p class="text-slate-400">手术日期</p>
            <p class="font-medium">{{ project.date || '未填写' }}</p>
          </div>
        </div>

        <p v-if="project.description" class="text-sm text-slate-600 mt-4 whitespace-pre-wrap">
          {{ project.description }}
        </p>

        <!-- 共享手术视频 -->
        <div v-if="project.hasVideo" class="mt-5">
          <div class="rounded-xl overflow-hidden bg-black">
            <video
              ref="videoRef"
              class="w-full max-h-[420px]"
              controls
              playsinline
              preload="metadata"
              :src="videoUrl"
              @error="onVideoError"
            ></video>
          </div>
          <p v-if="videoError" class="text-xs text-red-500 mt-2">
            <i class="fas fa-triangle-exclamation mr-1"></i>{{ videoError }}
          </p>
          <p v-else class="text-xs text-slate-400 mt-2">
            <i class="fas fa-video mr-1"></i>社区共享视频 · {{ project.videoFileName || '' }}
          </p>
        </div>

        <div class="flex items-center gap-2 mt-5 pt-4 border-t border-slate-200">
          <button
            class="engagement-button"
            :class="project.liked ? 'engagement-on' : ''"
            @click="toggleLike"
          >
            <i class="fas" :class="project.liked ? 'fa-heart' : 'fa-heart fa-regular'"></i>
            <span>{{ project.likeCount }}</span>
            <span class="text-xs text-slate-400">{{ project.liked ? '已赞' : '点赞' }}</span>
          </button>
          <button
            class="engagement-button"
            :class="project.favorited ? 'engagement-fav' : ''"
            @click="toggleFavorite"
          >
            <i class="fas" :class="project.favorited ? 'fa-star' : 'fa-star fa-regular'"></i>
            <span>{{ project.favoriteCount }}</span>
            <span class="text-xs text-slate-400">{{ project.favorited ? '已收藏' : '收藏' }}</span>
          </button>
        </div>
      </section>

      <!-- 阶段分析区 -->
      <section v-if="phaseData?.result" class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">
          <i class="fas fa-chart-line mr-2 text-blue-600"></i>阶段分析
        </h2>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm text-slate-600 mb-6">
          <div>
            <p class="text-slate-400">视频时长</p>
            <p class="font-medium">{{ formatDuration(result.meta?.durationSeconds) || '—' }}</p>
          </div>
          <div>
            <p class="text-slate-400">分析步骤</p>
            <p class="font-medium">{{ steps.length }} 步</p>
          </div>
          <div>
            <p class="text-slate-400">AI 生成片段</p>
            <p class="font-medium">{{ aiSegmentCount }} 段</p>
          </div>
          <div>
            <p class="text-slate-400">人工修正片段</p>
            <p class="font-medium">{{ editedSegmentCount }} 段</p>
          </div>
        </div>

        <div v-if="distribution.length" class="mb-6">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">
            阶段分布
            <span v-if="useEditedDistribution" class="ml-2 text-xs font-normal text-blue-600">
              <i class="fas fa-user-pen mr-1"></i>按人工标记
            </span>
          </h3>
          <div class="space-y-2">
            <div
              v-for="(item, index) in distribution"
              :key="item.phaseLabel + '-' + index"
              class="flex items-center gap-3"
            >
              <span class="text-xs text-slate-500 w-32 truncate">{{ phaseLabelText(item.phaseLabel) }}</span>
              <div class="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :style="{ width: `${phasePercent(item.seconds)}%`, background: phaseColor(index) }"
                ></div>
              </div>
              <span class="text-xs text-slate-500 w-16 text-right">{{ formatDuration(item.seconds) }}</span>
            </div>
          </div>
        </div>

        <div v-if="steps.length">
          <h3 class="text-sm font-semibold text-slate-700 mb-3">分析步骤</h3>
          <ol class="space-y-3">
            <li
              v-for="(step, index) in steps"
              :key="index"
              class="border border-slate-200 rounded-xl p-4 bg-slate-50"
            >
              <div class="flex justify-between items-center gap-3 flex-wrap">
                <h4 class="font-medium text-slate-800">
                  <span class="text-blue-600 font-bold mr-2">{{ index + 1 }}.</span>
                  {{ step.title }}
                </h4>
                <div class="flex items-center gap-3 text-xs">
                  <span class="text-slate-500">{{ step.time }}</span>
                  <span
                    class="rounded-full px-2 py-0.5 font-semibold"
                    :class="stepLevelClass(step.level)"
                  >
                    <i class="fas mr-1" :class="stepLevelIcon(step.level)"></i>
                    {{ step.level }}
                  </span>
                  <span v-if="step.confidence != null" class="text-slate-500">
                    置信度 {{ formatConfidence(step.confidence) }}
                  </span>
                </div>
              </div>
              <p v-if="step.description" class="text-sm text-slate-600 mt-2">{{ step.description }}</p>
            </li>
          </ol>
        </div>
      </section>

      <!-- 评论区 -->
      <section class="bg-white rounded-lg shadow-md p-6">
        <CommentList target-type="project" :target-id="project.id" :can-manage="isSelf" />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getProject, getUserProfile, followUser, projectVideoUrl, setFavorite, setLike } from '../api/community'
import { currentUser } from '../lib/auth'
import CommentList from '../components/CommentList.vue'

const route = useRoute()
const router = useRouter()

const project = ref(null)
const loading = ref(true)
const isFollowing = ref(false)
const videoRef = ref(null)
const videoError = ref('')
const isSelf = computed(() => project.value && currentUser.value?.id === project.value.author.id)
const videoUrl = computed(() =>
  project.value?.hasVideo ? projectVideoUrl(project.value.id) : ''
)

function onVideoError() {
  videoError.value = '视频加载失败，可能已被作者移除或文件损坏。'
}

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

function formatDuration(secondsValue) {
  if (!Number.isFinite(secondsValue) || secondsValue < 0) return ''
  const total = Math.round(secondsValue)
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const seconds = total % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

function formatConfidence(value) {
  if (!Number.isFinite(value)) return ''
  return `${Math.round(value * 100)}%`
}

function phaseLabelText(key) {
  if (!key) return '未知阶段'
  return key
}

const phaseData = computed(() => project.value?.phaseData || null)
const result = computed(() => phaseData.value?.result || {})
const editedSegments = computed(() => phaseData.value?.editedSegments || [])

// 有人工标记片段时按标记片段展示步骤时间线，否则回退到 AI 生成的步骤摘要
const steps = computed(() => {
  const edited = editedSegments.value
  if (edited.length) {
    return edited.map((seg) => ({
      title: seg.title || seg.phaseLabel || seg.phaseKey || '未命名片段',
      time: seg.time || formatTimeRange(seg.startSeconds, seg.endSeconds),
      description: seg.description || '',
      level: '人工标记',
      confidence: null,
    }))
  }
  return result.value.steps || []
})

function formatTimeRange(startSeconds, endSeconds) {
  if (!Number.isFinite(Number(startSeconds))) return ''
  const fmt = (value) => {
    const total = Math.max(0, Math.round(Number(value)))
    const minutes = Math.floor(total / 60)
    const seconds = total % 60
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  const start = fmt(startSeconds)
  if (!Number.isFinite(Number(endSeconds))) return start
  return `${start} - ${fmt(endSeconds)}`
}

function stepLevelClass(level) {
  if (level === '高置信度') return 'bg-green-100 text-green-700'
  if (level === '人工标记') return 'bg-blue-100 text-blue-700'
  return 'bg-amber-100 text-amber-700'
}

function stepLevelIcon(level) {
  if (level === '高置信度') return 'fa-check-circle'
  if (level === '人工标记') return 'fa-user-pen'
  return 'fa-exclamation-circle'
}

// 有人工标记片段时按标记计算阶段分布，否则回退到 AI 原始分布
const useEditedDistribution = computed(() => editedSegments.value.length > 0)
const distribution = computed(() => {
  const edited = editedSegments.value
  if (edited.length) {
    const totals = new Map()
    const order = new Map()
    for (const seg of edited) {
      const seconds = Number(seg.endSeconds ?? 0) - Number(seg.startSeconds ?? 0)
      if (!Number.isFinite(seconds) || seconds <= 0) continue
      const label = seg.phaseLabel || seg.phaseKey || '未知阶段'
      if (!totals.has(label)) {
        totals.set(label, 0)
        order.set(label, order.size)
      }
      totals.set(label, totals.get(label) + seconds)
    }
    const items = [...totals.entries()]
      .sort((a, b) => order.get(a[0]) - order.get(b[0]))
      .map(([phaseLabel, seconds]) => ({ phaseLabel, seconds }))
    if (items.length) {
      return items
    }
  }
  return result.value.distribution || []
})

const aiSegmentCount = computed(
  () => editedSegments.value.filter((seg) => seg.source === 'ai' && !seg.edited).length
)
const editedSegmentCount = computed(
  () => editedSegments.value.filter((seg) => seg.edited || seg.source === 'manual').length
)

function phasePercent(seconds) {
  const total = distribution.value.reduce((sum, item) => sum + (item.seconds || 0), 0)
  if (!total) return 0
  return Math.max(2, Math.round(((seconds || 0) / total) * 100))
}

const PHASE_COLORS = ['#2563eb', '#16a34a', '#ea580c', '#7c3aed', '#0891b2', '#dc2626', '#ca8a04', '#4f46e5']

function phaseColor(index) {
  return PHASE_COLORS[index % PHASE_COLORS.length]
}

async function toggleLike() {
  try {
    const next = !project.value.liked
    const resultData = await setLike('project', project.value.id, next)
    project.value.liked = resultData.liked
    project.value.likeCount = resultData.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

async function toggleFavorite() {
  try {
    const next = !project.value.favorited
    const resultData = await setFavorite('project', project.value.id, next)
    project.value.favorited = resultData.favorited
    project.value.favoriteCount = resultData.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

async function toggleFollow() {
  try {
    const next = !isFollowing.value
    const resultData = await followUser(project.value.author.id, next)
    isFollowing.value = resultData.following
    showStatus(next ? '已关注作者' : '已取消关注')
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

onMounted(async () => {
  try {
    const data = await getProject(route.params.id)
    project.value = data.item

    if (data.item && currentUser.value?.id !== data.item.author.id) {
      try {
        const profile = await getUserProfile(data.item.author.id)
        isFollowing.value = profile.isFollowing
      } catch {
        isFollowing.value = false
      }
    }
  } catch (error) {
    project.value = null
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
.project-detail-page {
  width: 100%;
  max-width: none;
}
.engagement-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #475569;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.15s ease;
}
.engagement-button:hover {
  background: #f1f5f9;
  color: #334155;
}
.engagement-on {
  color: #e11d48;
  background: #fff1f2;
  border-color: #fecdd3;
}
.engagement-fav {
  color: #d97706;
  background: #fffbeb;
  border-color: #fde68a;
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
