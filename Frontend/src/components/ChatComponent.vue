<template>
  <div class="flex flex-col justify-between items-center h-screen w-full">
    <!-- Central Content -->
    <div v-if="!hasSentMessage" class="flex flex-col justify-center items-center flex-grow">
      <div class="text-center mb-8">
        <div class="bg-white shadow-lg inline-block mb-6 border rounded-lg">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="size-20 mx-auto"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z"
            />
          </svg>
        </div>
        <h1 class="text-4xl font-bold mb-4">Chat with me</h1>
        <p class="text-gray-600 max-w-md mb-4">Chat with Meta's Latest AI model - Llama 3.1</p>
        <button
          class="mt-6 py-2 px-4 bg-white text-black border border-gray-300 rounded-md shadow-sm hover:bg-gray-100"
        >
          Get started with a model
        </button>
      </div>
    </div>

    <!-- Chat Area -->
    <div
      v-if="hasSentMessage"
      class="w-8/12 p-4 flex flex-col mb-2 mt-10 rounded-md overflow-y-auto"
    >
      <!-- Display Chat History -->
      <div
        v-for="(message, index) in chatHistory"
        :key="index"
        :class="message.role === 'user' ? 'text-right' : 'text-left'"
      >
        <p
          :class="
            message.role === 'user' ? 'bg-blue-200 text-blue-800' : 'bg-green-200 text-green-800'
          "
          class="inline-block px-4 py-2 rounded-md max-w-xs"
        >
          {{ message.content }}
        </p>
      </div>
      <!-- Loading Indicator -->
      <div v-if="loading" class="text-center mt-4">
        <p class="inline-block px-4 py-2 rounded-md bg-gray-200 text-gray-800 max-w-xs">
          AI is thinking...
        </p>
      </div>
    </div>
    <!-- Input Area -->
    <div class="w-8/12 rounded-md p-4 flex items-center mb-2 relative">
      <textarea
        v-model="userInput"
        placeholder="Ask a question or make a request..."
        class="flex-grow p-3 rounded-md border-none bg-gray-100 resize-none h-32 focus:outline-none"
      ></textarea>
      <select
        class="bg-white border-2 rounded-md py-2 px-2 absolute bottom-7 left-6 focus:outline-none cursor-pointer"
      >
        <option>Llama 3.1</option>
      </select>
      <button
        @click="sendMessage"
        class="bg-lime-300 text-gray-800 p-3 rounded-md hover:bg-lime-400 absolute bottom-7 right-6"
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
            d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChatComponent',
  data() {
    return {
      userInput: '',
      chatHistory: [],
      hasSentMessage: false,
      loading: false
    }
  },
  methods: {
    async sendMessage() {
      if (this.userInput.trim() === '') return

      // Update the flag to show chat area and hide central content
      this.hasSentMessage = true
      this.loading = true

      // Add user input to chat history
      this.chatHistory.push({ role: 'user', content: this.userInput })

      // Clear the user input
      const userInputCopy = this.userInput;
      this.userInput = ''

      try {
        // Make API call to the backend
        const response = await fetch('http://127.0.0.1:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ query: userInputCopy })
        })

        const result = await response.json()

        // Add AI response to chat history
        this.chatHistory.push({ role: 'ai', content: result.answer })
      } catch (error) {
        console.error('Error:', error)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>
