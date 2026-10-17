import '@mdi/font/css/materialdesignicons.css'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { createAppVuetify } from './plugins/vuetify'
import { createAppRouter } from './router'
import './styles.css'

createApp(App)
  .use(createPinia())
  .use(createAppRouter())
  .use(createAppVuetify())
  .mount('#app')
