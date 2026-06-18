import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/validating/:task_id',
    name: 'Validating',
    component: () => import('../views/Validating.vue')
  },
  {
    path: '/report/:task_id',
    name: 'Report',
    component: () => import('../views/Report.vue')
  },
  {
    path: '/crawler/auth',
    name: 'CrawlerAuth',
    component: () => import('../views/CrawlerAuth.vue')
  },
  {
    path: '/crawler/task',
    name: 'CrawlerTask',
    component: () => import('../views/CrawlerTask.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
