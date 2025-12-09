export interface WidgetConfig {
  widget_type: 'KPI' | 'Chart' | 'Table'
  widget_title: string
  widget_description?: string
  width: number
  height: number
  x_position: number
  y_position: number
  data_source_type: 'DocType' | 'Report' | 'Query'
  data_source: string
  // KPI specific
  metric_field?: string
  aggregation_type?: 'Count' | 'Sum' | 'Average' | 'Min' | 'Max'
  // Chart specific
  chart_type?: 'Bar' | 'Line' | 'Pie' | 'Area'
  x_axis_field?: string
  y_axis_field?: string
  group_by_field?: string
  // Table specific
  table_columns?: string[]
  table_filters?: Record<string, any>
  // Display options
  color_scheme?: 'Blue' | 'Green' | 'Orange' | 'Red' | 'Purple' | 'Gray'
  show_refresh?: boolean
  refresh_interval?: number
  drilldown_doctype?: string
  drilldown_filters?: Record<string, any>
}

export interface DashboardFilters {
  from_date?: string
  to_date?: string
  date_range_type?: string
  user_filter?: string
  team_filter?: string
}

export interface DashboardConfig {
  name?: string
  dashboard_name: string
  description?: string
  is_default: boolean
  is_public: boolean
  widgets: WidgetConfig[]
  filters?: DashboardFilters
}

export const WIDGET_TYPES = [
  { label: 'KPI Card', value: 'KPI', icon: 'bar-chart-2' },
  { label: 'Chart', value: 'Chart', icon: 'trending-up' },
  { label: 'Table', value: 'Table', icon: 'table' }
] as const

export const CHART_TYPES = [
  { label: 'Bar Chart', value: 'Bar' },
  { label: 'Line Chart', value: 'Line' },
  { label: 'Pie Chart', value: 'Pie' },
  { label: 'Area Chart', value: 'Area' }
] as const

export const AGGREGATION_TYPES = [
  { label: 'Count', value: 'Count' },
  { label: 'Sum', value: 'Sum' },
  { label: 'Average', value: 'Average' },
  { label: 'Min', value: 'Min' },
  { label: 'Max', value: 'Max' }
] as const

export const COLOR_SCHEMES = [
  { label: 'Blue', value: 'Blue', color: 'bg-blue-500' },
  { label: 'Green', value: 'Green', color: 'bg-green-500' },
  { label: 'Orange', value: 'Orange', color: 'bg-orange-500' },
  { label: 'Red', value: 'Red', color: 'bg-red-500' },
  { label: 'Purple', value: 'Purple', color: 'bg-purple-500' },
  { label: 'Gray', value: 'Gray', color: 'bg-gray-500' }
] as const

export const DATE_RANGE_TYPES = [
  { label: 'Today', value: 'Today' },
  { label: 'Yesterday', value: 'Yesterday' },
  { label: 'This Week', value: 'This Week' },
  { label: 'Last Week', value: 'Last Week' },
  { label: 'This Month', value: 'This Month' },
  { label: 'Last Month', value: 'Last Month' },
  { label: 'This Quarter', value: 'This Quarter' },
  { label: 'Last Quarter', value: 'Last Quarter' },
  { label: 'This Year', value: 'This Year' },
  { label: 'Last Year', value: 'Last Year' },
  { label: 'Custom', value: 'Custom' }
] as const

