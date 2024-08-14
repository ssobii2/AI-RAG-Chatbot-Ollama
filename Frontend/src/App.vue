<template>
  <div class="flex h-screen">
    <SidebarComponent
      :threads="threads"
      @selectThread="selectThread"
      @createThread="createThread"
    />
    <ChatComponent :sessionId="selectedThreadId" @updateSession="updateSessionId" />
  </div>
</template>

<script>
import SidebarComponent from './components/SidebarComponent.vue'
import ChatComponent from './components/ChatComponent.vue'

export default {
  name: 'App',
  components: {
    SidebarComponent,
    ChatComponent
  },
  data() {
    return {
      threads: [],
      selectedThreadId: null
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
        this.updateSessionId(result.session_id)
      } catch (error) {
        console.error('Error creating chat session:', error)
      }
    },
    selectThread(threadId) {
      this.selectedThreadId = threadId
    },
    updateSessionId(newSessionId) {
      if (!this.threads.includes(newSessionId)) {
        this.threads.push(newSessionId)
      }
      this.selectedThreadId = newSessionId
    }
  }
}
</script>
