<template>
  <div
    :class="[
      'sidebar bg-gray-100 text-gray-800 p-4 h-screen flex flex-col justify-between transition-width duration-300 ease-in-out',
      collapsed ? 'w-20' : 'w-72'
    ]"
  >
    <!-- Top Section -->
    <div>
      <!-- Logo and Title -->
      <div class="flex items-center mb-6 justify-between">
        <div class="flex">
          <button v-if="!collapsed">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke-width="1.5"
              stroke="currentColor"
              class="size-6"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z"
              />
            </svg>
          </button>
          <div v-if="!collapsed" class="text-base font-semibold ml-2">AI RAG Chatbot</div>
        </div>
        <button @click="toggleCollapse" :class="{ 'mx-auto': collapsed }">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="{1.5}"
            stroke="currentColor"
            class="w-5 h-5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m18.75 4.5-7.5 7.5 7.5 7.5m-6-15L5.25 12l7.5 7.5"
            />
          </svg>
        </button>
      </div>

      <!-- New Thread Button -->
      <hr class="my-2 border-gray-300" />
      <button
        @click="createThread()"
        class="flex items-center bg-white text-gray-800 py-2 px-3 mb-4 rounded-lg w-full"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="size-5"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        <span class="ml-2" v-if="!collapsed">New thread</span>
      </button>
      <router-link
        to="/manage-pdfs"
        class="flex items-center bg-white text-gray-800 py-2 px-3 mb-4 rounded-lg w-full"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="1.5"
          stroke="currentColor"
          class="size-5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"
          />
        </svg>
        <span class="ml-2" v-if="!collapsed">Manage PDFs</span>
      </router-link>

      <!-- Menu Items -->
      <ul>
        <li
          class="flex items-center mb-3 cursor-pointer hover:bg-gray-200 py-2 px-3 rounded-lg"
          @click="navigateToHome"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="size-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
            />
          </svg>
          <span class="ml-2" v-if="!collapsed">Home</span>
        </li>
        <li class="flex items-center mb-3 cursor-pointer hover:bg-gray-200 py-2 px-3 rounded-lg">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="size-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99"
            />
          </svg>
          <span class="ml-2" v-if="!collapsed">Syncs</span>
        </li>
        <li class="flex items-center mb-3 cursor-pointer hover:bg-gray-200 py-2 px-3 rounded-lg">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="size-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3"
            />
          </svg>
          <span class="ml-2" v-if="!collapsed">Models</span>
        </li>
        <hr class="my-10 border-gray-300" />
        <li class="flex items-center mb-3 cursor-pointer hover:bg-gray-200 py-2 px-3 rounded-lg">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="size-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z"
            />
          </svg>
          <span class="ml-2" v-if="!collapsed">Threads</span>
        </li>
        <div v-if="!collapsed" class="overflow-y-auto max-h-52">
          <li
            v-for="thread in threads"
            :key="thread.session_id"
            @click="navigateToThread(thread.session_id)"
            class="flex items-center justify-between mb-3 cursor-pointer hover:bg-gray-200 py-2 px-3 rounded-lg"
          >
            {{ thread.title }}
            <button v-if="!collapsed" @click.stop="deleteThread(thread.session_id)">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.5"
                stroke="currentColor"
                class="size-5"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
                />
              </svg>
            </button>
          </li>
        </div>
      </ul>
    </div>

    <!-- Bottom Section -->
    <div>
      <ul>
        <li class="flex items-center mb-3 cursor-pointer hover:bg-gray-200 py-2 px-3 rounded-lg">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="size-5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
            />
          </svg>
          <span class="ml-2" v-if="!collapsed">Settings</span>
        </li>
      </ul>
      <hr class="my-2 border-gray-300" />

      <!-- User Section -->
      <div class="flex items-center mt-4">
        <div
          class="bg-yellow-500 rounded-full w-7 h-7 flex items-center justify-center text-white font-light text-xs"
          :class="{ 'mx-auto': collapsed }"
        >
          DE
        </div>
        <span v-if="!collapsed" class="ml-2">Demo User</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ElMessageBox } from 'element-plus'

export default {
  name: 'SidebarComponent',
  props: {
    threads: Array
  },
  data() {
    return {
      collapsed: false,
      pdfsAvailable: false
    }
  },
  async created() {
    await this.checkPDFsAvailability()
  },
  methods: {
    async checkPDFsAvailability() {
      try {
        const pdfResponse = await fetch('http://127.0.0.1:8000/list_pdfs')
        const pdfs = await pdfResponse.json()
        this.pdfsAvailable = pdfs.length > 0
      } catch (error) {
        console.error('Error checking PDFs availability:', error)
        this.pdfsAvailable = false
      }
    },
    async createThread() {
      await this.checkPDFsAvailability()
      if (!this.pdfsAvailable) {
        ElMessageBox.alert(
          'No PDFs available. Please upload at least one PDF to start chatting.',
          'Alert',
          {
            confirmButtonText: 'OK',
            callback: () => {
              this.$router.push('/manage-pdfs')
            }
          }
        )
      } else {
        this.$emit('createThread')
      }
    },
    async navigateToHome() {
      await this.checkPDFsAvailability()
      if (!this.pdfsAvailable) {
        ElMessageBox.alert(
          'No PDFs available. Please upload at least one PDF to start chatting.',
          'Alert',
          {
            confirmButtonText: 'OK',
            callback: () => {
              this.$router.push('/manage-pdfs')
            }
          }
        )
      } else {
        this.$emit('home')
        this.$router.push('/')
      }
    },
    async navigateToThread(threadId) {
      await this.checkPDFsAvailability()
      if (!this.pdfsAvailable) {
        ElMessageBox.alert(
          'No PDFs available. Please upload at least one PDF to start chatting.',
          'Alert',
          {
            confirmButtonText: 'OK',
            callback: () => {
              this.$router.push('/manage-pdfs')
            }
          }
        )
      } else {
        this.$router.push(`/chat/${threadId}`)
      }
    },
    async deleteThread(threadId) {
      try {
        const response = await fetch(`http://127.0.0.1:8000/delete_chat_session/${threadId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error('Error deleting PDF.')
        }
        this.$emit('threadDeleted', threadId)
        this.$router.push('/')
      } catch (error) {
        console.error('Error deleting thread:', error)
      }
    },
    toggleCollapse() {
      this.collapsed = !this.collapsed
    }
  },
  beforeRouteEnter(to, from, next) {
    next(async (vm) => {
      await vm.checkPDFsAvailability()
    })
  }
}
</script>
