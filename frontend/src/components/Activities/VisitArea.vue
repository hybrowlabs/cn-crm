<template>
  <div v-if="visits.length">
    <div v-for="(visit, i) in visits" :key="visit.name">
      <div
        class="activity flex cursor-pointer gap-4 rounded p-2.5 duration-300 ease-in-out hover:bg-surface-gray-1"
        @click="navigateToVisit(visit)"
      >
        <div class="flex flex-1 flex-col gap-1.5 text-base truncate">
          <div class="font-medium text-ink-gray-9 truncate">
            {{ visit.name }}
          </div>
          <div class="flex flex-wrap gap-1.5 text-ink-gray-8">
            <div v-if="visit.visit_date" class="flex items-center gap-1.5">
              <CalendarIcon />
              <Tooltip :text="formatDate(visit.visit_date, 'ddd, MMM D, YYYY')">
                <div>{{ formatDate(visit.visit_date, 'D MMM, YYYY') }}</div>
              </Tooltip>
            </div>
            <div v-if="visit.visit_type" class="flex items-center justify-center">
              <DotIcon class="h-2.5 w-2.5 text-ink-gray-5" :radius="2" />
            </div>
            <div v-if="visit.visit_type" class="truncate">
              {{ visit.visit_type }}
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-1.5 text-ink-gray-8">
            <div v-if="visit.sales_person" class="flex items-center gap-1.5">
              <UserAvatar :user="visit.sales_person" size="xs" />
              <span class="truncate">{{ getSalesPersonName(visit) }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-center">
          <Badge
            v-if="visit.status"
            :label="visit.status"
            :theme="getStatusTheme(visit.status)"
            variant="subtle"
          />
        </div>
      </div>
      <div
        v-if="i < visits.length - 1"
        class="mx-2 h-px border-t border-outline-gray-modals"
      />
    </div>
  </div>
</template>

<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { formatDate } from '@/utils'
import { Tooltip, Badge } from 'frappe-ui'
import { useRouter } from 'vue-router'

const props = defineProps({
  visits: {
    type: Array,
    default: () => [],
  },
})

const router = useRouter()

function navigateToVisit(visit) {
  router.push({ name: 'Visit', params: { visitId: visit.name } })
}

function getSalesPersonName(visit) {
  if (visit.sales_person_name) return visit.sales_person_name
  if (visit.sales_person?.full_name) return visit.sales_person.full_name
  return visit.sales_person || ''
}

function getStatusTheme(status) {
  const statusThemes = {
    'Planned': 'blue',
    'Confirmed': 'green',
    'In Progress': 'orange',
    'Completed': 'green',
    'Cancelled': 'red',
    'Rescheduled': 'yellow',
  }
  return statusThemes[status] || 'gray'
}
</script>
