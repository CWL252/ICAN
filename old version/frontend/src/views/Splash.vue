<template>
  <div class="splash-page">
    <div class="splash-center">
      <div class="splash-logo">
        <i class="fas fa-stethoscope"></i>
      </div>
      <h1>SurgReview</h1>
      <p>交互式智慧外科平台</p>
      <div class="splash-progress-shell">
        <div class="splash-progress-bar" :style="{ width: `${progress}%` }"></div>
      </div>
      <span class="splash-progress-text">{{ progress }}%</span>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const progress = ref(0)
let progressTimer = null

onMounted(() => {
  progressTimer = window.setInterval(() => {
    progress.value = Math.min(100, progress.value + 1)
    if (progress.value >= 100) {
      window.clearInterval(progressTimer)
      progressTimer = null
      window.setTimeout(() => {
        router.replace('/home')
      }, 240)
    }
  }, 50)
})

onBeforeUnmount(() => {
  if (progressTimer) {
    window.clearInterval(progressTimer)
    progressTimer = null
  }
})
</script>

<style scoped>
.splash-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 30%, rgba(59, 130, 246, 0.12), transparent 34%),
    linear-gradient(135deg, #f8fafc 0%, #eef6ff 48%, #f8fafc 100%);
}
.splash-center {
  width: min(420px, calc(100vw - 48px));
  text-align: center;
}
.splash-logo {
  width: 88px;
  height: 88px;
  margin: 0 auto 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  background: #2563eb;
  color: #fff;
  font-size: 38px;
  box-shadow: 0 18px 36px rgba(37, 99, 235, 0.26);
}
.splash-center h1 {
  margin: 0;
  color: #0f172a;
  font-size: 38px;
  font-weight: 900;
  letter-spacing: 0;
}
.splash-center p {
  margin: 8px 0 28px;
  color: #64748b;
  font-size: 15px;
  font-weight: 700;
}
.splash-progress-shell {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: #dbeafe;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.08);
}
.splash-progress-bar {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2563eb, #0ea5e9);
  transition: width 0.08s ease;
}
.splash-progress-text {
  display: inline-block;
  margin-top: 12px;
  color: #2563eb;
  font-size: 13px;
  font-weight: 900;
}
</style>
