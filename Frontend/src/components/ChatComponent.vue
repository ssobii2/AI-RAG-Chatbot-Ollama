<template>
  <div class="flex flex-col justify-between items-center h-screen w-full bg-zinc-800 text-white">
    <!-- Central Content -->
    <div v-if="!hasSentMessage && !loading" class="flex flex-col justify-center items-center flex-grow">
      <div class="text-center mb-8">
        <div class="inline-block mb-6 rounded-lg">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
            stroke="currentColor" class="size-20 mx-auto">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
          </svg>
        </div>
        <h1 class="text-4xl font-bold mb-4">Chat with me</h1>
        <p class="max-w-md mb-2">Chat with Meta's Latest AI model - Llama 3.1</p>
        <p class="max-w-md mb-4">
          Create a new Thread or Click below to start chatting
        </p>
        <button class="mt-6 py-2 px-4 bg-zinc-800 text-white border border-gray-400 rounded-md hover:bg-zinc-900"
          @click="startChat">
          Get started with a model
        </button>
      </div>
    </div>

    <!-- Chat Area -->
    <div v-if="hasSentMessage || chatHistory.length > 0"
      class="w-8/12 p-4 flex flex-col mb-2 mt-10 rounded-md overflow-y-auto">
      <!-- Display Chat History -->
      <div v-for="(message, index) in chatHistory" :key="index"
        :class="message.role === 'user' ? 'text-right mb-4' : 'text-left mb-4'">
        <div :class="message.role === 'ai' ? 'flex items-start' : ''">
          <svg v-if="message.role === 'ai'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
            stroke-width="1.5" stroke="currentColor" class="size-6 mr-2 flex-shrink-0">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
          </svg>
          <p :class="message.role === 'user' ? 'bg-zinc-700 text-white' : 'bg-zinc-800 text-white'"
            class="inline-block px-4 py-2 rounded-md">
            {{ message.content }}
          </p>
        </div>
      </div>
      <!-- Loading Indicator -->
      <div v-if="loading" class="text-center mt-4">
        <el-table v-loading="loading" style="width: 100%" element-loading-text="AI is thinking..."
          element-loading-background="#27272A">
          <el-table-column label="AI" />
        </el-table>
        <!-- <p class="inline-block px-4 py-2 rounded-md bg-gray-200 text-gray-800 max-w-xs">
          AI is thinking...
        </p> -->
      </div>
    </div>
    <div v-if="sessionId" class="w-8/12 rounded-md p-4 flex items-center mb-2 relative">
      <textarea v-model="userInput" placeholder="Ask a question or make a request..."
        class="flex-grow p-3 rounded-md border-none bg-zinc-700 resize-none h-32 focus:outline-none"></textarea>
      <!-- <select
        class="bg-white border-2 rounded-md py-2 px-2 absolute bottom-7 left-6 focus:outline-none cursor-pointer"
      >
        <option>Llama 3.1</option>
      </select> -->
      <button @click="sendMessage" :disabled="loading"
        class="bg-zinc-800 border border-gray-400 p-3 rounded-md hover:bg-zinc-900 absolute bottom-7 right-6">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"
          class="size-5">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
        </svg>
      </button>

      <!-- Audio Recording Button -->
      <button @click="toggleRecording"
        :class="recording ? 'bg-red-500 hover:bg-red-600' : 'bg-zinc-800 hover:bg-zinc-900'"
        class="p-3 border border-gray-400 rounded-md absolute bottom-7 left-6">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"
          class="size-5">
          <path stroke-linecap="round" stroke-linejoin="round"
            d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
import { ElMessageBox } from 'element-plus'

export default {
  name: 'ChatComponent',
  props: {
    sessionId: {
      type: String,
      default: null
    },
    threads: Array,
    createThread: Function
  },
  data() {
    return {
      userInput: '',
      chatHistory: [],
      hasSentMessage: false,
      loading: false,
      recording: false,
      mediaRecorder: null,
      audioChunks: [],
      mediaRecorderState: null,
      websocket: null
    }
  },
  watch: {
    sessionId: {
      handler(newSessionId) {
        if (newSessionId) {
          this.loadChatHistory(newSessionId)
        }
      },
      immediate: true
    }
  },
  mounted() {
    if (this.sessionId) {
      // Open WebSocket connection
      this.openWebSocket()
    }
  },
  beforeUnmount() {
    // Clean up WebSocket connection
    if (this.websocket) {
      this.websocket.close()
    }
  },
  created() {
    if (this.sessionId) {
      this.loadChatHistory(this.sessionId)
    } else {
      this.checkFilesAvailability()
    }
  },
  methods: {
    async startChat() {
      await this.createThread()
    },
    async checkFilesAvailability() {
      try {
        const filesResponse = await fetch('http://127.0.0.1:8000/list_files')
        const files = await filesResponse.json()

        if (files.length === 0) {
          ElMessageBox.alert(
            'No Files available. Please upload at least one File to start chatting.',
            'Alert',
            {
              confirmButtonText: 'OK',
              callback: () => {
                this.$router.push('/manage-files')
              }
            }
          )
        }
      } catch (error) {
        console.error('Error checking Files availability:', error)
        this.$router.push('/manage-files')
      }
    },
    async loadChatHistory(sessionId) {
      if (!sessionId) return
      try {
        const response = await fetch(`http://127.0.0.1:8000/chat_history/${sessionId}`)
        const chatHistory = await response.json()
        this.chatHistory = chatHistory.map((msg) => ({
          role: msg.type === 'human' ? 'user' : 'ai',
          content: msg.content
        }))
        this.hasSentMessage = this.chatHistory.length > 0
      } catch (error) {
        console.error('Error loading chat history:', error)
      }
    },
    async sendMessage() {
      if (this.userInput.trim() === '') return;

      this.hasSentMessage = true;
      this.loading = true;

      const userMessage = { role: 'user', content: this.userInput };
      const userInputCopy = this.userInput;
      this.userInput = '';

      let sessionId = this.sessionId;
      try {
        if (!sessionId) {
          const response = await fetch('http://127.0.0.1:8000/create_chat_session', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            }
          });
          const result = await response.json();
          sessionId = result.session_id;
          this.$emit('updateSession', sessionId);
        }

        this.chatHistory.push(userMessage);

        const response = await fetch('http://127.0.0.1:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            query: userInputCopy,
            session_id: sessionId
          })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let aiMessage = { role: 'ai', content: '' };
        this.chatHistory.push(aiMessage);

        let firstChunkReceived = false;

        let done = false;
        while (!done) {
          const { done: readerDone, value } = await reader.read();
          done = readerDone;
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          aiMessage.content += chunk;
          if (!firstChunkReceived) {
            this.loading = false;
            firstChunkReceived = true;
            this.fetchSessionTitle(sessionId);
          }
          this.$forceUpdate();
        }

      } catch (error) {
        console.error('Error:', error);
        this.loading = false;
      }
    },
    async fetchSessionTitle(sessionId) {
      try {
        const response = await fetch(`http://127.0.0.1:8000/session/${sessionId}/title`);
        const result = await response.json();
        const title = result.title;
        this.$emit('updateTitle', { session_id: sessionId, title });
      } catch (error) {
        console.error('Error fetching session title:', error);
      }
    },
    async toggleRecording() {
      if (this.recording) {
        this.stopRecording()
      } else {
        await this.startRecording()
      }
    },
    async startRecording() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        this.mediaRecorder = new MediaRecorder(stream)
        this.audioChunks = []

        // Establish WebSocket connection
        this.openWebSocket()

        // Send audio data when recording stops
        this.mediaRecorder.ondataavailable = (event) => {
          this.audioChunks.push(event.data)
        }

        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' })
          const reader = new FileReader()

          reader.onload = () => {
            const arrayBuffer = reader.result

            // Send the audio data to the backend via WebSocket
            if (this.websocket) {
              this.websocket.send(arrayBuffer)
            }
          }

          reader.readAsArrayBuffer(audioBlob)
        }

        this.mediaRecorder.start()
        this.recording = true
        this.mediaRecorderState = 'recording'
      } catch (error) {
        console.error('Error accessing microphone:', error)
      }
    },
    stopRecording() {
      if (this.mediaRecorder) {
        this.mediaRecorder.stop()
        this.mediaRecorderState = 'stopping'
        this.recording = false
      }
    },
    openWebSocket() {
      if (this.websocket) {
        this.websocket.close()
      }

      this.websocket = new WebSocket(
        `ws://127.0.0.1:8000/ws/audio_chat?session_id=${this.sessionId}`
      )

      this.websocket.onmessage = (event) => {
        // Receive transcription from WebSocket and set it to user input
        this.userInput = event.data
      }

      this.websocket.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }
  }
}
</script>
