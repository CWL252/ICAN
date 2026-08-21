<template>
  <div class="post-detail-page px-4 sm:px-6 lg:px-8 py-6">
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

    <div v-else-if="!post" class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
      <i class="fas fa-comment-slash text-3xl mb-3 text-blue-500"></i>
      <p>帖子不存在或已被作者删除。</p>
      <router-link to="/community" class="btn-primary inline-block mt-4">
        <i class="fas fa-arrow-left mr-2"></i>返回社区
      </router-link>
    </div>

    <div v-else class="space-y-6">
      <section class="bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-start gap-4 flex-wrap">
          <div class="min-w-0">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">{{ post.title }}</h1>
            <div class="flex items-center gap-3 text-sm text-slate-500 flex-wrap">
              <span class="flex items-center gap-1">
                <i class="fas fa-circle-user text-blue-600"></i>
                <span class="font-semibold text-slate-700">{{ post.author.username }}</span>
              </span>
              <span>{{ formatDate(post.createdAt) }}</span>
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

        <div class="markdown-body mt-5" v-html="renderedContent"></div>

        <div class="flex items-center gap-2 mt-6 pt-4 border-t border-slate-200">
          <button
            class="engagement-button"
            :class="post.liked ? 'engagement-on' : ''"
            @click="toggleLike"
          >
            <i class="fas" :class="post.liked ? 'fa-heart' : 'fa-heart fa-regular'"></i>
            <span>{{ post.likeCount }}</span>
            <span class="text-xs text-slate-400">{{ post.liked ? '已赞' : '点赞' }}</span>
          </button>
          <button
            class="engagement-button"
            :class="post.favorited ? 'engagement-fav' : ''"
            @click="toggleFavorite"
          >
            <i class="fas" :class="post.favorited ? 'fa-star' : 'fa-star fa-regular'"></i>
            <span>{{ post.favoriteCount }}</span>
            <span class="text-xs text-slate-400">{{ post.favorited ? '已收藏' : '收藏' }}</span>
          </button>
        </div>
      </section>

      <section class="bg-white rounded-lg shadow-md p-6">
        <CommentList target-type="post" :target-id="post.id" :can-manage="isSelf" />
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPost, getUserProfile, followUser, setFavorite, setLike } from '../api/community'
import { currentUser } from '../lib/auth'
import { renderMarkdown } from '../lib/markdown'
import CommentList from '../components/CommentList.vue'

const route = useRoute()
const router = useRouter()

const post = ref(null)
const loading = ref(true)
const isFollowing = ref(false)

const statusMessage = ref('')
const statusType = ref('success')
let statusTimer = null

const renderedContent = computed(() => renderMarkdown(post.value?.content || ''))
const isSelf = computed(() => post.value && currentUser.value?.id === post.value.author.id)

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

async function toggleLike() {
  try {
    const next = !post.value.liked
    const result = await setLike('post', post.value.id, next)
    post.value.liked = result.liked
    post.value.likeCount = result.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

async function toggleFavorite() {
  try {
    const next = !post.value.favorited
    const result = await setFavorite('post', post.value.id, next)
    post.value.favorited = result.favorited
    post.value.favoriteCount = result.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

async function toggleFollow() {
  try {
    const next = !isFollowing.value
    const result = await followUser(post.value.author.id, next)
    isFollowing.value = result.following
    showStatus(next ? '已关注作者' : '已取消关注')
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

onMounted(async () => {
  try {
    const data = await getPost(route.params.id)
    post.value = data.item

    if (data.item && currentUser.value?.id !== data.item.author.id) {
      try {
        const profile = await getUserProfile(data.item.author.id)
        isFollowing.value = profile.isFollowing
      } catch {
        isFollowing.value = false
      }
    }
  } catch (error) {
    post.value = null
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
.post-detail-page {
  width: 100%;
  max-width: none;
}
.markdown-body {
  line-height: 1.7;
  color: #334155;
  font-size: 15px;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  color: #1e293b;
  font-weight: 700;
  margin: 18px 0 10px;
}
.markdown-body :deep(h1) {
  font-size: 22px;
}
.markdown-body :deep(h2) {
  font-size: 19px;
}
.markdown-body :deep(h3) {
  font-size: 16px;
}
.markdown-body :deep(p) {
  margin: 8px 0;
}
.markdown-body :deep(ul) {
  margin: 8px 0;
  padding-left: 24px;
  list-style: disc;
}
.markdown-body :deep(li) {
  margin: 4px 0;
}
.markdown-body :deep(code) {
  background: #f1f5f9;
  color: #be123c;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 13px;
  font-family: Consolas, Monaco, monospace;
}
.markdown-body :deep(pre) {
  background: #0f172a;
  color: #e2e8f0;
  padding: 14px 16px;
  border-radius: 12px;
  overflow-x: auto;
  margin: 12px 0;
}
.markdown-body :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
  font-size: 13px;
}
.markdown-body :deep(blockquote) {
  border-left: 4px solid #bfdbfe;
  background: #eff6ff;
  padding: 8px 14px;
  border-radius: 0 10px 10px 0;
  margin: 10px 0;
  color: #475569;
}
.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: underline;
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
