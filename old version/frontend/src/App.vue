<template>
  <div class="min-h-screen flex flex-col">
    <nav v-if="!isSplashPage" class="bg-white shadow-sm py-4 sticky top-0 z-50">
      <div class="app-shell px-4 sm:px-6 lg:px-8 flex justify-between items-center gap-4 flex-wrap">
        <div class="flex items-center">
          <i class="fas fa-stethoscope text-2xl text-blue-600 mr-2"></i>
          <div>
            <span class="text-xl font-bold text-gray-800">SurgReview</span>
            <p class="text-xs text-gray-500">交互式智慧外科平台——赋能外科质控、科研与培训</p>
          </div>
        </div>
        <div class="flex space-x-4 text-sm">
          <router-link to="/home" class="btn-secondary">
          <i class="fas fa-house mr-2"></i>首页</router-link>
        </div>
      </div>
    </nav>


    <main class="flex-1">
      <router-view />
    </main>

    <footer v-if="!isSplashPage && !isAnalysisPage" class="bg-gray-900 text-white py-6 mt-8">
      <div class="app-shell px-4 sm:px-6 lg:px-8 text-center text-gray-400 text-sm">
        © 2026 SurgReview. 专注于数据驱动的外科见解。
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isSplashPage = computed(() => route.name === 'Splash')
const isAnalysisPage = computed(() => route.name === 'Analysis')
</script>

<style scoped>
.app-shell {
  width: 100%;
  max-width: none;
}
</style>
