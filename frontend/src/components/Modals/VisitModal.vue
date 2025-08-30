<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Site Visit') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              @click="openQuickEntryModal"
            >
              <template #icon>
                <EditIcon />
              </template>
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <template #icon>
                <FeatherIcon name="x" class="size-4" />
              </template>
            </Button>
          </div>
        </div>
        <div>
          <FieldLayout 
            v-if="tabs.data" 
            :tabs="tabs.data" 
            :data="visit.doc" 
            doctype="CRM Site Visit"
          />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isVisitCreating"
            @click="createVisit"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useDocument } from '@/data/document'
import { capture } from '@/telemetry'
import { handleResourceError } from '@/utils/errorHandler'
import { createResource } from 'frappe-ui'
import { computed, ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { getUser, isManager } = usersStore()
const { statusOptions } = statusesStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isVisitCreating = ref(false)

const { document: visit, triggerOnBeforeCreate } = useDocument('CRM Site Visit')

const visitStatuses = computed(() => {
  let statuses = [
    { label: 'Planned', value: 'Planned', color: 'blue' },
    { label: 'In Progress', value: 'In Progress', color: 'orange' },
    { label: 'Completed', value: 'Completed', color: 'green' },
    { label: 'Cancelled', value: 'Cancelled', color: 'red' },
    { label: 'Postponed', value: 'Postponed', color: 'gray' },
  ]
  
  if (!visit.doc.status) {
    visit.doc.status = statuses[0]?.value
  }
  return statuses
})

const visitTypes = computed(() => [
  { label: 'Initial Meeting', value: 'Initial Meeting' },
  { label: 'Demo/Presentation', value: 'Demo/Presentation' },
  { label: 'Negotiation', value: 'Negotiation' },
  { label: 'Contract Signing', value: 'Contract Signing' },
  { label: 'Follow-up', value: 'Follow-up' },
  { label: 'Support', value: 'Support' },
  { label: 'Other', value: 'Other' },
])

const priorityOptions = computed(() => [
  { label: 'Low', value: 'Low' },
  { label: 'Medium', value: 'Medium' },
  { label: 'High', value: 'High' },
  { label: 'Urgent', value: 'Urgent' },
])

const referenceTypes = computed(() => [
  { label: 'CRM Lead', value: 'CRM Lead' },
  { label: 'CRM Deal', value: 'CRM Deal' },
  { label: 'Customer', value: 'Customer' },
])

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Site Visit'],
  params: { doctype: 'CRM Site Visit', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = visitStatuses.value
              field.prefix = getStatusColor(visit.doc.status)
            }

            if (field.fieldname == 'visit_type') {
              field.fieldtype = 'Select'
              field.options = visitTypes.value
            }

            if (field.fieldname == 'priority') {
              field.fieldtype = 'Select'
              field.options = priorityOptions.value
            }

            if (field.fieldname == 'reference_type') {
              field.fieldtype = 'Select'
              field.options = referenceTypes.value
            }

            if (field.fieldtype === 'Table') {
              visit.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

function getStatusColor(status) {
  const statusObj = visitStatuses.value.find(s => s.value === status)
  return statusObj?.color || 'gray'
}

async function createVisit() {
  // Set current date if not provided
  if (!visit.doc.visit_date) {
    visit.doc.visit_date = new Date().toISOString().split('T')[0]
  }

  // Set current user as sales person if not provided
  if (!visit.doc.sales_person) {
    visit.doc.sales_person = getUser().name
  }

  await triggerOnBeforeCreate?.()

  createResource({
    url: 'frappe.client.insert',
    params: {
      doc: {
        doctype: 'CRM Site Visit',
        ...visit.doc,
      },
    },
    auto: true,
    validate() {
      error.value = null

      // Required field validation
      if (!visit.doc.visit_date) {
        error.value = __('Visit Date is required')
        return error.value
      }

      if (!visit.doc.visit_type) {
        error.value = __('Visit Type is required')
        return error.value
      }

      if (!visit.doc.reference_type || !visit.doc.reference_name) {
        error.value = __('Reference (Lead/Deal/Customer) is required')
        return error.value
      }

      if (!visit.doc.sales_person) {
        error.value = __('Sales Person is required')
        return error.value
      }

      if (!visit.doc.visit_purpose) {
        error.value = __('Visit Purpose is required')
        return error.value
      }

      // Phone number validation
      if (visit.doc.contact_phone && isNaN(visit.doc.contact_phone.replace(/[-+() ]/g, ''))) {
        error.value = __('Contact Phone should be a valid number')
        return error.value
      }

      // Email validation
      if (visit.doc.contact_email && !visit.doc.contact_email.includes('@')) {
        error.value = __('Invalid Email')
        return error.value
      }

      // Status validation
      if (!visit.doc.status) {
        error.value = __('Status is required')
        return error.value
      }

      // Potential value validation (if provided)
      if (visit.doc.potential_value && isNaN(visit.doc.potential_value)) {
        error.value = __('Potential Value should be a number')
        return error.value
      }

      // Probability percentage validation (if provided)
      if (visit.doc.probability_percentage && (visit.doc.probability_percentage < 0 || visit.doc.probability_percentage > 100)) {
        error.value = __('Success Probability should be between 0 and 100')
        return error.value
      }

      isVisitCreating.value = true
    },
    onSuccess(data) {
      capture('site_visit_created')
      isVisitCreating.value = false
      show.value = false
      router.push({ name: 'Visit', params: { visitId: data.name } })
    },
    onError(err) {
      isVisitCreating.value = false
      
      // Use global error handler for comprehensive error processing
      handleResourceError(err, 'create site visit')
      
      // Still set local error for component display
      if (err._server_messages || err.exception || err.exc_type) {
        // Global handler will show toast, just set a simple message for component
        error.value = 'Please check the error message above and try again'
      } else if (err.messages && Array.isArray(err.messages)) {
        error.value = err.messages.join('\n')
      } else if (err.message) {
        error.value = err.message
      } else {
        error.value = 'Failed to create site visit'
      }
    },
  })
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Site Visit' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  // Set default values
  visit.doc = {
    visit_date: new Date().toISOString().split('T')[0],
    visit_type: 'Initial Meeting',
    status: 'Planned',
    priority: 'Medium',
  }
  
  // Apply any passed defaults
  Object.assign(visit.doc, props.defaults)

  // Set default sales person
  if (!visit.doc.sales_person) {
    visit.doc.sales_person = getUser().name
  }

  // Set default status
  if (!visit.doc.status && visitStatuses.value[0]?.value) {
    visit.doc.status = visitStatuses.value[0].value
  }
})
</script>