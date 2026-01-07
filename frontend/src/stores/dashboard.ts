import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createResource, call } from 'frappe-ui'
import type { DashboardConfig, WidgetConfig, DashboardFilters } from '@/data/dashboardWidgets'

export const useDashboardStore = defineStore('dashboard', () => {
  const currentDashboard = ref<DashboardConfig | null>(null)
  const isEditMode = ref(false)
  const filters = ref<DashboardFilters>({})
  const widgets = ref<WidgetConfig[]>([])
  
  const dashboardsResource = createResource({
    url: 'crm.fcrm.doctype.crm_dashboard.api.get_dashboards',
    auto: true,
    onError: (error) => {
      console.error('Failed to load dashboards:', error)
      // Set empty array on error to prevent crashes
      dashboardsResource.data = []
    },
  })
  
  const availableDataSources = createResource({
    url: 'crm.fcrm.doctype.crm_dashboard.api.get_available_data_sources',
    auto: true,
    onError: (error) => {
      console.error('Failed to load data sources:', error)
      // Set default data sources on error
      availableDataSources.data = {
        DocType: ['CRM Lead', 'CRM Deal'],
        Report: [],
        Query: []
      }
    },
  })
  
  async function loadDashboard(name?: string) {
    try {
      const dashboardData = await call('crm.fcrm.doctype.crm_dashboard.api.get_dashboard', {
        name: name || null
      })
      
      currentDashboard.value = dashboardData
      
      // Ensure widgets array is properly populated
      const widgetsList = dashboardData.widgets || []
      widgets.value = widgetsList.map((w: any) => ({
        ...w,
        table_columns: typeof w.table_columns === 'string' ? JSON.parse(w.table_columns || '[]') : w.table_columns,
        table_filters: typeof w.table_filters === 'string' ? JSON.parse(w.table_filters || '{}') : w.table_filters,
        drilldown_filters: typeof w.drilldown_filters === 'string' ? JSON.parse(w.drilldown_filters || '{}') : w.drilldown_filters,
      }))
      
      // Log for debugging
      if (widgets.value.length === 0) {
        console.warn('Dashboard loaded but no widgets found:', dashboardData)
      } else {
        console.log('Dashboard widgets loaded:', widgets.value.length, widgets.value)
      }
      
      filters.value = {
        from_date: dashboardData.from_date,
        to_date: dashboardData.to_date,
        date_range_type: dashboardData.date_range_type,
        user_filter: dashboardData.user_filter,
        team_filter: dashboardData.team_filter,
      }
      
      return dashboardData
    } catch (error) {
      console.error('Failed to load dashboard:', error)
      throw error
    }
  }
  
  async function saveDashboard(dashboard: DashboardConfig) {
    try {
      // Serialize JSON fields
      const serializedDashboard = {
        ...dashboard,
        widgets: dashboard.widgets.map(w => ({
          ...w,
          table_columns: Array.isArray(w.table_columns) ? JSON.stringify(w.table_columns) : w.table_columns,
          table_filters: w.table_filters ? JSON.stringify(w.table_filters) : null,
          drilldown_filters: w.drilldown_filters ? JSON.stringify(w.drilldown_filters) : null,
        }))
      }
      
      const saved = await call('crm.fcrm.doctype.crm_dashboard.api.save_dashboard', {
        dashboard_data: serializedDashboard
      })
      
      currentDashboard.value = saved
      widgets.value = (saved.widgets || []).map((w: any) => ({
        ...w,
        table_columns: typeof w.table_columns === 'string' ? JSON.parse(w.table_columns || '[]') : w.table_columns,
        table_filters: typeof w.table_filters === 'string' ? JSON.parse(w.table_filters || '{}') : w.table_filters,
        drilldown_filters: typeof w.drilldown_filters === 'string' ? JSON.parse(w.drilldown_filters || '{}') : w.drilldown_filters,
      }))
      
      // Reload dashboards list
      dashboardsResource.reload()
      
      return saved
    } catch (error) {
      console.error('Failed to save dashboard:', error)
      throw error
    }
  }
  
  async function deleteDashboard(name: string) {
    try {
      await call('crm.fcrm.doctype.crm_dashboard.api.delete_dashboard', { name })
      dashboardsResource.reload()
      
      if (currentDashboard.value?.name === name) {
        currentDashboard.value = null
        widgets.value = []
      }
    } catch (error) {
      console.error('Failed to delete dashboard:', error)
      throw error
    }
  }
  
  function addWidget(widget: WidgetConfig) {
    widgets.value.push(widget)
  }
  
  function removeWidget(index: number) {
    widgets.value.splice(index, 1)
  }
  
  function updateWidget(index: number, updates: Partial<WidgetConfig>) {
    if (widgets.value[index]) {
      widgets.value[index] = { ...widgets.value[index], ...updates }
    }
  }
  
  function updateWidgetPosition(index: number, x: number, y: number) {
    if (widgets.value[index]) {
      widgets.value[index].x_position = x
      widgets.value[index].y_position = y
    }
  }
  
  function updateWidgetSize(index: number, width: number, height: number) {
    if (widgets.value[index]) {
      widgets.value[index].width = width
      widgets.value[index].height = height
    }
  }
  
  function setFilters(newFilters: DashboardFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }
  
  function setEditMode(edit: boolean) {
    isEditMode.value = edit
  }
  
  const dashboards = computed(() => dashboardsResource.data || [])
  
  return {
    currentDashboard,
    isEditMode,
    filters,
    widgets,
    dashboards,
    availableDataSources,
    loadDashboard,
    saveDashboard,
    deleteDashboard,
    addWidget,
    removeWidget,
    updateWidget,
    updateWidgetPosition,
    updateWidgetSize,
    setFilters,
    setEditMode,
  }
})

