<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="[{ label: __('Reports'), route: { name: 'Reports' } }]" />
      </template>
    </LayoutHeader>

    <div class="flex h-full flex-col">
      <div class="mx-5 mb-4 sm:mx-6">
        <div class="mb-6">
          <h1 class="text-2xl font-semibold text-gray-900">{{ __('Reports') }}</h1>
          <p class="mt-2 text-gray-600">
            {{ __('View comprehensive analytics and performance reports for your CRM data') }}
          </p>
        </div>

        <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="report in reports"
            :key="report.name"
            class="cursor-pointer rounded-lg border border-gray-200 p-6 transition-colors hover:border-gray-300 hover:bg-gray-50"
            @click="openReport(report.name)"
          >
            <div class="flex items-start">
              <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-blue-100">
                <ReportsIcon class="h-6 w-6 text-blue-600" />
              </div>
              <div class="ml-4 flex-1">
                <h3 class="text-base font-semibold text-gray-900">{{ __(report.label) }}</h3>
                <p class="mt-1 text-sm text-gray-600">{{ __(report.description) }}</p>
                <div class="mt-3">
                  <span
                    v-for="tag in report.tags"
                    :key="tag"
                    class="mr-2 inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800"
                  >
                    {{ __(tag) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call, Breadcrumbs } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import ReportsIcon from '@/components/Icons/ReportsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'

const { isManager } = usersStore()
const router = useRouter()

const reports = ref([
  {
    name: 'Leads Created Report',
    label: 'Leads Created Report',
    description: 'Track lead creation trends and analyze pipeline flow over time',
    tags: ['Leads', 'Analytics', 'Trends']
  },
  {
    name: 'Stage-wise Leads Report',
    label: 'Stage-wise Leads Report',
    description: 'Analyze lead distribution across different pipeline stages',
    tags: ['Leads', 'Pipeline', 'Stages']
  },
  {
    name: 'Conversion Rates Report',
    label: 'Conversion Rates Report',
    description: 'Monitor conversion rates by territory, source, and team members',
    tags: ['Conversion', 'Performance', 'Analytics']
  },
  {
    name: 'Revenue Report',
    label: 'Revenue Report',
    description: 'Comprehensive revenue analysis with growth trends and forecasting',
    tags: ['Revenue', 'Growth', 'Financial']
  },
  {
    name: 'Team Performance Report',
    label: 'Team Performance Report',
    description: 'Individual team member performance metrics and comparisons',
    tags: ['Team', 'Performance', 'KPIs']
  },
  {
    name: 'Individual Metrics Report',
    label: 'Individual Metrics Report',
    description: 'Personal performance tracking and goal achievement analysis',
    tags: ['Individual', 'Goals', 'Metrics']
  },
  {
    name: 'Team Metrics Summary Report',
    label: 'Team Metrics Summary Report',
    description: 'Executive overview of team performance across territories and roles',
    tags: ['Summary', 'Executive', 'Teams']
  }
])

const availableReports = ref([])

onMounted(async () => {
  try {
    // Get available reports based on user permissions
    const response = await call('frappe.desk.query_report.get_reports', {
      module: 'Fcrm'
    })

    if (response) {
      const userReports = response.filter(report =>
        reports.value.some(r => r.name === report.name)
      )
      availableReports.value = userReports
    }
  } catch (error) {
    console.error('Failed to fetch reports:', error)
  }
})

function openReport(reportName) {
  router.push({
    name: 'Report Viewer',
    params: { reportName: reportName }
  })
}
</script>