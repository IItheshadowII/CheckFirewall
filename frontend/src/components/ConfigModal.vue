<script setup>
import { ref } from 'vue'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'save'])

const threshold = ref(5)
const email = ref('admin@example.com')

const save = () => {
    emit('save', { threshold: threshold.value, email: email.value })
    emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
    <div class="bg-gray-800 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-700 bg-gray-900/50">
        <h3 class="text-lg font-medium text-white">Settings</h3>
      </div>
      
      <div class="p-6 space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-400 mb-1">Alert Threshold (Minutes)</label>
          <input v-model="threshold" type="number" min="1" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all" />
          <p class="text-xs text-gray-500 mt-1">Send alert if host is silent for more than this time.</p>
        </div>
        
        <div>
           <label class="block text-sm font-medium text-gray-400 mb-1">Alert Recipient Email</label>
           <input v-model="email" type="email" class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all" />
        </div>
      </div>
      
      <div class="px-6 py-4 bg-gray-900/50 border-t border-gray-700 flex justify-end gap-3">
        <button @click="$emit('close')" class="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors">Cancel</button>
        <button @click="save" class="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-lg shadow-indigo-500/20 transition-all">Save Changes</button>
      </div>
    </div>
  </div>
</template>
