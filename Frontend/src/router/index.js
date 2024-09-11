import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import ChatComponent from '@/components/ChatComponent.vue'
import FilesComponent from '@/components/FilesComponent.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'home',
        component: ChatComponent,
        props: true
      },
      {
        path: 'chat/:sessionId',
        name: 'chat',
        component: ChatComponent,
        props: true
      },
      {
        path: 'manage-files',
        name: 'files',
        component: FilesComponent,
        props: true
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
