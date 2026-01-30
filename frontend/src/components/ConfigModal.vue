<script setup>
const props = defineProps({
  isOpen: Boolean,
  threshold: {
    type: Number,
    default: 5,
  },
  email: {
    type: String,
    default: 'admin@example.com',
  },
})

const emit = defineEmits(['close'])
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
          <input :value="threshold" type="number" min="1" readonly class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-300 opacity-80 cursor-not-allowed" />
          <p class="text-xs text-gray-500 mt-1">Configured on the server (ALERT_TIMEOUT_MINUTES).</p>
        </div>
        
        <div>
           <label class="block text-sm font-medium text-gray-400 mb-1">Alert Recipient Email</label>
           <input :value="email" type="email" readonly class="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-gray-300 opacity-80 cursor-not-allowed" />
           <p class="text-xs text-gray-500 mt-1">Configured on the server (ALERT_RECIPIENT_EMAIL).</p>
        </div>
      </div>
      
      <div class="px-6 py-4 bg-gray-900/50 border-t border-gray-700 flex justify-end gap-3">
        <button @click="$emit('close')" class="px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-lg shadow-indigo-500/20 transition-all">Close</button>
      </div>
    </div>
  </div>
</template>
