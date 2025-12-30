import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import GroupDrawCeremony from '../components/GroupDrawCeremony.vue'
import RefereeDashboard from '../views/RefereeDashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
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

export default router
