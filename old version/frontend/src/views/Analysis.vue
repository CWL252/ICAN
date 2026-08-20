<template>
  <div class="analysis-page px-4 sm:px-6 lg:px-8 py-6">
    <transition name="toast-slide">
      <div v-if="statusMessage" :class="['top-toast', statusType === 'error' ? 'error' : 'success']">
        <i class="fas" :class="statusType === 'error' ? 'fa-circle-exclamation' : 'fa-circle-check'"></i>
        <span>{{ statusMessage }}</span>
      </div>
    </transition>

    <div class="flex justify-between items-center mb-6 flex-wrap gap-3">
      <h1 class="text-2xl font-bold text-gray-800 flex items-center">
        <i class="fas fa-chart-line mr-2 text-blue-500"></i>手术视频分析
      </h1>
      <div class="flex flex-wrap gap-2">
        <button v-if="shouldShowUploadButton" class="btn-primary" @click="triggerVideoUpload">
          <i class="fas fa-upload mr-2"></i>上传视频
        </button>
        <input ref="videoFileInput" class="hidden" type="file" accept="video/*" @change="onVideoSelected" />
        <button class="btn-secondary" @click="exportAnnotations">
          <i class="fas fa-share-alt mr-2"></i>导出标注
        </button>
        <button class="btn-secondary" :class="isTracking ? 'btn-active' : ''" @click="toggleTracking">
          <i class="fas fa-broadcast-tower mr-2"></i>实时追踪: {{ isTracking ? '开' : '关' }}
        </button>
        <button class="btn-secondary" @click="exportSummary">
          <i class="fas fa-download mr-2"></i>导出报告
        </button>
      </div>
    </div>

    <div class="analysis-workspace-card bg-white rounded-lg shadow-md p-6">
      <div class="analysis-main-grid">
        <div class="analysis-video-column space-y-4">
          <div class="video-container" ref="videoContainer">
            <video
              ref="videoEl"
              :src="uploadedVideoUrl"
              class="w-full h-full object-contain"
              controls
              playsinline
              preload="metadata"
              @loadedmetadata="onLoadedMetadata"
              @canplay="setCanvasSize"
              @timeupdate="onTimeUpdate"
              @click.stop.prevent="toggleVideoPlayback"
              v-show="uploadedVideoUrl"
            ></video>
            <img :src="analysisImageSrc" alt="手术视频" class="w-full h-full object-contain" v-show="!uploadedVideoUrl" />
            <canvas ref="maskCanvas" class="mask-canvas"></canvas>
            <div class="points-layer">
              <span
                v-for="(point, idx) in pointsForDisplay"
                :key="idx"
                class="point-dot"
                :class="point.kind === 'positive' ? 'point-positive' : 'point-negative'"
                :style="`left: ${point.x}px; top: ${point.y}px`"
              ></span>
            </div>
          </div>

          <div class="seg-toolbar-external">
            <button class="seg-btn" :class="isAddPositive ? 'seg-btn-active' : ''" @click="setPointMode(true)">
              <i class="fas fa-plus-circle text-green-600 mr-1"></i>正样本
            </button>
            <button class="seg-btn" :class="!isAddPositive ? 'seg-btn-active neg' : ''" @click="setPointMode(false)">
              <i class="fas fa-minus-circle text-red-500 mr-1"></i>负样本
            </button>
            <button class="seg-btn" @click="clearPoints">
              <i class="fas fa-undo mr-1"></i>清点
            </button>
            <button class="seg-btn primary" :disabled="isProcessing" @click="runSegmentation">
              <i class="fas" :class="isProcessing ? 'fa-spinner fa-spin' : 'fa-magic'"></i>
              <span class="ml-2">视频分析</span>
            </button>
          </div>

          <div class="flex flex-wrap items-center gap-3">
            <div class="text-sm text-slate-700 font-semibold flex items-center gap-2">
              <i class="fas fa-clock text-blue-500"></i>
              <span>{{ formatTimeLabel(currentTime) }} / {{ formatTimeLabel(duration) }}</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="text-sm text-slate-600">掩码透明度</label>
              <input type="range" min="0.2" max="0.8" step="0.05" v-model.number="maskOpacity" @input="onOpacityChange" />
            </div>
            <div class="badge" :class="currentMask ? '' : 'ghost'">{{ currentMask ? '已生成分割' : '等待生成' }}</div>
          </div>

          <div class="timeline-shell">
            <div class="timeline-bar">
              <div class="h-full bg-blue-600 progress" :style="{ width: progressPercent }"></div>
              <span
                v-for="note in notesSorted"
                :key="note.id"
                class="note-marker"
                :style="{ left: markerLeft(note.time) }"
                :title="formatTimeLabel(note.time) + ' ' + note.text"
              ></span>
            </div>
            <div class="flex justify-between mt-2 text-sm text-gray-600">
              <span>00:00</span>
              <span>{{ formatTimeLabel(duration || 165) }}</span>
            </div>
          </div>

          <div class="note-panel">
            <h3 class="font-semibold text-lg mb-3 flex items-center">
              <i class="fas fa-stopwatch mr-2 text-blue-500"></i>文字注释
            </h3>
            <div class="note-form">
              <button
                class="annotation-timer"
                :class="isTimingAnnotation ? 'recording' : ''"
                :title="isTimingAnnotation ? '结束计时' : '开始计时'"
                @click="toggleAnnotationTimer"
              >
                <i class="fas" :class="isTimingAnnotation ? 'fa-stop' : 'fa-clock'"></i>
                <span>{{ annotationIntervalLabel }}</span>
              </button>
              <input v-model="noteTimeInput" class="input note-time" placeholder="mm:ss - mm:ss" style="width: 130px;" />
              <input v-model="noteTextInput" class="input note-text" placeholder="输入文字注释内容" />
              <button class="btn-secondary compact" @click="addNote">添加注释</button>
              <button class="btn-secondary compact" @click="clearAnnotationTimer">
                清除计时
              </button>
              <button v-if="activeLoopNoteId" class="btn-secondary compact" @click="exitNoteLoop">
                退出循环
              </button>
            </div>
            <div class="note-list" :class="{ 'is-empty': !notesSorted.length }">
              <div v-show="!notesSorted.length" class="note-empty">暂无文字注释</div>
              <div v-show="notesSorted.length">
                <div
                  v-for="note in notesSorted"
                  :key="note.id"
                  class="note-row"
                  :class="activeLoopNoteId === note.id ? 'active-loop' : ''"
                  @click="playNoteLoop(note)"
                >
                  <div>
                    <p class="note-time-label"><i class="fas fa-clock"></i> {{ formatNoteRange(note) }}</p>
                    <p class="note-text">{{ note.text }}</p>
                  </div>
                  <div class="note-actions">
                    <span v-if="activeLoopNoteId === note.id" class="loop-chip">循环播放中</span>
                    <button class="note-delete" @click.stop="removeNote(note.id)"><i class="fas fa-trash"></i></button>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>

          <div class="analysis-side-panel">
          <div class="middle-video-aligned-panel">
          <div class="side-card bg-gray-50 p-4 rounded-lg shadow-sm">
            <h3 class="font-semibold text-lg mb-3 flex items-center">
              <i class="fas fa-circle-info mr-2 text-blue-500"></i>基本信息
            </h3>
            <div class="space-y-3">
              <div class="bg-white p-4 rounded-md shadow-sm space-y-3">
                <div class="flex justify-between items-center text-sm">
                  <span class="text-gray-500">项目名称</span>
                  <span class="font-semibold text-slate-800">{{ currentProject?.title || '未命名项目' }}</span>
                </div>
                <div class="flex justify-between items-center text-sm">
                  <span class="text-gray-500">术式名称</span>
                  <span class="font-semibold text-slate-800">{{ currentProject?.procedure || '未填写' }}</span>
                </div>
                <div class="flex justify-between items-center text-sm">
                  <span class="text-gray-500">术者</span>
                  <span class="font-semibold text-slate-800">{{ currentProject?.surgeon || '未填写' }}</span>
                </div>
                <div class="flex justify-between items-center text-sm">
                  <span class="text-gray-500">日期</span>
                  <span class="font-semibold text-slate-800">{{ currentProject?.date || '未填写' }}</span>
                </div>
                <div class="flex justify-between items-center text-sm">
                  <span class="text-gray-500">视频总时长</span>
                  <span class="font-semibold text-slate-800">{{ formatTimeLabel(duration || 165) }}</span>
                </div>
                <div class="flex justify-between items-center text-sm">
                  <span class="text-gray-500">状态</span>
                  <span
                    class="text-xs rounded-full px-3 py-1"
                    :class="statusClass(currentProject?.status)"
                  >
                    {{ currentProject?.status || '待分析' }}
                  </span>
                </div>
                <div class="flex justify-between items-center text-sm">
                  <span class="text-gray-500">视频文件</span>
                  <span class="font-semibold text-slate-800 break-all text-right max-w-[65%]">{{ currentProject?.fileName || '未上传' }}</span>
                </div>
              </div>
            </div>

          </div>

          <div class="side-card overview-side-card bg-gray-50 p-4 rounded-lg">
            <h3 class="font-semibold text-lg mb-3 flex items-center">
              <i class="fas fa-chart-pie mr-2 text-blue-500"></i>分析概览
            </h3>
            <div class="overview-grid">
              <div class="overview-card">
                <div class="overview-icon"><i class="fas fa-clock"></i></div>
                <div class="overview-card-body">
                  <p class="text-sm text-gray-500">手术时长</p>
                  <p class="font-bold">{{ formatTimeLabel(duration || 165) }}</p>
                </div>
              </div>
              <div class="overview-card">
                <div class="overview-icon"><i class="fas fa-list-ol"></i></div>
                <div class="overview-card-body">
                  <p class="text-sm text-gray-500">关键步骤</p>
                  <p class="font-bold">{{ generatedSteps.length }}</p>
                </div>
              </div>
              <div class="overview-card">
                <div class="overview-icon"><i class="fas fa-note-sticky"></i></div>
                <div class="overview-card-body">
                  <p class="text-sm text-gray-500">文字注释</p>
                  <p class="font-bold">{{ notes.length }}</p>
                </div>
              </div>
              <div class="overview-card">
                <div class="overview-icon"><i class="fas fa-toolbox"></i></div>
                <div class="overview-card-body">
                  <p class="text-sm text-gray-500">器械类型</p>
                  <p class="font-bold">{{ instrumentTypeCountLabel }}</p>
                </div>
              </div>
              <div class="overview-status-card overview-card-wide">
                <div class="overview-status-main">
                  <div class="overview-icon warning"><i class="fas fa-triangle-exclamation"></i></div>
                  <div>
                    <p class="text-sm text-gray-500">异常检测</p>
                    <p class="font-bold" :class="anomalyStatus.toneClass">
                      {{ anomalyStatus.label }}
                    </p>
                  </div>
                </div>
                <p class="text-xs text-slate-400">将由独立异常模型提供</p>
              </div>
            </div>
          </div>

          <div class="side-card instrument-side-card bg-gray-50 p-4 rounded-lg">
            <h3 class="font-semibold text-lg mb-3 flex items-center">
              <i class="fas fa-chart-bar mr-2 text-blue-500"></i>器械使用频率
            </h3>
            <div v-if="instrumentStatsStatus === 'idle'" class="instrument-empty">
              上传视频后将自动统计器械出现时长。
            </div>
            <div v-else-if="instrumentStatsStatus === 'loading'" class="instrument-loading">
              <i class="fas fa-spinner fa-spin text-blue-500 text-2xl"></i>
              <div>
                <p class="font-bold text-slate-800">{{ instrumentStatsMessage }}</p>
              </div>
            </div>
            <div v-else class="instrument-chart">
              <div class="instrument-y-axis">
                <span>{{ formatTimeLabel(instrumentMaxSeconds) }}</span>
                <span>{{ formatTimeLabel(Math.round(instrumentMaxSeconds / 2)) }}</span>
                <span>00:00</span>
              </div>
              <div class="instrument-plot">
                <div class="instrument-grid-line top"></div>
                <div class="instrument-grid-line middle"></div>
                <div
                  v-for="item in instrumentStats"
                  :key="item.key"
                  class="instrument-bar-item"
                >
                  <div class="instrument-bar-shell">
                    <div
                      class="instrument-bar"
                      :style="{
                        height: `${instrumentChartExpanded ? item.ratio : 0}%`,
                        background: item.color,
                      }"
                    ></div>
                  </div>
                  <p class="instrument-duration">{{ formatTimeLabel(item.seconds) }}</p>
                  <p class="instrument-label">{{ item.label }}</p>
                </div>
              </div>
            </div>
          </div>
          </div>

          <div class="phase-analysis-card bg-gray-50 p-4 rounded-lg">
            <div class="phase-header">
              <div>
                <h2 class="phase-title">
                  <i class="fas fa-list-ol text-blue-500"></i>关键步骤分析
                </h2>
                <p v-if="phaseAnalysisResult?.meta" class="phase-meta">
                  已采样 {{ phaseAnalysisResult.meta.sampleCount }} 帧，设备 {{ phaseAnalysisResult.meta.device }}
                </p>
                <p v-if="phaseAnalysisState?.status" class="phase-meta">
                  任务状态：{{ phaseStatusLabel }}
                </p>
              </div>
              <button class="btn-secondary" :disabled="phaseLoading || isPhaseRunning" @click="runPhaseAnalysis">
                <i class="fas" :class="phaseLoading ? 'fa-spinner fa-spin' : 'fa-wand-magic-sparkles'"></i>
                <span class="ml-2">{{ phaseLoading ? '提交中' : isPhaseRunning ? '分析中' : '开始分析' }}</span>
              </button>
            </div>

            <div v-if="phaseAnalysisState" class="phase-progress-panel">
              <div class="flex justify-between items-center gap-3 flex-wrap">
                <div>
                  <p class="phase-stage">{{ phaseAnalysisState.stageLabel || phaseStatusLabel }}</p>
                  <p class="phase-message">{{ phaseAnalysisState.message || '等待关键步骤分析任务更新。' }}</p>
                </div>
                <span class="phase-percent">{{ phaseAnalysisState.progress || 0 }}%</span>
              </div>
              <div class="phase-progress-track">
                <div class="phase-progress-bar" :style="{ width: `${phaseAnalysisState.progress || 0}%` }"></div>
              </div>
            </div>

            <div v-if="!projectVideoFile" class="empty phase-empty">
              当前项目还没有可分析的视频，请先上传视频后再执行关键步骤分析。
            </div>

            <div v-else-if="phaseError" class="status-box error mb-4">
              {{ phaseError }}
            </div>

            <div v-else-if="isPhaseRunning" class="empty phase-empty">
              关键步骤分析正在后台运行。你现在可以离开当前页面继续查看其他项目，稍后返回时结果会自动同步并保存到当前项目。
            </div>

            <div v-else-if="!generatedSteps.length" class="empty phase-empty">
              模型分析结果会在这里展示。点击“开始分析”后，将根据当前项目视频生成高置信度阶段时间线。
            </div>

            <div v-else class="phase-steps-list">
              <div v-for="(step, index) in generatedSteps" :key="step.id" class="phase-step-row">
                <div class="phase-step-index">{{ index + 1 }}</div>
                <div class="phase-step-body">
                  <div class="flex items-center gap-3 flex-wrap">
                    <h3 class="font-medium">{{ step.title }}</h3>
                    <span class="text-xs rounded-full px-2 py-1 bg-slate-100 text-slate-600">
                      置信度 {{ formatConfidence(step.confidence) }}
                    </span>
                  </div>
                  <p class="text-sm text-gray-600 mt-1">{{ step.description }}</p>
                  <div class="mt-2 flex items-center text-sm flex-wrap gap-x-3 gap-y-1">
                    <span class="text-gray-500">{{ step.time }}</span>
                    <span :class="step.level === '高置信度' ? 'text-green-600' : 'text-yellow-600'">
                      <i :class="step.level === '高置信度' ? 'fas fa-check-circle mr-1' : 'fas fa-exclamation-circle mr-1'"></i>{{ step.level }}
                    </span>
                  </div>
                </div>
                <button class="phase-step-play" @click="seekTo(step.seconds)"><i class="fas fa-play"></i></button>
              </div>
            </div>
          </div>

          </div>

        <div class="analysis-assistant-panel">
          <div class="assistant-tabs">
            <button
              class="assistant-tab"
              :class="activeInsightTab === 'report' ? 'active' : ''"
              @click="setInsightTab('report')"
            >
              <i class="fas fa-file-medical-alt"></i>
              <span>分析报告</span>
            </button>
            <button
              class="assistant-tab"
              :class="activeInsightTab === 'qa' ? 'active' : ''"
              @click="setInsightTab('qa')"
            >
              <i class="fas fa-comments"></i>
              <span>智能问答</span>
            </button>
          </div>

          <div v-if="activeInsightTab === 'report'" class="assistant-content">
            <div v-if="aiReportStatus !== 'completed'" class="ai-report-gate">
              <button class="ai-report-button" :disabled="aiReportStatus === 'loading'" @click="runAiReportAnalysis">
                <i class="fas" :class="aiReportStatus === 'loading' ? 'fa-spinner fa-spin' : 'fa-wand-magic-sparkles'"></i>
                <span>{{ aiReportStatus === 'loading' ? '正在分析' : '查看AI分析' }}</span>
              </button>
              <p>{{ aiReportStatus === 'loading' ? '正在结合关键步骤、器械统计和异常检测生成报告...' : 'AI 分析报告会基于当前视频分析结果生成。' }}</p>
            </div>

            <template v-else>
              <div class="report-header">
                <p class="report-title">{{ currentProject?.title || '未命名项目' }}</p>
                <span :class="['report-status', statusClass(currentProject?.status)]">{{ currentProject?.status || '待分析' }}</span>
              </div>

              <div class="report-section">
                <h4>总结</h4>
                <p>{{ reportSummary }}</p>
              </div>

              <div class="report-section">
                <h4>关键指标</h4>
                <div class="report-metrics">
                  <div v-for="item in reportMetrics" :key="item.label" class="report-metric">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }}</strong>
                  </div>
                </div>
              </div>

              <div class="report-section">
                <h4>关键步骤</h4>
                <div v-if="generatedSteps.length" class="report-list">
                  <div v-for="step in generatedSteps.slice(0, 4)" :key="step.id" class="report-list-row">
                    <span>{{ step.time }}</span>
                    <p>{{ step.title }}</p>
                  </div>
                </div>
                <p v-else class="report-empty">关键步骤分析完成后将在这里汇总。</p>
              </div>

              <div class="report-section">
                <h4>器械使用情况</h4>
                <div v-if="instrumentStatsStatus === 'loading'" class="report-empty">
                  {{ instrumentStatsMessage || '正在统计器械使用频率...' }}
                </div>
                <div v-else-if="instrumentStats.length" class="report-list">
                  <div v-for="item in instrumentStats.slice(0, 4)" :key="item.key" class="report-list-row">
                    <span>{{ formatTimeLabel(item.seconds) }}</span>
                    <p>{{ item.label }}</p>
                  </div>
                </div>
                <p v-else class="report-empty">上传视频后会自动生成器械出现时长。</p>
              </div>

              <div class="report-section">
                <h4>操作评估</h4>
                <ul class="report-bullets">
                  <li v-for="item in operationAssessment" :key="item">{{ item }}</li>
                </ul>
              </div>

              <div class="report-section">
                <h4>关键问题</h4>
                <ul class="report-bullets">
                  <li v-for="item in keyIssues" :key="item">{{ item }}</li>
                </ul>
              </div>

              <div class="report-section">
                <h4>改进建议</h4>
                <ul class="report-bullets">
                  <li v-for="item in improvementSuggestions" :key="item">{{ item }}</li>
                </ul>
              </div>
            </template>
          </div>

          <div v-else class="assistant-content qa-content">
            <div class="qa-messages">
              <div
                v-for="message in qaMessages"
                :key="message.id"
                class="qa-message"
                :class="message.role === 'user' ? 'user' : 'assistant'"
              >
                {{ message.text }}
              </div>
            </div>
            <div class="qa-input-row">
              <input
                v-model="qaInput"
                class="input qa-input"
                placeholder="询问当前视频分析结果"
                @keyup.enter="sendQaMessage"
              />
              <button class="qa-send" title="发送" :disabled="qaLoading" @click="sendQaMessage">
                <i class="fas" :class="qaLoading ? 'fa-spinner fa-spin' : 'fa-paper-plane'"></i>
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
import { askDoubao } from '../api/chat'
import { createPhaseAnalysisJob, getPhaseAnalysisJob } from '../api/phaseAnalysis'
import { applyPhaseAnalysisToProject, syncProjectPhaseAnalysis } from '../phaseAnalysisStore'
import { getActiveProject, saveProject, setActiveProject } from '../projectStore'
import { getProjectVideo, saveProjectVideo } from '../videoStore'

const videoFileInput = ref(null)
const uploadedVideoUrl = ref('')
const currentProject = ref(null)
const projectVideoFile = ref(null)

const videoEl = ref(null)
const videoContainer = ref(null)
const maskCanvas = ref(null)
const maskCtx = ref(null)

const positivePoints = ref([])
const negativePoints = ref([])
const isAddPositive = ref(true)
const isProcessing = ref(false)
const maskOpacity = ref(0.45)
const currentMask = ref(null)
const annotations = ref([])
const selectedAnnotationId = ref(null)
const annotationName = ref('关键器械')
const annotationType = ref('scalpel')
const statusMessage = ref('')
const statusType = ref('success')

const notes = ref([])
const noteTimeInput = ref('')
const noteTextInput = ref('')
const annotationTimerStart = ref(null)
const annotationTimerEnd = ref(null)
const isTimingAnnotation = ref(false)
const activeLoopNoteId = ref(null)
const activeLoopRange = ref(null)
let statusTimer = null

const currentTime = ref(0)
const duration = ref(165)
const phaseAnalysisResult = ref(null)
const phaseLoading = ref(false)
const phaseError = ref('')
const phaseJobStatus = ref('')
let phasePollingTimer = null

const instrumentStatsStatus = ref('idle')
const instrumentStatsMessage = ref('')
const instrumentStats = ref([])
const instrumentChartExpanded = ref(false)
let instrumentStatsTimer = null

const activeInsightTab = ref('report')
const aiReportStatus = ref('idle')
const qaInput = ref('')
const qaLoading = ref(false)
const defaultQaMessages = [
  {
    id: 'assistant-welcome',
    role: 'assistant',
    text: '我可以根据当前视频的关键步骤、器械统计和异常检测，模拟回答分析相关问题。',
  },
]
const qaMessages = ref([...defaultQaMessages])
let aiReportTimer = null

const simulatedInstrumentStats = [
  { key: 'grasper', label: '抓持钳', seconds: 92, color: '#2563eb' },
  { key: 'hook', label: '电凝钩', seconds: 126, color: '#0ea5e9' },
  { key: 'dissector', label: '分离钳', seconds: 74, color: '#10b981' },
  { key: 'scissors', label: '剪刀', seconds: 38, color: '#f59e0b' },
  { key: 'suction', label: '吸引器', seconds: 52, color: '#8b5cf6' },
]

const typeOptions = [
  { value: 'scalpel', label: '电凝钩' },
  { value: 'clamp', label: '抓持钳' },
  { value: 'needle', label: '夹闭夹' },
  { value: 'scissors', label: '剪刀' },
  { value: 'forceps', label: '分离钳' },
  { value: 'other', label: '其他器械' },
]

const colorMap = {
  scalpel: '#ef4444',
  clamp: '#3b82f6',
  needle: '#8b5cf6',
  scissors: '#10b981',
  forceps: '#f59e0b',
  other: '#0ea5e9',
}

const isTracking = ref(false)
const lastTrackTime = ref(0)

const pointsForDisplay = computed(() => [
  ...positivePoints.value.map((p) => ({ ...p, kind: 'positive' })),
  ...negativePoints.value.map((p) => ({ ...p, kind: 'negative' })),
])

const shouldShowUploadButton = computed(() => {
  if (!currentProject.value) return true
  return !currentProject.value.hasVideo && !uploadedVideoUrl.value
})

const progressPercent = computed(() => {
  if (!duration.value) return '0%'
  const ratio = Math.min(1, currentTime.value / duration.value)
  return `${(ratio * 100).toFixed(1)}%`
})

const shouldRequireVideo = computed(() => {
  if (!currentProject.value) return true
  return currentProject.value.status === '草稿' || !projectVideoFile.value || !uploadedVideoUrl.value
})

const notesSorted = computed(() => notes.value.slice().sort((a, b) => a.time - b.time))

const annotationIntervalLabel = computed(() => {
  if (annotationTimerStart.value === null) return '计时'
  if (annotationTimerEnd.value === null) return `${formatTimeLabel(annotationTimerStart.value)} - ...`
  return `${formatTimeLabel(annotationTimerStart.value)} - ${formatTimeLabel(annotationTimerEnd.value)}`
})

const generatedSteps = computed(() => mergeAdjacentPhaseSteps(phaseAnalysisResult.value?.steps || []))

const phaseAnalysisState = computed(() => currentProject.value?.phaseAnalysis || null)

const isPhaseRunning = computed(() => ['queued', 'running'].includes(phaseAnalysisState.value?.status))

const phaseStatusLabel = computed(() => {
  const status = phaseAnalysisState.value?.status
  if (status === 'queued') return '排队中'
  if (status === 'running') return '分析中'
  if (status === 'completed') return '分析完成'
  if (status === 'failed') return '分析失败'
  return status || '待分析'
})

const anomalyStatus = computed(() => {
  return { label: '待接入', toneClass: 'text-slate-500' }
})

const instrumentMaxSeconds = computed(() => {
  return Math.max(...instrumentStats.value.map((item) => item.seconds), 1)
})

const instrumentTypeCountLabel = computed(() => {
  if (instrumentStatsStatus.value === 'loading') return '统计中'
  if (instrumentStatsStatus.value !== 'completed') return '待统计'
  return `${instrumentStats.value.length}`
})

const reportSummary = computed(() => {
  if (shouldRequireVideo.value) {
    return '当前项目尚未上传视频，上传后会在这里生成分析摘要。'
  }
  if (isPhaseRunning.value) {
    return '关键步骤分析正在进行中，报告会随后台进度持续更新。'
  }
  if (generatedSteps.value.length) {
    return `已识别 ${generatedSteps.value.length} 个关键步骤，结合器械统计和异常检测结果形成当前报告。`
  }
  return '视频已加载，可先执行关键步骤分析，报告内容会结合异常检测和器械统计自动汇总。'
})

const reportMetrics = computed(() => [
  { label: '视频时长', value: formatTimeLabel(duration.value || 0) },
  { label: '关键步骤', value: `${generatedSteps.value.length} 个` },
  { label: '异常检测', value: anomalyStatus.value.label },
  { label: '器械类型', value: instrumentStatsStatus.value === 'completed' ? `${instrumentStats.value.length} 类` : instrumentTypeCountLabel.value },
])

const operationAssessment = computed(() => {
  if (shouldRequireVideo.value) {
    return ['尚未上传视频，暂无法形成操作评估。']
  }
  if (isPhaseRunning.value) {
    return ['关键步骤模型仍在分析中，操作评估将在结果完成后更新。']
  }
  return [
    '胆囊切除流程整体符合腹腔镜胆囊切除术的常规路径，画面推进围绕胆囊牵拉、胆囊三角显露、管道处理和胆囊床分离等关键阶段展开。',
    generatedSteps.value.length ? `系统已识别 ${generatedSteps.value.length} 个关键步骤，可用于术后复盘和教学定位。` : '关键步骤识别尚未完成，当前操作评估以预设模板展示。',
    instrumentStats.value.length ? '器械使用以抓持、分离和电凝相关器械为主，使用频率分布与胆囊切除术常见操作节奏基本一致。' : '器械统计结果尚未完成，暂无法对器械切换节奏进行量化判断。',
  ]
})

const keyIssues = computed(() => {
  if (shouldRequireVideo.value) {
    return ['当前项目未上传视频，无法定位关键问题。']
  }
  return [
    generatedSteps.value.length ? '关键步骤结果仍需结合原始视频逐段复核，尤其关注胆囊三角显露和夹闭前确认阶段。' : '关键步骤尚未完成识别，阶段性风险点仍需等待模型输出。',
    instrumentStatsStatus.value === 'loading' ? '器械统计仍在进行中，暂不能判断是否存在器械使用时间异常。' : '器械使用频率目前仅反映出现时长，尚不能直接判断操作质量或器械使用合理性。',
    '当前报告为 AI 分析内容，结论应作为复盘线索，不能替代术者和上级医师的专业判断。',
  ]
})

const improvementSuggestions = computed(() => {
  if (shouldRequireVideo.value) {
    return ['请先上传手术视频，再生成完整分析报告。']
  }
  return [
    '建议术者在胆囊三角处理阶段持续保持清晰暴露，夹闭或离断前重点复核胆囊管、胆囊动脉及周围组织关系。',
    '建议在牵拉胆囊颈部和分离胆囊床时控制牵拉力度与电凝范围，减少组织撕裂、热损伤和渗血风险。',
    '若术中出现烟雾、镜头污染或视野遮挡，应及时清理镜头并恢复稳定视野后再继续关键操作。',
    '术后复盘时建议重点回看关键步骤时间段，关注夹闭前确认、出血处理、胆囊床分离完整性和器械切换节奏。',
  ]
})

const reportInstrumentRows = computed(() => {
  if (instrumentStatsStatus.value === 'loading') {
    return [instrumentStatsMessage.value || '正在统计器械使用频率...']
  }
  if (!instrumentStats.value.length) {
    return ['上传视频后会自动生成器械出现时长。']
  }
  return instrumentStats.value.map((item) => `${item.label}：${formatTimeLabel(item.seconds)}`)
})

function triggerVideoUpload() {
  videoFileInput.value?.click()
}

function setInsightTab(tab) {
  if (requireVideoBeforeAction()) return
  activeInsightTab.value = tab
}

function runAiReportAnalysis() {
  if (requireVideoBeforeAction()) return Promise.resolve(false)
  if (aiReportStatus.value === 'completed') return Promise.resolve(true)
  if (aiReportStatus.value === 'loading') {
    return new Promise((resolve) => {
      const wait = window.setInterval(() => {
        if (aiReportStatus.value !== 'loading') {
          window.clearInterval(wait)
          resolve(aiReportStatus.value === 'completed')
        }
      }, 100)
    })
  }

  aiReportStatus.value = 'loading'
  showStatus('正在生成 AI 分析报告', 'success')
  return new Promise((resolve) => {
    aiReportTimer = window.setTimeout(() => {
      aiReportStatus.value = 'completed'
      aiReportTimer = null
      persistProjectAssistantState()
      showStatus('AI 分析报告已生成', 'success')
      resolve(true)
    }, 1200)
  })
}

function requireVideoBeforeAction() {
  if (!shouldRequireVideo.value) return false
  showStatus('请先上传视频后再进行操作', 'error')
  return true
}

function persistProjectNotes() {
  if (!currentProject.value) return
  const updatedProject = {
    ...currentProject.value,
    notes: notes.value,
    updatedAt: new Date().toISOString(),
    updatedAtLabel: new Date().toLocaleString('zh-CN'),
  }
  currentProject.value = updatedProject
  saveProject(updatedProject)
  setActiveProject(updatedProject)
}

function persistProjectAssistantState() {
  if (!currentProject.value) return
  const updatedProject = {
    ...currentProject.value,
    assistantState: {
      aiReportStatus: aiReportStatus.value === 'loading' ? 'idle' : aiReportStatus.value,
      qaMessages: qaMessages.value,
      updatedAt: new Date().toISOString(),
    },
    updatedAt: new Date().toISOString(),
    updatedAtLabel: new Date().toLocaleString('zh-CN'),
  }
  currentProject.value = updatedProject
  saveProject(updatedProject)
  setActiveProject(updatedProject)
}

function revokeUploadedVideoUrl() {
  if (uploadedVideoUrl.value && uploadedVideoUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(uploadedVideoUrl.value)
    uploadedVideoUrl.value = ''
  }
}

function restoreInstrumentStatsIfAvailable() {
  const savedStats = currentProject.value?.instrumentStats
  if (!savedStats || savedStats.fileName !== currentProject.value?.fileName || !Array.isArray(savedStats.items)) {
    return false
  }

  instrumentStats.value = savedStats.items
  instrumentStatsStatus.value = 'completed'
  instrumentStatsMessage.value = savedStats.message || '器械使用频率统计完成'
  instrumentChartExpanded.value = true
  return true
}

function persistInstrumentStats() {
  if (!currentProject.value) return
  const updatedProject = {
    ...currentProject.value,
    instrumentStats: {
      fileName: currentProject.value.fileName,
      status: instrumentStatsStatus.value,
      message: instrumentStatsMessage.value,
      items: instrumentStats.value,
      updatedAt: new Date().toISOString(),
    },
    updatedAt: new Date().toISOString(),
    updatedAtLabel: new Date().toLocaleString('zh-CN'),
  }
  currentProject.value = updatedProject
  saveProject(updatedProject)
  setActiveProject(updatedProject)
}

function startInstrumentStatsSimulation(force = false) {
  if (instrumentStatsStatus.value === 'loading') return
  if (!uploadedVideoUrl.value && !projectVideoFile.value) return
  if (!force && restoreInstrumentStatsIfAvailable()) return

  if (instrumentStatsTimer) {
    window.clearTimeout(instrumentStatsTimer)
  }

  instrumentStatsStatus.value = 'loading'
  instrumentStatsMessage.value = '正在加载器械检测模型...'
  instrumentStats.value = []
  instrumentChartExpanded.value = false

  instrumentStatsTimer = window.setTimeout(() => {
    instrumentStatsMessage.value = '正在逐帧统计器械出现时长...'
    instrumentStatsTimer = window.setTimeout(() => {
      const maxSeconds = Math.max(...simulatedInstrumentStats.map((item) => item.seconds), 1)
      instrumentStats.value = simulatedInstrumentStats.map((item) => ({
        ...item,
        ratio: Math.max(6, Math.round((item.seconds / maxSeconds) * 100)),
      }))
      instrumentStatsStatus.value = 'completed'
      instrumentStatsMessage.value = '器械使用频率统计完成'
      persistInstrumentStats()
      instrumentStatsTimer = window.setTimeout(() => {
        instrumentChartExpanded.value = true
        instrumentStatsTimer = null
      }, 80)
    }, 1600)
  }, 900)
}

async function onVideoSelected(event) {
  const file = event?.target?.files?.[0]
  if (!file) return

  revokeUploadedVideoUrl()
  uploadedVideoUrl.value = URL.createObjectURL(file)
  projectVideoFile.value = file
  phaseAnalysisResult.value = null
  phaseError.value = ''
  phaseJobStatus.value = ''
  aiReportStatus.value = 'idle'
  qaMessages.value = [...defaultQaMessages]
  qaInput.value = ''
  qaLoading.value = false

  if (currentProject.value) {
    await saveProjectVideo(currentProject.value.id, file)
    const updatedProject = {
      ...currentProject.value,
      fileName: file.name,
      hasVideo: true,
      videoUrl: '',
      status: '待分析',
      phaseAnalysis: null,
      instrumentStats: null,
      assistantState: {
        aiReportStatus: 'idle',
        qaMessages: [...defaultQaMessages],
        updatedAt: new Date().toISOString(),
      },
      updatedAt: new Date().toISOString(),
      updatedAtLabel: new Date().toLocaleString('zh-CN'),
    }
    currentProject.value = updatedProject
    saveProject(updatedProject)
    setActiveProject(updatedProject)
    startInstrumentStatsSimulation(true)
    showStatus('视频已加载到当前项目，可继续分析', 'success')
  }
}

function onLoadedMetadata() {
  duration.value = videoEl.value?.duration || duration.value
  setCanvasSize()
}

function onTimeUpdate() {
  currentTime.value = videoEl.value?.currentTime || 0
  syncLoopPlayback()
  if (isTracking.value) updateMaskTracking()
}

function syncLoopPlayback() {
  if (!videoEl.value || !activeLoopRange.value) return

  const { startTime, endTime } = activeLoopRange.value
  if (currentTime.value < startTime) {
    videoEl.value.currentTime = startTime
    return
  }

  if (currentTime.value >= endTime) {
    videoEl.value.currentTime = startTime
    videoEl.value.play?.()
  }
}

function updateMaskTracking() {
  if (!currentMask.value || !videoEl.value || videoEl.value.paused) return
  const now = currentTime.value
  let dt = now - lastTrackTime.value
  if (dt <= 0) return
  dt = Math.min(dt, 0.2)

  const velocity = currentMask.value.velocity || { x: 20, y: 8 }
  const dx = velocity.x * dt
  const dy = velocity.y * dt
  const nextPoints = currentMask.value.points.map((pt) => ({ x: pt.x + dx, y: pt.y + dy }))

  currentMask.value = {
    ...currentMask.value,
    points: nextPoints,
    lastCenter: getPolygonCenter(nextPoints),
  }

  drawMask(currentMask.value)
  lastTrackTime.value = now
}

function setCanvasSize() {
  if (!videoContainer.value || !maskCanvas.value) return
  const { clientWidth, clientHeight } = videoContainer.value
  maskCanvas.value.width = clientWidth
  maskCanvas.value.height = clientHeight
  if (!maskCtx.value) maskCtx.value = maskCanvas.value.getContext('2d')
  if (currentMask.value) drawMask(currentMask.value)
}

function markerLeft(time) {
  if (!duration.value) return '0%'
  const ratio = Math.min(1, Math.max(0, time / duration.value))
  return `${(ratio * 100).toFixed(2)}%`
}

function toggleVideoPlayback() {
  if (requireVideoBeforeAction()) return
  if (!videoEl.value) return
  if (videoEl.value.paused) {
    videoEl.value.play?.()
  } else {
    videoEl.value.pause()
  }
}

function toggleAnnotationTimer() {
  if (requireVideoBeforeAction()) return
  const seconds = videoEl.value?.currentTime ?? currentTime.value
  if (!Number.isFinite(seconds)) return

  if (!isTimingAnnotation.value) {
    annotationTimerStart.value = seconds
    annotationTimerEnd.value = null
    isTimingAnnotation.value = true
    noteTimeInput.value = `${formatTimeLabel(seconds)} - ...`
    showStatus('注释开始时间已记录', 'success')
    return
  }

  const start = annotationTimerStart.value ?? seconds
  annotationTimerStart.value = Math.min(start, seconds)
  annotationTimerEnd.value = Math.max(start, seconds)
  isTimingAnnotation.value = false
  noteTimeInput.value = `${formatTimeLabel(annotationTimerStart.value)} - ${formatTimeLabel(annotationTimerEnd.value)}`
  showStatus('注释结束时间已记录，可输入文字内容保存', 'success')
}

function clearAnnotationTimer() {
  if (requireVideoBeforeAction()) return
  annotationTimerStart.value = null
  annotationTimerEnd.value = null
  isTimingAnnotation.value = false
  noteTimeInput.value = ''
}

function setPointMode(isPositive) {
  if (requireVideoBeforeAction()) return
  isAddPositive.value = isPositive
}

function clearPoints() {
  if (requireVideoBeforeAction()) return
  positivePoints.value = []
  negativePoints.value = []
}

function onOpacityChange() {
  if (currentMask.value) {
    currentMask.value.opacity = maskOpacity.value
    drawMask(currentMask.value)
  }
}

async function runSegmentation() {
  if (requireVideoBeforeAction()) return
  if (!positivePoints.value.length) {
    showStatus('请至少添加一个正样本点', 'error')
    return
  }

  isProcessing.value = true
  showStatus('正在生成分析掩码...', 'success')
  await new Promise((resolve) => setTimeout(resolve, 400))

  const color = colorMap[annotationType.value] || '#3b82f6'
  const maskPoints = generateMaskFromPoints(positivePoints.value, negativePoints.value)

  currentMask.value = {
    points: maskPoints,
    color,
    opacity: maskOpacity.value,
    velocity: { x: 20, y: 8 },
    lastCenter: getPolygonCenter(maskPoints),
  }

  drawMask(currentMask.value)
  isTracking.value = true
  lastTrackTime.value = currentTime.value
  isProcessing.value = false
  showStatus('已生成分析区域，可以保存标注', 'success')
}

async function runPhaseAnalysis() {
  if (requireVideoBeforeAction()) return
  if (!projectVideoFile.value) {
    phaseError.value = '当前项目没有可分析的视频文件。'
    return
  }

  phaseLoading.value = true
  phaseError.value = ''
  showStatus('已提交关键步骤分析任务，后台会继续处理。', 'success')

  try {
    const job = await createPhaseAnalysisJob(projectVideoFile.value, { sampleSeconds: 2 })
    phaseJobStatus.value = job.status

    if (currentProject.value) {
      const updatedProject = applyPhaseAnalysisToProject(currentProject.value, job)
      currentProject.value = updatedProject
      saveProject(updatedProject)
      setActiveProject(updatedProject)
    }

    startPhasePolling()
  } catch (error) {
    phaseError.value = error?.message || '关键步骤分析失败，请检查后端服务是否启动。'
    showStatus(phaseError.value, 'error')
  } finally {
    phaseLoading.value = false
  }
}

function stopPhasePolling() {
  if (phasePollingTimer) {
    window.clearInterval(phasePollingTimer)
    phasePollingTimer = null
  }
}

function startPhasePolling() {
  stopPhasePolling()
  phasePollingTimer = window.setInterval(async () => {
    await refreshPhaseJob()
  }, 4000)
}

async function refreshPhaseJob() {
  const jobId = currentProject.value?.phaseAnalysis?.jobId
  const status = currentProject.value?.phaseAnalysis?.status
  if (!jobId || !['queued', 'running'].includes(status)) {
    stopPhasePolling()
    return
  }

  try {
    const job = await getPhaseAnalysisJob(jobId)
    phaseJobStatus.value = job.status
    const updatedProject = applyPhaseAnalysisToProject(currentProject.value, job)
    currentProject.value = updatedProject
    phaseAnalysisResult.value = job.result || null
    phaseError.value = job.error || ''
    saveProject(updatedProject)
    setActiveProject(updatedProject)

    if (job.status === 'completed') {
      stopPhasePolling()
      showStatus(`关键步骤分析完成，保留 ${job.result?.steps?.length || 0} 个高置信度步骤`, 'success')
    } else if (job.status === 'failed') {
      stopPhasePolling()
      showStatus(job.error || '关键步骤分析失败', 'error')
    }
  } catch (error) {
    phaseError.value = error?.message || '关键步骤分析状态获取失败'
  }
}

function mergeAdjacentPhaseSteps(steps) {
  if (!Array.isArray(steps) || !steps.length) return []

  const merged = []
  for (const step of steps) {
    const previous = merged[merged.length - 1]
    if (previous && isSamePhaseStep(previous, step)) {
      previous.endSeconds = getStepEndSeconds(step)
      previous.time = `${formatTimeLabel(previous.startSeconds)} - ${formatTimeLabel(previous.endSeconds)}`
      previous.confidences.push(getStepConfidence(step))
      previous.confidence = average(previous.confidences)
      previous.level = previous.confidence >= 0.65 ? '高置信度' : '建议复核'
      continue
    }

    const startSeconds = getStepStartSeconds(step)
    const endSeconds = getStepEndSeconds(step)
    const confidence = getStepConfidence(step)
    merged.push({
      ...step,
      id: `merged-step-${merged.length + 1}`,
      index: merged.length + 1,
      startSeconds,
      endSeconds,
      seconds: startSeconds,
      time: `${formatTimeLabel(startSeconds)} - ${formatTimeLabel(endSeconds)}`,
      confidence,
      confidences: [confidence],
    })
  }

  return merged.map(({ confidences, ...step }, index) => ({
    ...step,
    id: `merged-step-${index + 1}`,
    index: index + 1,
  }))
}

function isSamePhaseStep(a, b) {
  const aKey = a?.phaseKey ?? a?.phaseId ?? a?.title
  const bKey = b?.phaseKey ?? b?.phaseId ?? b?.title
  return String(aKey) === String(bKey)
}

function getStepStartSeconds(step) {
  if (Number.isFinite(step?.startSeconds)) return step.startSeconds
  if (Number.isFinite(step?.seconds)) return step.seconds
  const parsed = parseTimeRange(step?.time || '')
  return parsed?.startTime ?? 0
}

function getStepEndSeconds(step) {
  if (Number.isFinite(step?.endSeconds)) return step.endSeconds
  const parsed = parseTimeRange(step?.time || '')
  if (Number.isFinite(parsed?.endTime)) return parsed.endTime
  return getStepStartSeconds(step)
}

function getStepConfidence(step) {
  return Number.isFinite(step?.confidence) ? step.confidence : 0
}

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / Math.max(values.length, 1)
}

function drawMask(mask) {
  if (!maskCtx.value || !maskCanvas.value) return
  maskCtx.value.clearRect(0, 0, maskCanvas.value.width, maskCanvas.value.height)
  const { r, g, b } = hexToRgb(mask.color)
  maskCtx.value.fillStyle = `rgba(${r}, ${g}, ${b}, ${mask.opacity || maskOpacity.value})`
  maskCtx.value.beginPath()
  mask.points.forEach((pt, idx) => {
    if (idx === 0) maskCtx.value.moveTo(pt.x, pt.y)
    else maskCtx.value.lineTo(pt.x, pt.y)
  })
  maskCtx.value.closePath()
  maskCtx.value.fill()
  maskCtx.value.strokeStyle = mask.color
  maskCtx.value.lineWidth = 2
  maskCtx.value.stroke()
}

function addAnnotation() {
  if (!currentMask.value) {
    showStatus('请先生成分析结果', 'error')
    return
  }

  const type = annotationType.value
  const typeLabel = typeOptions.find((item) => item.value === type)?.label || type
  const record = {
    id: Date.now(),
    name: annotationName.value.trim() || '未命名标注',
    type,
    typeLabel,
    time: formatTimeLabel(currentTime.value),
    mask: { ...currentMask.value },
    points: {
      positive: [...positivePoints.value],
      negative: [...negativePoints.value],
    },
  }

  annotations.value = [record, ...annotations.value]
  selectedAnnotationId.value = record.id
  clearPoints()
  showStatus('标注已保存', 'success')
}

function selectAnnotation(item) {
  selectedAnnotationId.value = item.id
  currentMask.value = { ...item.mask }
  positivePoints.value = [...(item.points?.positive || [])]
  negativePoints.value = [...(item.points?.negative || [])]
  drawMask(item.mask)
}

function removeAnnotation(id) {
  annotations.value = annotations.value.filter((item) => item.id !== id)
  if (selectedAnnotationId.value === id) {
    selectedAnnotationId.value = null
    currentMask.value = null
    clearCanvas()
    clearPoints()
  }
}

function clearAllAnnotations() {
  annotations.value = []
  selectedAnnotationId.value = null
  currentMask.value = null
  clearCanvas()
  clearPoints()
}

function clearCanvas() {
  if (!maskCtx.value || !maskCanvas.value) return
  maskCtx.value.clearRect(0, 0, maskCanvas.value.width, maskCanvas.value.height)
}

function toggleTracking() {
  if (requireVideoBeforeAction()) return
  isTracking.value = !isTracking.value
  showStatus(`实时追踪已${isTracking.value ? '开启' : '关闭'}`, 'success')
}

async function sendQaMessage() {
  if (requireVideoBeforeAction()) return
  if (qaLoading.value) return
  const question = qaInput.value.trim()
  if (!question) {
    showStatus('请输入需要提问的内容', 'error')
    return
  }

  qaMessages.value = [
    ...qaMessages.value,
    {
      id: `user-${Date.now()}`,
      role: 'user',
      text: question,
    },
  ]
  persistProjectAssistantState()
  qaInput.value = ''
  qaLoading.value = true

  try {
    const answer = await askDoubao(question, buildQaContext())
    qaMessages.value = [
      ...qaMessages.value,
      {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: answer || '豆包没有返回有效回答。',
      },
    ]
    persistProjectAssistantState()
  } catch (error) {
    qaMessages.value = [
      ...qaMessages.value,
      {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        text: error?.message || '智能问答请求失败，请检查后端服务和 ARK_API_KEY 配置。',
      },
    ]
    persistProjectAssistantState()
    showStatus(error?.message || '智能问答请求失败', 'error')
  } finally {
    qaLoading.value = false
  }
}

function buildQaContext() {
  return {
    project: {
      title: currentProject.value?.title || '',
      procedure: currentProject.value?.procedure || '',
      surgeon: currentProject.value?.surgeon || '',
      date: currentProject.value?.date || '',
      status: currentProject.value?.status || '',
      fileName: currentProject.value?.fileName || '',
    },
    video: {
      duration: formatTimeLabel(duration.value || 0),
      currentTime: formatTimeLabel(currentTime.value || 0),
    },
    phaseAnalysis: {
      status: phaseStatusLabel.value,
      progress: phaseAnalysisState.value?.progress || 0,
      steps: generatedSteps.value.map((step) => ({
        title: step.title,
        time: step.time,
        confidence: formatConfidence(step.confidence),
        level: step.level,
        description: step.description,
      })),
    },
    instrumentStats: {
      status: instrumentStatsStatus.value,
      message: instrumentStatsMessage.value,
      items: instrumentStats.value.map((item) => ({
        label: item.label,
        duration: formatTimeLabel(item.seconds),
      })),
    },
    anomaly: {
      status: anomalyStatus.value.label,
    },
    notes: notes.value.map((note) => ({
      time: formatNoteRange(note),
      text: note.text,
    })),
  }
}

function buildQaReply(question) {
  const normalizedQuestion = question.toLowerCase()
  if (normalizedQuestion.includes('器械') || normalizedQuestion.includes('instrument')) {
    if (instrumentStatsStatus.value === 'loading') {
      return '器械使用频率仍在统计中，完成后会给出各器械出现时长。'
    }
    if (instrumentStats.value.length) {
      const topInstrument = [...instrumentStats.value].sort((a, b) => b.seconds - a.seconds)[0]
      return `当前模拟统计中，${topInstrument.label} 出现时长最长，约 ${formatTimeLabel(topInstrument.seconds)}。`
    }
    return '当前还没有器械统计结果，请等待自动统计完成。'
  }

  if (normalizedQuestion.includes('步骤') || normalizedQuestion.includes('阶段') || normalizedQuestion.includes('phase')) {
    if (isPhaseRunning.value) {
      return `关键步骤分析正在进行，当前进度 ${phaseAnalysisState.value?.progress || 0}%。`
    }
    if (generatedSteps.value.length) {
      return `当前已识别 ${generatedSteps.value.length} 个关键步骤，首个步骤是“${generatedSteps.value[0].title}”。`
    }
    return '当前还没有关键步骤结果，可以先点击“开始关键步骤分析”。'
  }

  if (normalizedQuestion.includes('注释') || normalizedQuestion.includes('标注')) {
    return `当前共有 ${notes.value.length} 条文字注释、${annotations.value.length} 条区域标注。`
  }

  return `当前项目视频时长约 ${formatTimeLabel(duration.value || 0)}，已有 ${generatedSteps.value.length} 个关键步骤，异常检测状态为“${anomalyStatus.value.label}”。后续接入大模型后，这里会基于完整报告进行更深入问答。`
}

function exportAnnotations() {
  if (requireVideoBeforeAction()) return
  if (!annotations.value.length) return
  const blob = new Blob([JSON.stringify(annotations.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'video-annotations.json'
  link.click()
  URL.revokeObjectURL(url)
}

async function exportSummary() {
  if (requireVideoBeforeAction()) return
  const reportWindow = window.open('', '_blank')
  if (!reportWindow) {
    showStatus('浏览器拦截了报告窗口，请允许弹窗后重试', 'error')
    return
  }

  reportWindow.document.open()
  reportWindow.document.write(buildReportLoadingHtml())
  reportWindow.document.close()
  reportWindow.focus()
  await runAiReportAnalysis()

  reportWindow.document.open()
  reportWindow.document.write(buildReportPdfHtml())
  reportWindow.document.close()
  reportWindow.focus()
  window.setTimeout(() => {
    reportWindow.print()
  }, 500)

  if (currentProject.value) {
    const updatedProject = {
      ...currentProject.value,
      notes: notes.value,
      updatedAt: new Date().toISOString(),
      updatedAtLabel: new Date().toLocaleString('zh-CN'),
    }
    currentProject.value = updatedProject
    saveProject(updatedProject)
    setActiveProject(updatedProject)
    showStatus('已生成分析报告 PDF 导出窗口', 'success')
  }
}

function buildReportLoadingHtml() {
  return `
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>AI 分析报告生成中</title>
        <style>
          body { margin: 0; min-height: 100vh; display: grid; place-items: center; font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif; background: #f8fafc; color: #0f172a; }
          .box { width: min(520px, calc(100vw - 32px)); padding: 32px; border: 1px solid #dbeafe; border-radius: 18px; background: #fff; text-align: center; box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12); }
          .spinner { width: 34px; height: 34px; margin: 0 auto 16px; border: 4px solid #dbeafe; border-top-color: #2563eb; border-radius: 999px; animation: spin 0.8s linear infinite; }
          h1 { margin: 0 0 10px; font-size: 22px; }
          p { margin: 0; color: #64748b; line-height: 1.7; }
          @keyframes spin { to { transform: rotate(360deg); } }
        </style>
      </head>
      <body>
        <div class="box">
          <div class="spinner"></div>
          <h1>正在生成 AI 分析报告</h1>
          <p>正在汇总关键步骤、器械使用情况、异常检测和操作评估，稍后将进入 PDF 预览。</p>
        </div>
      </body>
    </html>
  `
}

function buildReportPdfHtml() {
  const project = currentProject.value || {}
  const generatedAt = new Date().toLocaleString('zh-CN')
  const metricsHtml = reportMetrics.value
    .map((item) => `<div class="metric"><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong></div>`)
    .join('')
  const stepsHtml = generatedSteps.value.length
    ? generatedSteps.value
        .map((step, index) => `<li><strong>${index + 1}. ${escapeHtml(step.title)}</strong><span>${escapeHtml(step.time || '')}</span><p>${escapeHtml(step.description || '')}</p></li>`)
        .join('')
    : '<li>关键步骤分析完成后将在这里汇总。</li>'
  const instrumentHtml = reportInstrumentRows.value.map((item) => `<li>${escapeHtml(item)}</li>`).join('')
  const assessmentHtml = operationAssessment.value.map((item) => `<li>${escapeHtml(item)}</li>`).join('')
  const issuesHtml = keyIssues.value.map((item) => `<li>${escapeHtml(item)}</li>`).join('')
  const suggestionsHtml = improvementSuggestions.value.map((item) => `<li>${escapeHtml(item)}</li>`).join('')

  return `
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>${escapeHtml(project.title || '手术视频分析报告')}</title>
        <style>
          * { box-sizing: border-box; }
          body { margin: 0; padding: 32px; color: #0f172a; font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif; background: #f8fafc; }
          .page { max-width: 860px; margin: 0 auto; padding: 34px; background: #fff; border: 1px solid #e2e8f0; }
          .header { display: flex; justify-content: space-between; gap: 24px; border-bottom: 2px solid #2563eb; padding-bottom: 18px; margin-bottom: 24px; }
          h1 { margin: 0; font-size: 28px; }
          .meta { margin-top: 10px; color: #475569; font-size: 13px; line-height: 1.7; }
          .status { display: inline-block; padding: 6px 10px; border-radius: 999px; background: #eff6ff; color: #1d4ed8; font-weight: 800; font-size: 12px; white-space: nowrap; }
          section { margin-top: 22px; break-inside: avoid; }
          h2 { margin: 0 0 10px; color: #1e3a8a; font-size: 17px; }
          p { margin: 0; color: #334155; line-height: 1.75; font-size: 14px; }
          ul { margin: 0; padding-left: 20px; color: #334155; line-height: 1.75; font-size: 14px; }
          li + li { margin-top: 6px; }
          li span { display: block; color: #64748b; font-size: 12px; margin-top: 2px; }
          .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
          .metric { padding: 12px; border: 1px solid #e2e8f0; border-radius: 10px; background: #f8fafc; }
          .metric span { display: block; color: #64748b; font-size: 12px; }
          .metric strong { display: block; margin-top: 6px; font-size: 16px; }
          @media print {
            body { padding: 0; background: #fff; }
            .page { max-width: none; border: none; }
          }
        </style>
      </head>
      <body>
        <main class="page">
          <div class="header">
            <div>
              <h1>手术视频分析报告</h1>
              <div class="meta">
                <div>项目名称：${escapeHtml(project.title || '未命名项目')}</div>
                <div>术式名称：${escapeHtml(project.procedure || '未填写')}</div>
                <div>术者：${escapeHtml(project.surgeon || '未填写')} ｜ 日期：${escapeHtml(project.date || '未填写')}</div>
                <div>视频文件：${escapeHtml(project.fileName || '未上传')} ｜ 生成时间：${escapeHtml(generatedAt)}</div>
              </div>
            </div>
            <span class="status">${escapeHtml(project.status || '待分析')}</span>
          </div>

          <section>
            <h2>总结</h2>
            <p>${escapeHtml(reportSummary.value)}</p>
          </section>

          <section>
            <h2>关键指标</h2>
            <div class="metrics">${metricsHtml}</div>
          </section>

          <section>
            <h2>关键步骤</h2>
            <ul>${stepsHtml}</ul>
          </section>

          <section>
            <h2>器械使用情况</h2>
            <ul>${instrumentHtml}</ul>
          </section>

          <section>
            <h2>操作评估</h2>
            <ul>${assessmentHtml}</ul>
          </section>

          <section>
            <h2>关键问题</h2>
            <ul>${issuesHtml}</ul>
          </section>

          <section>
            <h2>改进建议</h2>
            <ul>${suggestionsHtml}</ul>
          </section>
        </main>
      </body>
    </html>
  `
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
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

function getPolygonCenter(points) {
  if (!points.length) return { x: 0, y: 0 }
  const sum = points.reduce((acc, point) => ({ x: acc.x + point.x, y: acc.y + point.y }), { x: 0, y: 0 })
  return { x: sum.x / points.length, y: sum.y / points.length }
}

function generateMaskFromPoints(positive, negative) {
  if (!positive.length) return []
  const center = getPolygonCenter(positive)
  const avgDistance = positive.reduce((acc, point) => acc + Math.hypot(point.x - center.x, point.y - center.y), 0) / positive.length
  let radius = Math.max(40, avgDistance * 1.5)

  if (negative.length) {
    const nearest = negative.reduce((best, point) => {
      const distance = Math.hypot(point.x - center.x, point.y - center.y)
      return distance < best ? distance : best
    }, Infinity)
    radius = Math.max(24, Math.min(radius, nearest * 0.85))
  }

  const points = []
  for (let i = 0; i < 48; i += 1) {
    const angle = (i / 48) * Math.PI * 2
    const scale = radius * (0.7 + 0.2 * Math.sin(angle * 3))
    points.push({ x: center.x + scale * Math.cos(angle), y: center.y + scale * Math.sin(angle) })
  }
  return points
}

function hexToRgb(hex) {
  const stripped = hex.replace('#', '')
  const bigint = parseInt(stripped, 16)
  return {
    r: (bigint >> 16) & 255,
    g: (bigint >> 8) & 255,
    b: bigint & 255,
  }
}

function formatTimeLabel(value) {
  if (!Number.isFinite(value) || value < 0) return '00:00'
  const minutes = Math.floor(value / 60)
  const seconds = Math.floor(value % 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function formatConfidence(value) {
  if (!Number.isFinite(value)) return '--'
  return `${Math.round(value * 100)}%`
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

function parseTime(text) {
  const match = text.match(/^(\d{1,2}):(\d{2})$/)
  if (!match) return NaN
  const minutes = parseInt(match[1], 10)
  const seconds = parseInt(match[2], 10)
  return minutes * 60 + seconds
}

function parseTimeRange(text) {
  const parts = text.split('-').map((item) => item.trim()).filter(Boolean)
  if (!parts.length || parts.some((part) => part === '...')) {
    return null
  }

  const start = parseTime(parts[0])
  const end = parts[1] ? parseTime(parts[1]) : start
  if (!Number.isFinite(start) || !Number.isFinite(end)) {
    return null
  }

  return {
    startTime: Math.min(start, end),
    endTime: Math.max(start, end),
  }
}

function addNote() {
  if (requireVideoBeforeAction()) return
  const range = parseTimeRange(noteTimeInput.value.trim())
  if (!range) {
    showStatus('请先用计时器记录时间段，或输入 mm:ss - mm:ss 格式时间', 'error')
    return
  }
  if (!noteTextInput.value.trim()) {
    showStatus('请输入文字注释内容', 'error')
    return
  }
  notes.value = [
    ...notes.value,
    {
      id: Date.now(),
      time: range.startTime,
      startTime: range.startTime,
      endTime: range.endTime,
      text: noteTextInput.value.trim(),
    },
  ]
  persistProjectNotes()
  noteTextInput.value = ''
  clearAnnotationTimer()
  showStatus('文字注释已添加', 'success')
}

function formatNoteRange(note) {
  const start = note.startTime ?? note.time
  const end = note.endTime ?? note.time
  if (!Number.isFinite(end) || end === start) {
    return formatTimeLabel(start)
  }
  return `${formatTimeLabel(start)} - ${formatTimeLabel(end)}`
}

function playNoteLoop(note) {
  if (requireVideoBeforeAction()) return
  if (!videoEl.value) {
    showStatus('请先加载视频后再播放注释片段', 'error')
    return
  }

  if (activeLoopNoteId.value === note.id) {
    exitNoteLoop()
    return
  }

  const startTime = note.startTime ?? note.time
  const endTime = note.endTime ?? note.time
  if (!Number.isFinite(startTime) || !Number.isFinite(endTime) || endTime <= startTime) {
    showStatus('该注释没有有效的时间区间', 'error')
    return
  }

  activeLoopNoteId.value = note.id
  activeLoopRange.value = { startTime, endTime }
  videoEl.value.currentTime = startTime
  videoEl.value.play?.()
  showStatus(`正在循环播放注释片段 ${formatTimeLabel(startTime)} - ${formatTimeLabel(endTime)}`, 'success')
}

function exitNoteLoop() {
  if (requireVideoBeforeAction()) return
  activeLoopNoteId.value = null
  activeLoopRange.value = null
  showStatus('已退出注释片段循环播放', 'success')
}

function removeNote(id) {
  if (requireVideoBeforeAction()) return
  if (activeLoopNoteId.value === id) {
    activeLoopNoteId.value = null
    activeLoopRange.value = null
  }
  notes.value = notes.value.filter((item) => item.id !== id)
  persistProjectNotes()
}

function seekTo(seconds) {
  if (requireVideoBeforeAction()) return
  if (!videoEl.value) return
  videoEl.value.currentTime = seconds
  currentTime.value = seconds
}

onMounted(() => {
  currentProject.value = getActiveProject()
  notes.value = Array.isArray(currentProject.value?.notes) ? currentProject.value.notes : []
  aiReportStatus.value = currentProject.value?.assistantState?.aiReportStatus === 'completed' ? 'completed' : 'idle'
  qaMessages.value = Array.isArray(currentProject.value?.assistantState?.qaMessages) && currentProject.value.assistantState.qaMessages.length
    ? currentProject.value.assistantState.qaMessages
    : [...defaultQaMessages]
  phaseAnalysisResult.value = currentProject.value?.phaseAnalysis?.result || null
  phaseError.value = currentProject.value?.phaseAnalysis?.error || ''
  phaseJobStatus.value = currentProject.value?.phaseAnalysis?.status || ''

  if (currentProject.value?.videoUrl) {
    uploadedVideoUrl.value = currentProject.value.videoUrl
    startInstrumentStatsSimulation()
  } else if (currentProject.value?.hasVideo) {
    getProjectVideo(currentProject.value.id)
      .then((file) => {
        if (file) {
          projectVideoFile.value = file
          uploadedVideoUrl.value = URL.createObjectURL(file)
          startInstrumentStatsSimulation()
        } else {
          showStatus('未找到该项目的视频文件，请重新上传', 'error')
        }
      })
      .catch(() => {
        showStatus('项目视频加载失败，请重新上传', 'error')
      })
  }

  if (currentProject.value?.phaseAnalysis?.jobId && ['queued', 'running'].includes(currentProject.value.phaseAnalysis.status)) {
    syncProjectPhaseAnalysis(currentProject.value)
      .then((project) => {
        currentProject.value = project
        phaseAnalysisResult.value = project?.phaseAnalysis?.result || null
        phaseError.value = project?.phaseAnalysis?.error || ''
        phaseJobStatus.value = project?.phaseAnalysis?.status || ''
        if (['queued', 'running'].includes(project?.phaseAnalysis?.status)) {
          startPhasePolling()
        }
      })
      .catch(() => {
        startPhasePolling()
      })
  }

  if (maskCanvas.value) maskCtx.value = maskCanvas.value.getContext('2d')
  window.addEventListener('resize', setCanvasSize)
  setCanvasSize()
})

onBeforeUnmount(() => {
  stopPhasePolling()
  if (statusTimer) {
    window.clearTimeout(statusTimer)
    statusTimer = null
  }
  if (instrumentStatsTimer) {
    window.clearTimeout(instrumentStatsTimer)
    instrumentStatsTimer = null
  }
  if (aiReportTimer) {
    window.clearTimeout(aiReportTimer)
    aiReportTimer = null
  }
  revokeUploadedVideoUrl()
  window.removeEventListener('resize', setCanvasSize)
  if (videoEl.value) {
    videoEl.value.pause()
    videoEl.value.src = ''
    videoEl.value.load()
  }
})

const analysisImageSrc =
  'data:image/svg+xml;charset=UTF-8,' +
  encodeURIComponent(`
    <svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="#0f172a"/>
          <stop offset="1" stop-color="#1d4ed8"/>
        </linearGradient>
      </defs>
      <rect width="1280" height="720" fill="url(#g)"/>
      <g fill="#ffffff" opacity="0.9" font-family="Segoe UI, Arial" text-anchor="middle">
        <text x="640" y="360" font-size="44" font-weight="700">SurgReview 分析示例</text>
        <text x="640" y="420" font-size="20" opacity="0.85">请上传或选择项目视频开始分析</text>
      </g>
    </svg>
  `)
</script>

<style scoped>
.analysis-page {
  width: 100%;
  max-width: none;
  height: calc(100vh - 80px);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-size: 17px;
  --analysis-panel-height: 100%;
}
.analysis-workspace-card {
  flex: 1;
  min-height: 0;
  display: flex;
  overflow: hidden;
}
.analysis-main-grid {
  flex: 1;
  height: 100%;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(500px, 0.95fr) minmax(420px, 0.72fr) minmax(360px, 0.58fr);
  gap: 16px;
  align-items: stretch;
}
.analysis-video-column {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}
.analysis-video-column > :not([hidden]) ~ :not([hidden]) {
  margin-top: 0 !important;
}
.analysis-side-panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}
.middle-video-aligned-panel {
  flex: 0 0 clamp(300px, 23vw, 43vh);
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: auto minmax(92px, 1fr);
  gap: 12px;
  overflow: hidden;
}
.side-card {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}
.overview-side-card {
  display: flex;
  flex-direction: column;
}
.side-card h3,
.note-panel h3 {
  font-size: 21px;
  line-height: 1.35;
}
.side-card .text-sm {
  font-size: 16px;
  line-height: 1.55;
}
.side-card .text-xs {
  font-size: 14px;
  line-height: 1.45;
}
.instrument-side-card {
  grid-column: 1 / -1;
  height: auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.overview-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr)) minmax(0, 1.25fr);
  gap: 10px;
}
.overview-card {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}
.overview-icon {
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #eff6ff;
  color: #2563eb;
  font-size: 15px;
}
.overview-icon.warning {
  background: #fff7ed;
  color: #f97316;
}
.overview-card-body {
  min-width: 0;
}
.overview-card p:first-child {
  font-size: 15px;
  line-height: 1.35;
  white-space: nowrap;
}
.overview-card .font-bold {
  margin-top: 2px;
  font-size: 18px;
  line-height: 1.35;
}
.overview-card-wide {
  grid-column: 1 / -1;
}
.overview-status-card {
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}
.overview-status-main {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.overview-status-card > .text-xs {
  flex: 0 0 auto;
  margin: 0;
  white-space: nowrap;
}
.analysis-side-panel::-webkit-scrollbar {
  width: 8px;
}
.analysis-side-panel::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: #cbd5e1;
}
.analysis-side-panel::-webkit-scrollbar-track {
  background: transparent;
}
.video-container {
  flex: 0 0 auto;
  position: relative;
  aspect-ratio: 16 / 9;
  width: 100%;
  max-height: 43vh;
  background-color: #000;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.25);
}
.video-container > video,
.video-container > img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}
.mask-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.annotation-timer {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 86px;
  justify-content: center;
  padding: 9px 11px;
  border-radius: 10px;
  background: #0f172a;
  color: white;
  border: 1px solid #1e293b;
  font-size: 13px;
  font-weight: 800;
}
.annotation-timer.recording {
  background: #dc2626;
  border-color: #b91c1c;
}
.points-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.point-dot {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
  border: 2px solid #fff;
}
.point-positive { background-color: rgba(34, 197, 94, 0.95); }
.point-negative { background-color: rgba(239, 68, 68, 0.95); }
.video-container,
.video-container video { cursor: default; }
.seg-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-weight: 700;
  font-size: 14px;
  background: #f1f5f9;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}
.seg-btn.primary { background: linear-gradient(135deg, #2563eb, #0ea5e9); color: white; border: none; }
.seg-btn-active { background: #e0f2fe; border-color: #bae6fd; }
.seg-btn-active.neg { background: #fee2e2; border-color: #fecdd3; }
.badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: #dcfce7;
  color: #166534;
  font-weight: 600;
  font-size: 14px;
}
.badge.ghost { background: #e2e8f0; color: #334155; }
.timeline-bar {
  position: relative;
  height: 10px;
  background-color: #e2e8f0;
  border-radius: 5px;
  overflow: hidden;
}
.timeline-bar .progress { height: 100%; }
.note-marker {
  position: absolute;
  top: -3px;
  width: 2px;
  height: 16px;
  background: #f59e0b;
  transform: translateX(-1px);
}
.note-panel {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 15px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
}
.note-form { flex: 0 0 auto; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.note-time { width: 110px; }
.note-form .note-text { flex: 1 1 320px; min-width: 220px; }
.note-panel .input {
  font-size: 16px;
}
.note-list {
  flex: 1;
  min-height: 0;
  margin-top: 10px;
  padding-right: 4px;
  display: grid;
  gap: 8px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
.note-list.is-empty {
  display: flex;
  align-items: center;
  justify-content: center;
}
.note-empty {
  color: #94a3b8;
  font-size: 16px;
  font-weight: 700;
  text-align: center;
}
.note-list::-webkit-scrollbar,
.phase-steps-list::-webkit-scrollbar {
  width: 8px;
}
.note-list::-webkit-scrollbar-thumb,
.phase-steps-list::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: #cbd5e1;
}
.note-list::-webkit-scrollbar-track,
.phase-steps-list::-webkit-scrollbar-track {
  background: transparent;
}
.note-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 11px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}
.note-row:hover {
  border-color: #bfdbfe;
  background: #f8fafc;
}
.note-row.active-loop {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}
.note-time-label { font-weight: 800; color: #0f172a; font-size: 16px; }
.note-text {
  margin-top: 3px;
  color: #334155;
  font-size: 16px;
  line-height: 1.6;
}
.note-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.loop-chip {
  padding: 4px 8px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 800;
  white-space: nowrap;
}
.note-delete {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecdd3;
  border-radius: 8px;
  padding: 6px 8px;
}
.chart-container { height: 250px; }
.instrument-empty,
.instrument-loading {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  background: #f8fafc;
  color: #64748b;
  text-align: center;
}
.instrument-chart {
  flex: 1;
  min-height: 0;
  height: 100%;
  max-height: none;
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 12px;
}
.instrument-y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 8px 0 46px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  text-align: right;
}
.instrument-plot {
  position: relative;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  align-items: end;
  gap: 12px;
  padding: 8px 0 0;
}
.instrument-grid-line {
  position: absolute;
  left: 0;
  right: 0;
  border-top: 1px dashed #cbd5e1;
  pointer-events: none;
}
.instrument-grid-line.top { top: 8px; }
.instrument-grid-line.middle { top: 47%; }
.instrument-bar-item {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}
.instrument-bar-shell {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.instrument-bar {
  width: min(40px, 72%);
  min-height: 4px;
  border-radius: 8px 8px 2px 2px;
  transition: height 0.7s ease;
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.12);
}
.instrument-duration {
  margin-top: 9px;
  font-size: 14px;
  font-weight: 800;
  color: #0f172a;
}
.instrument-label {
  margin-top: 3px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
}
.annotation-list { margin-top: 14px; border-top: 1px dashed #e2e8f0; padding-top: 10px; display: grid; gap: 10px; }
.annotation-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}
.annotation-row.active { box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15); border-color: #bfdbfe; }
.dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.time-chip { background: #e0f2fe; padding: 4px 8px; border-radius: 8px; display: inline-flex; align-items: center; }
.seg-mini {
  font-size: 12px;
  padding: 6px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #f8fafc;
  font-weight: 600;
}
.seg-mini.danger { background: #fef2f2; border-color: #fecdd3; color: #b91c1c; }
.empty { margin-top: 12px; padding: 12px; border: 1px dashed #e5e7eb; border-radius: 10px; color: #64748b; font-size: 13px; background: #f8fafc; }
.phase-analysis-card {
  grid-column: 1 / -1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 0;
}
.phase-analysis-card > .flex {
  flex: 0 0 auto;
}
.phase-analysis-card .phase-progress-panel {
  flex: 0 0 auto;
}
.phase-analysis-card .empty,
.phase-analysis-card .status-box {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.phase-steps-list {
  flex: 1;
  min-height: 0;
  max-height: none;
  height: auto;
  padding-right: 6px;
  display: grid;
  gap: 12px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
.analysis-assistant-panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
}
.assistant-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  padding: 8px;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
}
.assistant-tab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 0;
  padding: 9px 8px;
  border: 1px solid transparent;
  border-radius: 10px;
  color: #64748b;
  font-size: 13px;
  font-weight: 800;
  transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}
.assistant-tab.active {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1d4ed8;
}
.assistant-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 15px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}
.phase-analysis-content {
  overflow: hidden;
}
.phase-header {
  flex: 0 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}
.phase-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
  font-size: 17px;
  font-weight: 900;
}
.phase-meta {
  margin-top: 4px;
  color: #64748b;
  font-size: 16px;
  font-weight: 700;
}
.phase-empty {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.phase-step-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 13px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}
.phase-step-index {
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 16px;
  font-weight: 900;
}
.phase-step-body {
  min-width: 0;
  flex: 1;
}
.phase-step-play {
  flex: 0 0 auto;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 9px;
  background: #eff6ff;
  color: #2563eb;
}
.assistant-content::-webkit-scrollbar,
.qa-messages::-webkit-scrollbar {
  width: 8px;
}
.assistant-content::-webkit-scrollbar-thumb,
.qa-messages::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: #cbd5e1;
}
.assistant-content::-webkit-scrollbar-track,
.qa-messages::-webkit-scrollbar-track {
  background: transparent;
}
.ai-report-gate {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  border: 1px dashed #bfdbfe;
  border-radius: 12px;
  background: #f8fbff;
  text-align: center;
}
.ai-report-gate p {
  max-width: 260px;
  color: #64748b;
  font-size: 16px;
  line-height: 1.6;
}
.ai-report-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 144px;
  padding: 10px 14px;
  border-radius: 10px;
  background: #2563eb;
  color: #fff;
  font-size: 15px;
  font-weight: 900;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.22);
}
.ai-report-button:disabled {
  cursor: wait;
  opacity: 0.86;
}
.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}
.report-title {
  min-width: 0;
  color: #0f172a;
  font-size: 16px;
  font-weight: 900;
  line-height: 1.35;
}
.report-status {
  flex: 0 0 auto;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 800;
  white-space: nowrap;
}
.report-section {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #fff;
}
.report-section h4 {
  margin-bottom: 8px;
  color: #334155;
  font-size: 14px;
  font-weight: 900;
}
.report-section p {
  color: #475569;
  font-size: 14px;
  line-height: 1.65;
}
.report-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.report-metric {
  min-width: 0;
  padding: 9px;
  border-radius: 9px;
  background: #f8fafc;
}
.report-metric span {
  display: block;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}
.report-metric strong {
  display: block;
  margin-top: 3px;
  color: #0f172a;
  font-size: 15px;
}
.report-list {
  display: grid;
  gap: 8px;
}
.report-list-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.report-list-row span {
  flex: 0 0 auto;
  padding: 3px 6px;
  border-radius: 7px;
  background: #e0f2fe;
  color: #0369a1;
  font-size: 11px;
  font-weight: 800;
}
.report-list-row p {
  min-width: 0;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.45;
}
.report-empty {
  color: #64748b;
  font-size: 13px;
}
.report-bullets {
  display: grid;
  gap: 7px;
  margin: 0;
  padding-left: 16px;
  color: #475569;
  font-size: 14px;
  line-height: 1.6;
}
.report-bullets li::marker {
  color: #2563eb;
}
.qa-content {
  gap: 10px;
}
.qa-messages {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  overscroll-behavior: contain;
}
.qa-message {
  max-width: 92%;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.55;
}
.qa-message.assistant {
  align-self: flex-start;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #334155;
}
.qa-message.user {
  align-self: flex-end;
  background: #2563eb;
  color: #fff;
}
.qa-input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.qa-input {
  min-width: 0;
  flex: 1;
}
.qa-send {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: #2563eb;
  color: #fff;
}
@media (max-width: 1599px) {
  .analysis-main-grid {
    grid-template-columns: minmax(440px, 0.92fr) minmax(360px, 0.7fr) minmax(340px, 0.58fr);
  }
  .analysis-assistant-panel {
    height: 100%;
  }
  .analysis-side-panel {
    height: 100%;
  }
}
@media (max-width: 1023px) {
  .analysis-page {
    height: auto;
    overflow: visible;
  }
  .analysis-main-grid {
    grid-template-columns: 1fr;
    height: auto;
  }
  .analysis-video-column {
    overflow: visible;
  }
  .note-panel {
    flex: 0 0 auto;
    height: 280px;
  }
  .phase-analysis-card,
  .analysis-assistant-panel {
    grid-column: auto;
    grid-row: auto;
    height: min(560px, calc(100vh - 160px));
  }
  .analysis-side-panel {
    display: flex;
    overflow: visible;
  }
  .middle-video-aligned-panel {
    flex: 0 0 auto;
    height: auto;
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: auto;
    overflow: visible;
  }
}
@media (min-width: 1600px) {
  .note-form {
    flex-wrap: nowrap;
  }
}
.analysis-page :deep(button),
.analysis-page :deep(input),
.analysis-page :deep(select),
.analysis-page :deep(textarea),
.analysis-page .input,
.analysis-page .btn-secondary,
.analysis-page .btn-ghost,
.analysis-page .compact {
  font-size: 16px !important;
  line-height: 1.5;
}
.analysis-page .text-xs {
  font-size: 14px !important;
  line-height: 1.5;
}
.analysis-page .text-sm {
  font-size: 16px !important;
  line-height: 1.6;
}
.analysis-page h2,
.analysis-page .text-xl {
  font-size: 24px !important;
  line-height: 1.35;
}
.analysis-page h3,
.analysis-page .text-lg {
  font-size: 21px !important;
  line-height: 1.38;
}
.assistant-tab {
  font-size: 17px !important;
  padding: 12px 12px;
}
.report-status,
.report-list-row span {
  font-size: 14px !important;
}
.report-title,
.report-section h4,
.report-metric strong,
.overview-card .font-bold {
  font-size: 18px !important;
  line-height: 1.4;
}
.report-metric span,
.overview-card p:first-child,
.instrument-label,
.instrument-y-axis,
.loop-chip,
.note-empty,
.report-empty {
  font-size: 15px !important;
  line-height: 1.5;
}
.report-section,
.qa-message,
.phase-step-row,
.overview-card,
.note-row {
  font-size: 16px !important;
}
.report-section p,
.report-bullets,
.qa-message,
.phase-step-row p,
.note-text {
  font-size: 16px !important;
  line-height: 1.7;
}
.phase-title {
  font-size: 21px !important;
}
.phase-meta,
.phase-stage,
.phase-message {
  font-size: 15px !important;
  line-height: 1.55;
}
.instrument-duration {
  font-size: 15px !important;
}
.instrument-label,
.instrument-y-axis {
  font-size: 14px !important;
}
.annotation-timer,
.seg-btn,
.badge,
.note-panel .input,
.qa-input,
.qa-send,
.ai-report-button,
.phase-step-play,
.note-delete {
  font-size: 16px !important;
}
.phase-step-body h3,
.phase-step-body .font-medium {
  font-size: 17px !important;
  line-height: 1.45;
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
.status-box {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 13px;
}
.status-box.success { background: #ecfdf3; color: #166534; border: 1px solid #bbf7d0; }
.status-box.error { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.phase-progress-panel {
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #eff6ff;
}
.phase-stage {
  font-weight: 800;
  color: #1e3a8a;
}
.phase-message {
  margin-top: 2px;
  font-size: 13px;
  color: #475569;
}
.phase-percent {
  font-weight: 800;
  color: #2563eb;
}
.phase-progress-track {
  height: 8px;
  margin-top: 12px;
  overflow: hidden;
  border-radius: 999px;
  background: #dbeafe;
}
.phase-progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
  transition: width 0.2s ease;
}
</style>
