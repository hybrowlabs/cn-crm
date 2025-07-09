<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-900">Lead Sources</h3>
      <button class="text-sm text-blue-600 hover:text-blue-700 font-medium">
        View Details
      </button>
    </div>
    
    <div v-if="isLoading" class="h-80 flex items-center justify-center">
      <div class="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
    </div>
    
    <div v-else class="relative h-80">
      <canvas ref="chartCanvas" class="w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import { createResource } from 'frappe-ui'

Chart.register(...registerables)

const props = defineProps({
  period: { type: String, default: 'thisMonth' }
})

const chartCanvas = ref(null)
let chartInstance = null

// API Resource for lead sources
const leadSourcesResource = createResource({
  url: 'crm.fcrm.doctype.crm_lead.crm_lead.get_lead_sources_chart',
  params: () => ({ period: props.period }),
  cache: ['leadSources', props.period],
  auto: true,
  onError: err => console.error('Lead sources failed to load:', err)
})

const isLoading = computed(() => leadSourcesResource.loading)

const chartData = computed(() => leadSourcesResource.data || {
  labels: ["Website", "Referrals", "Social Media", "Email", "Direct"],
  data: [35, 25, 20, 12, 8],
  colors: ["#1565C0", "#388E3C", "#F57C00", "#7B1FA2", "#D32F2F"]
})

const createChart = async () => {
  if (!chartCanvas.value || !chartData.value) return

  // Destroy existing chart
  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = chartCanvas.value.getContext('2d')
  const data = chartData.value

  chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.data,
        backgroundColor: data.colors,
        borderWidth: 2,
        borderColor: '#fff',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true,
            font: { size: 12 }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const total = context.dataset.data.reduce((a, b) => a + b, 0)
              const percentage = ((context.parsed / total) * 100).toFixed(1)
              return `${context.label}: ${percentage}%`
            }
          }
        }
      },
      cutout: '60%'
    }
  })
}

watch(() => chartData.value, () => {
  nextTick(() => {
    createChart()
  })
})

watch(() => props.period, () => {
  leadSourcesResource.reload()
})

onMounted(() => {
  nextTick(() => {
    createChart()
  })
})
</script>