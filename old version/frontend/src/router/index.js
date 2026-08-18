import { createRouter, createWebHistory } from 'vue-router'
import Splash from '../views/Splash.vue'
import Home from '../views/Home.vue'
import Analysis from '../views/Analysis.vue'

const routes = [
  { path: '/', name: 'Splash', component: Splash },
  { path: '/home', name: 'Home', component: Home },
  { path: '/analysis', name: 'Analysis', component: Analysis },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
