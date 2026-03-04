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
import { ref, onMounted } from 'vue'
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

const reloadPage = () => window.location.reload()

const initializeDashboard = () => {
  error.value = ''
  initialized.value = false
  
  // Wait for a tick to ensure refs are bound
  setTimeout(() => {
    if (window.crm) {
      try {
        if (window.crm.am_dashboard_widget && amDashboardRef.value) {
          window.crm.am_dashboard_widget.render(amDashboardRef.value)
        }
        if (window.crm.combined_dashboard_widget && combinedDashboardRef.value) {
          window.crm.combined_dashboard_widget.render(combinedDashboardRef.value)
        }
        if (window.crm.pending_tasks_widget && pendingTasksRef.value) {
          window.crm.pending_tasks_widget.render(pendingTasksRef.value)
        }
        initialized.value = true
      } catch (err) {
        console.error('Failed to render widgets:', err)
        error.value = 'Failed to render dashboard widgets.'
      }
    } else {
      console.warn('CRM library not found in window object')
      error.value = 'CRM library not found. Please check if scripts are loaded.'
    }
  }, 300)
}

onMounted(() => {
  initializeDashboard()
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
