<template>
  <div class="comment-list">
    <h3 class="text-lg font-semibold text-slate-800 mb-4">
      <i class="fas fa-comment-dots mr-2 text-blue-600"></i>评论（{{ totalCount }}）
    </h3>

    <div v-if="loading" class="py-6 text-center text-gray-400">
      <i class="fas fa-circle-notch fa-spin text-xl"></i>
    </div>

    <div v-else-if="!comments.length" class="border border-dashed border-slate-300 rounded-lg p-8 text-center text-gray-500">
      <i class="fas fa-comment-slash text-2xl mb-2 text-blue-400"></i>
      <p>还没有评论，来说两句吧。</p>
    </div>

    <div v-else class="space-y-4">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        :target-type="targetType"
        :target-id="targetId"
        :can-manage="canManage"
        @deleted="loadComments"
        @error="showStatus($event, 'error')"
      />
    </div>

    <div class="mt-6">
      <textarea
        v-model="draft"
        class="input min-h-[90px]"
        placeholder="写下你的评论..."
        :disabled="submitting"
        @keydown.ctrl.enter="submitComment"
      ></textarea>
      <div class="flex items-center justify-between mt-3">
        <span class="text-xs text-slate-400">Ctrl + Enter 快捷发布</span>
        <button
          class="btn-primary"
          :disabled="submitting || !draft.trim()"
          @click="submitComment"
        >
          <i class="fas fa-paper-plane mr-2"></i>{{ submitting ? '发布中...' : '发布评论' }}
        </button>
      </div>
    </div>

    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { createComment, listComments } from '../api/community'
import CommentItem from './CommentItem.vue'

const props = defineProps({
  targetType: { type: String, required: true }, // 'project' | 'post'
  targetId: { type: [String, Number], required: true },
  // 内容(项目/帖子)作者:可删除其内容下的任意评论
  canManage: { type: Boolean, default: false },
})

const comments = ref([])
const draft = ref('')
const loading = ref(false)
const submitting = ref(false)

// 递归统计:每条评论自身 + 所有层级的回复
function countTree(comment) {
  return 1 + (comment.replies || []).reduce((sum, reply) => sum + countTree(reply), 0)
}

const totalCount = computed(() =>
  comments.value.reduce((sum, comment) => sum + countTree(comment), 0)
)

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

async function loadComments() {
  loading.value = true
  try {
    const data = await listComments(props.targetType, props.targetId)
    comments.value = data.items || []
  } catch (error) {
    comments.value = []
    showStatus(error.message || '加载评论失败', 'error')
  } finally {
    loading.value = false
  }
}

async function submitComment() {
  const content = draft.value.trim()
  if (!content) return

  submitting.value = true
  try {
    await createComment(props.targetType, props.targetId, content)
    draft.value = ''
    await loadComments()
  } catch (error) {
    showStatus(error.message || '评论发布失败', 'error')
  } finally {
    submitting.value = false
  }
}

watch(
  () => props.targetId,
  () => {
    if (props.targetId) {
      loadComments()
    }
  }
)

onMounted(() => {
  if (props.targetId) {
    loadComments()
  }
})

onBeforeUnmount(() => {
  if (statusTimer) {
    window.clearTimeout(statusTimer)
  }
})
</script>

<style scoped>
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
