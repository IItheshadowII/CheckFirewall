import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import axios from 'axios'

const runtimeEnv = (typeof window !== 'undefined' && window.__FW_ENV) ? window.__FW_ENV : {}

// Configure axios base URL from Vite env when present. If it is not
// defined (for example when the hosting platform does not inject
// build-time env vars), fall back to using the same host but port
// 8000, assuming the backend is exposed there.
let apiUrl = import.meta.env.VITE_API_URL || runtimeEnv.VITE_API_URL
if (!apiUrl) {
	const { protocol, hostname } = window.location
	apiUrl = `${protocol}//${hostname}:8000`
	console.warn('VITE_API_URL not set; falling back to', apiUrl)
}
axios.defaults.baseURL = apiUrl

createApp(App).mount('#app')
