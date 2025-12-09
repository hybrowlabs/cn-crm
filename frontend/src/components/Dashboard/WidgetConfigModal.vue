<template>
  <Dialog v-model="show" :options="{ size: '2xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ widget.name ? __('Edit Widget') : __('Add Widget') }}
          </h3>
          <Button variant="ghost" class="w-7" @click="show = false">
            <template #icon>
              <FeatherIcon name="x" class="size-4" />
            </template>
          </Button>
        </div>
        
        <div class="space-y-4">
          <!-- Widget Type -->
          <div>
            <label class="mb-1.5 block text-xs font-medium text-ink-gray-7">
              {{ __('Widget Type') }} <span class="text-red-500">*</span>
            </label>
            <Dropdown :options="widgetTypeOptions">
              <Button :label="selectedWidgetType?.label || __('Select Type')" class="w-full justify-between">
                <template #suffix>
                  <FeatherIcon name="chevron-down" class="h-4 w-4" />
                </template>
              </Button>
            </Dropdown>
          </div>
          
          <!-- Basic Info -->
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="config.widget_title"
              :label="__('Title')"
              required
              :placeholder="__('Widget Title')"
            />
            <FormControl
              v-model="config.width"
              :label="__('Width (grid units)')"
              type="number"
              required
            />
          </div>
          
          <FormControl
            v-model="config.widget_description"
            :label="__('Description')"
            :placeholder="__('Optional description')"
          />
          
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              v-model="config.height"
              :label="__('Height (grid units)')"
              type="number"
              required
            />
            <Dropdown :options="colorSchemeOptions">
              <Button :label="selectedColorScheme?.label || __('Select Color')" class="w-full justify-between">
                <template #suffix>
                  <FeatherIcon name="chevron-down" class="h-4 w-4" />
                </template>
              </Button>
            </Dropdown>
          </div>
          
          <!-- Data Source -->
          <div class="border-t pt-4">
            <h4 class="mb-3 text-sm font-medium text-gray-700">{{ __('Data Source') }}</h4>
            <div class="grid grid-cols-2 gap-4">
              <Dropdown :options="dataSourceTypeOptions">
                <Button :label="selectedDataSourceType?.label || __('Select Source Type')" class="w-full justify-between">
                  <template #suffix>
                    <FeatherIcon name="chevron-down" class="h-4 w-4" />
                  </template>
                </Button>
              </Dropdown>
            <Link
              v-if="config.data_source_type === 'DocType'"
              v-model="config.data_source"
              doctype="DocType"
              :filters="availableDocTypes.length > 0 ? { name: ['in', availableDocTypes] } : {}"
              :placeholder="__('Select DocType')"
            />
            </div>
          </div>
          
          <!-- KPI Specific -->
          <div v-if="config.widget_type === 'KPI'" class="border-t pt-4 space-y-4">
            <h4 class="text-sm font-medium text-gray-700">{{ __('KPI Configuration') }}</h4>
            <div class="grid grid-cols-2 gap-4">
              <FormControl
                v-model="config.metric_field"
                :label="__('Metric Field')"
                :placeholder="__('e.g., deal_value')"
              />
              <Dropdown :options="aggregationOptions">
                <Button :label="selectedAggregation?.label || __('Select Aggregation')" class="w-full justify-between">
                  <template #suffix>
                    <FeatherIcon name="chevron-down" class="h-4 w-4" />
                  </template>
                </Button>
              </Dropdown>
            </div>
          </div>
          
          <!-- Chart Specific -->
          <div v-if="config.widget_type === 'Chart'" class="border-t pt-4 space-y-4">
            <h4 class="text-sm font-medium text-gray-700">{{ __('Chart Configuration') }}</h4>
            <div class="grid grid-cols-2 gap-4">
              <Dropdown :options="chartTypeOptions">
                <Button :label="selectedChartType?.label || __('Select Chart Type')" class="w-full justify-between">
                  <template #suffix>
                    <FeatherIcon name="chevron-down" class="h-4 w-4" />
                  </template>
                </Button>
              </Dropdown>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <FormControl
                v-model="config.x_axis_field"
                :label="__('X Axis Field')"
                :placeholder="__('e.g., status')"
              />
              <FormControl
                v-model="config.y_axis_field"
                :label="__('Y Axis Field')"
                :placeholder="__('e.g., deal_value')"
              />
            </div>
            <FormControl
              v-model="config.group_by_field"
              :label="__('Group By Field')"
              :placeholder="__('Optional')"
            />
          </div>
          
          <!-- Table Specific -->
          <div v-if="config.widget_type === 'Table'" class="border-t pt-4 space-y-4">
            <h4 class="text-sm font-medium text-gray-700">{{ __('Table Configuration') }}</h4>
            <FormControl
              v-model="tableColumnsText"
              :label="__('Columns (comma-separated)')"
              :placeholder="__('e.g., name, status, deal_value')"
            />
          </div>
          
          <!-- Display Options -->
          <div class="border-t pt-4">
            <h4 class="mb-3 text-sm font-medium text-gray-700">{{ __('Display Options') }}</h4>
            <div class="space-y-2">
              <label class="flex items-center gap-2">
                <input
                  type="checkbox"
                  v-model="config.show_refresh"
                  class="rounded border-gray-300"
                />
                <span class="text-sm text-gray-700">{{ __('Show Refresh Button') }}</span>
              </label>
              <FormControl
                v-model="config.refresh_interval"
                :label="__('Auto-refresh Interval (seconds, 0 = disabled)')"
                type="number"
              />
            </div>
          </div>
          
          <ErrorMessage v-if="error" :message="error" />
        </div>
      </div>
      
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button variant="solid" :label="__('Save')" @click="saveWidget" />
          <Button variant="ghost" :label="__('Cancel')" @click="show = false" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Dialog, Button, FeatherIcon, FormControl, Dropdown, ErrorMessage } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { WIDGET_TYPES, CHART_TYPES, AGGREGATION_TYPES, COLOR_SCHEMES } from '@/data/dashboardWidgets'

const props = defineProps({
  widget: {
    type: Object,
    default: null
  },
  availableDocTypes: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['save', 'close'])

const show = defineModel()
const error = ref(null)

const config = ref({
  widget_type: 'KPI',
  widget_title: '',
  width: 4,
  height: 3,
  x_position: 0,
  y_position: 0,
  data_source_type: 'DocType',
  data_source: '',
  color_scheme: 'Blue',
  show_refresh: true,
  refresh_interval: 0
})

const tableColumnsText = ref('')

const widgetTypeOptions = computed(() => 
  WIDGET_TYPES.map(w => ({
    label: w.label,
    onClick: () => {
      config.value.widget_type = w.value
      // Reset type-specific fields when changing type
      if (w.value !== 'KPI') {
        config.value.metric_field = undefined
        config.value.aggregation_type = undefined
      }
      if (w.value !== 'Chart') {
        config.value.chart_type = undefined
        config.value.x_axis_field = undefined
        config.value.y_axis_field = undefined
        config.value.group_by_field = undefined
      }
      if (w.value !== 'Table') {
        config.value.table_columns = undefined
      }
    }
  }))
)

const chartTypeOptions = computed(() =>
  CHART_TYPES.map(c => ({
    label: c.label,
    onClick: () => { config.value.chart_type = c.value }
  }))
)

const aggregationOptions = computed(() =>
  AGGREGATION_TYPES.map(a => ({
    label: a.label,
    onClick: () => { config.value.aggregation_type = a.value }
  }))
)

const colorSchemeOptions = computed(() =>
  COLOR_SCHEMES.map(c => ({
    label: c.label,
    onClick: () => { config.value.color_scheme = c.value }
  }))
)

const dataSourceTypeOptions = [
  { label: 'DocType', onClick: () => { config.value.data_source_type = 'DocType' } },
  { label: 'Report', onClick: () => { config.value.data_source_type = 'Report' } },
  { label: 'Query', onClick: () => { config.value.data_source_type = 'Query' } }
]

const selectedWidgetType = computed(() => 
  WIDGET_TYPES.find(w => w.value === config.value.widget_type)
)

const selectedChartType = computed(() =>
  CHART_TYPES.find(c => c.value === config.value.chart_type)
)

const selectedAggregation = computed(() =>
  AGGREGATION_TYPES.find(a => a.value === config.value.aggregation_type)
)

const selectedColorScheme = computed(() =>
  COLOR_SCHEMES.find(c => c.value === config.value.color_scheme)
)

const selectedDataSourceType = computed(() =>
  dataSourceTypeOptions.find(d => d.label === config.value.data_source_type)
)

watch(() => props.widget, (newWidget) => {
  if (newWidget) {
    config.value = { ...newWidget }
    if (newWidget.table_columns) {
      tableColumnsText.value = Array.isArray(newWidget.table_columns) 
        ? newWidget.table_columns.join(', ')
        : newWidget.table_columns
    }
  } else {
    // Reset to defaults
    config.value = {
      widget_type: 'KPI',
      widget_title: '',
      width: 4,
      height: 3,
      x_position: 0,
      y_position: 0,
      data_source_type: 'DocType',
      data_source: '',
      color_scheme: 'Blue',
      show_refresh: true,
      refresh_interval: 0
    }
    tableColumnsText.value = ''
  }
}, { immediate: true })

function saveWidget() {
  error.value = null
  
  // Validation
  if (!config.value.widget_title) {
    error.value = __('Title is required')
    return
  }
  
  if (!config.value.data_source) {
    error.value = __('Data Source is required')
    return
  }
  
  if (config.value.widget_type === 'KPI' && !config.value.aggregation_type) {
    error.value = __('Aggregation Type is required for KPI widgets')
    return
  }
  
  if (config.value.widget_type === 'Chart') {
    if (!config.value.chart_type) {
      error.value = __('Chart Type is required')
      return
    }
    if (!config.value.x_axis_field || !config.value.y_axis_field) {
      error.value = __('X Axis and Y Axis fields are required')
      return
    }
  }
  
  if (config.value.widget_type === 'Table') {
    if (!tableColumnsText.value.trim()) {
      error.value = __('Table Columns are required')
      return
    }
    config.value.table_columns = tableColumnsText.value.split(',').map(c => c.trim()).filter(c => c)
  }
  
  emit('save', { ...config.value })
  show.value = false
}
</script>

