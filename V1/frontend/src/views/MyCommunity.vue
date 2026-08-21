<template>
  <div class="my-community-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <button class="btn-secondary mb-6" @click="router.push('/community')">
      <i class="fas fa-arrow-left mr-2"></i>返回社区
    </button>

    <h1 class="text-2xl font-bold text-gray-800 mb-4">
      <i class="fas fa-user-shield mr-2 text-blue-600"></i>我的社区
    </h1>

    <div class="flex gap-2 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-button"
        :class="activeTab === tab.key ? 'tab-button-active' : ''"
        @click="switchTab(tab.key)"
      >
        <i class="fas mr-2" :class="tab.icon"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- 我的项目 -->
    <section v-if="activeTab === 'projects' && !manageTarget" class="bg-white rounded-lg shadow-md p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-xl"></i>
      </div>
      <div v-else-if="!projects.length" class="py-10 text-center text-gray-500">
        <i class="fas fa-box-open text-3xl mb-3 text-blue-400"></i>
        <p>还没有分享过项目。</p>
        <router-link to="/community" class="btn-primary inline-block mt-4">
          <i class="fas fa-plus mr-2"></i>去开源广场看看
        </router-link>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="project in projects"
          :key="project.id"
          class="border border-slate-200 rounded-xl p-4 flex justify-between items-center gap-3 flex-wrap"
        >
          <div class="min-w-0">
            <p class="font-semibold text-slate-800 truncate">
              {{ project.title }}
              <i v-if="project.hasVideo" class="fas fa-video ml-2 text-blue-500 text-xs"></i>
            </p>
            <p class="text-xs text-slate-400 mt-1">
              {{ formatDate(project.createdAt) }} · {{ project.author.username }}
            </p>
          </div>
          <div class="flex items-center gap-2 shrink-0 flex-wrap">
            <button class="btn-secondary" @click="openCommentManager('project', project.id, project.title)">
              <i class="fas fa-comment-dots mr-1"></i>评论管理
            </button>
            <button class="btn-secondary" @click="router.push(`/community/projects/${project.id}`)">
              <i class="fas fa-eye mr-1"></i>查看
            </button>
            <button class="btn-danger" @click="removeProject(project)">
              <i class="fas fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 我的帖子 -->
    <section v-else-if="activeTab === 'posts' && !manageTarget" class="bg-white rounded-lg shadow-md p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-xl"></i>
      </div>
      <div v-else-if="!posts.length" class="py-10 text-center text-gray-500">
        <i class="fas fa-comments text-3xl mb-3 text-blue-400"></i>
        <p>还没有发过帖子。</p>
        <router-link to="/community" class="btn-primary inline-block mt-4">
          <i class="fas fa-plus mr-2"></i>去讨论区发帖
        </router-link>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="post in posts"
          :key="post.id"
          class="border border-slate-200 rounded-xl p-4 flex justify-between items-center gap-3 flex-wrap"
        >
          <div class="min-w-0">
            <p class="font-semibold text-slate-800 truncate">{{ post.title }}</p>
            <p class="text-xs text-slate-400 mt-1">
              {{ formatDate(post.createdAt) }} · {{ post.commentCount }} 条评论
            </p>
          </div>
          <div class="flex items-center gap-2 shrink-0 flex-wrap">
            <button class="btn-secondary" @click="openCommentManager('post', post.id, post.title)">
              <i class="fas fa-comment-dots mr-1"></i>评论管理
            </button>
            <button class="btn-secondary" @click="router.push(`/community/posts/${post.id}`)">
              <i class="fas fa-eye mr-1"></i>查看
            </button>
            <button class="btn-danger" @click="removePost(post)">
              <i class="fas fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 评论管理面板 -->
    <section v-if="manageTarget" class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center flex-wrap gap-3 mb-4">
        <div>
          <h2 class="text-xl font-semibold text-gray-800">
            <i class="fas fa-comment-dots mr-2 text-blue-600"></i>评论管理
          </h2>
          <p class="text-sm text-slate-500 mt-1">
            {{ manageTarget.type === 'project' ? '项目' : '帖子' }}「{{ manageTarget.title }}」
          </p>
        </div>
        <button class="btn-secondary" @click="closeCommentManager">
          <i class="fas fa-arrow-left mr-2"></i>返回
        </button>
      </div>

      <div class="mb-4">
        <input
          v-model="manageSearch"
          class="input"
          placeholder="按内容筛选评论..."
          :disabled="manageLoading"
        />
      </div>

      <div v-if="manageLoading" class="py-8 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-xl"></i>
      </div>
      <div v-else-if="!filteredComments.length" class="py-8 text-center text-gray-500">
        <i class="fas fa-comment-slash text-2xl mb-2 text-blue-400"></i>
        <p>{{ manageSearch.trim() ? '没有匹配的评论。' : '还没有评论。' }}</p>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="comment in filteredComments"
          :key="comment.id"
          class="border border-slate-200 rounded-xl p-4"
          :style="{ marginLeft: Math.min(comment.depth, 6) * 24 + 'px' }"
        >
          <div class="flex justify-between items-center gap-3 flex-wrap">
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 text-xs text-slate-500">
                <i class="fas fa-circle-user" :class="comment.depth === 0 ? 'text-blue-500' : 'text-blue-400'"></i>
                <span class="font-semibold text-slate-700">{{ comment.author.username }}</span>
                <span>{{ formatDate(comment.createdAt) }}</span>
                <span v-if="comment.depth > 0" class="rounded-full px-2 py-0.5 bg-slate-100 text-slate-400">
                  回复
                </span>
              </div>
              <p class="text-sm text-slate-700 mt-1.5 whitespace-pre-wrap break-words">
                {{ comment.content }}
              </p>
            </div>
            <button class="btn-danger shrink-0" @click="removeManagedComment(comment)">
              <i class="fas fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 我的评论 -->
    <section v-else class="bg-white rounded-lg shadow-md p-6">
      <div v-if="loading" class="py-10 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-xl"></i>
      </div>
      <div v-else-if="!comments.length" class="py-10 text-center text-gray-500">
        <i class="fas fa-comment-slash text-3xl mb-3 text-blue-400"></i>
        <p>还没有发表过评论。</p>
      </div>
      <div v-else class="space-y-3">
        <div
          v-for="comment in comments"
          :key="comment.id"
          class="border border-slate-200 rounded-xl p-4"
        >
          <div class="flex justify-between items-center gap-3 flex-wrap">
            <p class="text-sm text-slate-700 whitespace-pre-wrap break-words min-w-0 flex-1">
              {{ comment.content }}
            </p>
            <button class="btn-danger shrink-0" @click="removeComment(comment)">
              <i class="fas fa-trash mr-1"></i>删除
            </button>
          </div>
          <div class="flex items-center gap-3 mt-2 text-xs text-slate-400">
            <span class="text-slate-500">{{ formatDate(comment.createdAt) }}</span>
            <button
              class="hover:text-blue-600 transition-colors"
              @click="router.push(targetRoute(comment))"
            >
              <i class="fas fa-comment-dots mr-1"></i>
              {{ comment.targetTitle || '已删除的内容' }}
              <span v-if="comment.replyCount > 0" class="ml-1 text-slate-400">
                · 收到 {{ comment.replyCount }} 条回复
              </span>
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  deleteComment,
  deletePost,
  deleteProject,
  listComments,
  listMyComments,
  listPosts,
  listProjects,
} from '../api/community'

const router = useRouter()

const tabs = [
  { key: 'projects', label: '我的项目', icon: 'fa-box-open' },
  { key: 'posts', label: '我的帖子', icon: 'fa-comments' },
  { key: 'comments', label: '我的评论', icon: 'fa-comment-dots' },
]

const activeTab = ref('projects')
const loading = ref(false)
const projects = ref([])
const posts = ref([])
const comments = ref([])

// 评论管理面板状态
const manageTarget = ref(null) // { type: 'project' | 'post', id, title }
const manageComments = ref([])
const manageSearch = ref('')
const manageLoading = ref(false)

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

async function switchTab(key) {
  activeTab.value = key
  loading.value = true
  try {
    if (key === 'projects') {
      projects.value = (await listProjects({ mine: true })).items || []
    } else if (key === 'posts') {
      posts.value = (await listPosts({ mine: true })).items || []
    } else {
      comments.value = (await listMyComments()).items || []
    }
  } catch (error) {
    showStatus(error.message || '加载失败，请稍后重试', 'error')
  } finally {
    loading.value = false
  }
}

function targetRoute(comment) {
  if (comment.targetType === 'post') {
    return `/community/posts/${comment.targetId}`
  }
  return `/community/projects/${comment.targetId}`
}

// ------------------------------------------------------------- 评论管理

function openCommentManager(type, id, title) {
  manageTarget.value = { type, id, title }
  manageSearch.value = ''
  loadManageComments()
}

function closeCommentManager() {
  manageTarget.value = null
  manageComments.value = []
  manageSearch.value = ''
}

async function loadManageComments() {
  if (!manageTarget.value) return
  manageLoading.value = true
  try {
    const data = await listComments(manageTarget.value.type, manageTarget.value.id)
    manageComments.value = data.items || []
  } catch (error) {
    manageComments.value = []
    showStatus(error.message || '加载评论失败', 'error')
  } finally {
    manageLoading.value = false
  }
}

// 按内容关键词过滤树:节点自身匹配则保留其子树;自身不匹配但子树有匹配则保留父链
function filterTree(nodes, keyword) {
  const result = []
  for (const node of nodes) {
    const children = filterTree(node.replies || [], keyword)
    const selfMatch = node.content.includes(keyword)
    if (selfMatch || children.length) {
      result.push({ ...node, replies: children })
    }
  }
  return result
}

// 树 → 扁平列表(带 depth 用于缩进)
function flattenTree(nodes, depth = 0, out = []) {
  for (const node of nodes) {
    out.push({ ...node, depth })
    flattenTree(node.replies || [], depth + 1, out)
  }
  return out
}

const filteredComments = computed(() => {
  const keyword = manageSearch.value.trim()
  const roots = keyword ? filterTree(manageComments.value, keyword) : manageComments.value
  return flattenTree(roots)
})

async function removeManagedComment(comment) {
  const replyCount = comment.replies?.length || 0
  const hint =
    replyCount > 0 ? `该评论下有 ${replyCount} 条回复，删除后回复将一并删除。` : ''
  if (!window.confirm(`确定删除这条评论吗？${hint}`)) return
  try {
    await deleteComment(comment.id)
    showStatus('评论已删除')
    await loadManageComments()
  } catch (error) {
    showStatus(error.message || '删除失败，请稍后重试', 'error')
  }
}

async function removeProject(project) {
  if (!window.confirm(`确定删除分享「${project.title}」吗？删除后其他用户将无法查看。`)) return
  try {
    await deleteProject(project.id)
    projects.value = projects.value.filter((item) => item.id !== project.id)
    showStatus('项目分享已删除')
  } catch (error) {
    showStatus(error.message || '删除失败，请稍后重试', 'error')
  }
}

async function removePost(post) {
  if (!window.confirm(`确定删除帖子「${post.title}」吗？删除后其下所有评论将一并删除。`)) return
  try {
    await deletePost(post.id)
    posts.value = posts.value.filter((item) => item.id !== post.id)
    showStatus('帖子已删除')
  } catch (error) {
    showStatus(error.message || '删除失败，请稍后重试', 'error')
  }
}

async function removeComment(comment) {
  const hint = comment.replyCount > 0 ? `该评论收到 ${comment.replyCount} 条回复，删除后回复将一并删除。` : ''
  if (!window.confirm(`确定删除这条评论吗？${hint}`)) return
  try {
    await deleteComment(comment.id)
    comments.value = comments.value.filter((item) => item.id !== comment.id)
    showStatus('评论已删除')
  } catch (error) {
    showStatus(error.message || '删除失败，请稍后重试', 'error')
  }
}

onMounted(() => {
  switchTab('projects')
})

onBeforeUnmount(() => {
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
})
</script>

<style scoped>
.my-community-page {
  width: 100%;
  max-width: none;
}
.tab-button {
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.15s ease;
}
.tab-button:hover {
  color: #334155;
  background: #e2e8f0;
}
.tab-button-active {
  color: #ffffff;
  background: #2563eb;
  border-color: #2563eb;
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
