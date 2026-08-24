<template>
  <div v-if="points.length === 0" class="growth-curve-empty">
    暂无数据
  </div>
  <div v-else-if="points.length === 1" class="growth-curve-empty">
    再上传 1 个同小类视频后展示成长曲线
  </div>
  <div v-else class="growth-curve">
    <svg
      :viewBox="`0 0 ${W} ${H}`"
      class="w-full h-auto"
      role="img"
      aria-label="视频时长成长曲线"
    >
      <!-- 水平网格线(最大值 / 中间 / 最小值) -->
      <line
        v-for="gy in gridYs"
        :key="gy.y"
        :x1="PAD_L"
        :y1="gy.y"
        :x2="W - PAD_R"
        :y2="gy.y"
        class="growth-grid-line"
      />
      <!-- Y 轴刻度标签 -->
      <text
        v-for="gy in gridYs"
        :key="'t' + gy.y"
        :x="PAD_L - 6"
        :y="gy.y + 3.5"
        text-anchor="end"
        class="growth-axis-label"
      >
        {{ gy.label }}
      </text>
      <!-- 折线:y 为视频时长,越短越熟练,下行代表进步 -->
      <polyline
        :points="linePoints"
        fill="none"
        stroke="#2563eb"
        stroke-width="2"
        stroke-linejoin="round"
        stroke-linecap="round"
      />
      <!-- 数据点 -->
      <circle
        v-for="(p, i) in plotPoints"
        :key="i"
        :cx="p.x"
        :cy="p.y"
        r="3.5"
        fill="#2563eb"
      >
        <title>{{ p.label }} · 时长 {{ p.durationText }}</title>
      </circle>
      <!-- X 轴首末日期标签 -->
      <text
        :x="plotPoints[0].x"
        :y="H - 8"
        text-anchor="middle"
        class="growth-axis-label"
      >
        {{ plotPoints[0].label }}
      </text>
      <text
        :x="plotPoints[plotPoints.length - 1].x"
        :y="H - 8"
        text-anchor="middle"
        class="growth-axis-label"
      >
        {{ plotPoints[plotPoints.length - 1].label }}
      </text>
    </svg>
    <p class="growth-hint">
      <i class="fas fa-arrow-trend-down mr-1"></i>
      纵轴为视频时长,时长越短表示越熟练,曲线下行代表进步
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  // [{ label: '08-12', time: 1723000000000, durationSeconds: 900, durationText: '15:00' }]
  points: {
    type: Array,
    default: () => []
  }
})

const W = 360
const H = 96
const PAD_L = 46
const PAD_R = 10
const PAD_T = 8
const PAD_B = 18
const PLOT_W = W - PAD_L - PAD_R
const PLOT_H = H - PAD_T - PAD_B

const plotPoints = computed(() => {
  const list = props.points
  if (list.length === 0) return []
  const durations = list.map((p) => p.durationSeconds)
  const dMin = Math.min(...durations)
  const dMax = Math.max(...durations)
  const span = dMax - dMin
  const xMid = PAD_L + PLOT_W / 2
  const yMid = PAD_T + PLOT_H / 2
  // x 轴按真实上传时间线性排布:时间相同则点重合,时间相近则靠拢
  const times = list.map((p) => Number(p.time) || 0)
  const tMin = Math.min(...times)
  const tMax = Math.max(...times)

  return list.map((p, i) => {
    let x
    if (list.length === 1 || tMax === tMin) {
      x = xMid
    } else {
      const t = (times[i] - tMin) / (tMax - tMin)
      x = PAD_L + t * PLOT_W
    }
    const y = span === 0 ? yMid : PAD_T + (1 - (p.durationSeconds - dMin) / span) * PLOT_H
    return { ...p, x, y }
  })
})

const linePoints = computed(() =>
  plotPoints.value.map((p) => `${p.x},${p.y}`).join(' ')
)

const gridYs = computed(() => {
  if (plotPoints.value.length < 2) return []
  const ys = plotPoints.value.map((p) => p.y)
  const yMax = Math.max(...ys)
  const yMin = Math.min(...ys)
  const yMid = (yMax + yMin) / 2
  const durs = props.points.map((p) => p.durationSeconds)
  const dMin = Math.min(...durs)
  const dMax = Math.max(...durs)
  const fmt = (s) => {
    const h = Math.floor(s / 3600)
    const m = Math.floor((s % 3600) / 60)
    const sec = Math.floor(s % 60)
    return h > 0
      ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
      : `${m}:${String(sec).padStart(2, '0')}`
  }
  return [
    { y: yMin, label: fmt(dMax) },
    { y: yMid, label: fmt((dMax + dMin) / 2) },
    { y: yMax, label: fmt(dMin) }
  ]
})
</script>

<style scoped>
.growth-curve-empty {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: #94a3b8;
  background: #f8fafc;
  border-radius: 10px;
}

.growth-grid-line {
  stroke: #e2e8f0;
  stroke-width: 1;
}

.growth-axis-label {
  font-size: 10px;
  fill: #94a3b8;
}

.growth-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
  text-align: center;
}
</style>
