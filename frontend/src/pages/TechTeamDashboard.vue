<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button v-if="error" label="Retry" @click="initializeDashboard" />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-auto bg-gray-50 p-6">
    <div v-if="error" class="max-w-7xl mx-auto p-12 text-center bg-white rounded-xl shadow-sm border border-red-100">
      <div class="text-red-500 font-medium mb-2">{{ error }}</div>
      <p class="text-gray-500 mb-6 text-sm">Please ensure you are connected to the network and refresh the page.</p>
      <Button label="Refresh Page" @click="reloadPage" />
    </div>
    
    <div v-if="!initialized && !error" class="max-w-7xl mx-auto p-12 text-center">
      <div class="p-8 text-center text-gray-400 animate-pulse">Loading Technical Team Dashboard...</div>
    </div>

    <div v-show="initialized && !error" class="max-w-4xl mx-auto space-y-8">
      <!-- Technical Team Requests Widget -->
      <div ref="techTeamDashboardRef" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[200px]"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, Button } from 'frappe-ui'

const breadcrumbs = [
  { label: 'Technical Team Dashboard', route: { name: 'Technical Team Dashboard' } }
]

const techTeamDashboardRef = ref(null)
const initialized = ref(false)
const error = ref('')

let initializationTimeout = null
let pollInterval = null

const reloadPage = () => window.location.reload()

const initializeDashboard = () => {
  error.value = ''
  initialized.value = false
  
  if (initializationTimeout) clearTimeout(initializationTimeout)
  if (pollInterval) clearTimeout(pollInterval)

  const waitForCRM = (attempts = 0) => {
    const isReady = window.crm_ready && 
                    window.crm && 
                    window.crm.tech_team_widget && 
                    window.frappe && 
                    window.frappe.call;

    if (isReady) {
      try {
        initialized.value = true;
        
        initializationTimeout = setTimeout(() => {
          if (techTeamDashboardRef.value) {
            window.crm.tech_team_widget.render(techTeamDashboardRef.value)
          }
        }, 50);

      } catch (err) {
        console.error('Failed to render widget:', err)
        error.value = 'Failed to render dashboard widget.'
      }
    } else if (attempts < 40) {
      pollInterval = setTimeout(() => waitForCRM(attempts + 1), 250)
    } else {
      error.value = 'Dashboard dependencies failed to load.'
    }
  }

  waitForCRM()
}

onMounted(() => {
  initializeDashboard()
})

onUnmounted(() => {
  if (initializationTimeout) clearTimeout(initializationTimeout)
  if (pollInterval) clearTimeout(pollInterval)
})
</script>

<style scoped>
:deep(.tech-team-widget) {
  border: none !important;
  box-shadow: none !important;
}
</style>
