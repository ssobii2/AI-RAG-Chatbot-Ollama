<template>
  <div class="flex h-screen">
    <SidebarComponent
      :threads="threads"
      @createThread="createThread"
      @selectThread="selectThread"
      @home="resetChatState"
      @threadDeleted="updateThreads"
    />
    <router-view
      :key="currentRoute"
      :threads="threads"
      :createThread="createThread"
      @updateSession="updateSessionId"
      @updateTitle="updateTitle"
    ></router-view>
  </div>
</template>

<script>
import SidebarComponent from './SidebarComponent.vue'

export default {
  name: 'MainLayout',
  components: {
    SidebarComponent
  },
  data() {
    return {
      threads: [],
      currentRoute: this.$route.fullPath
    }
  },
  watch: {
    $route(to) {
      this.currentRoute = to.fullPath
    }
  },
  async created() {
    try {
      const response = await fetch('http://127.0.0.1:8000/chat_sessions')
      const sessions = await response.json()
      this.threads = sessions
    } catch (error) {
      console.error('Error fetching chat sessions:', error)
    }
  },
  methods: {
    async createThread() {
      try {
        const response = await fetch('http://127.0.0.1:8000/create_chat_session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        const result = await response.json()
        this.threads.push({ session_id: result.session_id, title: result.title })
        this.$router.push(`/chat/${result.session_id}`)
      } catch (error) {
        console.error('Error creating chat session:', error)
      }
    },
    selectThread(threadId) {
      this.$router.push(`/chat/${threadId}`)
    },
    resetChatState() {
      this.$router.push('/')
    },
    updateSessionId(newSessionId) {
      if (!this.threads.find((thread) => thread.session_id === newSessionId)) {
        this.threads.push(newSessionId)
      }
    },
    updateTitle({ session_id, title }) {
      const thread = this.threads.find((thread) => thread.session_id === session_id)
      if (thread) {
        thread.title = title
      }
    },
    updateThreads(threadId) {
      this.threads = this.threads.filter((thread) => thread.session_id !== threadId)
    }
  }
}
</script>