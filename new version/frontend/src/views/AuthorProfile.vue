<template>
  <div class="author-profile-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <button class="btn-secondary mb-6" @click="router.back()">
      <i class="fas fa-arrow-left mr-2"></i>返回
    </button>

    <section v-if="loading" class="bg-white rounded-lg shadow-md p-10 text-center text-gray-400">
      <i class="fas fa-circle-notch fa-spin text-2xl"></i>
    </section>

    <div v-else-if="!profile" class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
      <i class="fas fa-user-slash text-3xl mb-3 text-blue-500"></i>
      <p>用户不存在或已被删除。</p>
    </div>

    <div v-else class="space-y-6">
      <!-- 作者信息卡 -->
      <section class="bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-start gap-4 flex-wrap">
          <div class="flex items-center gap-4">
            <div
              class="w-16 h-16 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-2xl font-bold shrink-0"
            >
              {{ (profile.user.username || '?').charAt(0).toUpperCase() }}
            </div>
            <div>
              <h1 class="text-2xl font-bold text-gray-800">{{ profile.user.username }}</h1>
              <p class="text-xs text-slate-400 mt-1">加入于 {{ formatDate(profile.user.createdAt) }}</p>
            </div>
          </div>
          <button
            v-if="!profile.isSelf"
            class="btn-secondary"
            :class="profile.isFollowing ? 'text-blue-600' : ''"
            @click="toggleFollow"
          >
            <i class="fas mr-2" :class="profile.isFollowing ? 'fa-user-check' : 'fa-user-plus'"></i>
            {{ profile.isFollowing ? '已关注' : '关注作者' }}
          </button>
        </div>

        <div class="grid grid-cols-4 gap-3 text-center mt-6">
          <div>
            <p class="text-xl font-bold text-slate-800">{{ profile.stats.projectCount }}</p>
            <p class="text-xs text-slate-400">分享项目</p>
          </div>
          <div>
            <p class="text-xl font-bold text-slate-800">{{ profile.stats.postCount }}</p>
            <p class="text-xs text-slate-400">发帖</p>
          </div>
          <div>
            <p class="text-xl font-bold text-slate-800">{{ profile.stats.followerCount }}</p>
            <p class="text-xs text-slate-400">粉丝</p>
          </div>
          <div>
            <p class="text-xl font-bold text-slate-800">{{ profile.stats.followingCount }}</p>
            <p class="text-xs text-slate-400">关注</p>
          </div>
        </div>
      </section>

      <!-- 内容 tab -->
      <section class="bg-white rounded-lg shadow-md p-6">
        <div class="flex gap-2 mb-5">
          <button
            class="tab-button"
            :class="activeTab === 'projects' ? 'tab-button-active' : ''"
            @click="switchTab('projects')"
          >
            <i class="fas fa-box-open mr-2"></i>分享的项目
          </button>
          <button
            class="tab-button"
            :class="activeTab === 'posts' ? 'tab-button-active' : ''"
            @click="switchTab('posts')"
          >
            <i class="fas fa-comments mr-2"></i>帖子
          </button>
        </div>

        <div v-if="contentLoading" class="py-10 text-center text-gray-400">
          <i class="fas fa-circle-notch fa-spin text-xl"></i>
        </div>

        <div v-else-if="activeTab === 'projects'">
          <div v-if="!projects.length" class="py-10 text-center text-gray-500">
            <i class="fas fa-box-open text-3xl mb-3 text-blue-400"></i>
            <p>该作者还没有分享过项目。</p>
          </div>
          <div v-else class="space-y-3">
            <article
              v-for="project in projects"
              :key="project.id"
              class="border border-slate-200 rounded-xl p-4 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
              @click="router.push(`/community/projects/${project.id}`)"
            >
              <div class="flex justify-between items-center gap-3 flex-wrap">
                <h3 class="font-bold text-slate-800 truncate">
                  {{ project.title }}
                  <i v-if="project.hasVideo" class="fas fa-video ml-1 text-blue-500 text-xs" title="含共享视频"></i>
                </h3>
                <span class="text-xs rounded-full px-3 py-1 bg-emerald-100 text-emerald-700 shrink-0">
                  {{ project.status || '分析完成' }}
                </span>
              </div>
              <div class="flex items-center gap-4 text-xs text-slate-400 mt-2 flex-wrap">
                <span>{{ project.procedure || '未填写术式' }}</span>
                <span>{{ formatDate(project.createdAt) }}</span>
                <span>
                  <i class="fas fa-heart mr-1 text-rose-400"></i>{{ project.likeCount }}
                  <i class="fas fa-star ml-2 mr-1 text-amber-400"></i>{{ project.favoriteCount }}
                </span>
              </div>
              <p v-if="project.description" class="text-sm text-slate-600 mt-2 line-clamp-2">
                {{ project.description }}
              </p>
            </article>
          </div>
        </div>

        <div v-else>
          <div v-if="!posts.length" class="py-10 text-center text-gray-500">
            <i class="fas fa-comments text-3xl mb-3 text-blue-400"></i>
            <p>该作者还没有发过帖子。</p>
          </div>
          <div v-else class="space-y-3">
            <article
              v-for="post in posts"
              :key="post.id"
              class="border border-slate-200 rounded-xl p-4 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
              @click="router.push(`/community/posts/${post.id}`)"
            >
              <h3 class="font-bold text-slate-800">{{ post.title }}</h3>
              <p v-if="post.excerpt" class="text-sm text-slate-600 mt-2 line-clamp-2">{{ post.excerpt }}</p>
              <p class="text-xs text-slate-400 mt-2">
                {{ formatDate(post.createdAt) }} ·
                <i class="fas fa-comment-dots mr-1"></i>{{ post.commentCount }} 条评论
              </p>
            </article>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { followUser, getUserProfile, listPosts, listProjects } from '../api/community'

const route = useRoute()
const router = useRouter()

const profile = ref(null)
const loading = ref(true)
const activeTab = ref('projects')
const contentLoading = ref(false)
const projects = ref([])
const posts = ref([])

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
  contentLoading.value = true
  try {
    if (key === 'projects') {
      projects.value = (await listProjects({ authorId: route.params.id })).items || []
    } else {
      posts.value = (await listPosts({ authorId: route.params.id })).items || []
    }
  } catch (error) {
    showStatus(error.message || '加载失败，请稍后重试', 'error')
  } finally {
    contentLoading.value = false
  }
}

async function toggleFollow() {
  if (!profile.value) return
  try {
    const result = await followUser(profile.value.user.id, !profile.value.isFollowing)
    profile.value.isFollowing = result.following
    profile.value.stats.followerCount = result.followingCount
    showStatus(result.following ? '已关注作者' : '已取消关注')
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

onMounted(async () => {
  try {
    profile.value = await getUserProfile(route.params.id)
  } catch (error) {
    profile.value = null
  } finally {
    loading.value = false
  }
  if (profile.value) {
    await switchTab('projects')
  }
})

onBeforeUnmount(() => {
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
})
</script>

<style scoped>
.author-profile-page {
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
