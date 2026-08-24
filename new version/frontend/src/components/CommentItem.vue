<template>
  <div>
    <!-- 评论卡片 -->
    <div class="border border-slate-200 rounded-xl p-4 bg-slate-50">
      <div class="flex justify-between items-center gap-3">
        <div class="flex items-center gap-2 text-sm text-slate-600">
          <i class="fas fa-circle-user text-blue-500"></i>
          <span class="font-semibold text-slate-700">{{ comment.author.username }}</span>
          <span class="text-xs text-slate-400">{{ formatDate(comment.createdAt) }}</span>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <button
            class="text-xs text-slate-400 hover:text-blue-600 transition-colors"
            @click="toggleReplyBox"
          >
            <i class="fas fa-reply mr-1"></i>回复
          </button>
          <button
            v-if="comment.isMine || canManage"
            class="text-xs text-slate-400 hover:text-red-600 transition-colors"
            @click="removeComment"
          >
            <i class="fas fa-trash mr-1"></i>删除
          </button>
        </div>
      </div>
      <p class="text-sm text-slate-700 mt-2 whitespace-pre-wrap break-words">{{ comment.content }}</p>

      <!-- 回复框 -->
      <div v-if="replyOpen" class="mt-3">
        <div class="flex gap-2">
          <input
            v-model="replyDraft"
            class="input flex-1"
            :placeholder="`回复 ${comment.author.username}...`"
            :disabled="replying"
            @keydown.enter.prevent="submitReply"
          />
          <button
            class="btn-primary shrink-0"
            :disabled="replying || !replyDraft.trim()"
            @click="submitReply"
          >
            <i class="fas fa-paper-plane mr-1"></i>{{ replying ? '发布中...' : '回复' }}
          </button>
          <button class="btn-secondary shrink-0" @click="replyOpen = false">
            <i class="fas fa-xmark"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- 子回复:递归渲染 -->
    <div
      v-if="comment.replies?.length"
      class="mt-3 ml-5 pl-4 border-l-2 border-slate-200 space-y-3"
    >
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        :target-type="targetType"
        :target-id="targetId"
        :can-manage="canManage"
        @deleted="emitDeleted"
        @error="emitError"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { createComment, deleteComment } from '../api/community'

// SFC 通过文件名隐式自引用,实现任意层级嵌套回复

const props = defineProps({
  comment: { type: Object, required: true },
  targetType: { type: String, required: true },
  targetId: { type: [String, Number], required: true },
  // 内容(项目/帖子)作者:可删除其内容下的任意评论
  canManage: { type: Boolean, default: false },
})

const emit = defineEmits(['deleted', 'error'])

const replyOpen = ref(false)
const replyDraft = ref('')
const replying = ref(false)

function formatDate(raw) {
  if (!raw) return ''
  return String(raw).slice(0, 16).replace('T', ' ')
}

function toggleReplyBox() {
  replyOpen.value = !replyOpen.value
  replyDraft.value = ''
}

async function submitReply() {
  const content = replyDraft.value.trim()
  if (!content) return

  replying.value = true
  try {
    await createComment(props.targetType, props.targetId, content, props.comment.id)
    replyDraft.value = ''
    replyOpen.value = false
    emitDeleted()
  } catch (error) {
    emitError(error)
  } finally {
    replying.value = false
  }
}

function emitDeleted() {
  emit('deleted')
}

function emitError(error) {
  emit('error', error.message || '操作失败')
}

async function removeComment() {
  const replyCount = props.comment.replies?.length || 0
  if (
    replyCount > 0 &&
    !window.confirm(`该评论下有 ${replyCount} 条回复，删除后回复将一并删除，确定删除吗？`)
  ) {
    return
  }
  try {
    await deleteComment(props.comment.id)
    emitDeleted()
  } catch (error) {
    emitError(error)
  }
}
</script>
