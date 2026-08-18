<template>
  <div class="home-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <section class="bg-white rounded-lg shadow-md p-6 mb-6">
      <div class="flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 mb-2">视频项目首页</h1>
          <p class="text-gray-600">集中查看所有视频分析项目。点击“创建项目”后在弹窗里填写描述并上传视频，创建完成后即可进入对应分析页。</p>
        </div>
        <button class="btn-primary" @click="openCreateModal">
          <i class="fas fa-plus mr-2"></i>创建项目
        </button>
      </div>
    </section>

    <section class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow-md p-5">
        <p class="text-sm text-gray-500">项目总数</p>
        <p class="text-3xl font-bold text-slate-800 mt-2">{{ projects.length }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-md p-5">
        <p class="text-sm text-gray-500">已填写描述</p>
        <p class="text-3xl font-bold text-slate-800 mt-2">{{ describedCount }}</p>
      </div>
      <div class="bg-white rounded-lg shadow-md p-5">
        <p class="text-sm text-gray-500">最近更新</p>
        <p class="text-lg font-bold text-slate-800 mt-2">{{ latestUpdated }}</p>
      </div>
    </section>

    <section class="bg-white rounded-lg shadow-md p-6">
      <div class="flex justify-between items-center mb-4 flex-wrap gap-3">
        <h2 class="text-xl font-semibold text-gray-800">全部视频项目</h2>
        <span class="text-sm text-gray-500">点击项目即可直接进入对应的视频分析页</span>
      </div>

      <div v-if="!projects.length" class="border border-dashed border-slate-300 rounded-lg p-10 text-center text-gray-500">
        <i class="fas fa-folder-open text-3xl mb-3 text-blue-500"></i>
        <p class="mb-4">当前还没有视频项目，先创建一个项目并上传手术视频吧。</p>
        <button class="btn-primary" @click="openCreateModal">
          <i class="fas fa-plus mr-2"></i>创建第一个项目
        </button>
      </div>

      <div v-else class="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-4">
        <article
          v-for="project in projects"
          :key="project.id"
          class="project-card border border-slate-200 rounded-xl p-5 bg-slate-50 hover:bg-white transition-colors cursor-pointer"
          @click="openAnalysis(project)"
        >
          <div class="flex justify-between items-start gap-4">
            <div>
              <h3 class="text-lg font-bold text-slate-800">{{ project.title }}</h3>
              <p class="text-sm text-slate-500 mt-1">{{ project.procedure || '未填写术式' }}</p>
            </div>
            <span
              class="text-xs rounded-full px-3 py-1"
              :class="statusClass(project.status)"
            >
              {{ project.status || '待分析' }}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-3 text-sm text-slate-600 mt-4">
            <div>
              <p class="text-slate-400">术者</p>
              <p class="font-medium">{{ project.surgeon || '未填写' }}</p>
            </div>
            <div>
              <p class="text-slate-400">上传日期</p>
              <p class="font-medium">{{ project.date || '未填写' }}</p>
            </div>
            <div>
              <p class="text-slate-400">视频文件</p>
              <p class="font-medium break-all">{{ project.fileName || '未上传' }}</p>
            </div>
            <div>
              <p class="text-slate-400">视频时长</p>
              <p class="font-medium">{{ project.duration || '待补充' }}</p>
            </div>
          </div>

          <p v-if="project.description" class="text-sm text-slate-600 mt-4 line-clamp-3">
            {{ project.description }}
          </p>

          <div class="flex gap-3 mt-5">
            <button class="btn-secondary" @click.stop="removeProjectItem(project)">
              <i class="fas fa-trash mr-2"></i>删除项目
            </button>
            <button class="btn-secondary" @click.stop="editProject(project)">
              <i class="fas fa-copy mr-2"></i>修改信息
            </button>
          </div>
        </article>
      </div>
    </section>

    <div v-if="showCreateModal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
      <div class="modal-panel bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <h2 class="text-2xl font-bold text-slate-800">{{ editingProjectId ? '修改视频项目' : '创建视频项目' }}</h2>
            <p class="text-sm text-slate-500 mt-1">{{ editingProjectId ? '修改项目描述和视频信息，保存后会更新原项目。' : '填写项目描述并上传视频，创建后会直接进入对应的分析页。' }}</p>
          </div>
          <button class="text-slate-400 hover:text-slate-700" @click="closeCreateModal">
            <i class="fas fa-xmark text-2xl"></i>
          </button>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
          <div class="space-y-4">
            <div>
              <label class="input-label">项目名称 <span class="required-mark">*</span></label>
              <input
                v-model="form.title"
                class="input"
                :class="formErrors.title ? 'input-error' : ''"
                placeholder="例如：LC-病例-001"
                @input="formErrors.title = ''"
              />
              <p v-if="formErrors.title" class="field-error">{{ formErrors.title }}</p>
            </div>
            <div>
              <label class="input-label">术式名称</label>
              <input v-model="form.procedure" class="input" placeholder="例如：腹腔镜胆囊切除术" />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="input-label">术者</label>
                <input v-model="form.surgeon" class="input" placeholder="输入术者姓名" />
              </div>
              <div>
                <label class="input-label">科室</label>
                <input v-model="form.department" class="input" placeholder="例如：肝胆外科" />
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="input-label">手术日期</label>
                <input v-model="form.date" type="date" class="input" />
              </div>
              <div>
                <label class="input-label">视频时长</label>
                <div class="input bg-slate-50 text-slate-700">
                  {{ form.duration || '上传后自动统计' }}
                </div>
              </div>
            </div>
            <div>
              <label class="input-label">项目描述</label>
              <textarea v-model="form.description" class="input min-h-[140px]" placeholder="填写病例背景、教学目标、分析关注点"></textarea>
            </div>
          </div>

          <div class="space-y-4">
            <div class="border border-dashed border-slate-300 rounded-xl p-6 bg-slate-50">
              <h3 class="text-lg font-semibold text-slate-800 mb-3">视频文件 <span class="required-mark">*</span></h3>
              <button class="btn-primary mb-4" @click="triggerUpload">
                <i class="fas fa-video mr-2"></i>选择手术视频
              </button>
              <input ref="fileInputRef" type="file" accept="video/*" class="hidden" @change="onFileSelected" />
              <p class="text-sm text-slate-500">当前项目的视频将在本次会话内直接用于分析页播放与标注。</p>
              <div v-if="form.fileName" class="mt-4 text-sm text-slate-700">
                <p><span class="text-slate-400">文件名：</span>{{ form.fileName }}</p>
                <p><span class="text-slate-400">视频时长：</span>{{ form.duration || '正在读取...' }}</p>
              </div>
            </div>

            <div class="border border-slate-200 rounded-xl overflow-hidden bg-black">
              <video v-if="form.videoUrl" :src="form.videoUrl" class="w-full h-[280px] object-cover" controls></video>
              <div v-else class="h-[280px] flex items-center justify-center text-slate-400 bg-slate-900">
                上传后可在这里预览视频
              </div>
            </div>

            <div class="flex gap-3 flex-wrap">
              <button class="btn-primary" @click="createProject">
                <i class="fas fa-save mr-2"></i>{{ editingProjectId ? '保存修改' : '创建并进入分析' }}
              </button>
              <button class="btn-secondary" @click="closeCreateModal">
                <i class="fas fa-arrow-left mr-2"></i>取消
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deleteProject, getProjects, saveProject, setActiveProject } from '../projectStore'
import { syncRunningProjectsPhaseAnalysis } from '../phaseAnalysisStore'
import { deleteProjectVideo, getProjectVideo, saveProjectVideo } from '../videoStore'

const router = useRouter()
const projects = ref([])
const showCreateModal = ref(false)
const fileInputRef = ref(null)
const form = ref(getEmptyForm())
const formErrors = ref({ title: '' })
const selectedVideoFile = ref(null)
const statusMessage = ref('')
const statusType = ref('success')
const editingProjectId = ref('')
let syncTimer = null
let durationReadPromise = null
let statusTimer = null

const describedCount = computed(() => projects.value.filter((item) => item.description).length)
const latestUpdated = computed(() => projects.value[0]?.updatedAtLabel || '暂无')

function getEmptyForm() {
  return {
    title: '',
    procedure: '',
    surgeon: '',
    department: '',
    date: '',
    duration: '',
    description: '',
    fileName: '',
    videoUrl: '',
    hasVideo: false,
    status: '草稿',
  }
}

function loadProjects() {
  projects.value = getProjects()
}

function statusClass(status) {
  if (status === '草稿') return 'bg-amber-100 text-amber-700'
  if (status === '正在上传') return 'bg-sky-100 text-sky-700'
  if (status === '待分析') return 'bg-slate-100 text-slate-700'
  if (status === '正在分析') return 'bg-blue-100 text-blue-700'
  if (status === '分析完成' || status === '完成') return 'bg-emerald-100 text-emerald-700'
  if (status === '分析失败') return 'bg-red-100 text-red-700'
  return 'bg-slate-100 text-slate-700'
}

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

function openCreateModal() {
  form.value = getEmptyForm()
  formErrors.value = { title: '' }
  selectedVideoFile.value = null
  editingProjectId.value = ''
  durationReadPromise = null
  showCreateModal.value = true
}

function closeCreateModal() {
  if (form.value.videoUrl && form.value.videoUrl.startsWith('blob:')) {
    URL.revokeObjectURL(form.value.videoUrl)
  }
  selectedVideoFile.value = null
  editingProjectId.value = ''
  durationReadPromise = null
  showCreateModal.value = false
}

function triggerUpload() {
  fileInputRef.value?.click()
}

async function onFileSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return
  selectedVideoFile.value = file
  formErrors.value.title = ''
  if (form.value.videoUrl && form.value.videoUrl.startsWith('blob:')) {
    URL.revokeObjectURL(form.value.videoUrl)
  }
  form.value.fileName = file.name
  form.value.videoUrl = URL.createObjectURL(file)
  form.value.hasVideo = true
  form.value.duration = ''

  try {
    durationReadPromise = readVideoDuration(form.value.videoUrl)
    form.value.duration = await durationReadPromise
  } catch {
    form.value.duration = '无法读取'
  } finally {
    durationReadPromise = null
  }
}

function readVideoDuration(videoUrl) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      resolve(formatDuration(video.duration))
      video.removeAttribute('src')
      video.load()
    }
    video.onerror = () => {
      reject(new Error('视频时长读取失败'))
      video.removeAttribute('src')
      video.load()
    }
    video.src = videoUrl
  })
}

function formatDuration(secondsValue) {
  if (!Number.isFinite(secondsValue) || secondsValue < 0) {
    return ''
  }

  const totalSeconds = Math.round(secondsValue)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

async function createProject() {
  if (!form.value.title.trim()) {
    formErrors.value.title = '请填写项目名称'
    showStatus('请先填写必填项：项目名称', 'error')
    return
  }
  if (durationReadPromise) {
    try {
      form.value.duration = await durationReadPromise
    } catch {
      form.value.duration = form.value.duration || '无法读取'
    }
  }

  const now = new Date()
  const isEditing = Boolean(editingProjectId.value)
  const projectId = editingProjectId.value || `project-${now.getTime()}`
  let project = {
    ...form.value,
    id: projectId,
    hasVideo: Boolean(selectedVideoFile.value) || Boolean(form.value.hasVideo),
    videoUrl: '',
    status: selectedVideoFile.value ? '正在上传' : form.value.status,
    updatedAt: now.toISOString(),
    updatedAtLabel: now.toLocaleString('zh-CN'),
  }

  saveProject(project)

  if (selectedVideoFile.value) {
    await saveProjectVideo(projectId, selectedVideoFile.value)
    project = {
      ...project,
      status: '待分析',
      updatedAt: new Date().toISOString(),
      updatedAtLabel: new Date().toLocaleString('zh-CN'),
    }
  }

  saveProject(project)
  setActiveProject(project)
  loadProjects()
  closeCreateModal()
  if (isEditing) {
    showStatus('项目信息已更新', 'success')
  } else {
    router.push('/analysis')
  }
}

function openAnalysis(project) {
  saveProject(project)
  setActiveProject(project)
  router.push('/analysis')
}

async function editProject(project) {
  if (form.value.videoUrl && form.value.videoUrl.startsWith('blob:')) {
    URL.revokeObjectURL(form.value.videoUrl)
  }
  form.value = {
    title: project.title || '',
    procedure: project.procedure || '',
    surgeon: project.surgeon || '',
    department: project.department || '',
    date: project.date || '',
    duration: project.duration || '',
    description: project.description || '',
    fileName: project.fileName || '',
    videoUrl: '',
    hasVideo: Boolean(project.hasVideo),
    status: project.status || '草稿',
    phaseAnalysis: project.phaseAnalysis || null,
    instrumentStats: project.instrumentStats || null,
    notes: project.notes || [],
  }
  editingProjectId.value = project.id
  formErrors.value = { title: '' }
  selectedVideoFile.value = null
  durationReadPromise = null
  showCreateModal.value = true

  if (project.hasVideo || project.fileName) {
    try {
      const file = await getProjectVideo(project.id)
      if (file && editingProjectId.value === project.id) {
        form.value.videoUrl = URL.createObjectURL(file)
      } else if (editingProjectId.value === project.id) {
        showStatus('未找到原视频文件，请重新上传', 'error')
      }
    } catch {
      if (editingProjectId.value === project.id) {
        showStatus('原视频加载失败，请重新上传', 'error')
      }
    }
  }
}

async function removeProjectItem(project) {
  await deleteProjectVideo(project.id)
  deleteProject(project.id)
  loadProjects()
}

onMounted(async () => {
  await syncRunningProjectsPhaseAnalysis()
  loadProjects()
  syncTimer = window.setInterval(async () => {
    await syncRunningProjectsPhaseAnalysis()
    loadProjects()
  }, 5000)
})

onBeforeUnmount(() => {
  if (syncTimer) {
    window.clearInterval(syncTimer)
  }
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
})
</script>

<style scoped>
.home-page {
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
