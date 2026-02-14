<template>
  <div class="h-full w-full rounded-lg border bg-white p-4 shadow-sm flex flex-col">
    <div class="flex items-start justify-between mb-4">
      <div class="flex-1">
        <h3 class="text-sm font-medium text-gray-700">{{ widget.widget_title }}</h3>
        <p v-if="widget.widget_description" class="text-xs text-gray-500 mt-1">
          {{ widget.widget_description }}
        </p>
      </div>
      <div class="flex items-center gap-1">
        <Button
          v-if="widget.show_refresh"
          variant="ghost"
          size="sm"
          @click="refreshData"
          :loading="loading"
        >
          <template #icon>
            <FeatherIcon name="refresh-cw" class="h-4 w-4" />
          </template>
        </Button>
        <Button
          v-if="isEditMode"
          variant="ghost"
          size="sm"
          @click="$emit('edit')"
        >
          <template #icon>
            <FeatherIcon name="edit" class="h-4 w-4" />
          </template>
        </Button>
        <Button
          v-if="isEditMode"
          variant="ghost"
          size="sm"
          @click="$emit('delete')"
        >
          <template #icon>
            <FeatherIcon name="trash-2" class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </div>
    
    <div v-if="loading" class="flex items-center justify-center flex-1">
      <LoadingIndicator class="h-6 w-6" />
    </div>
    
    <div v-else-if="error" class="flex items-center justify-center flex-1 text-red-600">
      <div class="text-center">
        <FeatherIcon name="alert-circle" class="h-6 w-6 mx-auto mb-2" />
        <p class="text-sm">{{ error }}</p>
      </div>
    </div>
    
    <div v-else-if="tableData?.rows?.length" class="flex-1 overflow-auto">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 sticky top-0">
          <tr>
            <th
              v-for="column in tableData.columns"
              :key="column"
              class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              {{ formatColumnName(column) }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr
            v-for="(row, index) in tableData.rows"
            :key="index"
            class="hover:bg-gray-50 cursor-pointer"
            @click="handleRowClick(row)"
          >
            <td
              v-for="column in tableData.columns"
              :key="column"
              class="px-4 py-2 whitespace-nowrap text-sm text-gray-900"
            >
              {{ formatCellValue(row[column]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-else class="flex items-center justify-center flex-1 text-gray-400">
      <p class="text-sm">No data available</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Button, FeatherIcon } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'
import { useRouter } from 'vue-router'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'

// Safe API call that handles all error cases, including malformed responses
async function safeCall(method, args) {
  const path = method.startsWith('/') ? method : `/api/method/${method}`
  const headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json; charset=utf-8',
    'X-Frappe-Site-Name': window.location.hostname,
  }
  
  if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') {
    headers['X-Frappe-CSRF-Token'] = window.csrf_token
  }
  
  try {
    const response = await fetch(path, {
      method: 'POST',
      headers,
      body: JSON.stringify(args),
    })
    
    const text = await response.text()
    
    if (!response.ok) {
      // Check if response is HTML (Werkzeug debugger or error page)
      if (text.trim().startsWith('<!') || text.includes('<html') || text.includes('Werkzeug')) {
        const error = new Error(`Server error: ${response.status} ${response.statusText}`)
        error.messages = ['An error occurred on the server. Please try again or contact support.']
        error.status = response.status
        console.error('Server returned HTML error page:', text.substring(0, 200))
        throw error
      }
      
      // Try to parse error response as JSON
      let errorData = null
      try {
        errorData = JSON.parse(text)
      } catch (e) {
        // If parsing fails, create a safe error with the raw response
        const error = new Error(`Server error: ${response.status} ${response.statusText}`)
        error.messages = [text.substring(0, 200) || `Server returned ${response.status} ${response.statusText}`]
        error.status = response.status
        console.error('Failed to parse error response:', text.substring(0, 200))
        throw error
      }
      
      // Extract error message from Frappe error format
      const errorMsg = errorData._error_message || errorData.message || errorData.exc || `Server error: ${response.status}`
      const error = new Error(errorMsg)
      error.messages = []
      error.status = response.status
      
      // Try to extract server messages
      if (errorData._server_messages) {
        try {
          const serverMessages = JSON.parse(errorData._server_messages)
          error.messages = serverMessages.map(m => {
            try {
              const parsed = JSON.parse(m)
              return parsed.message || m
            } catch {
              return m
            }
          })
        } catch {
          error.messages = [errorData._server_messages]
        }
      }
      
      // Fallback to error message or exc
      if (!error.messages.length) {
        if (errorData.exc) {
          try {
            const excMessages = JSON.parse(errorData.exc)
            error.messages = Array.isArray(excMessages) ? excMessages : [excMessages]
          } catch {
            error.messages = [errorData.exc]
          }
        } else {
          error.messages = [errorMsg]
        }
      }
      
      console.error('API Error:', errorData)
      throw error
    }
    
    // Parse successful response
    try {
      const data = JSON.parse(text)
      return data.message || data
    } catch (e) {
      throw new Error('Invalid response format from server')
    }
  } catch (err) {
    // If it's already an Error with messages, re-throw
    if (err instanceof Error && err.messages) {
      throw err
    }
    // Otherwise wrap it
    const error = new Error(err?.message || 'Failed to load widget data')
    error.messages = [err?.message || 'An unexpected error occurred']
    throw error
  }
}

const props = defineProps({
  widget: {
    type: Object,
    required: true
  },
  filters: {
    type: Object,
    default: () => ({})
  },
  isEditMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit', 'delete'])

const router = useRouter()
const loading = ref(false)
const error = ref(null)
const tableData = ref(null)

function formatColumnName(column) {
  return column.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatCellValue(value) {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function handleRowClick(row) {
  if (props.widget.drilldown_doctype && row.name) {
    const routeMap = {
      'CRM Lead': { name: 'Lead', params: { leadId: row.name } },
      'CRM Deal': { name: 'Deal', params: { dealId: row.name } },
      'CRM Site Visit': { name: 'Meeting', params: { visitId: row.name } },
      'Contact': { name: 'Contact', params: { contactId: row.name } }
    }
    
    const route = routeMap[props.widget.drilldown_doctype]
    if (route) {
      router.push(route)
    }
  }
}

async function fetchData() {
  loading.value = true
  error.value = null
  
  try {
    const result = await safeCall('crm.fcrm.doctype.crm_dashboard.api.get_widget_data', {
      widget_config: JSON.stringify(props.widget),
      filters: JSON.stringify(props.filters)
    })
    
    tableData.value = result
  } catch (err) {
    // Handle different error formats safely
    let errorMessage = 'Failed to load table data'
    try {
      if (err) {
        if (Array.isArray(err.messages) && err.messages.length > 0) {
          errorMessage = err.messages[0]
        } else if (err.message) {
          errorMessage = err.message
        } else if (typeof err === 'string') {
          errorMessage = err
        }
      }
    } catch (parseErr) {
      // If even error parsing fails, use default message
      errorMessage = 'Failed to load widget data'
    }
    error.value = errorMessage
    console.error('Table widget error:', err)
  } finally {
    loading.value = false
  }
}

function refreshData() {
  fetchData()
}

onMounted(() => {
  fetchData()
})

// Debounce filter changes to prevent too many concurrent requests
watchDebounced(() => props.filters, () => {
  fetchData()
}, { debounce: 300, deep: true })

// Debounce widget changes
watchDebounced(() => props.widget, () => {
  fetchData()
}, { debounce: 300, deep: true })
</script>

