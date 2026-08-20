import { createRouter, createWebHistory } from 'vue-router'

import Splash from '../views/Splash.vue'
import Home from '../views/Home.vue'
import Analysis from '../views/Analysis.vue'
import Login from '../views/Login.vue'

import { getToken } from '../lib/auth'

const routes = [
  {
    path: '/',
    name: 'Splash',
    component: Splash,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: Analysis,
    meta: {
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const loggedIn = getToken()

  if (to.meta.requiresAuth && !loggedIn) {
    return {
      name: 'Login'
    }
  }

  if (to.name === 'Login' && loggedIn) {
    return {
      name: 'Home'
    }
  }

  return true
})

export default router