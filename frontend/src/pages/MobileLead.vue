<template>
  <div v-if="document.doc" class="flex flex-col h-full bg-white">
    <div class="flex items-center justify-between h-12 border-b px-3 py-2.5">
      <div class="flex items-center gap-2">
        <CustomActions
          v-if="lead.data._customActions?.length"
          :actions="lead.data._customActions"
        />
        <CustomActions
          v-if="document.actions?.length"
          :actions="document.actions"
        />
      </div>
      <div class="flex items-center gap-2">
        <div v-if="document.doc && ['Contacted', 'Nurture'].includes(document.doc.status)" class="flex items-center gap-2">
          <span class="text-sm text-ink-gray-5">{{ __('Meeting Outcome') }}:</span>
          <Dropdown
            :options="meetingOutcomeOptions"
          >
            <template #default>
              <Button icon="more-horizontal">
                <template #prefix v-if="document.doc.meeting_outcomes">
                  <IndicatorIcon
                    :class="getOutcomeColor(document.doc.meeting_outcomes)"
                  />
                </template>
              </Button>
            </template>
          </Dropdown>
        </div>
        <Button
          v-if="['Contacted', 'Nurture'].includes(document.doc?.status) && document.doc?.meeting_outcomes === 'Qualified'"
          :label="__('Convert')"
          variant="solid"
          @click="showConvertToDealModal = true"
        />
      </div>
    </div>
    <div v-if="lead?.data" class="flex h-full overflow-hidden">
      <Tabs as="div" v-model="tabIndex" :tabs="tabs" class="overflow-auto">
        <template #tab-panel="{ tab }">
          <div v-if="tab.name == 'Details'">
            <SLASection
              v-if="lead.data.sla_status"
              v-model="lead.data"
              @updateField="updateField"
            />
            <div class="flex flex-col gap-3 p-3">
              <FieldLayout
                v-for="section in sections"
                :key="section.label"
                :label="section.label"
                :fields="section.fields"
              />
            </div>
          </div>
          <div v-else-if="tab.name == 'Activities'" class="h-full flex-1 overflow-auto">
            <Activities
              class="p-3"
              doctype="CRM Lead"
              :docname="document.doc.name"
            />
          </div>
          <div v-else-if="tab.name == 'Attachments'" class="h-full flex-1 overflow-auto">
            <FilesUploader
              class="p-3"
              doctype="CRM Lead"
              :docname="document.doc.name"
              @upload-complete="() => document.reload()"
            />
          </div>
        </template>
      </Tabs>
    </div>
  </div>
  <div v-else-if="lead.error" class="flex h-full items-center justify-center p-4">
    <div class="text-center">
      <div class="mb-4 flex justify-center text-ink-gray-4">
        <Icon name="alert-circle" class="h-10 w-10" />
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
import { capture } from '@/telemetry'
import {
  Button,
  Dropdown,
  Tabs,
  Dialog,
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

const meetingOutcomeColorMap = {
  Qualified: 'text-green-500',
  'Follow-up Required': 'text-blue-500',
  Nurture: 'text-orange-500',
  Disqualified: 'text-red-500',
  Closed: 'text-gray-500',
}

function getOutcomeColor(outcome) {
  return meetingOutcomeColorMap[outcome] || 'text-gray-500'
}

const meetingOutcomeOptions = computed(() => {
  const fields = doctypeMeta['CRM Lead']?.fields || []
  const field = fields.find((f) => f.fieldname === 'meeting_outcomes')
  if (!field || !field.options) return []

  return field.options.split('\n').map((option) => ({
    label: option,
    value: option,
    icon: () => h(IndicatorIcon, { class: getOutcomeColor(option) }),
    onClick: () => {
      triggerOnChange('meeting_outcomes', option)
      document.save.submit()
    },
  }))
})

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

const tabIndex = ref(0)
const tabs = computed(() => {
  let list = [
    {
      name: 'Details',
      label: __('Details'),
      icon: DetailsIcon,
    },
    {
      name: 'Activities',
      label: __('Activities'),
      icon: ActivityIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
  ]
  return list
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
  return mandatoryFields.filter((f) => !document.doc?.[f.fieldname])
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
  const missingFields = getMissingFields(value)

  if (missingFields.length) {
    statusValidation.fields = missingFields
    statusValidation.targetStatus = value
    statusValidation.show = true
    return
  }
  await triggerOnChange('status', value)
  document.save.submit()
}
</script>
