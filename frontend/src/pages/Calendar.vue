<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Calendar" />
    </template>
  </LayoutHeader>
  <div class="flex h-screen px-5 flex-col overflow-hidden">
    <Calendar
      :key="calendarKey"
      :config="{
        defaultMode: 'Day',
        isEditMode: true,
        eventIcons: {
        },
        allowCustomClickEvents: true,
        redundantCellHeight: 100,
        enableShortcuts: false,
        noBorder: !true,
      }"
      :events="calendarEvents"
    >
      <template
        #header="{
          currentMonthYear,
          enabledModes,
          activeView,
          decrement,
          increment,
          updateActiveView,
        }"
      >
        <div class="my-4 flex justify-between">
          <!-- left side  -->
          <!-- Year, Month -->
          <span class="text-lg font-medium text-ink-gray-8">
            {{ currentMonthYear }}
          </span>
          <!-- right side -->
          <!-- actions buttons for calendar -->
          <div class="flex gap-x-1">
            <!-- Increment and Decrement Button-->

            <Button
              @click="decrement()"
              variant="ghost"
              class="h-4 w-4"
              icon="chevron-left"
            />
            <Button
              @click="increment()"
              variant="ghost"
              class="h-4 w-4"
              icon="chevron-right"
            />

            <!--  View change button, default is months or can be set via props!  -->
            <TabButtons
              :buttons="enabledModes"
              class="ml-2"
              :modelValue="activeView"
              @update:modelValue="updateActiveView($event)"
            />
          </div>
        </div>
      </template>
    </Calendar>
  </div>
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { sessionStore } from '@/stores/session'
import { Calendar, createListResource, TabButtons, Button } from 'frappe-ui'
import { watch, ref, computed } from 'vue';

const { user } = sessionStore()

console.log('Current user:', user)

const events = createListResource({
  doctype: 'Event',
  fields: ['name', 'status', 'subject', 'starts_on', 'ends_on', 'color'],
  filters: { status: 'Open' },
  auto: true,
  transform: (data) => {
    console.log('Events raw data:', data)
    const transformed = data.map((event) => {
      const eventObj = {
        id: event.name,
        title: event.subject,
        fromDate: event.starts_on,
        toDate: event.ends_on,
        color: event.color || '#3b82f6',
      }
      console.log('Individual event transformed:', eventObj)
      return eventObj
    })
    console.log('Events transformed data:', transformed)
    return transformed
  },
})

// Watch events data changes
watch(() => events.data, (newEvents) => {
  console.log('Events data changed:', newEvents)
  if (newEvents?.length > 0) {
    console.log('Sample event:', newEvents[0])
  }
}, { deep: true })

const calendarKey = ref(0)
const calendarEvents = computed(() => {
  console.log('Computing calendar events:', events.data)
  return events.data || []
})

// Force calendar re-render when events change
watch(() => events.data, () => {
  console.log('Forcing calendar re-render')
  calendarKey.value++
})

</script>