import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import axios from 'axios'

// Backend base URL: use env if present, otherwise fall back to the
// EasyPanel backend URL so the app works even without VITE_API_URL.
const API_URL = import.meta.env.VITE_API_URL || 'https://monitor-firewallmonitor.koswui.easypanel.host'
axios.defaults.baseURL = API_URL

createApp(App).mount('#app')
