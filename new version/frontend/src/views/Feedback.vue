<template>
  <div class="feedback-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <div class="flex justify-between items-center mb-6 flex-wrap gap-3">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">
          <i class="fas fa-bullhorn mr-2 text-blue-600"></i>反馈建议
        </h1>
        <p class="text-sm text-slate-500 mt-1">你的每一条建议都会帮助 SurgReview 变得更好</p>
      </div>
      <router-link to="/community" class="btn-secondary">
        <i class="fas fa-arrow-left mr-2"></i>返回社区
      </router-link>
    </div>

    <!-- 提交反馈 -->
    <section class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">
        <i class="fas fa-pen-to-square mr-2 text-blue-600"></i>提出建议
      </h2>
      <div class="space-y-4">
        <div>
          <label class="input-label">反馈类型</label>
          <div class="flex gap-2 flex-wrap">
            <button
              v-for="type in feedbackTypes"
              :key="type"
              type="button"
              class="type-chip"
              :class="feedbackForm.type === type ? 'type-chip-active' : ''"
              @click="feedbackForm.type = type"
            >
              {{ type }}
            </button>
          </div>
        </div>
        <div>
          <label class="input-label">反馈内容 <span class="required-mark">*</span></label>
          <textarea
            v-model="feedbackForm.content"
            class="input min-h-[120px]"
            maxlength="2000"
            placeholder="说说你的建议、遇到的困难或希望增加的功能…"
          ></textarea>
          <p class="text-xs text-slate-400 mt-1.5 text-right">{{ feedbackForm.content.length }}/2000</p>
        </div>
        <div class="flex justify-end">
          <button class="btn-primary" :disabled="submitting" @click="handleSubmit">
            <i class="fas mr-2" :class="submitting ? 'fa-circle-notch fa-spin' : 'fa-paper-plane'"></i>
            {{ submitting ? '提交中...' : '提交反馈' }}
          </button>
        </div>
      </div>
    </section>

    <!-- 我的反馈 -->
    <section class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">
        <i class="fas fa-clock-rotate-left mr-2 text-blue-600"></i>我的反馈
        <span v-if="items.length" class="text-sm font-normal text-slate-400 ml-1">({{ items.length }})</span>
      </h2>

      <div v-if="loading" class="text-center text-gray-400 py-8">
        <i class="fas fa-circle-notch fa-spin text-2xl"></i>
      </div>

      <div v-else-if="!items.length" class="text-center py-10">
        <i class="fas fa-inbox text-3xl mb-3 text-slate-300"></i>
        <p class="text-slate-400">还没有提交过反馈，说出你的第一个建议吧</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="item in items"
          :key="item.id"
          class="border border-slate-200 rounded-xl p-4"
        >
          <div class="flex justify-between items-start gap-3">
            <div class="min-w-0">
              <div class="flex items-center gap-2 flex-wrap mb-1">
                <span class="type-badge" :class="typeBadgeClass(item.type)">{{ item.type }}</span>
                <span class="status-badge" :class="statusBadgeClass(item.status)">{{ item.status }}</span>
                <span class="text-xs text-slate-400">{{ item.createdAt }}</span>
              </div>
              <p class="text-sm text-slate-700 whitespace-pre-wrap">{{ item.content }}</p>
              <p v-if="item.reply" class="text-sm mt-2 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 text-emerald-800">
                <i class="fas fa-reply mr-1"></i>平台回复：{{ item.reply }}
              </p>
            </div>
            <button
              class="btn-danger shrink-0"
              @click="handleDelete(item)"
            >
              <i class="fas fa-trash-can mr-1"></i>删除
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { deleteFeedback, listMyFeedback, submitFeedback } from '../api/community'

const feedbackTypes = ['功能建议', '体验优化', '问题反馈', '其他']
const feedbackForm = ref({ type: '功能建议', content: '' })
const items = ref([])
const loading = ref(false)
const submitting = ref(false)

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

function typeBadgeClass(type) {
  if (type === '功能建议') return 'type-badge-blue'
  if (type === '体验优化') return 'type-badge-violet'
  if (type === '问题反馈') return 'type-badge-amber'
  return 'type-badge-slate'
}

function statusBadgeClass(status) {
  if (status === '已采纳') return 'status-done'
  if (status === '已处理') return 'status-done'
  return 'status-pending'
}

async function loadItems() {
  loading.value = true
  try {
    const data = await listMyFeedback()
    items.value = data.items || []
  } catch (error) {
    showStatus(error.message || '加载反馈记录失败', 'error')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const content = feedbackForm.value.content.trim()
  if (!content) {
    showStatus('请先填写反馈内容', 'error')
    return
  }
  submitting.value = true
  try {
    await submitFeedback({
      type: feedbackForm.value.type,
      content,
    })
    feedbackForm.value.content = ''
    showStatus('反馈已提交，感谢你的建议！')
    loadItems()
  } catch (error) {
    showStatus(error.message || '提交失败，请稍后重试', 'error')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(item) {
  if (!window.confirm('确定删除这条反馈吗？')) {
    return
  }
  try {
    await deleteFeedback(item.id)
    items.value = items.value.filter((it) => it.id !== item.id)
    showStatus('反馈已删除')
  } catch (error) {
    showStatus(error.message || '删除失败，请稍后重试', 'error')
  }
}

onMounted(() => {
  loadItems()
})
</script>

<style scoped>
.feedback-page {
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
}
.input-label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 6px;
}
.required-mark {
  color: #e11d48;
}
.type-chip {
  padding: 7px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.15s ease;
}
.type-chip:hover {
  color: #2563eb;
  background: #eff6ff;
  border-color: #bfdbfe;
}
.type-chip-active {
  color: #ffffff;
  background: #2563eb;
  border-color: #2563eb;
}
.type-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.type-badge-blue {
  color: #1d4ed8;
  background: #dbeafe;
}
.type-badge-violet {
  color: #6d28d9;
  background: #ede9fe;
}
.type-badge-amber {
  color: #b45309;
  background: #fef3c7;
}
.type-badge-slate {
  color: #475569;
  background: #e2e8f0;
}
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}
.status-pending {
  color: #b45309;
  background: #fef3c7;
}
.status-done {
  color: #047857;
  background: #d1fae5;
}
.btn-primary {
  display: inline-flex;
  align-items: center;
  padding: 10px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
  background: #2563eb;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease;
}
.btn-primary:hover {
  background: #1d4ed8;
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-secondary {
  display: inline-flex;
  align-items: center;
  padding: 9px 16px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  background: #ffffff;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-secondary:hover {
  background: #f8fafc;
  border-color: #94a3b8;
}
.btn-danger {
  padding: 7px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-danger:hover {
  background: #fee2e2;
  border-color: #fca5a5;
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
