<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { formatDistanceToNow } from 'date-fns'
import StatusBadge from './StatusBadge.vue'

const hosts = ref([])
const loading = ref(true)
const updatedSecondsAgo = ref(0)
const refreshInterval = ref(null)
const timerInterval = ref(null)

const fetchHosts = async () => {
  try {
    // In production/docker, /api will be proxied. Locally with vite we set up proxy.
    const response = await axios.get('/api/hosts', {
        headers: { 'X-API-KEY': 'change-me-please' } // Should use env var
    })
    hosts.value = response.data
    updatedSecondsAgo.value = 0
  } catch (error) {
    console.error("Failed to fetch hosts:", error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHosts()
  refreshInterval.value = setInterval(fetchHosts, 10000) // 10s auto-refresh
  timerInterval.value = setInterval(() => {
      updatedSecondsAgo.value++
  }, 1000)
})

onUnmounted(() => {
  clearInterval(refreshInterval.value)
  clearInterval(timerInterval.value)
})

const getProfileStatus = (host, profileName) => {
    // profiles_status can be a dict from JSON
    if (!host.profiles_status) return false
    // Case insensible check might be safer but backend sends what agent sends
    return host.profiles_status[profileName] === true
}

const formatLastSeen = (dateStr) => {
    try {
        return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
    } catch (e) {
        return dateStr
    }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Stats -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gray-800/50 backdrop-blur border border-gray-700/50 rounded-xl p-6 shadow-xl relative overflow-hidden group">
            <div class="absolute inset-0 bg-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p class="text-sm font-medium text-gray-400">Total Hosts</p>
            <p class="text-3xl font-bold text-white mt-1">{{ hosts.length }}</p>
        </div>
        <div class="bg-gray-800/50 backdrop-blur border border-gray-700/50 rounded-xl p-6 shadow-xl relative overflow-hidden group">
             <div class="absolute inset-0 bg-emerald-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p class="text-sm font-medium text-gray-400">Healthy</p>
            <p class="text-3xl font-bold text-emerald-400 mt-1">{{ hosts.filter(h => h.firewall_status).length }}</p>
        </div>
         <div class="bg-gray-800/50 backdrop-blur border border-gray-700/50 rounded-xl p-6 shadow-xl relative overflow-hidden group">
             <div class="absolute inset-0 bg-rose-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <p class="text-sm font-medium text-gray-400">At Risk</p>
            <p class="text-3xl font-bold text-rose-400 mt-1">{{ hosts.filter(h => !h.firewall_status).length }}</p>
        </div>
    </div>

    <!-- Main Table -->
    <div class="bg-gray-800/40 border border-gray-700/50 rounded-xl shadow-2xl overflow-hidden backdrop-blur-sm">
      <div class="px-6 py-4 border-b border-gray-700/50 flex justify-between items-center bg-gray-800/60">
        <h2 class="text-lg font-semibold text-white">Monitored Infrastructure</h2>
        <div class="flex items-center gap-3 text-xs text-gray-400">
            <span class="flex items-center gap-1.5">
                <span class="relative flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                </span>
                Live Updates
            </span>
            <span>Updated {{ updatedSecondsAgo }}s ago</span>
        </div>
      </div>
      
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-700/50 bg-gray-800/30">
              <th class="px-6 py-4">Hostname</th>
              <th class="px-6 py-4">IP Address</th>
              <th class="px-6 py-4">Overall Status</th>
              <th class="px-6 py-4">Profiles (Dom/Priv/Pub)</th>
              <th class="px-6 py-4 text-right">Last Heartbeat</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-700/30">
            <tr v-if="loading" class="animate-pulse">
                <td colspan="5" class="px-6 py-8 text-center text-gray-500">Connecting to agents...</td>
            </tr>
            <tr v-else v-for="host in hosts" :key="host.id" class="group hover:bg-gray-700/20 transition-colors">
              <td class="px-6 py-4 font-medium text-white group-hover:text-indigo-300 transition-colors">{{ host.hostname }}</td>
              <td class="px-6 py-4 text-gray-400 font-mono text-sm">{{ host.ip_address }}</td>
              <td class="px-6 py-4">
                <StatusBadge :status="host.firewall_status" />
              </td>
              <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                      <StatusBadge type="profile" text="Dom" :status="getProfileStatus(host, 'Domain')" />
                      <StatusBadge type="profile" text="Priv" :status="getProfileStatus(host, 'Private')" />
                      <StatusBadge type="profile" text="Pub" :status="getProfileStatus(host, 'Public')" />
                  </div>
              </td>
              <td class="px-6 py-4 text-right text-gray-400 text-sm">
                  {{ formatLastSeen(host.last_seen) }}
              </td>
            </tr>
            <tr v-if="!loading && hosts.length === 0">
                 <td colspan="5" class="px-6 py-12 text-center text-gray-500">
                     <p class="text-lg font-medium text-gray-400 mb-1">No agents found</p>
                     <p class="text-sm">Install the PowerShell agent on your VMs to start monitoring.</p>
                 </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
