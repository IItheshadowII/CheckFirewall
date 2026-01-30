import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import axios from 'axios'

// Configure axios base URL from Vite env. If not set, requests remain relative.
if (import.meta.env.VITE_API_URL) {
	axios.defaults.baseURL = import.meta.env.VITE_API_URL
}

createApp(App).mount('#app')
