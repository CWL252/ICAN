import { createRouter, createWebHistory } from 'vue-router'

import Splash from '../views/Splash.vue'
import Home from '../views/Home.vue'
import Analysis from '../views/Analysis.vue'
import Login from '../views/Login.vue'
import Community from '../views/Community.vue'
import ProjectDetail from '../views/ProjectDetail.vue'
import PostDetail from '../views/PostDetail.vue'
import MyCommunity from '../views/MyCommunity.vue'
import AuthorProfile from '../views/AuthorProfile.vue'
import Downloads from '../views/Downloads.vue'
import Feedback from '../views/Feedback.vue'

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
  },
  {
    path: '/community',
    name: 'Community',
    component: Community,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/community/projects/:id',
    name: 'ProjectDetail',
    component: ProjectDetail,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/community/posts/:id',
    name: 'PostDetail',
    component: PostDetail,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/community/mine',
    name: 'MyCommunity',
    component: MyCommunity,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/community/users/:id',
    name: 'AuthorProfile',
    component: AuthorProfile,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/community/downloads',
    name: 'Downloads',
    component: Downloads,
    meta: {
      requiresAuth: true
    }
  },
  {
    path: '/community/feedback',
    name: 'Feedback',
    component: Feedback,
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