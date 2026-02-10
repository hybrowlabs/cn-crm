<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Meetings" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="meetingsListView?.customListActions"
        :actions="meetingsListView.customListActions"
      />
      <!-- <Button
        variant="solid"
        :label="__('Create')"
        @click="showMeetingModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button> -->
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="meetings"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Meeting"
  />
  <MeetingListView
    ref="meetingsListView"
    v-if="meetings.data && rows.length"
    v-model="meetings.data.page_length_count"
    v-model:list="meetings"
    :rows="rows"
    :columns="meetings.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: meetings.data.row_count,
      totalCount: meetings.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <div
    v-else-if="meetings.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
    >
      <CalendarIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Meetings')]) }}</span>
      <Button :label="__('Create')" @click="showMeetingModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <MeetingModal
    v-if="showMeetingModal"
    v-model="showMeetingModal"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import MeetingModal from '@/components/Modals/MeetingModal.vue'
import MeetingListView from '@/components/ListViews/MeetingListView.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { ref, computed } from 'vue'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Meeting')

const meetingsListView = ref(null)
const showMeetingModal = ref(false)

// meetings data is loaded in the ViewControls component
const meetings = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !meetings.value?.data?.data ||
    !['list', 'group_by'].includes(meetings.value.data.view_type)
  )
    return []
  return meetings.value?.data.data.map((meeting) => {
    let _rows = {}
    meetings.value?.data.rows.forEach((row) => {
      _rows[row] = meeting[row]

      let fieldType = meetings.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(
          meeting[row],
          '',
          true,
          fieldType == 'Datetime',
        )
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, meeting)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, meeting)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, meeting)
      }

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(meeting[row]),
          timeAgo: __(timeAgo(meeting[row])),
        }
      }
    })
    return _rows
  })
})
</script>
