import { createApp } from 'vue'
import './index.css'
import App from './App.vue'

/* Apply SF Pro on all iOS browsers (Safari, Chrome, Firefox) */
if (/iPhone|iPad|iPod/.test(navigator.userAgent)) {
  document.documentElement.classList.add('ios')
}

createApp(App).mount('#app')
