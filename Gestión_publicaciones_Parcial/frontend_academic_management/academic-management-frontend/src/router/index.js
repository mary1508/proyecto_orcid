// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/countries',
    name: 'Countries',
    component: () => import('@/views/Countries.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/keywords',
    name: 'Keywords',
    component: () => import('@/views/Keywords.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/publication-types',
    name: 'PublicationTypes',
    component: () => import('@/views/PublicationTypes.vue'),
    meta: { requiresAuth: true }
  },
  
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // Inicializar autenticación si no está inicializada
  if (!authStore.user && localStorage.getItem('access_token')) {
    authStore.initializeAuth()
  }
  
  // Verificar rutas que requieren autenticación
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // Verificar rutas para invitados (como login)
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router