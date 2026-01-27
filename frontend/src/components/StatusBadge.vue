<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: Boolean,
  text: String,
  type: {
      type: String,
      default: 'general' // 'general' or 'profile'
  }
})

const badgeClasses = computed(() => {
    if (props.type === 'profile') {
        return props.status 
        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
        : 'bg-red-500/10 text-red-400 border-red-500/20'
    }
    
    // General status
    return props.status 
        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' 
        : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
})

const icon = computed(() => {
    return props.status 
        ? 'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
        : 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z'
})
</script>

<template>
  <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors shadow-sm" :class="badgeClasses">
    <svg v-if="type === 'general'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-3.5 h-3.5">
        <path stroke-linecap="round" stroke-linejoin="round" :d="icon" />
    </svg>
    {{ text || (status ? 'Active' : 'Risk') }}
  </span>
</template>
