<template>
  <div ref="chartContainer" :style="{ height: height + 'px' }" class="flex items-center justify-center">
    <div v-if="!chartLoaded" class="text-gray-500">
      {{ __('Chart visualization will be available when frappe-charts is loaded') }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'

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
const chartLoaded = ref(false)
let chart = null

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

watch(() => props.data, () => {
  if (chart) {
    try {
      chart.update(props.data)
    } catch (error) {
      console.warn('Chart update failed:', error)
    }
  } else {
    nextTick(() => {
      initChart()
    })
  }
}, { deep: true })

function initChart() {
  if (!chartContainer.value || !props.data) return

  try {
    // Try to load frappe-charts from global scope or import
    if (typeof window !== 'undefined' && window.Chart) {
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
      chartLoaded.value = true
    } else {
      // Fallback: create a simple data table instead of chart
      createFallbackVisualization()
    }
  } catch (error) {
    console.warn('Chart initialization failed, using fallback:', error)
    createFallbackVisualization()
  }
}

function createFallbackVisualization() {
  if (!chartContainer.value || !props.data) return

  const { labels, datasets } = props.data
  if (!labels || !datasets || !datasets.length) return

  const table = document.createElement('table')
  table.className = 'w-full border-collapse'

  // Create header
  const thead = document.createElement('thead')
  const headerRow = document.createElement('tr')

  const labelHeader = document.createElement('th')
  labelHeader.textContent = 'Category'
  labelHeader.className = 'border p-2 text-left'
  headerRow.appendChild(labelHeader)

  datasets.forEach(dataset => {
    const th = document.createElement('th')
    th.textContent = dataset.name
    th.className = 'border p-2 text-left'
    headerRow.appendChild(th)
  })

  thead.appendChild(headerRow)
  table.appendChild(thead)

  // Create body
  const tbody = document.createElement('tbody')

  labels.forEach((label, index) => {
    const row = document.createElement('tr')

    const labelCell = document.createElement('td')
    labelCell.textContent = label
    labelCell.className = 'border p-2'
    row.appendChild(labelCell)

    datasets.forEach(dataset => {
      const valueCell = document.createElement('td')
      valueCell.textContent = dataset.values[index] || 0
      valueCell.className = 'border p-2 text-right'
      row.appendChild(valueCell)
    })

    tbody.appendChild(row)
  })

  table.appendChild(tbody)
  chartContainer.value.innerHTML = ''
  chartContainer.value.appendChild(table)
  chartLoaded.value = true
}
</script>