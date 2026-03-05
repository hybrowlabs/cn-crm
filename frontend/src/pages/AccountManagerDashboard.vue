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
      <div class="p-8 text-center text-gray-400 animate-pulse">Loading Account Manager Dashboard...</div>
    </div>

    <div v-show="initialized && !error" class="max-w-7xl mx-auto space-y-8">
      <!-- AM Dashboard Widget -->
      <div ref="amDashboardRef" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[100px]"></div>

      <!-- Combined Dashboard Widget -->
      <div ref="combinedDashboardRef" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[100px]"></div>

      <!-- Pending Tasks Widget -->
      <div ref="pendingTasksRef" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[100px]"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, Button } from 'frappe-ui'

const breadcrumbs = [
  { label: 'Account Manager Dashboard', route: { name: 'Account Manager Dashboard' } }
]

const amDashboardRef = ref(null)
const combinedDashboardRef = ref(null)
const pendingTasksRef = ref(null)
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

  // Poll for window.crm to be ready (loaded async via index.html script chain)
  // Retries every 250ms up to 12 seconds before giving up
  const waitForCRM = (attempts = 0) => {
    // Check for crm_ready flag from index.html loader and existence of widgets
    const isReady = window.crm_ready && 
                    window.crm && 
                    window.crm.am_dashboard_widget && 
                    window.crm.combined_dashboard_widget && 
                    window.crm.pending_tasks_widget &&
                    window.frappe && 
                    window.frappe.call;

    if (isReady) {
      try {
        console.log('CRM and dependencies are ready, preparing to render widgets...');
        
        // Ensure container is visible BEFORE rendering
        // Widgets like Frappe Charts need the container to be visible to calculate dimensions
        initialized.value = true;
        
        // Small delay to let Vue update the DOM (v-show)
        initializationTimeout = setTimeout(() => {
          if (amDashboardRef.value) {
            window.crm.am_dashboard_widget.render(amDashboardRef.value)
          }
          if (combinedDashboardRef.value) {
            window.crm.combined_dashboard_widget.render(combinedDashboardRef.value)
          }
          if (pendingTasksRef.value) {
            window.crm.pending_tasks_widget.render(pendingTasksRef.value)
          }
        }, 50);

      } catch (err) {
        console.error('Failed to render widgets:', err)
        error.value = 'Failed to render dashboard widgets.'
      }
    } else if (attempts < 48) {
      // Not ready yet — try again in 250ms (max 48 × 250ms = 12s)
      pollInterval = setTimeout(() => waitForCRM(attempts + 1), 250)
    } else {
      console.warn('CRM library or dependencies not found after waiting 12s')
      error.value = 'Dashboard dependencies failed to load. Please refresh the page.'
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
/* Ensure the widgets don't have conflicting global styles if possible, 
   though they inject their own styles. */
:deep(.am-dashboard-widget),
:deep(.ptw-widget),
:deep(.combined-widget-row) {
  border: none !important;
  box-shadow: none !important;
}
</style>
