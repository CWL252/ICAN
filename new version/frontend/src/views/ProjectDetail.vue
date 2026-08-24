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
              <span
                v-if="project.category"
                class="text-xs rounded-full px-3 py-1 bg-blue-100 text-blue-700"
              >
                <i class="fas fa-tags mr-1"></i
                >{{ project.subcategory || project.category }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0 flex-wrap">
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

      <div class="detail-grid">
        <div class="detail-main">
          <!-- 共享手术视频 -->
          <section v-if="project.hasVideo" class="bg-white rounded-lg shadow-md p-6">
            <div class="rounded-xl overflow-hidden bg-black">
              <video
                ref="videoRef"
                class="w-full max-h-[480px]"
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

      <!-- 器械使用统计 -->
      <section v-if="instrumentItems.length" class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">
          <i class="fas fa-syringe mr-2 text-blue-600"></i>器械使用统计
        </h2>
        <div class="space-y-2">
          <div
            v-for="item in instrumentItems"
            :key="item.key || item.label"
            class="flex items-center gap-3"
          >
            <span class="text-sm text-slate-600 w-32 truncate">{{ item.label }}</span>
            <div class="flex-1 h-4 bg-slate-100 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full"
                :style="{ width: `${instrumentPercent(item.seconds)}%`, background: instrumentColor(item) }"
              ></div>
            </div>
            <span class="text-sm text-slate-500 w-16 text-right">{{ formatInstrumentTime(item.seconds) }}</span>
          </div>
        </div>
      </section>

      <!-- AI 分析报告 -->
      <section v-if="report" class="bg-white rounded-lg shadow-md p-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">
          <i class="fas fa-file-lines mr-2 text-blue-600"></i>AI 分析报告
        </h2>

        <div v-if="report.summary" class="rounded-xl border border-slate-200 p-4 mb-4">
          <h3 class="text-sm font-bold text-slate-700 mb-2">
            <i class="fas fa-align-left mr-1 text-blue-600"></i>总结
          </h3>
          <p class="text-sm text-slate-600 leading-relaxed">{{ report.summary }}</p>
        </div>

        <div
          v-if="report.metrics?.length"
          class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4"
        >
          <div
            v-for="metric in report.metrics"
            :key="metric.label"
            class="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center"
          >
            <span class="block text-xs text-slate-500 mb-1">{{ metric.label }}</span>
            <strong class="block text-lg text-slate-800">{{ metric.value }}</strong>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="rounded-xl border border-slate-200 p-4">
            <h3 class="text-sm font-bold text-slate-700 mb-2">
              <i class="fas fa-clipboard-check mr-1 text-emerald-600"></i>操作评估
            </h3>
            <ul class="space-y-2">
              <li
                v-for="(line, index) in report.operationAssessment || []"
                :key="index"
                class="text-sm text-slate-600 leading-relaxed flex gap-2"
              >
                <span class="text-emerald-500 mt-0.5">•</span>{{ line }}
              </li>
            </ul>
          </div>
          <div class="rounded-xl border border-slate-200 p-4">
            <h3 class="text-sm font-bold text-slate-700 mb-2">
              <i class="fas fa-triangle-exclamation mr-1 text-amber-600"></i>关键问题
            </h3>
            <ul class="space-y-2">
              <li
                v-for="(line, index) in report.keyIssues || []"
                :key="index"
                class="text-sm text-slate-600 leading-relaxed flex gap-2"
              >
                <span class="text-amber-500 mt-0.5">•</span>{{ line }}
              </li>
            </ul>
          </div>
          <div class="rounded-xl border border-slate-200 p-4">
            <h3 class="text-sm font-bold text-slate-700 mb-2">
              <i class="fas fa-lightbulb mr-1 text-blue-600"></i>改进建议
            </h3>
            <ul class="space-y-2">
              <li
                v-for="(line, index) in report.improvementSuggestions || []"
                :key="index"
                class="text-sm text-slate-600 leading-relaxed flex gap-2"
              >
                <span class="text-blue-500 mt-0.5">•</span>{{ line }}
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- 评论区 -->
      <section class="bg-white rounded-lg shadow-md p-6">
        <CommentList target-type="project" :target-id="project.id" :can-manage="isSelf" />
      </section>
      </div>

      <aside class="detail-aside">
        <!-- 智能问答 -->
        <section class="qa-side-card">
            <h2 class="text-xl font-semibold text-gray-800 mb-1">
              <i class="fas fa-robot mr-2 text-blue-600"></i>智能问答
            </h2>
            <p class="text-sm text-slate-400 mb-3">
              基于该项目的分析数据向 AI 提问，如「这台手术的关键步骤有哪些？」
            </p>
            <div ref="qaPanelRef" class="qa-panel">
              <div
                v-if="!qaMessages.length"
                class="text-center flex-1 flex flex-col items-center justify-center"
              >
                <i class="fas fa-comments text-3xl mb-3 text-slate-300"></i>
                <p class="text-slate-400 text-sm">还没有提问，问问 AI 关于这台手术的分析结论吧</p>
              </div>
              <div
                v-for="(msg, index) in qaMessages"
                :key="index"
                class="qa-row"
                :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
              >
                <div class="qa-bubble" :class="msg.role === 'user' ? 'qa-user' : 'qa-ai'">
                  {{ msg.content }}
                </div>
              </div>
              <div v-if="qaLoading" class="qa-row justify-start">
                <div class="qa-bubble qa-ai">
                  <i class="fas fa-circle-notch fa-spin mr-2"></i>AI 思考中…
                </div>
              </div>
            </div>
            <div class="flex gap-2 mt-3">
              <input
                v-model="qaInput"
                class="input flex-1"
                placeholder="输入你的问题，回车发送"
                :disabled="qaLoading"
                @keyup.enter="sendQuestion"
              />
              <button
                class="btn-primary"
                :disabled="qaLoading || !qaInput.trim()"
                @click="sendQuestion"
              >
                <i class="fas fa-paper-plane mr-1"></i>发送
              </button>
            </div>
            <div class="flex items-center justify-between mt-2">
              <p class="text-xs text-slate-400">回答由 AI 生成，医学结论请以专业医师判断为准</p>
              <button
                v-if="qaMessages.length"
                class="text-xs text-slate-400 hover:text-slate-600"
                @click="qaMessages = []"
              >
                清空对话
              </button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  askProjectQuestion,
  getProject,
  getUserProfile,
  followUser,
  projectVideoUrl,
  setFavorite,
  setLike,
} from '../api/community'
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

// 器械使用统计与 AI 分析报告(分享时携带,旧项目可能没有)
const instrumentItems = computed(
  () => project.value?.phaseData?.instrumentStats?.items || []
)
const report = computed(() => project.value?.phaseData?.report || null)

function formatInstrumentTime(secondsValue) {
  const total = Math.max(0, Math.round(Number(secondsValue) || 0))
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

function instrumentPercent(secondsValue) {
  const total = instrumentItems.value.reduce(
    (sum, item) => sum + (Number(item.seconds) || 0),
    0
  )
  if (!total) return 0
  return Math.max(2, Math.round(((Number(secondsValue) || 0) / total) * 100))
}

const INSTRUMENT_COLORS = ['#2563eb', '#16a34a', '#ea580c', '#7c3aed', '#0891b2', '#dc2626', '#ca8a04', '#4f46e5']

function instrumentColor(item) {
  const index = instrumentItems.value.findIndex((it) => (it.key || it.label) === (item.key || item.label))
  return INSTRUMENT_COLORS[(index >= 0 ? index : 0) % INSTRUMENT_COLORS.length]
}

// 智能问答
const qaMessages = ref([])
const qaInput = ref('')
const qaLoading = ref(false)
const qaPanelRef = ref(null)

function scrollQaToBottom() {
  requestAnimationFrame(() => {
    if (qaPanelRef.value) {
      qaPanelRef.value.scrollTop = qaPanelRef.value.scrollHeight
    }
  })
}

async function sendQuestion() {
  const question = qaInput.value.trim()
  if (!question || qaLoading.value) return
  qaMessages.value.push({ role: 'user', content: question })
  qaInput.value = ''
  qaLoading.value = true
  scrollQaToBottom()
  try {
    const data = await askProjectQuestion(project.value.id, question)
    qaMessages.value.push({ role: 'ai', content: data.answer })
  } catch (error) {
    qaMessages.value.push({
      role: 'ai',
      content: error.message || 'AI 服务暂时不可用，请稍后再试',
    })
  } finally {
    qaLoading.value = false
    scrollQaToBottom()
  }
}

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
/* 两栏布局：左侧视频+分析，右侧吸顶智能问答（仿 Analysis 页右侧助手面板） */
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}
.detail-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.detail-aside {
  min-width: 0;
}
.qa-side-card {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.1);
  padding: 24px;
}
@media (min-width: 1024px) {
  .detail-grid {
    grid-template-columns: minmax(0, 1fr) 480px;
  }
  .detail-aside {
    position: sticky;
    top: 88px;
    height: calc(100vh - 130px);
    min-height: 420px;
  }
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
/* 点赞/收藏图标状态色：未点击灰色，已赞红色，已收藏橙色 */
.engagement-button i {
  color: #94a3b8;
}
.engagement-button.engagement-on i {
  color: #e11d48;
}
.engagement-button.engagement-fav i {
  color: #d97706;
}
.qa-panel {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}
.qa-row {
  display: flex;
}
.qa-bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}
.qa-user {
  background: #2563eb;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}
.qa-ai {
  background: #ffffff;
  color: #334155;
  border: 1px solid #e2e8f0;
  border-bottom-left-radius: 4px;
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
