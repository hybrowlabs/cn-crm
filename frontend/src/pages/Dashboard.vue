<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <div class="flex items-center gap-2">
        <Dropdown :options="dashboardOptions">
          <Button
            :label="selectedDashboard?.dashboard_name || __('Dashboard')"
            variant="outline"
            class="max-w-[140px] truncate sm:max-w-none"
          >
            <template #suffix>
              <FeatherIcon name="chevron-down" class="h-4 w-4" />
            </template>
          </Button>
        </Dropdown>
        <Button
          variant="subtle"
          @click="refreshDashboard"
          :loading="loading"
          class="items-center px-3"
        >
          <template #prefix>
            <RefreshIcon class="h-4 w-4" />
          </template>
        </Button>
        <Button
          variant="solid"
          @click="goToBuilder"
          class="hidden sm:flex items-center gap-1"
        >
          <template #prefix>
            <FeatherIcon name="layout" class="h-4 w-4" />
          </template>
          {{ __('Dashboard Builder') }}
        </Button>
        <!-- Icon-only on mobile -->
        <Button variant="solid" @click="goToBuilder" class="flex sm:hidden p-2">
          <FeatherIcon name="layout" class="h-4 w-4" />
        </Button>
        <Button
          variant="solid"
          @click="showDealModal = true"
          :label="__('Create Opportunity')"
        >
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </template>
  </LayoutHeader>

  <div class="flex flex-col overflow-auto" style="height: calc(100vh - 4rem)">
    <!-- Empty state -->
    <div v-if="widgets.length === 0" class="flex flex-1 items-center justify-center p-6">
      <div class="text-center">
        <FeatherIcon name="layout" class="mx-auto mb-4 h-10 w-10 text-gray-400 sm:h-12 sm:w-12" />
        <p class="text-sm text-gray-500 sm:text-base">
          {{ __('No widgets yet. Select another dashboard or build one.') }}
        </p>
        <Button variant="solid" class="mt-4" @click="goToBuilder">
          {{ __('Go to Builder') }}
        </Button>
      </div>
    </div>

    <!-- Mobile: stacked cards layout -->
    <div v-else class="block bg-gray-100 p-3 sm:hidden">
      <div
        v-for="(widget, index) in widgets"
        :key="widget.name || `widget-${index}`"
        class="mb-3 rounded-lg border border-gray-200 bg-white shadow-sm overflow-hidden"
        style="min-height: 200px"
      >
        <component
          :is="getWidgetComponent(widget.widget_type)"
          :widget="widget"
          :filters="filters"
          :is-edit-mode="false"
        />
      </div>
    </div>

    <!-- Desktop: absolute positioned grid -->
    <div v-if="widgets.length > 0" class="hidden flex-1 overflow-auto bg-gray-100 p-6 sm:block">
      <div
        ref="gridContainer"
        class="relative mx-auto"
        :style="{ width: `${gridWidth}px`, height: `${gridHeight}px` }"
      >
        <div
          v-for="(widget, index) in widgets"
          :key="widget.name || `widget-${index}`"
          class="absolute rounded-lg border-2 border-transparent transition-all"
          :style="{
            left: `${(widget.x_position || 0) * gridUnitSize}px`,
            top: `${(widget.y_position || 0) * gridUnitSize}px`,
            width: `${(widget.width || 12) * gridUnitSize}px`,
            height: `${(widget.height || 6) * gridUnitSize}px`
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
  <DealModal v-model="showDealModal" />
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
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import DealModal from '@/components/Modals/DealModal.vue'

const router = useRouter()
const dashboardStore = useDashboardStore()
const loading = ref(false)
const showDealModal = ref(false)

const title = 'Dashboard'
const breadcrumbs = [{ label: title, route: { name: 'Dashboard' } }]

const widgets = computed(() => dashboardStore.widgets)
const filters = computed(() => dashboardStore.filters)
const dashboards = computed(() => dashboardStore.dashboards)

const gridContainer = ref(null)
const gridUnitSize = 80
const gridWidth = computed(() => Math.max(1200, window.innerWidth - 100))
const gridHeight = computed(() => {
  if (!widgets.value.length) return 600
  return Math.max(...widgets.value.map(w => ((w.y_position || 0) + (w.height || 6)) * gridUnitSize)) + 80
})

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
  loading.value = true
  try {
    await dashboardStore.loadDashboard(name)
    dashboardStore.setEditMode(false)
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  } finally {
    loading.value = false
  }
}

function refreshDashboard() {
  if (dashboardStore.currentDashboard?.name) {
    loadDashboard(dashboardStore.currentDashboard.name)
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
