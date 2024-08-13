<template>
    <div class="flex">
      <SidebarComponent />
      <ChatComponent />
    </div>
</template>
  
<script>
    import SidebarComponent from './components/SidebarComponent.vue'
    import ChatComponent from './components/ChatComponent.vue'
    export default {
    components: { SidebarComponent, ChatComponent },
        name: 'App'
    }
</script>