<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-6">Sales Funnel</h3>
    
    <div v-if="isLoading" class="space-y-4">
      <div v-for="i in 4" :key="i" class="animate-pulse">
        <div class="h-4 bg-gray-200 rounded w-full mb-2"></div>
        <div class="h-3 bg-gray-200 rounded w-full"></div>
      </div>
    </div>
    
    <div v-else class="space-y-4">
      <div v-for="(stage, index) in funnelData" :key="stage.stage" class="funnel-stage">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-gray-700">{{ stage.stage }}</span>
          <span class="text-sm text-gray-500">{{ stage.count }}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-3">
          <div 
            :class="`h-3 rounded-full transition-all duration-500 ${
              index === funnelData.length - 1 ? 'bg-green-600' : 'bg-blue-600'
            }`"
            :style="{ width: `${stage.percentage}%` }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue'
import { createResource } from 'frappe-ui'

const props = defineProps({
  period: { type: String, default: 'thisMonth' }
})

// API Resource for sales funnel
const funnelResource = createResource({
  url: 'crm.fcrm.doctype.crm_deal.crm_deal.get_sales_funnel',
  params: () => ({ period: props.period }),
  cache: ['salesFunnel', props.period],
  auto: true,
  onError: err => console.error('Sales funnel failed to load:', err)
})

const isLoading = computed(() => funnelResource.loading)

const funnelData = computed(() => 
  funnelResource.data || [
    { stage: 'Prospects', count: 500, percentage: 100 },
    { stage: 'Qualified Leads', count: 280, percentage: 56 },
    { stage: 'Proposals', count: 147, percentage: 29.4 },
    { stage: 'Closed Won', count: 89, percentage: 17.8 },
  ]
)

watch(() => props.period, () => {
  funnelResource.reload()
})
</script>