<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  
  <!-- Your existing SPANCO Widget -->
  <SpancoWidget />
  
  <!-- New Metrics Dashboard -->
  <MetricsDashboard />
  
  <!-- Additional Charts Section -->
  <div class="w-full max-w-7xl mx-auto p-4">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <LeadSourcesChart :period="selectedPeriod" />
      <SalesFunnel :period="selectedPeriod" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs } from 'frappe-ui'
import SpancoWidget from '@/components/Dashboard Elements/SpancoWidget.vue'
import MetricsDashboard from '@/components/Dashboard Elements/MetricsDashboard.vue'
import LeadSourcesChart from '@/components/Dashboard Elements/LeadSourcesChart.vue'
import SalesFunnel from '@/components/Dashboard Elements/SalesFunnel.vue'

const title = 'Dashboard'
const breadcrumbs = [{ label: title, route: { name: 'Dashboard' } }]
const selectedPeriod = ref('thisMonth')
</script>