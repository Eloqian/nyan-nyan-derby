import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import GroupDrawCeremony from '../components/GroupDrawCeremony.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
