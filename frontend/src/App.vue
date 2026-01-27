<script setup>
import { ref } from 'vue'
import Dashboard from './components/Dashboard.vue'
import ConfigModal from './components/ConfigModal.vue'

const isConfigOpen = ref(false)
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-white font-sans selection:bg-indigo-500 selection:text-white">
    <header class="bg-gray-900/50 backdrop-blur-md border-b border-gray-800 sticky top-0 z-50">
      <div class="container mx-auto px-4 h-16 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-5 h-5 text-white">
                  <path fill-rule="evenodd" d="M12.963 2.286a.75.75 0 00-1.071-.136 9.742 9.742 0 00-3.539 6.177 7.547 7.547 0 01-1.705-1.715.75.75 0 00-1.152-.082A9 9 0 1015.68 4.534a7.46 7.46 0 01-2.717-2.248zM15.75 14.25a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" clip-rule="evenodd" />
                </svg>
            </div>
          <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">FirewallWatch</h1>
        </div>
        
        <button @click="isConfigOpen = true" class="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-all">
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.157.922c.418.169.85.398 1.296.657l.666-.575c.42-.361.99-.404 1.45-.106l.54.347c.72.463.916 1.436.435 2.155l-.475.733c.189.44.331.91.42 1.393l.89.13c.558.081.96.566.96 1.123v.586c0 .557-.402 1.042-.96 1.123l-.89.13c-.089.484-.231.953-.42 1.393l.475.733c.48.719.284 1.692-.435 2.155l-.54.347c-.46.297-1.03.255-1.45-.106l-.666-.575c-.446.259-.878.488-1.296.657l-.157.922c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.02-.398-1.11-.94l-.157-.922c-.418-.169-.85-.398-1.296-.657l-.666.575c-.42.361-.99.404-1.45.106l-.54-.347c-.72-.463-.916-1.436-.435-2.155l.475-.733c-.189-.44-.331-.91-.42-1.393l-.89-.13c-.558-.081-.96-.566-.96-1.123v-.586c0-.557.402-1.042.96-1.123l.89-.13c.089-.484.231-.953.42-1.393l-.475-.733c-.48-.719-.284-1.692.435-2.155l.54-.347c.46-.297 1.03-.255 1.45.106l.666.575c.446-.259.878-.488 1.296-.657l.157-.922z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
        </button>
      </div>
    </header>

    <main class="container mx-auto px-4 py-8">
      <Dashboard />
      <ConfigModal :isOpen="isConfigOpen" @close="isConfigOpen = false" />
    </main>
  </div>
</template>
