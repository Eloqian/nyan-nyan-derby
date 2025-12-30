import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import GroupDrawCeremony from '../components/GroupDrawCeremony.vue'
import RefereeDashboard from '../views/RefereeDashboard.vue'
import StageStandings from '../views/standings/StageStandings.vue'

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
  },
  {
    path: '/standings/:stageId?',
    name: 'StageStandings',
    component: StageStandings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
