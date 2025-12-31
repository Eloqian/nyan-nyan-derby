import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import GroupDrawCeremony from '../components/GroupDrawCeremony.vue'
import RefereeDashboard from '../views/RefereeDashboard.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import { useAuthStore } from '../stores/auth'

import LiveTournament from '../views/LiveTournament.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/live',
    name: 'LiveTournament',
    component: LiveTournament
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/ceremony',
    name: 'GroupDrawCeremony',
    component: GroupDrawCeremony
  },
  {
    path: '/referee/:stageId?', // Optional stageId param
    name: 'RefereeDashboard',
    component: RefereeDashboard
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _, next) => {
  const auth = useAuthStore()
  
  // Attempt to restore user session if token exists but user is null
  if (auth.token && !auth.user) {
     await auth.fetchUser()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
