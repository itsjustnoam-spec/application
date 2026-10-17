import { defineStore } from 'pinia'
import { ref } from 'vue'

const useNavigationStore = defineStore('navigation', () => {
  const isDrawerOpen = ref<boolean>(true)

  const toggleDrawer = (): void => {
    isDrawerOpen.value = !isDrawerOpen.value
  }

  return { isDrawerOpen, toggleDrawer }
})

export { useNavigationStore }
