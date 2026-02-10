<template>
  <LayoutHeader v-if="meeting?.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions
        v-if="meeting.data._customActions?.length"
        :actions="meeting.data._customActions"
      />
      <AssignTo
        v-model="assignees.data"
        :data="meeting.data"
        doctype="CRM Meeting"
      />
      <Dropdown :options="meetingStatusOptions">
        <template #default="{ open }">
          <Button :label="meeting.data.status || 'Open'">
            <template #prefix>
              <IndicatorIcon :class="getStatusColor(meeting.data.status)" />
            </template>
            <template #suffix>
              <FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
              />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div v-if="meeting?.data" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-panel>
        <Activities
          ref="activities"
          doctype="CRM Meeting"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          v-model="meeting"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(meeting.data.name)"
      >
        {{ __(meeting.data.name) }}
      </div>
      <div class="flex items-center justify-start gap-5 border-b p-5">
        <div class="group relative size-12">
          <Avatar
            size="3xl"
            class="size-12"
            :label="title"
            :image="null"
          />
        </div>
        <div class="flex flex-col gap-2.5 truncate">
          <Tooltip :text="meeting.data.lead || __('Meeting Title')">
            <div class="truncate text-2xl font-medium text-ink-gray-9">
              {{ title }}
            </div>
          </Tooltip>
          <div class="flex gap-1.5">
            <Tooltip :text="__('Attach a file')">
              <div>
                <Button class="h-7 w-7" @click="showFilesUploader = true">
                  <AttachmentIcon class="h-4 w-4" />
                </Button>
              </div>
            </Tooltip>
          </div>
        </div>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <div class="flex-1 overflow-y-auto">
          <SidePanelLayout
            :sections="sections.data"
            doctype="CRM Meeting"
            :docname="meeting.data.name"
            @reload="sections.reload"
          />
        </div>
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <FilesUploader
    v-if="meeting.data?.name"
    v-model="showFilesUploader"
    doctype="CRM Meeting"
    :docname="meeting.data.name"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
  setupCustomizations,
  copyToClipboard,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { handleResourceError } from '@/utils/errorHandler'
import {
  createResource,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  Button,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import { useDocument } from '@/data/document'


const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { doctypeMeta } = getMeta('CRM Meeting')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  meetingId: {
    type: String,
    required: true,
  },
})

const errorTitle = ref('')
const errorMessage = ref('')

const { assignees } = useDocument('CRM Meeting', props.meetingId)

const meeting = createResource({
  url: 'frappe.client.get',
  params: { doctype: 'CRM Meeting', name: props.meetingId },
  cache: ['meeting', props.meetingId],
  auto: true,
  onSuccess: (data) => {
    errorTitle.value = ''
    errorMessage.value = ''
    setupCustomizations(meeting, {
      doc: data,
      $dialog,
      $socket,
      router,
      toast,
      updateField,
      createToast: toast.create,
      deleteDoc: deleteMeeting,
      resource: { meeting, sections },
      call,
    })
  },
  onError: (err) => {
    if (err.messages?.[0]) {
      errorTitle.value = __('Not permitted')
      errorMessage.value = __(err.messages?.[0])
    } else {
      router.push({ name: 'Meetings' })
    }
  },
})

onMounted(() => {
  if (meeting?.data) return
  meeting.fetch()
})

const reload = ref(false)
const showFilesUploader = ref(false)

function updateMeeting(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

  if (!Array.isArray(fieldname) && validateRequired(fieldname, value)) return

  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Meeting',
      name: props.meetingId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      meeting.reload()
      reload.value = true
      toast.success(__('Meeting updated successfully'))
      callback?.()
    },
    onError: (err) => {
      handleResourceError(err, 'update meeting')
    },
  })
}

function validateRequired(fieldname, value) {
  let meta = meeting.data.fields_meta || {}
  if (meta[fieldname]?.reqd && !value) {
    toast.error(__('{0} is a required field', [meta[fieldname].label]))
    return true
  }
  return false
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Meetings'), route: { name: 'Meetings' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Meeting')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Meetings',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Meeting', params: { meetingId: meeting.data.name } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta?.['CRM Meeting']?.title_field || 'name'
  return meeting?.data?.[t] || props.meetingId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },
    {
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
    },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
  ]
  return tabOptions
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastMeetingTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Meeting'],
  params: { doctype: 'CRM Meeting' },
  auto: true,
})

// Meeting status options
const meetingStatusOptions = computed(() => [
  {
    label: __('Open'),
    onClick: () => updateField('status', 'Open'),
  },
  {
    label: __('Completed'),
    onClick: () => updateField('status', 'Completed'),
  },
  {
    label: __('Cancelled'),
    onClick: () => updateField('status', 'Cancelled'),
  },
])

function getStatusColor(status) {
  const colors = {
    'Open': 'text-blue-600',
    'Completed': 'text-green-600',
    'Cancelled': 'text-red-600',
  }
  return colors[status] || 'text-gray-600'
}

function updateField(name, value, callback) {
  updateMeeting(name, value, () => {
    meeting.data[name] = value
    callback?.()
  })
}

async function deleteMeeting(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Meeting',
    name,
  })
  router.push({ name: 'Meetings' })
}

const activities = ref(null)
</script>
