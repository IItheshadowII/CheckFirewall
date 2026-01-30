<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import { formatDistanceToNow } from 'date-fns'
import StatusBadge from './StatusBadge.vue'

const hosts = ref([])
const loading = ref(true)
const updatedSecondsAgo = ref(0)
let refreshInterval = null
let timerInterval = null

// Backend base URL: prefer Vite env, otherwise derive from current
// host assuming backend listens on port 8000.
let API_URL = import.meta.env.VITE_API_URL || ''
if (!API_URL) {
  const { protocol, hostname } = window.location
  API_URL = `${protocol}//${hostname}:8000`
}

const fetchHosts = async () => {
  try {
    const res = await axios.get('/api/hosts', { headers: { 'X-API-KEY': 'change-me-please' } })
    hosts.value = res.data || []
    updatedSecondsAgo.value = 0
  } catch (e) {
    console.error('fetchHosts error', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHosts()
  refreshInterval = setInterval(fetchHosts, 10000)
  timerInterval = setInterval(() => { updatedSecondsAgo.value++ }, 1000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
  clearInterval(timerInterval)
})

// WebSocket real-time updates
let ws = null
let reconnectTimeout = null

const handleWsMessage = (event) => {
  try {
    const msg = JSON.parse(event.data)
    if (!msg || !msg.action) return
    if (msg.action === 'upsert' && msg.host) {
      const incoming = msg.host
      const idx = hosts.value.findIndex(h => h.id === incoming.id)
      if (idx === -1) {
        hosts.value.unshift(incoming)
      } else {
        // merge fields
        hosts.value[idx] = { ...hosts.value[idx], ...incoming }
      }
    } else if (msg.action === 'delete' && msg.host && msg.host.id) {
      hosts.value = hosts.value.filter(h => h.id !== msg.host.id)
    }
  } catch (e) {
    console.error('ws message parse error', e)
  }
}

const connectWS = () => {
  try {
    if (API_URL) {
      const u = new URL(API_URL)
      const wsScheme = u.protocol === 'https:' ? 'wss' : 'ws'
      const wsUrl = `${wsScheme}://${u.host}/ws/hosts`
      ws = new WebSocket(wsUrl)
    } else {
      const scheme = location.protocol === 'https:' ? 'wss' : 'ws'
      const url = `${scheme}://${location.host}/ws/hosts`
      ws = new WebSocket(url)
    }
  } catch (e) {
    console.error('connectWS error', e)
    return
  }
  ws.onopen = () => {
    console.debug('WS connected')
    if (reconnectTimeout) { clearTimeout(reconnectTimeout); reconnectTimeout = null }
  }
  ws.onmessage = handleWsMessage
  ws.onclose = () => {
    console.debug('WS closed, reconnecting...')
    reconnectTimeout = setTimeout(connectWS, 2000)
  }
  ws.onerror = (e) => {
    console.debug('WS error', e)
    try { ws.close() } catch (_) {}
  }
}

onMounted(() => {
  // connect WebSocket after initial mount
  connectWS()
})

onUnmounted(() => {
  if (ws) try { ws.close() } catch (_) {}
  if (reconnectTimeout) clearTimeout(reconnectTimeout)
})

const deleteHost = async (id) => {
  if (!confirm('Eliminar agente permanentemente?')) return
  try {
    const res = await axios.delete(`/api/hosts/${id}`, { headers: { 'X-API-KEY': 'change-me-please' } })
    if (res.status === 200 || res.status === 204) {
      hosts.value = hosts.value.filter(h => h.id !== id)
    } else {
      alert('Error eliminando agente: ' + res.status)
    }
  } catch (e) {
    alert('Error al eliminar agente: ' + (e?.response?.data?.detail || e.message))
  }
}

const getProfileStatus = (host, profileName) => {
  if (!host || !host.profiles_status) return false
  return host.profiles_status[profileName] === true
}

const formatLastSeen = (dateStr) => {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
  } catch (e) {
    return dateStr || ''
  }
}

const totalHosts = computed(() => hosts.value.length)
const healthyCount = computed(() => hosts.value.filter(h => h.firewall_status).length)
const atRiskCount = computed(() => hosts.value.filter(h => !h.firewall_status).length)
</script>

<template>
  <div class="space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gray-800/50 backdrop-blur border border-gray-700/50 rounded-xl p-6 shadow-xl">
        <p class="text-sm font-medium text-gray-400">Total Hosts</p>
        <p class="text-3xl font-bold text-white mt-1">{{ totalHosts }}</p>
      </div>
      <div class="bg-gray-800/50 backdrop-blur border border-gray-700/50 rounded-xl p-6 shadow-xl">
        <p class="text-sm font-medium text-gray-400">Healthy</p>
        <p class="text-3xl font-bold text-emerald-400 mt-1">{{ healthyCount }}</p>
      </div>
      <div class="bg-gray-800/50 backdrop-blur border border-gray-700/50 rounded-xl p-6 shadow-xl">
        <p class="text-sm font-medium text-gray-400">At Risk</p>
        <p class="text-3xl font-bold text-rose-400 mt-1">{{ atRiskCount }}</p>
      </div>
    </div>

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
              <th class="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-700/30">
            <tr v-if="loading" class="animate-pulse">
              <td colspan="6" class="px-6 py-8 text-center text-gray-500">Connecting to agents...</td>
            </tr>
            <tr v-else v-for="host in hosts" :key="host.id" class="group hover:bg-gray-700/20 transition-colors">
              <td class="px-6 py-4 font-medium text-white group-hover:text-indigo-300 transition-colors">{{ host.hostname }}</td>
              <td class="px-6 py-4 text-gray-400 font-mono text-sm">{{ host.ip_address }}</td>
              <td class="px-6 py-4"><StatusBadge :status="host.firewall_status" /></td>
              <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                  <StatusBadge type="profile" text="Dom" :status="getProfileStatus(host, 'Domain')" />
                  <StatusBadge type="profile" text="Priv" :status="getProfileStatus(host, 'Private')" />
                  <StatusBadge type="profile" text="Pub" :status="getProfileStatus(host, 'Public')" />
                </div>
              </td>
              <td class="px-6 py-4 text-right text-gray-400 text-sm">{{ formatLastSeen(host.last_seen) }}</td>
              <td class="px-6 py-4 text-right">
                <button @click="deleteHost(host.id)" class="text-red-400 hover:text-red-600">Eliminar</button>
              </td>
            </tr>
            <tr v-if="!loading && hosts.length === 0">
              <td colspan="6" class="px-6 py-12 text-center text-gray-500">
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
