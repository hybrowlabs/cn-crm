<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Dropdown :options="dashboardOptions">
          <Button :label="selectedDashboard?.dashboard_name || __('Select Dashboard')" variant="outline">
            <template #suffix>
              <FeatherIcon name="chevron-down" class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
        <Button
          :label="isEditMode ? __('View Mode') : __('Edit Mode')"
          :variant="isEditMode ? 'outline' : 'solid'"
          @click="toggleEditMode"
        >
          <template #prefix>
            <FeatherIcon :name="isEditMode ? 'eye' : 'edit'" class="h-4 w-4" />
          </template>
        </Button>
        <Button
          v-if="isEditMode"
          :label="__('Save')"
          variant="solid"
          @click="saveDashboard"
          :loading="saving"
        />
        <Button
          :label="__('New Dashboard')"
          variant="solid"
          @click="createNewDashboard"
        >
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </template>
  </LayoutHeader>
  
  <div class="flex h-[calc(100vh-4rem)] flex-col overflow-hidden">
    <!-- Global Filters -->
    <div class="border-b bg-white px-6 py-4">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2">
          <label class="text-sm font-medium text-gray-700">{{ __('Date Range') }}:</label>
          <Dropdown :options="dateRangeOptions">
            <Button :label="selectedDateRange?.label || __('Select Range')" variant="outline" size="sm">
              <template #suffix>
                <FeatherIcon name="chevron-down" class="h-4 w-4" />
              </template>
            </Button>
          </Dropdown>
        </div>
        
        <div v-if="filters.date_range_type === 'Custom'" class="flex items-center gap-2">
          <FormControl
            v-model="filters.from_date"
            type="date"
            :label="__('From')"
            size="sm"
          />
          <FormControl
            v-model="filters.to_date"
            type="date"
            :label="__('To')"
            size="sm"
          />
        </div>
        
        <div class="flex items-center gap-2">
          <label class="text-sm font-medium text-gray-700">{{ __('User') }}:</label>
          <div class="w-full min-w-[180px] sm:w-52 md:w-60">
            <Link
              v-model="filters.user_filter"
              doctype="User"
              :placeholder="__('All Users')"
              size="sm"
            />
          </div>
        </div>
        
        <Button
          variant="ghost"
          size="sm"
          @click="applyFilters"
        >
          <template #prefix>
            <FeatherIcon name="filter" class="h-4 w-4" />
          </template>
          {{ __('Apply Filters') }}
        </Button>
      </div>
    </div>
    
    <!-- Widget Palette (Edit Mode) -->
    <div v-if="isEditMode" class="border-b bg-gray-50 px-6 py-3">
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium text-gray-700">{{ __('Add Widget') }}:</span>
        <Button
          v-for="widgetType in WIDGET_TYPES"
          :key="widgetType.value"
          variant="outline"
          size="sm"
          @click="addWidget(widgetType.value)"
        >
          <template #prefix>
            <FeatherIcon :name="widgetType.icon" class="h-4 w-4" />
          </template>
          {{ widgetType.label }}
        </Button>
      </div>
    </div>
    
    <!-- Dashboard Grid -->
    <div class="flex-1 overflow-auto bg-gray-100 p-6">
      <div v-if="widgets.length === 0" class="flex h-full items-center justify-center">
        <div class="text-center">
          <FeatherIcon name="layout" class="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p class="text-gray-500">{{ __('No widgets yet. Add widgets to get started.') }}</p>
        </div>
      </div>
      
      <div
        v-else
        ref="gridContainer"
        class="relative mx-auto"
        :style="{ width: `${gridWidth}px` }"
      >
        <div
          v-for="(widget, index) in widgets"
          :key="index"
          :class="[
            'absolute rounded-lg border-2 transition-all',
            isEditMode ? 'cursor-move border-blue-300 hover:border-blue-500' : 'border-transparent',
            isDragging === index ? 'z-50 shadow-lg' : 'z-0'
          ]"
          :style="{
            left: `${widget.x_position * gridUnitSize}px`,
            top: `${widget.y_position * gridUnitSize}px`,
            width: `${widget.width * gridUnitSize}px`,
            height: `${widget.height * gridUnitSize}px`
          }"
          @mousedown="isEditMode ? startDrag(index, $event) : null"
        >
          <component
            :is="getWidgetComponent(widget.widget_type)"
            :widget="widget"
            :filters="filters"
            :is-edit-mode="isEditMode"
            @edit="editWidget(index)"
            @delete="deleteWidget(index)"
          />
        </div>
      </div>
    </div>
  </div>
  
  <!-- Widget Config Modal -->
  <WidgetConfigModal
    v-model="showWidgetModal"
    :widget="editingWidget"
    :available-doc-types="availableDocTypes"
    @save="handleWidgetSave"
  />
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, Button, FeatherIcon, Dropdown, FormControl } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { useDashboardStore } from '@/stores/dashboard'
import { WIDGET_TYPES, DATE_RANGE_TYPES } from '@/data/dashboardWidgets'
import KPIWidget from '@/components/Dashboard/KPIWidget.vue'
import ChartWidget from '@/components/Dashboard/ChartWidget.vue'
import TableWidget from '@/components/Dashboard/TableWidget.vue'
import SpancoWidget from '@/components/Dashboard Elements/SpancoWidget.vue'
import WidgetConfigModal from '@/components/Dashboard/WidgetConfigModal.vue'

const router = useRouter()
const dashboardStore = useDashboardStore()

const breadcrumbs = [{ label: __('Dashboard Builder'), route: { name: 'Dashboard Builder' } }]

const isEditMode = computed(() => dashboardStore.isEditMode)
const widgets = computed(() => dashboardStore.widgets)
const filters = computed(() => dashboardStore.filters)
const dashboards = computed(() => dashboardStore.dashboards)
const availableDataSources = computed(() => dashboardStore.availableDataSources)

const saving = ref(false)
const showWidgetModal = ref(false)
const editingWidget = ref(null)
const editingIndex = ref(-1)

const gridContainer = ref(null)
const gridUnitSize = 80 // pixels per grid unit
const gridWidth = computed(() => Math.max(1200, window.innerWidth - 100))
const isDragging = ref(-1)
const dragStart = ref({ x: 0, y: 0, widgetX: 0, widgetY: 0 })

const selectedDashboard = computed(() => {
  if (!dashboardStore.currentDashboard) return null
  return dashboards.value.find(d => d.name === dashboardStore.currentDashboard?.name)
})

const availableDocTypes = computed(() => {
  return availableDataSources.value?.data?.DocType || []
})

const dateRangeOptions = computed(() =>
  DATE_RANGE_TYPES.map(d => ({
    label: d.label,
    onClick: () => {
      filters.value.date_range_type = d.value
      updateDateRange(d.value)
    }
  }))
)

const selectedDateRange = computed(() =>
  DATE_RANGE_TYPES.find(d => d.value === filters.value.date_range_type)
)

const dashboardOptions = computed(() => [
  ...dashboards.value.map(d => ({
    label: d.dashboard_name,
    onClick: () => loadDashboard(d.name)
  })),
  { label: __('Manage Dashboards...'), onClick: () => {} }
])

function getWidgetComponent(type) {
  const components = {
    KPI: KPIWidget,
    Chart: ChartWidget,
    Table: TableWidget,
    LMOTPO: SpancoWidget,
  }
  return components[type] || KPIWidget
}

function toggleEditMode() {
  dashboardStore.setEditMode(!isEditMode.value)
}

async function loadDashboard(name) {
  try {
    await dashboardStore.loadDashboard(name)
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
}

async function saveDashboard() {
  if (!dashboardStore.currentDashboard) return
  
  saving.value = true
  try {
    const dashboardConfig = {
      ...dashboardStore.currentDashboard,
      widgets: widgets.value,
      filters: filters.value
    }
    await dashboardStore.saveDashboard(dashboardConfig)
  } catch (error) {
    console.error('Failed to save dashboard:', error)
  } finally {
    saving.value = false
  }
}

function createNewDashboard() {
  // Default LMOTPO widget for new dashboards
  const defaultLmotpoWidget = {
    widget_type: 'LMOTPO',
    widget_title: 'LMOTPO Pipeline',
    widget_description: 'Lead → Meetings → Opportunities → Trial → Pricing → Order Booking',
    width: 12,
    height: 6,
    x_position: 0,
    y_position: 0,
    show_refresh: false,
  }

  dashboardStore.currentDashboard = {
    dashboard_name: 'New Dashboard',
    description: '',
    is_default: false,
    is_public: false,
    widgets: [defaultLmotpoWidget],
    filters: {}
  }
  dashboardStore.widgets = [defaultLmotpoWidget]
  dashboardStore.setEditMode(true)
}

function addWidget(type) {
  const baseY = widgets.value.length > 0
    ? Math.max(...widgets.value.map(w => w.y_position + w.height))
    : 0

  const defaults = {
    widget_type: type,
    widget_title: `New ${type} Widget`,
    width: type === 'LMOTPO' ? 12 : 4,
    height: type === 'LMOTPO' ? 6 : 3,
    x_position: 0,
    y_position: baseY,
    color_scheme: 'Blue',
    show_refresh: type === 'LMOTPO' ? false : true,
    refresh_interval: 0
  }

  if (type !== 'LMOTPO') {
    Object.assign(defaults, {
      data_source_type: 'DocType',
      data_source: '',
    })
  }

  editingWidget.value = defaults
  
  editingIndex.value = -1
  showWidgetModal.value = true
}

function editWidget(index) {
  editingWidget.value = { ...widgets.value[index] }
  editingIndex.value = index
  showWidgetModal.value = true
}

function deleteWidget(index) {
  if (confirm(__('Are you sure you want to delete this widget?'))) {
    dashboardStore.removeWidget(index)
  }
}

function handleWidgetSave(widget) {
  if (editingIndex.value >= 0) {
    dashboardStore.updateWidget(editingIndex.value, widget)
  } else {
    // Find position for new widget
    const maxY = widgets.value.length > 0
      ? Math.max(...widgets.value.map(w => w.y_position + w.height))
      : 0
    widget.y_position = maxY
    dashboardStore.addWidget(widget)
  }
}

function startDrag(index, event) {
  if (!isEditMode.value) return
  
  isDragging.value = index
  const widget = widgets.value[index]
  dragStart.value = {
    x: event.clientX,
    y: event.clientY,
    widgetX: widget.x_position,
    widgetY: widget.y_position
  }
  
  const handleMouseMove = (e) => {
    if (isDragging.value !== index) return
    
    const deltaX = Math.round((e.clientX - dragStart.value.x) / gridUnitSize)
    const deltaY = Math.round((e.clientY - dragStart.value.y) / gridUnitSize)
    
    const newX = Math.max(0, dragStart.value.widgetX + deltaX)
    const newY = Math.max(0, dragStart.value.widgetY + deltaY)
    
    dashboardStore.updateWidgetPosition(index, newX, newY)
  }
  
  const handleMouseUp = () => {
    isDragging.value = -1
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  }
  
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

function updateDateRange(rangeType) {
  const today = new Date()
  let fromDate, toDate
  
  switch (rangeType) {
    case 'Today':
      fromDate = toDate = today.toISOString().split('T')[0]
      break
    case 'Yesterday':
      const yesterday = new Date(today)
      yesterday.setDate(yesterday.getDate() - 1)
      fromDate = toDate = yesterday.toISOString().split('T')[0]
      break
    case 'This Week':
      const weekStart = new Date(today)
      weekStart.setDate(today.getDate() - today.getDay())
      fromDate = weekStart.toISOString().split('T')[0]
      toDate = today.toISOString().split('T')[0]
      break
    case 'This Month':
      fromDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0]
      toDate = today.toISOString().split('T')[0]
      break
    case 'This Year':
      fromDate = new Date(today.getFullYear(), 0, 1).toISOString().split('T')[0]
      toDate = today.toISOString().split('T')[0]
      break
    default:
      return
  }
  
  filters.value.from_date = fromDate
  filters.value.to_date = toDate
}

function applyFilters() {
  // Filters are reactive, widgets will automatically refresh
  // This function can be used for additional filter logic if needed
}

onMounted(async () => {
  // Load available data sources first
  try {
    await dashboardStore.availableDataSources.reload()
  } catch (error) {
    console.error('Failed to load data sources:', error)
    // Continue anyway - default data sources will be used
  }
  
  // Load default dashboard or create new one
  const query = router.currentRoute.value.query
  if (query.new === 'true') {
    // Create new dashboard
    dashboardStore.currentDashboard = {
      dashboard_name: 'New Dashboard',
      description: '',
      is_default: false,
      is_public: false,
      widgets: [],
      filters: {}
    }
    dashboardStore.widgets = []
    dashboardStore.setEditMode(true)
  } else {
    // Load default dashboard
    try {
      await dashboardStore.loadDashboard()
    } catch (error) {
      // If no dashboard found, create a new one
      if (error.messages?.[0]?.includes('No dashboard found')) {
        dashboardStore.currentDashboard = {
          dashboard_name: 'My Dashboard',
          description: '',
          is_default: true,
          is_public: false,
          widgets: [],
          filters: {}
        }
        dashboardStore.widgets = []
        dashboardStore.setEditMode(true)
      } else {
        console.error('Failed to load dashboard:', error)
      }
    }
  }
})
</script>

