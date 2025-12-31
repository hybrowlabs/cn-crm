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
          :label="__('Dashboard Builder')"
          variant="solid"
          @click="goToBuilder"
        >
          <template #prefix>
            <FeatherIcon name="layout" class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </template>
  </LayoutHeader>

  <div class="flex h-[calc(100vh-4rem)] flex-col overflow-hidden">
    <div class="flex-1 overflow-auto bg-gray-100 p-6">
      <div v-if="widgets.length === 0" class="flex h-full items-center justify-center">
        <div class="text-center">
          <FeatherIcon name="layout" class="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p class="text-gray-500">{{ __('No widgets yet. Select another dashboard or build one.') }}</p>
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
            'border-transparent z-0'
          ]"
          :style="{
            left: `${widget.x_position * gridUnitSize}px`,
            top: `${widget.y_position * gridUnitSize}px`,
            width: `${widget.width * gridUnitSize}px`,
            height: `${widget.height * gridUnitSize}px`
          }"
        >
          <component
            :is="getWidgetComponent(widget.widget_type)"
            :widget="widget"
            :filters="filters"
            :is-edit-mode="false"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, Button, FeatherIcon, Dropdown } from 'frappe-ui'
import { useDashboardStore } from '@/stores/dashboard'
import KPIWidget from '@/components/Dashboard/KPIWidget.vue'
import ChartWidget from '@/components/Dashboard/ChartWidget.vue'
import TableWidget from '@/components/Dashboard/TableWidget.vue'
import SpancoWidget from '@/components/Dashboard Elements/SpancoWidget.vue'

const router = useRouter()
const dashboardStore = useDashboardStore()

const title = 'Dashboard'
const breadcrumbs = [{ label: title, route: { name: 'Dashboard' } }]

const widgets = computed(() => dashboardStore.widgets)
const filters = computed(() => dashboardStore.filters)
const dashboards = computed(() => dashboardStore.dashboards)

const gridContainer = ref(null)
const gridUnitSize = 80
const gridWidth = computed(() => Math.max(1200, window.innerWidth - 100))

const selectedDashboard = computed(() => {
  if (!dashboardStore.currentDashboard) return null
  return dashboards.value.find(d => d.name === dashboardStore.currentDashboard?.name)
})

const dashboardOptions = computed(() => [
  ...dashboards.value.map(d => ({
    label: d.dashboard_name,
    onClick: () => loadDashboard(d.name)
  })),
  { label: __('Manage Dashboards...'), onClick: () => goToBuilder() }
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

function goToBuilder() {
  router.push({ name: 'Dashboard Builder' })
}

async function loadDashboard(name) {
  try {
    await dashboardStore.loadDashboard(name)
    dashboardStore.setEditMode(false)
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
}

onMounted(async () => {
  try {
    await dashboardStore.loadDashboard()
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  } finally {
    dashboardStore.setEditMode(false)
  }
})
</script>
