import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import axios from 'axios'

// Configure axios base URL only from Vite env. Do NOT provide a
// hardcoded fallback here; if `VITE_API_URL` is missing requests
// remain relative and must be handled by the hosting environment.
if (import.meta.env.VITE_API_URL) {
	axios.defaults.baseURL = import.meta.env.VITE_API_URL
} else {
	console.warn('VITE_API_URL not set; axios will use relative URLs')
}

createApp(App).mount('#app')
