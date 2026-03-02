<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-auto bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto space-y-8">
      <!-- AM Dashboard Widget -->
      <div ref="amDashboardRef" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[100px]">
        <div class="p-8 text-center text-gray-400 animate-pulse">Loading Account Manager Dashboard...</div>
      </div>

      <!-- Combined Dashboard Widget -->
      <div ref="combinedDashboardRef" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[100px]">
        <div class="p-8 text-center text-gray-400 animate-pulse">Loading Combined Dashboard...</div>
      </div>

      <!-- Pending Tasks Widget -->
      <div ref="pendingTasksRef" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[100px]">
        <div class="p-8 text-center text-gray-400 animate-pulse">Loading Pending Tasks...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs } from 'frappe-ui'

const breadcrumbs = [
  { label: 'Account Manager Dashboard', route: { name: 'Account Manager Dashboard' } }
]

const amDashboardRef = ref(null)
const combinedDashboardRef = ref(null)
const pendingTasksRef = ref(null)

onMounted(() => {
  // Wait for a tick to ensure refs are bound
  setTimeout(() => {
    if (window.crm) {
      if (window.crm.am_dashboard_widget && amDashboardRef.value) {
        window.crm.am_dashboard_widget.render(amDashboardRef.value)
      }
      if (window.crm.combined_dashboard_widget && combinedDashboardRef.value) {
        window.crm.combined_dashboard_widget.render(combinedDashboardRef.value)
      }
      if (window.crm.pending_tasks_widget && pendingTasksRef.value) {
        window.crm.pending_tasks_widget.render(pendingTasksRef.value)
      }
    } else {
      console.warn('CRM library not found in window object')
    }
  }, 100)
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
