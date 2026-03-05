<template>
  <div class="min-h-screen bg-gray-50">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[
          { label: __('Reports'), route: { name: 'Reports' } },
          { label: reportTitle, route: { name: 'Report Viewer', params: { reportName } } }
        ]" />
      </template>
    </LayoutHeader>

    <div class="mx-auto max-w-7xl px-4 pb-12 pt-6 sm:px-6 lg:px-8">

        <!-- Header row -->
        <div class="mb-4 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-start sm:justify-between">
          <div class="flex-1">
            <h1 class="text-xl font-semibold text-gray-900 sm:text-2xl">{{ reportTitle }}</h1>
            <p v-if="reportDescription" class="mt-1 text-sm text-gray-500 sm:mt-2">{{ reportDescription }}</p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <Button
              variant="subtle"
              @click="refreshReport"
              :loading="loading"
              class="items-center px-3"
            >
              <template #prefix>
                <RefreshIcon class="h-4 w-4" />
              </template>
              {{ __('Refresh') }}
            </Button>
            <Button
              v-if="reportData.length"
              variant="subtle"
              @click="exportReport"
              class="items-center px-3"
            >
              <template #prefix>
                <DownloadIcon class="h-4 w-4" />
              </template>
              {{ __('Export') }}
            </Button>
          </div>
        </div>

        <!-- Filters -->
        <div v-if="availableFilters.length" class="mb-4 sm:mb-6">
          <div class="rounded-lg border border-gray-200 p-3 sm:p-4">
            <h3 class="mb-3 text-sm font-medium text-gray-900">{{ __('Filters') }}</h3>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div v-for="filter in availableFilters" :key="filter.fieldname">
                <label class="mb-1 block text-xs font-medium text-gray-700 sm:text-sm">
                  {{ __(filter.label) }}
                </label>
                <FormControl
                  v-if="filter.fieldtype === 'Date'"
                  type="date"
                  v-model="filters[filter.fieldname]"
                  @change="applyFilters"
                />
                <FormControl
                  v-else-if="filter.fieldtype === 'Select'"
                  type="select"
                  v-model="filters[filter.fieldname]"
                  :options="filter.options || []"
                  @change="applyFilters"
                />
                <FormControl
                  v-else
                  v-model="filters[filter.fieldname]"
                  @change="applyFilters"
                />
              </div>
            </div>
            <div class="mt-3 flex items-center gap-2">
              <Button variant="subtle" size="sm" @click="clearFilters">
                {{ __('Clear All') }}
              </Button>
            </div>
          </div>
        </div>

        <!-- Summary Cards -->
        <div v-if="summaryData.length" class="mb-4 grid grid-cols-2 gap-3 sm:mb-6 sm:grid-cols-2 lg:grid-cols-4">
          <div
            v-for="summary in summaryData"
            :key="summary.label"
            class="rounded-lg border border-gray-200 p-3 sm:p-4"
          >
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <p class="truncate text-xs font-medium text-gray-500 sm:text-sm">{{ __(summary.label) }}</p>
                <p class="mt-1 text-lg font-semibold text-gray-900 sm:text-2xl">
                  {{ formatSummaryValue(summary) }}
                </p>
              </div>
              <div
                class="ml-2 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full sm:h-8 sm:w-8"
                :class="getIndicatorClass(summary.indicator)"
              >
                <div class="h-1.5 w-1.5 rounded-full bg-current sm:h-2 sm:w-2"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chart -->
        <div v-if="chartData" class="mb-4 sm:mb-6">
          <div class="rounded-lg border border-gray-200 p-3 sm:p-6">
            <h3 class="mb-3 text-base font-medium text-gray-900 sm:mb-4 sm:text-lg">{{ __('Chart') }}</h3>
            <div class="h-56 sm:h-80">
              <Chart
                v-if="chartData.data"
                :type="chartData.type || 'bar'"
                :data="chartData.data"
                :colors="chartData.colors"
                :height="chartData.height || 300"
              />
            </div>
          </div>
        </div>

        <!-- Data Table -->
        <div class="rounded-lg border border-gray-200">
          <div class="border-b border-gray-200 px-4 py-3 sm:px-6 sm:py-4">
            <h3 class="text-base font-medium text-gray-900 sm:text-lg">{{ __('Data') }}</h3>
          </div>
          <div v-if="loading" class="flex justify-center py-8">
            <LoadingIndicator class="w-6" />
          </div>
          <div v-else-if="reportData.length === 0" class="py-8 text-center text-sm text-gray-500">
            {{ __('No data available') }}
          </div>
          <div v-else class="overflow-x-auto ring-1 ring-gray-200 rounded-lg">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th
                    v-for="column in columns"
                    :key="column.fieldname"
                    class="sticky top-0 z-10 bg-gray-50 whitespace-nowrap px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-500 sm:px-6 sm:py-3"
                  >
                    {{ __(column.label) }}
                  </th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr v-for="row in paginatedData" :key="row.name || Math.random()">
                  <td
                    v-for="column in columns"
                    :key="column.fieldname"
                    class="whitespace-nowrap px-4 py-3 text-xs sm:px-6 sm:py-4 sm:text-sm"
                  >
                    {{ formatCellValue(row[column.fieldname], column.fieldtype) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="reportData.length > pageSize" class="border-t border-gray-200 px-4 py-3 sm:px-6">
            <div class="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p class="text-xs text-gray-500 sm:text-sm">
                {{ __('Showing {0} to {1} of {2} results', [
                  (currentPage - 1) * pageSize + 1,
                  Math.min(currentPage * pageSize, reportData.length),
                  reportData.length
                ]) }}
              </p>
              <div class="flex items-center gap-2">
                <Button
                  variant="subtle"
                  size="sm"
                  :disabled="currentPage === 1"
                  @click="currentPage--"
                >
                  {{ __('Prev') }}
                </Button>
                <span class="text-xs text-gray-500">{{ currentPage }} / {{ totalPages }}</span>
                <Button
                  variant="subtle"
                  size="sm"
                  :disabled="currentPage === totalPages"
                  @click="currentPage++"
                >
                  {{ __('Next') }}
                </Button>
              </div>
            </div>
          </div>
        </div>
    </div>
  </div>
</template>


<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { call, Button, FormControl, LoadingIndicator, Breadcrumbs } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import DownloadIcon from '@/components/Icons/DownloadIcon.vue'
import Chart from '@/components/Chart.vue'

const route = useRoute()
const reportName = computed(() => route.params.reportName)

const loading = ref(false)
const reportData = ref([])
const columns = ref([])
const summaryData = ref([])
const chartData = ref(null)
const filters = ref({})
const availableFilters = ref([])

const reportTitle = computed(() => {
  return reportName.value || 'Report'
})

const reportDescription = computed(() => {
  const descriptions = {
    'Leads Created Report': 'Track lead creation trends and analyze pipeline flow over time',
    'Stage-wise Leads Report': 'Analyze lead distribution across different pipeline stages',
    'Conversion Rates Report': 'Monitor conversion rates by territory, source, and team members',
    'Revenue Report': 'Comprehensive revenue analysis with growth trends and forecasting',
    'Team Performance Report': 'Individual team member performance metrics and comparisons',
    'Individual Metrics Report': 'Personal performance tracking and goal achievement analysis',
    'Team Metrics Summary Report': 'Executive overview of team performance across territories and roles'
  }
  return descriptions[reportName.value] || ''
})

// Pagination
const currentPage = ref(1)
const pageSize = ref(50)
const totalPages = computed(() => Math.ceil(reportData.value.length / pageSize.value))
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return reportData.value.slice(start, end)
})

onMounted(() => {
  loadReport()
  setupFilters()
})

watch(reportName, () => {
  loadReport()
  setupFilters()
})

async function loadReport() {
  if (!reportName.value) return

  loading.value = true
  try {
    const response = await call('frappe.desk.query_report.run', {
      report_name: reportName.value,
      filters: filters.value
    })

    if (response) {
      columns.value = response.columns || []
      reportData.value = response.result || []
      summaryData.value = response.summary || []
      chartData.value = response.chart || null
    }
  } catch (error) {
    console.error('Failed to load report:', error)
  } finally {
    loading.value = false
  }
}

function setupFilters() {
  // Common filters for all reports
  availableFilters.value = [
    {
      fieldname: 'from_date',
      label: 'From Date',
      fieldtype: 'Date'
    },
    {
      fieldname: 'to_date',
      label: 'To Date',
      fieldtype: 'Date'
    }
  ]

  // Add report-specific filters
  if (reportName.value === 'Team Performance Report' || reportName.value === 'Individual Metrics Report') {
    availableFilters.value.push({
      fieldname: 'user',
      label: 'User',
      fieldtype: 'Link'
    })
  }

  if (reportName.value === 'Conversion Rates Report') {
    availableFilters.value.push({
      fieldname: 'territory',
      label: 'Territory',
      fieldtype: 'Link'
    })
  }
}

function applyFilters() {
  currentPage.value = 1
  loadReport()
}

function clearFilters() {
  filters.value = {}
  currentPage.value = 1
  loadReport()
}

function refreshReport() {
  loadReport()
}

function exportReport() {
  const csvContent = generateCSV()
  const blob = new Blob([csvContent], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${reportName.value}.csv`
  link.click()
  window.URL.revokeObjectURL(url)
}

function generateCSV() {
  if (!columns.value.length || !reportData.value.length) return ''

  const headers = columns.value.map(col => col.label).join(',')
  const rows = reportData.value.map(row =>
    columns.value.map(col =>
      formatCellValue(row[col.fieldname], col.fieldtype)
    ).join(',')
  ).join('\n')

  return headers + '\n' + rows
}

function formatCellValue(value, fieldtype) {
  if (value == null || value === '') return '-'

  switch (fieldtype) {
    case 'Date':
      if (value instanceof Date) {
        return value.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      } else {
        const date = new Date(value)
        return date.toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric'
        })
      }
    case 'Currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(value)
    case 'Percent':
      return `${value}%`
    case 'Float':
      return Number(value).toFixed(1)
    case 'Int':
      return Number(value).toLocaleString()
    default:
      return value
  }
}

function formatSummaryValue(summary) {
  if (summary.datatype === 'Currency') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(summary.value)
  }
  if (summary.datatype === 'Int') {
    return Number(summary.value).toLocaleString()
  }
  return summary.value
}

function getIndicatorClass(indicator) {
  const classes = {
    'Green': 'text-green-600 bg-green-100',
    'Blue': 'text-blue-600 bg-blue-100',
    'Orange': 'text-orange-600 bg-orange-100',
    'Red': 'text-red-600 bg-red-100',
    'Gray': 'text-gray-600 bg-gray-100',
    'Purple': 'text-purple-600 bg-purple-100'
  }
  return classes[indicator] || classes['Gray']
}
</script>