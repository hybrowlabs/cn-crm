<template>
  <div v-if="document.doc" class="flex flex-col h-full bg-white">
    <LayoutHeader>
      <template #left-header>
        <div class="flex-shrink min-w-0 overflow-hidden">
          <Breadcrumbs :items="breadcrumbs" class="truncate">
            <template #prefix="{ item }">
              <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
            </template>
          </Breadcrumbs>
        </div>
      </template>
      <template #right-header>
        <Dropdown
          v-if="document.doc"
          :options="
            statusOptions(
              'lead',
              document.statuses?.length
                ? document.statuses
                : lead.data?._customStatuses,
              triggerStatusChange,
              document.doc.status,
              { [document.doc.status]: statusVisibility }
            )
          "
        >
          <template #default>
            <Button :label="document.doc.status">
              <template #prefix>
                <IndicatorIcon
                  :class="getLeadStatus(document.doc.status).color"
                />
              </template>
              <template #suffix="{ open }">
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
    <div
      v-if="document.doc"
      class="flex h-12 items-center justify-between gap-2 border-b px-3 py-2.5"
    >
      <AssignTo
        v-model="assignees.data"
        :data="document.doc"
        doctype="CRM Lead"
      />
      <div class="flex items-center gap-2">
        <Button
          v-if="isQualified"
          :label="__('Convert to Deal')"
          variant="solid"
          @click="showConvertToDealModal = true"
        />
        <CustomActions
          v-if="lead.data?._customActions?.length"
          :actions="lead.data._customActions"
        />
        <CustomActions
          v-if="document.actions?.length"
          :actions="document.actions"
        />
      </div>
    </div>

    <div v-if="lead?.data" class="flex h-full overflow-hidden">
      <Tabs as="div" v-model="tabIndex" :tabs="tabs" class="flex flex-col flex-1 overflow-hidden">
        <template #tab-panel="{ tab }">
          <Activities
            ref="activities"
            doctype="CRM Lead"
            :tabs="tabs"
            v-model:reload="reload"
            v-model:tabIndex="tabIndex"
            v-model="lead"
            :linkedVisits="linkedVisits"
            @afterSave="handleAfterSave"
            @reloadVisits="reloadVisits"
          />
        </template>
      </Tabs>
    </div>
  </div>
  <div v-else-if="lead.error" class="flex h-full items-center justify-center p-4">
    <div class="text-center">
      <div class="mb-4 flex justify-center text-ink-gray-4">
        <Icon icon="alert-circle" class="h-10 w-10" />
      </div>
      <h3 class="mb-2 text-lg font-bold text-ink-gray-9">
        {{ __("Couldn't find Lead") }}
      </h3>
      <p class="mb-6 text-sm text-ink-gray-5">
        {{ lead.error.message || __("The lead you're looking for doesn't exist or you don't have permission to view it.") }}
      </p>
      <Button :label="__('Go Back')" @click="router.back()" />
    </div>
  </div>
  <div v-else class="flex h-full items-center justify-center p-4">
    <Icon name="loader" class="h-6 w-6 animate-spin text-ink-gray-4" />
  </div>

  <ConvertToDealModal
    v-if="showConvertToDealModal"
    v-model="showConvertToDealModal"
    :lead="lead.data"
    @next="
      (data) => {
        conversionData = data
        showConvertToDealModal = false
        showDealDetailModal = true
      }
    "
  />
  <DealDetailModal
    v-if="showDealDetailModal"
    v-model="showDealDetailModal"
    :lead="lead.data"
    :deal="conversionData.deal"
    :existingContact="conversionData.existingContact"
    :existingOrganization="conversionData.existingOrganization"
  />
  <StatusValidationModal
    v-if="statusValidation.show"
    v-model="statusValidation.show"
    :fields="statusValidation.fields"
    :targetStatus="statusValidation.targetStatus"
    :doc="document.doc"
    @proceed="proceedWithStatusChange"
  />
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import VisitsIcon from '@/components/Icons/VisitsIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import Link from '@/components/Controls/Link.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import CustomActions from '@/components/CustomActions.vue'
import StatusValidationModal from '@/components/Modals/StatusValidationModal.vue'
import DealDetailModal from '@/components/Modals/DealDetailModal.vue'
import { getFieldsForValidation } from '@/utils/validation'
import { setupCustomizations } from '@/utils'
import { getView } from '@/utils/view'
import { capture } from '@/telemetry'
import {
  Button,
  Dropdown,
  Tabs,
  Dialog,
  Breadcrumbs,
  FeatherIcon,
  call,
  toast,
  createResource,
} from 'frappe-ui'
import { ref, h, computed, reactive, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { whatsappEnabled, callEnabled } from '@/composables/settings'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()

const { assignees, document, triggerOnChange } = useDocument(
  'CRM Lead',
  props.leadId,
)

provide('data', document.doc)
provide('doctype', 'CRM Lead')
provide('preview', ref(false))
provide('isGridRow', false)

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Lead')

const lead = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead',
  params: { name: props.leadId },
  cache: ['lead', props.leadId],
  auto: true,
  onSuccess: (data) => {
    setupCustomizations(lead, {
      doc: data,
      $dialog,
      $socket,
      router,
      toast,
      updateField,
      createToast: toast.create,
      deleteDoc: deleteLead,
      resource: {
        lead,
        sections,
      },
      call,
    })
  },
})

const visits = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead_visits',
  params: { name: props.leadId },
  cache: ['lead', 'visits', props.leadId],
  auto: true,
  onSuccess: (data) => {
    linkedVisits.value = data
  },
})

const reload = ref(false)
const linkedVisits = ref([])
const activities = ref(null)

const tabs = computed(() => {
  let list = [
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
      label: __('Lead Data'),
      icon: DetailsIcon,
      condition: () =>
        !['Contacted', 'Nurture', 'Qualified'].includes(document.doc?.status),
    },
    {
      name: 'Meeting Data',
      label: __('Meeting Data'),
      icon: DetailsIcon,
      condition: () =>
        ['Contacted', 'Nurture', 'Qualified'].includes(document.doc?.status),
    },
    {
      name: 'Meetings',
      label: __('Meetings'),
      icon: VisitsIcon,
    },
    {
      name: 'Calls',
      label: __('Calls'),
      icon: PhoneIcon,
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
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return list.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastLeadTab')

function reloadVisits() {
  visits.reload()
}

function handleAfterSave(data) {
  if (data) {
    Object.assign(document.doc, data)
    if (lead.data) {
      Object.assign(lead.data, data)
    }
  }
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: lead.data?.name
      ? { name: 'Lead', params: { leadId: lead.data.name } }
      : undefined,
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['CRM Lead']?.title_field || 'name'
  return lead.data?.[t] || props.leadId
})

const statusVisibility = computed(() => {
  const status = document.doc?.status
  if (status === 'New') {
    return ['New', 'Contacted', 'Nurture', 'Disqualified', 'Junk']
  } else if (['Contacted', 'Nurture', 'Qualified'].includes(status)) {
    return ['Contacted', 'Nurture', 'Qualified', 'Disqualified', 'Junk']
  } else {
    // Junk, Disqualified, etc.
    return ['Contacted', 'Nurture', 'Disqualified', 'Junk']
  }
})

const isQualified = computed(() => {
  return (
    document.doc?.status === 'Qualified' ||
    lead.data?.status === 'Qualified'
  )
})

const sections = computed(() => {
  if (!lead.data) return []
  return lead.data._sections || []
})

const showConvertToDealModal = ref(false)
const showDealDetailModal = ref(false)
const conversionData = ref({})

async function updateField(fieldname, value) {
  await triggerOnChange(fieldname, value)
  document.reload()
}

async function deleteLead() {
  await call('frappe.client.delete', {
    doctype: 'CRM Lead',
    name: props.leadId,
  })
  router.push({ name: 'Leads' })
}



const statusValidation = reactive({
  show: false,
  fields: [],
  targetStatus: '',
})

function getMissingFields(targetStatus) {
  const mandatoryFields = getFieldsForValidation('CRM Lead', targetStatus)
  return mandatoryFields.filter((f) => {
    if (['primary_pain_category', 'technical_pain_category'].includes(f.fieldname)) {
      return !document.doc?.primary_pain_category?.length && !document.doc?.technical_pain_category?.length
    }
    return !document.doc?.[f.fieldname]
  })
}

async function proceedWithStatusChange() {
  const missingFields = getMissingFields(statusValidation.targetStatus)
  if (missingFields.length) {
    toast.error(__('Please fill all required fields'))
    return
  }
  await triggerOnChange('status', statusValidation.targetStatus)
  await document.save.submit()
  statusValidation.show = false
}

//add validation for meeting stage here 
async function triggerStatusChange(value) {
  const allValidationFields = getFieldsForValidation('CRM Lead', value)

  if (allValidationFields.length) {
    statusValidation.fields = allValidationFields
    statusValidation.targetStatus = value
    statusValidation.show = true
    return
  }
  await triggerOnChange('status', value)
  document.save.submit()
}
</script>
