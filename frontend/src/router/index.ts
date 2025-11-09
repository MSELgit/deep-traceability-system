// frontend/src/router/index.ts

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../views/ProjectList.vue')
  },
  {
    path: '/project/:id',
    name: 'ProjectDetail',
    component: () => import('../views/ProjectDetail.vue')
  },
  {
    path: '/project/:id/stakeholders',
    name: 'Stakeholders',
    component: () => import('../views/StakeholderManagement.vue')
  },
  {
    path: '/project/:id/performances',
    name: 'Performances',
    component: () => import('../views/PerformanceManagement.vue')
  },
  {
    path: '/project/:id/design-cases',
    name: 'DesignCases',
    component: () => import('../views/DesignCaseList.vue')
  },
  {
    path: '/project/:id/mountain',
    name: 'Mountain',
    component: () => import('../views/MountainView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
