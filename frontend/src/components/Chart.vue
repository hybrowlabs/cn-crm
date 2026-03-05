<template>
  <div :style="{ height: height + 'px' }" class="flex items-center justify-center w-full overflow-hidden">
    <!-- Frappe Chart Container -->
    <div 
      v-if="useFrappeCharts" 
      ref="chartContainer" 
      class="w-full h-full"
    ></div>

    <!-- Fallback Data Table (Built with Vue template, no manual DOM manipulation) -->
    <div 
      v-else-if="data && data.labels && data.labels.length > 0" 
      class="w-full h-full overflow-auto custom-scrollbar border border-gray-100 rounded-md bg-white"
    >
      <table class="w-full border-collapse text-[10px] sm:text-xs">
        <thead class="sticky top-0 z-10 bg-gray-50 shadow-sm">
          <tr>
            <th class="border-b border-gray-200 p-1.5 text-left font-semibold text-gray-700 min-w-[100px]">{{ __('Category') }}</th>
            <th 
              v-for="dataset in data.datasets" 
              :key="dataset.name" 
              class="border-b border-gray-200 p-1.5 text-right font-semibold text-gray-700"
            >
              {{ dataset.name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(label, index) in data.labels" :key="index" class="hover:bg-gray-50 transition-colors border-b border-gray-50 last:border-b-0">
            <td class="p-1.5 text-gray-600 font-medium truncate max-w-[150px]" :title="label">{{ label }}</td>
            <td 
              v-for="dataset in data.datasets" 
              :key="dataset.name" 
              class="p-1.5 text-right text-gray-600 tabular-nums"
            >
              {{ dataset.values[index] || 0 }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Loading / Empty State -->
    <div v-else class="text-gray-400 italic text-xs flex flex-col items-center gap-1">
      <svg class="w-6 h-6 opacity-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <span>{{ __('No visualization data') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'bar'
  },
  data: {
    type: Object,
    required: true
  },
  colors: {
    type: Array,
    default: () => ['#28a745', '#17a2b8', '#ffc107', '#dc3545', '#6f42c1']
  },
  height: {
    type: Number,
    default: 300
  }
})

const chartContainer = ref(null)
const useFrappeCharts = ref(false)
let chart = null

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

onUnmounted(() => {
  destroyChart()
})

watch(() => props.data, () => {
  if (chart) {
    try {
      chart.update(props.data)
    } catch (error) {
      console.warn('Chart update failed, re-initializing:', error)
      initChart()
    }
  } else {
    nextTick(() => {
      initChart()
    })
  }
}, { deep: true })

function destroyChart() {
  if (chart) {
    try {
      if (typeof chart.destroy === 'function') {
        chart.destroy()
      }
    } catch (e) {
      console.warn('Error destroying chart:', e)
    }
    chart = null
  }
}

function initChart() {
  const hasFrappeCharts = typeof window !== 'undefined' && window.Chart
  
  if (hasFrappeCharts && props.data && props.data.labels && props.data.labels.length > 0) {
    useFrappeCharts.value = true
    destroyChart()
    
    nextTick(() => {
      if (!chartContainer.value) {
        console.warn('Chart container not found after nextTick')
        return
      }

      try {
        chart = new window.Chart(chartContainer.value, {
          type: props.type,
          height: props.height,
          data: props.data,
          colors: props.colors,
          animate: true,
          truncateLegends: true,
          barOptions: {
            spaceRatio: 0.5
          },
          lineOptions: {
            regionFill: 1,
            hideLine: 0,
            hideDots: 0
          }
        })
      } catch (error) {
        console.warn('Frappe Chart initialization failed, falling back:', error)
        useFrappeCharts.value = false
        destroyChart()
      }
    })
  } else {
    useFrappeCharts.value = false
    destroyChart()
  }
}
</script>