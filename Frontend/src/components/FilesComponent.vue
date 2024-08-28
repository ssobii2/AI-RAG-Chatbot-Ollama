<template>
  <div class="container mx-auto p-4 max-w-4xl">
    <h1 class="text-2xl font-semibold mb-6 text-center">Manage PDF Files</h1>
    <!-- Upload Section -->
    <div class="p-6 mb-8">
      <h2 class="text-xl font-semibold mb-4">Upload PDF</h2>
      <form @submit.prevent="handleUpload">
        <input
          type="file"
          @change="handleFileChange"
          accept=".pdf"
          ref="fileInput"
          class="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-lime-100 file:text-lime-700 hover:file:bg-lime-200"
        />
        <button
          type="submit"
          class="mt-4 mb-2 px-4 py-2 bg-lime-400 text-white rounded-lg hover:bg-lime-500"
        >
          Upload
        </button>
      </form>
      <el-alert
        class="mt-2"
        v-if="uploadError"
        title="Upload Error"
        type="error"
        description="PDF Upload Failed!"
        show-icon
      />
      <el-alert
        class="mt-2"
        v-if="uploadSuccess"
        title="Upload Success"
        type="success"
        description="PDF Uploaded Successfully!"
        show-icon
      />
    </div>

    <!-- PDF List Section -->
    <div class="p-6">
      <h2 class="text-xl font-semibold mb-4">Existing PDFs</h2>
      <ul>
        <li
          v-for="(pdf, index) in pdfs"
          :key="index"
          class="flex justify-between items-center mb-2"
        >
          <span>{{ pdf }}</span>
          <button
            @click="handleDelete(pdf)"
            class="px-2 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600"
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
                d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
              />
            </svg>
          </button>
        </li>
      </ul>
      <el-alert
        class="mt-2"
        v-if="deleteSuccess"
        title="Delete Success"
        type="success"
        description="PDF Deleted Successfully!"
        show-icon
      />
      <el-alert
        class="mt-2"
        v-if="deleteError"
        title="Delete Error"
        type="error"
        description="PDF Delete Failed!"
        show-icon
      />
    </div>
  </div>
</template>
  
<script>
import { ElLoading } from 'element-plus'

export default {
  data() {
    return {
      pdfs: [],
      selectedFile: null,
      uploadError: false,
      uploadSuccess: false,
      deleteSuccess: false,
      deleteError: false,
      loadingInstance: null
    }
  },
  created() {
    this.refreshPDFList()
  },
  methods: {
    handleFileChange(event) {
      this.selectedFile = event.target.files[0]
    },
    async handleUpload() {
      if (!this.selectedFile) {
        this.uploadError = true
        this.clearMessage('uploadError')
        return
      }

      this.uploadError = false
      this.uploadSuccess = false
      this.startLoading()

      const formData = new FormData()
      formData.append('file', this.selectedFile)

      try {
        const response = await fetch('http://127.0.0.1:8000/upload_pdf', {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          throw new Error('Error uploading PDF.')
        }

        this.uploadSuccess = true
        this.clearMessage('uploadSuccess')
        this.refreshPDFList()
        this.$refs.fileInput.value = ''
        this.selectedFile = null
      } catch (error) {
        this.uploadError = true
        this.clearMessage('uploadError')
      } finally {
        this.stopLoading()
      }
    },
    async handleDelete(pdf) {
      this.deleteError = false
      this.deleteSuccess = false
      this.startLoading()

      try {
        const response = await fetch(`http://127.0.0.1:8000/delete_pdf/${pdf}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          throw new Error('Error deleting PDF.')
        }

        this.deleteSuccess = true
        this.clearMessage('deleteSuccess')
        this.refreshPDFList()
      } catch (error) {
        this.deleteError = true
        this.clearMessage('deleteError')
      } finally {
        this.stopLoading()
      }
    },
    async refreshPDFList() {
      try {
        const response = await fetch('http://127.0.0.1:8000/list_pdfs')
        if (!response.ok) {
          throw new Error('Error fetching PDF list.')
        }
        const pdfFiles = await response.json()
        this.pdfs = pdfFiles
      } catch (error) {
        console.error('Error fetching PDF list:', error)
      }
    },
    startLoading() {
      this.loadingInstance = ElLoading.service({
        fullscreen: true,
        lock: true,
        text: 'Processing Please Wait...',
        background: 'rgba(0, 0, 0, 0.7)'
      })
    },
    stopLoading() {
      if (this.loadingInstance) {
        this.loadingInstance.close()
      }
    },
    clearMessage(type) {
      setTimeout(() => {
        this[type] = null
      }, 5000)
    }
  }
}
</script>
  