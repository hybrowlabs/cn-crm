<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[
          { label: __('Reports'), route: { name: 'Reports' } },
          { label: reportTitle, route: { name: 'Report Viewer', params: { reportName } } }
        ]" />
      </template>
    </LayoutHeader>

    <div class="flex h-full flex-col">
      <div class="mx-5 mb-4 sm:mx-6">
        <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex-1">
            <h1 class="text-2xl font-semibold text-gray-900">{{ reportTitle }}</h1>
            <p v-if="reportDescription" class="mt-2 text-gray-600">{{ reportDescription }}</p>
          </div>
          <div class="flex shrink-0 items-center space-x-2">
            <Button
              variant="subtle"
              @click="refreshReport"
              :loading="loading"
              class="flex items-center gap-2"
            >
              <RefreshIcon class="h-4 w-4" />
              <span>{{ __('Refresh') }}</span>
            </Button>
            <Button
              v-if="reportData.length"
              variant="subtle"
              @click="exportReport"
              class="flex items-center gap-2"
            >
              <DownloadIcon class="h-4 w-4" />
              <span>{{ __('Export') }}</span>
            </Button>
          </div>
        </div>

        <!-- Filters -->
        <div v-if="availableFilters.length" class="mb-6">
          <div class="rounded-lg border border-gray-200 p-4">
            <h3 class="mb-4 text-sm font-medium text-gray-900">{{ __('Filters') }}</h3>
            <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div v-for="filter in availableFilters" :key="filter.fieldname">
                <label class="block text-sm font-medium text-gray-700 mb-1">
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
            <div class="mt-4 flex items-center space-x-2">
              <Button
                variant="subtle"
                size="sm"
                @click="clearFilters"
                class="flex items-center"
              >
                {{ __('Clear All') }}
              </Button>
            </div>
          </div>
        </div>

        <!-- Summary Cards -->
        <div v-if="summaryData.length" class="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div
            v-for="summary in summaryData"
            :key="summary.label"
            class="rounded-lg border border-gray-200 p-4"
          >
            <div class="flex items-center">
              <div class="flex-1">
                <p class="text-sm font-medium text-gray-600">{{ __(summary.label) }}</p>
                <p class="mt-1 text-2xl font-semibold text-gray-900">
                  {{ formatSummaryValue(summary) }}
                </p>
              </div>
              <div
                class="ml-4 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full"
                :class="getIndicatorClass(summary.indicator)"
              >
                <div class="h-2 w-2 rounded-full bg-current"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chart -->
        <div v-if="chartData" class="mb-6">
          <div class="rounded-lg border border-gray-200 p-6">
            <h3 class="mb-4 text-lg font-medium text-gray-900">{{ __('Chart') }}</h3>
            <div class="h-80">
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
          <div class="border-b border-gray-200 px-6 py-4">
            <h3 class="text-lg font-medium text-gray-900">{{ __('Data') }}</h3>
          </div>
          <div v-if="loading" class="flex justify-center py-8">
            <LoadingIndicator class="w-6" />
          </div>
          <div v-else-if="reportData.length === 0" class="py-8 text-center text-gray-500">
            {{ __('No data available') }}
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th
                    v-for="column in columns"
                    :key="column.fieldname"
                    class="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
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
                    class="whitespace-nowrap px-6 py-4 text-sm"
                  >
                    {{ formatCellValue(row[column.fieldname], column.fieldtype) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="reportData.length > pageSize" class="border-t border-gray-200 px-6 py-3">
            <div class="flex items-center justify-between">
              <p class="text-sm text-gray-700">
                {{ __('Showing {0} to {1} of {2} results', [
                  (currentPage - 1) * pageSize + 1,
                  Math.min(currentPage * pageSize, reportData.length),
                  reportData.length
                ]) }}
              </p>
              <div class="flex items-center space-x-2">
                <Button
                  variant="subtle"
                  size="sm"
                  :disabled="currentPage === 1"
                  @click="currentPage--"
                  class="flex items-center"
                >
                  {{ __('Previous') }}
                </Button>
                <Button
                  variant="subtle"
                  size="sm"
                  :disabled="currentPage === totalPages"
                  @click="currentPage++"
                  class="flex items-center"
                >
                  {{ __('Next') }}
                </Button>
              </div>
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