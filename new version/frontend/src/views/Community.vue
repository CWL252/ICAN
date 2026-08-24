<template>
  <div class="community-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <section class="bg-white rounded-lg shadow-md p-6 mb-6">
      <div class="flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 mb-2">开源社区</h1>
          <p class="text-gray-600">欢迎来到开源社区。您可以浏览大家分享的手术分析项目，参与技术讨论，也期待您分享自己的成果，与同行们共同交流、一起进步。</p>
        </div>
        <button class="btn-primary" @click="openCreatePost">
          <i class="fas fa-feather mr-2"></i>发帖讨论
        </button>
      </div>
    </section>

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
      <div class="ml-auto flex gap-2">
        <router-link to="/community/mine" class="tab-button tab-button-mine">
          <i class="fas fa-user-shield mr-2"></i>我的社区
        </router-link>
        <router-link to="/community/feedback" class="tab-button tab-button-mine">
          <i class="fas fa-bullhorn mr-2"></i>反馈建议
        </router-link>
      </div>
    </div>

    <!-- Tab 1: 开源广场 -->
    <section v-if="activeTab === 'projects'" class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-4 flex-wrap gap-3">
        <h2 class="text-xl font-semibold text-gray-800">开源广场</h2>
        <div class="flex items-center gap-3 flex-wrap">
          <input
            v-model="searchQuery"
            class="input !w-56"
            placeholder="搜索标题 / 术式 / 作者..."
            @input="onSearchInput"
          />
          <select v-model="projectSort" class="input !w-32" @change="loadProjects">
            <option value="newest">最新发布</option>
            <option value="popular">最受欢迎</option>
          </select>
        </div>
      </div>

      <!-- 分类筛选条:大类 + 小类联动 -->
      <div class="flex items-center gap-2 mb-5 flex-wrap">
        <label class="flex items-center gap-2 text-sm font-semibold text-slate-600 shrink-0">
          <i class="fas fa-layer-group text-blue-600"></i>分类
        </label>
        <select
          v-model="categoryFilter"
          class="input category-select"
          @change="onCategoryChange"
        >
          <option value="">全部</option>
          <option v-for="group in categoryGroups" :key="group.name" :value="group.name">
            {{ group.name }}
          </option>
        </select>
        <select
          v-if="categoryFilter"
          v-model="subcategoryFilter"
          class="input category-select"
          @change="loadProjects()"
        >
          <option value="">全部</option>
          <option v-for="sub in currentGroupItems" :key="sub" :value="sub">
            {{ sub }}
          </option>
        </select>
      </div>

      <div v-if="loading" class="py-10 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-2xl"></i>
      </div>

      <div v-else-if="!projects.length" class="border border-dashed border-slate-300 rounded-lg p-10 text-center text-gray-500">
        <i class="fas fa-box-open text-3xl mb-3 text-blue-500"></i>
        <p class="mb-4">广场上还没有项目，去首页把自己的分析项目分享出来吧。</p>
        <router-link to="/home" class="btn-primary">
          <i class="fas fa-house mr-2"></i>去首页分享项目
        </router-link>
      </div>

      <div v-else class="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-4">
        <article
          v-for="project in projects"
          :key="project.id"
          class="project-card border border-slate-200 rounded-xl p-5 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
          @click="openProject(project)"
        >
          <div class="flex justify-between items-start gap-4">
            <div class="min-w-0">
              <h3 class="text-lg font-bold text-slate-800 truncate">{{ project.title }}</h3>
              <p class="text-sm text-slate-500 mt-1 truncate">
                <i v-if="project.hasVideo" class="fas fa-video text-blue-500 mr-1" title="含共享视频"></i>
                <span v-if="project.subcategory || project.category" class="category-badge">
                  {{ project.subcategory || project.category }}
                </span>
                {{ project.procedure || '未填写术式' }}
              </p>
            </div>
            <span class="text-xs rounded-full px-3 py-1 bg-emerald-100 text-emerald-700 shrink-0">
              {{ project.status || '分析完成' }}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-3 text-sm text-slate-600 mt-4">
            <div>
              <p class="text-slate-400">作者</p>
              <p class="font-medium truncate">{{ project.author.username }}</p>
            </div>
            <div>
              <p class="text-slate-400">术者</p>
              <p class="font-medium truncate">{{ project.surgeon || '未填写' }}</p>
            </div>
            <div>
              <p class="text-slate-400">上传日期</p>
              <p class="font-medium">{{ project.date || '未填写' }}</p>
            </div>
            <div>
              <p class="text-slate-400">视频时长</p>
              <p class="font-medium">{{ project.duration || '待补充' }}</p>
            </div>
          </div>

          <p v-if="project.description" class="text-sm text-slate-600 mt-4 line-clamp-3">
            {{ project.description }}
          </p>

          <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-200">
            <div class="flex items-center gap-1 text-sm text-slate-500">
              <button
                class="engagement-button"
                :class="project.liked ? 'engagement-on' : ''"
                title="点赞"
                @click.stop="toggleProjectLike(project)"
              >
                <i class="fas" :class="project.liked ? 'fa-heart' : 'fa-heart fa-regular'"></i>
                <span>{{ project.likeCount }}</span>
              </button>
              <button
                class="engagement-button"
                :class="project.favorited ? 'engagement-favorite-on' : ''"
                title="收藏"
                @click.stop="toggleProjectFavorite(project)"
              >
                <i class="fas" :class="project.favorited ? 'fa-star' : 'fa-star fa-regular'"></i>
                <span>{{ project.favoriteCount }}</span>
              </button>
              <span class="engagement-button" title="评论数">
                <i class="fas fa-comment-dots"></i>
                <span>{{ project.commentCount }}</span>
              </span>
            </div>
            <span class="text-xs text-slate-400">{{ formatDate(project.createdAt) }}</span>
          </div>
        </article>
      </div>
    </section>

    <!-- Tab 2: 讨论区 -->
    <section v-else-if="activeTab === 'posts'" class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-4 flex-wrap gap-3">
        <h2 class="text-xl font-semibold text-gray-800">讨论区</h2>
        <input
          v-model="postSearchQuery"
          class="input !w-56"
          placeholder="搜索帖子 / 作者..."
          @input="onPostSearchInput"
        />
      </div>

      <div v-if="loading" class="py-10 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-2xl"></i>
      </div>

      <div v-else-if="!posts.length" class="border border-dashed border-slate-300 rounded-lg p-10 text-center text-gray-500">
        <i class="fas fa-comments text-3xl mb-3 text-blue-500"></i>
        <p class="mb-4">还没有人发帖，来抢个沙发聊聊手术分析心得吧。</p>
        <button class="btn-primary" @click="openCreatePost">
          <i class="fas fa-feather mr-2"></i>发布第一个帖子
        </button>
      </div>

      <div v-else class="space-y-4">
        <article
          v-for="post in posts"
          :key="post.id"
          class="post-card border border-slate-200 rounded-xl p-5 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
          @click="openPost(post)"
        >
          <h3 class="text-lg font-bold text-slate-800">{{ post.title }}</h3>
          <div class="flex items-center gap-3 text-xs text-slate-400 mt-2">
            <span class="flex items-center gap-1">
              <i class="fas fa-circle-user text-blue-500"></i>
              {{ post.author.username }}
            </span>
            <span>{{ formatDate(post.createdAt) }}</span>
          </div>
          <p v-if="post.excerpt" class="text-sm text-slate-600 mt-3 line-clamp-2">
            {{ post.excerpt }}
          </p>
          <div class="flex items-center gap-1 text-sm text-slate-500 mt-3">
            <button
              class="engagement-button"
              :class="post.liked ? 'engagement-on' : ''"
              title="点赞"
              @click.stop="togglePostLike(post)"
            >
              <i class="fas" :class="post.liked ? 'fa-heart' : 'fa-heart fa-regular'"></i>
              <span>{{ post.likeCount }}</span>
            </button>
            <button
              class="engagement-button"
              :class="post.favorited ? 'engagement-favorite-on' : ''"
              title="收藏"
              @click.stop="togglePostFavorite(post)"
            >
              <i class="fas" :class="post.favorited ? 'fa-star' : 'fa-star fa-regular'"></i>
              <span>{{ post.favoriteCount }}</span>
            </button>
            <span class="engagement-button" title="评论数">
              <i class="fas fa-comment-dots"></i>
              <span>{{ post.commentCount }}</span>
            </span>
          </div>
        </article>
      </div>
    </section>

    <!-- Tab 3: 关注动态 -->
    <section v-else class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-xl font-semibold text-gray-800 mb-4">关注动态</h2>
      <p class="text-sm text-slate-400 mb-4">这里展示的是你关注的博主，点击博主查看他分享的全部项目。</p>

      <div v-if="loading" class="py-10 text-center text-gray-400">
        <i class="fas fa-circle-notch fa-spin text-2xl"></i>
      </div>

      <div v-else-if="!bloggers.length" class="border border-dashed border-slate-300 rounded-lg p-10 text-center text-gray-500">
        <i class="fas fa-users-viewfinder text-3xl mb-3 text-blue-500"></i>
        <p class="mb-4">你还没有关注任何人。去项目或帖子里关注感兴趣的博主，他们会出现在这里。</p>
        <button class="btn-primary" @click="switchTab('projects')">
          <i class="fas fa-box-open mr-2"></i>去广场逛逛
        </button>
      </div>

      <div v-else class="space-y-4">
        <article
          v-for="blogger in bloggers"
          :key="blogger.id"
          class="post-card border border-slate-200 rounded-xl p-5 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
          @click="openBlogger(blogger)"
        >
          <div class="flex items-center gap-4 flex-wrap">
            <div
              class="w-14 h-14 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xl font-bold shrink-0"
            >
              {{ (blogger.username || '?').charAt(0).toUpperCase() }}
            </div>
            <div class="min-w-0 flex-1">
              <h3 class="text-lg font-bold text-slate-800 truncate">
                {{ blogger.username }}
                <i class="fas fa-circle-check text-blue-500 text-sm ml-1" title="已关注"></i>
              </h3>
              <p class="text-xs text-slate-400 mt-1">
                分享项目 {{ blogger.projectCount }} · 帖子 {{ blogger.postCount }} · 粉丝 {{ blogger.followerCount }}
              </p>
            </div>
            <span class="text-sm text-slate-400 shrink-0">
              <i class="fas fa-arrow-right mr-1"></i>查看主页
            </span>
          </div>
          <div v-if="blogger.latestProject || blogger.latestPost" class="mt-3 pt-3 border-t border-slate-200">
            <p class="text-xs text-slate-400">
              <i class="fas mr-1" :class="blogger.latestProject ? 'fa-box-open text-blue-500' : 'fa-comments text-purple-500'"></i>
              最新{{ blogger.latestProject ? '分享' : '帖子' }}：{{ blogger.latestProject || blogger.latestPost }}
            </p>
          </div>
        </article>
      </div>
    </section>

    <!-- 发帖模态框 -->
    <div v-if="showCreatePost" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="modal-panel bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <h2 class="text-2xl font-bold text-slate-800">发布帖子</h2>
            <p class="text-sm text-slate-500 mt-1">内容支持 Markdown 语法（标题、列表、加粗、代码等）。</p>
          </div>
          <button class="text-slate-400 hover:text-slate-700" @click="closeCreatePost">
            <i class="fas fa-xmark text-2xl"></i>
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div>
            <label class="input-label">帖子标题 <span class="required-mark">*</span></label>
            <input
              v-model="postForm.title"
              class="input"
              :class="postErrors.title ? 'input-error' : ''"
              placeholder="一句话说清你的问题或分享的主题"
              @input="postErrors.title = ''"
            />
            <p v-if="postErrors.title" class="field-error">{{ postErrors.title }}</p>
          </div>
          <div>
            <label class="input-label">帖子内容 <span class="required-mark">*</span></label>
            <textarea
              v-model="postForm.content"
              class="input min-h-[200px]"
              :class="postErrors.content ? 'input-error' : ''"
              placeholder="支持 Markdown：&#10;- 列表项&#10;**加粗**&#10;```代码块```"
              @input="postErrors.content = ''"
            ></textarea>
            <p v-if="postErrors.content" class="field-error">{{ postErrors.content }}</p>
          </div>
          <div class="flex gap-3">
            <button class="btn-primary" :disabled="submitting" @click="submitPost">
              <i class="fas fa-paper-plane mr-2"></i>{{ submitting ? '发布中...' : '发布' }}
            </button>
            <button class="btn-secondary" @click="closeCreatePost">
              <i class="fas fa-arrow-left mr-2"></i>取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser } from '../lib/auth'
import {
  createPost,
  listCategories,
  listMyFollowing,
  listPosts,
  listProjects,
  setFavorite,
  setLike,
} from '../api/community'

const router = useRouter()

const tabs = [
  { key: 'projects', label: '开源广场', icon: 'fa-box-open' },
  { key: 'posts', label: '讨论区', icon: 'fa-comments' },
  { key: 'feed', label: '关注动态', icon: 'fa-users-viewfinder' },
]

const activeTab = ref('projects')
const loading = ref(false)
const submitting = ref(false)

const projects = ref([])
const projectSort = ref('newest')
const searchQuery = ref('')
const categoryGroups = ref([])
const categoryFilter = ref('')
const subcategoryFilter = ref('')
const currentGroupItems = computed(() => {
  const group = categoryGroups.value.find((g) => g.name === categoryFilter.value)
  return group ? group.items : []
})

function onCategoryChange() {
  subcategoryFilter.value = ''
  loadProjects()
}
let searchTimer = null

const posts = ref([])
const postSearchQuery = ref('')
let postSearchTimer = null

const bloggers = ref([])

const showCreatePost = ref(false)
const postForm = ref({ title: '', content: '' })
const postErrors = ref({ title: '', content: '' })

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
  if (key === 'projects') {
    await loadProjects()
  } else if (key === 'posts') {
    await loadPosts()
  } else {
    await loadFollowing()
  }
}

async function loadProjects() {
  loading.value = true
  try {
    const data = await listProjects({
      q: searchQuery.value,
      sort: projectSort.value,
      category: categoryFilter.value,
      subcategory: subcategoryFilter.value,
    })
    projects.value = data.items || []
  } catch (error) {
    showStatus(error.message || '加载项目列表失败', 'error')
  } finally {
    loading.value = false
  }
}

async function loadPosts() {
  loading.value = true
  try {
    const data = await listPosts({ q: postSearchQuery.value })
    posts.value = data.items || []
  } catch (error) {
    showStatus(error.message || '加载帖子列表失败', 'error')
  } finally {
    loading.value = false
  }
}

async function loadFollowing() {
  loading.value = true
  try {
    const data = await listMyFollowing()
    bloggers.value = data.items || []
  } catch (error) {
    showStatus(error.message || '加载关注动态失败', 'error')
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  if (searchTimer) {
    window.clearTimeout(searchTimer)
  }
  searchTimer = window.setTimeout(loadProjects, 300)
}

function onPostSearchInput() {
  if (postSearchTimer) {
    window.clearTimeout(postSearchTimer)
  }
  postSearchTimer = window.setTimeout(loadPosts, 300)
}

async function toggleProjectLike(project) {
  try {
    const next = !project.liked
    const result = await setLike('project', project.id, next)
    project.liked = result.liked
    project.likeCount = result.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

async function toggleProjectFavorite(project) {
  try {
    const next = !project.favorited
    const result = await setFavorite('project', project.id, next)
    project.favorited = result.favorited
    project.favoriteCount = result.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

async function togglePostLike(post) {
  try {
    const next = !post.liked
    const result = await setLike('post', post.id, next)
    post.liked = result.liked
    post.likeCount = result.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

async function togglePostFavorite(post) {
  try {
    const next = !post.favorited
    const result = await setFavorite('post', post.id, next)
    post.favorited = result.favorited
    post.favoriteCount = result.count
  } catch (error) {
    showStatus(error.message || '操作失败', 'error')
  }
}

function openProject(project) {
  router.push(`/community/projects/${project.id}`)
}

function openPost(post) {
  router.push(`/community/posts/${post.id}`)
}

function openBlogger(blogger) {
  // 关注动态关注的是博主本人，点卡片进入博主主页
  router.push(`/community/users/${blogger.id}`)
}

function openCreatePost() {
  postForm.value = { title: '', content: '' }
  postErrors.value = { title: '', content: '' }
  showCreatePost.value = true
}

function closeCreatePost() {
  showCreatePost.value = false
}

async function submitPost() {
  if (!postForm.value.title.trim()) {
    postErrors.value.title = '请填写帖子标题'
    return
  }
  if (!postForm.value.content.trim()) {
    postErrors.value.content = '请填写帖子内容'
    return
  }

  submitting.value = true
  try {
    const data = await createPost({
      title: postForm.value.title.trim(),
      content: postForm.value.content.trim(),
    })
    closeCreatePost()
    showStatus('帖子发布成功')
    await switchTab('posts')
    // 置顶新发布的帖子
    posts.value = [
      data.item,
      ...posts.value.filter((item) => item.id !== data.item.id),
    ]
  } catch (error) {
    showStatus(error.message || '发布失败', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  loadProjects()
  try {
    categoryGroups.value = (await listCategories()).groups || []
  } catch {
    // 分类接口失败不阻塞页面，保留空筛选条
  }
})

onBeforeUnmount(() => {
  if (searchTimer) {
    window.clearTimeout(searchTimer)
  }
  if (postSearchTimer) {
    window.clearTimeout(postSearchTimer)
  }
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
})
</script>

<style scoped>
.community-page {
  width: 100%;
  max-width: none;
}
.required-mark {
  color: #dc2626;
  font-weight: 800;
}
.field-error {
  margin-top: 6px;
  color: #dc2626;
  font-size: 12px;
  font-weight: 700;
}
.input-error {
  border-color: #dc2626;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.12);
}
.tab-button {
  display: inline-flex;
  align-items: center;
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.15s ease;
}
.tab-button:hover {
  color: #2563eb;
  border-color: #bfdbfe;
}
.tab-button-active {
  color: #ffffff;
  background: #2563eb;
  border-color: #2563eb;
}
.tab-button-mine {
  color: #2563eb;
  border-color: #bfdbfe;
  background: #eff6ff;
}
.tab-button-mine:hover {
  background: #dbeafe;
}
.engagement-button {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}
.engagement-button:hover {
  background: #f1f5f9;
  color: #334155;
}
.engagement-on {
  color: #e11d48;
}
.engagement-favorite-on {
  color: #d97706;
}
/* 点赞/收藏图标状态色：未点击灰色，已赞红色，已收藏橙色 */
.engagement-button i {
  color: #94a3b8;
}
.engagement-button.engagement-on i {
  color: #e11d48;
}
.engagement-button.engagement-favorite-on i {
  color: #d97706;
}
.category-select {
  width: auto;
  min-width: 140px;
  max-width: 240px;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  background-color: #ffffff;
  cursor: pointer;
}
.category-badge {
  display: inline-block;
  margin-right: 6px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #1d4ed8;
  background: #dbeafe;
  vertical-align: middle;
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
