<template>
  <div class="w-full max-w-6xl mx-auto p-3 sm:p-6">
    <!-- Time Period Filter -->
    <div class="mb-6 flex flex-wrap gap-2 justify-center sm:justify-start">
      <button
        v-for="period in timePeriods"
        :key="period.value"
        @click="selectedPeriod = period.value"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
          selectedPeriod === period.value
            ? 'bg-blue-600 text-white shadow-lg'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200',
        ]"
      >
        {{ period.label }}
      </button>
    </div>

    <!-- Metrics Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <!-- Total Leads -->
      <MetricCard
        title="Total Leads"
        :value="leadsMetrics.total"
        :subtitle="selectedPeriodLabel"
        :growth="leadsMetrics.growth"
        :icon="UsersIcon"
        icon-bg-color="bg-blue-100"
        icon-color="text-blue-600"
      />

      <!-- Total Deals -->
      <MetricCard
        title="Total Deals"
        :value="dealsMetrics.total"
        :subtitle="selectedPeriodLabel"
        :growth="dealsMetrics.growth"
        :icon="TargetIcon"
        icon-bg-color="bg-green-100"
        icon-color="text-green-600"
      />

      <!-- Total Visits -->
      <MetricCard
        title="Total Visits"
        :value="visitsMetrics.total"
        :subtitle="selectedPeriodLabel"
        :growth="visitsMetrics.growth"
        :icon="MapPinIcon"
        icon-bg-color="bg-purple-100"
        icon-color="text-purple-600"
      />

      <!-- Conversion Rate -->
      <MetricCard
        title="Conversion Rate"
        :value="conversionMetrics.rate"
        subtitle="Leads to Deals"
        :growth="conversionMetrics.growth"
        :icon="TrendingUpIcon"
        icon-bg-color="bg-orange-100"
        icon-color="text-orange-600"
        :decimals="1"
        suffix="%"
      />
    </div>

    <!-- Additional Revenue Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- Deal Value -->
      <MetricCard
        title="Deal Value"
        :value="dealsMetrics.value"
        :subtitle="selectedPeriodLabel"
        :growth="dealsMetrics.valueGrowth"
        :icon="DollarSignIcon"
        icon-bg-color="bg-emerald-100"
        icon-color="text-emerald-600"
        prefix="$"
        :format="true"
      />

      <!-- New Leads -->
      <MetricCard
        title="New Leads"
        :value="leadsMetrics.new_leads"
        :subtitle="selectedPeriodLabel"
        :growth="leadsMetrics.growth"
        :icon="CalendarIcon"
        icon-bg-color="bg-indigo-100"
        icon-color="text-indigo-600"
      />

      <!-- Qualified Leads -->
      <MetricCard
        title="Qualified Leads"
        :value="leadsMetrics.qualified_leads"
        :subtitle="selectedPeriodLabel"
        :growth="leadsMetrics.growth"
        :icon="BarChart3Icon"
        icon-bg-color="bg-cyan-100"
        icon-color="text-cyan-600"
      />

      <!-- Activities -->
      <MetricCard
        title="Activities"
        :value="68"
        subtitle="Calls + Meetings"
        :growth="8.7"
        :icon="PhoneIcon"
        icon-bg-color="bg-rose-100"
        icon-color="text-rose-600"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource } from 'frappe-ui'
import {
  TrendingUp as TrendingUpIcon,
  Users as UsersIcon,
  Calendar as CalendarIcon,
  Target as TargetIcon,
  DollarSign as DollarSignIcon,
  Phone as PhoneIcon,
  MapPin as MapPinIcon,
  BarChart3 as BarChart3Icon
} from 'lucide-vue-next'
import MetricCard from './MetricCard.vue'

// Period Filter Setup
const selectedPeriod = ref('thisMonth')
const timePeriods = [
  { value: 'today', label: 'Today' },
  { value: 'thisWeek', label: 'This Week' },
  { value: 'thisMonth', label: 'This Month' },
  { value: 'thisQuarter', label: 'This Quarter' },
  { value: 'thisYear', label: 'This Year' }
]

const selectedPeriodLabel = computed(() => {
  return timePeriods.find(p => p.value === selectedPeriod.value)?.label || 'This Month'
})

// API Resources
const leadsResource = createResource({
  url: 'crm.fcrm.doctype.crm_lead.crm_lead.get_leads_metrics',
  params: () => ({ period: selectedPeriod.value }),
  cache: ['leadsMetrics', selectedPeriod],
  auto: true,
  onError: (err) => console.error('Failed to load leads metrics:', err)
})

console.log('Leads Resource:', leadsResource);
const dealsResource = createResource({
  url: 'crm.fcrm.doctype.crm_deal.crm_deal.get_deals_metrics',
  params: () => ({ period: selectedPeriod.value }),
  cache: ['dealsMetrics', selectedPeriod],
  auto: true,
  onError: err => console.error('Deals failed to load:', err)
})
console.log('Deals Resource:', dealsResource.data);


const visitsResource = createResource({
  url: 'crm.fcrm.doctype.crm_site_visit.crm_site_visit.get_visits_metrics',
  params: () => ({ period: selectedPeriod.value }),
  cache: ['visitsMetrics', selectedPeriod],
  auto: true,
  onError: err => console.error('Visits failed to load:', err)
})

console.log('Visits Resource:', visitsResource);

// Computed Metrics - MATCHES YOUR API EXACTLY
const leadsMetrics = computed(() => leadsResource.data || { 
  total: 150, 
  growth: 12.5, 
  new_leads: 45, 
  qualified_leads: 67 
})

const dealsMetrics = computed(() => dealsResource.data || { 
  total: 89, 
  growth: 8.3, 
  value: 450000, 
  valueGrowth: 18.2 
})

const visitsMetrics = computed(() => visitsResource.data || { 
  total: 78, 
  growth: 15.7 
})

const conversionMetrics = computed(() => {
  const leads = leadsMetrics.value.total || 1
  const deals = dealsMetrics.value.total || 0
  return { rate: (deals / leads) * 100, growth: 5.2 }
})

// Watch for period changes
watch(() => selectedPeriod.value, () => {
  leadsResource.reload()
  dealsResource.reload()
  visitsResource.reload()
})
</script>


