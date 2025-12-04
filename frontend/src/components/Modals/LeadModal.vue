<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Lead') }}
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
          <FieldLayout v-if="tabs.data" :tabs="tabs.data" :data="lead.doc" />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isLeadCreating"
            @click="createNewLead"
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
import { sessionStore } from '@/stores/session'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { user } = sessionStore()
const { getUser, isManager } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)

const { document: lead, triggerOnBeforeCreate } = useDocument('CRM Lead')

const leadStatuses = computed(() => {
  let statuses = statusOptions('lead')
  if (!lead.doc.status) {
    lead.doc.status = statuses?.[0]?.value
  }
  return statuses
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Lead'],
  params: { doctype: 'CRM Lead', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = leadStatuses.value
              field.prefix = getLeadStatus(lead.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              lead.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const createLead = createResource({
  url: 'frappe.client.insert',
})

function validateMandatoryFields() {
  error.value = null
  const errors = []

  // Get all fields from tabs
  const allFields = []
  if (tabs.data) {
    tabs.data.forEach(tab => {
      tab.sections.forEach(section => {
        section.columns.forEach(column => {
          column.fields.forEach(field => {
            allFields.push(field)
          })
        })
      })
    })
  }

  // Validate each field
  allFields.forEach(field => {
    // Check if field is mandatory
    const isRequired = field.reqd ||
      (field.mandatory_depends_on && evaluateMandatoryDependsOn(field.mandatory_depends_on))

    if (!isRequired || field.read_only || field.hidden) {
      return
    }

    // Check if field is visible based on depends_on
    if (field.depends_on && !evaluateDependsOn(field.depends_on)) {
      return
    }

    // Check if field has a value
    const value = lead.doc[field.fieldname]
    const isEmpty = value === null || value === undefined || value === '' ||
                    (Array.isArray(value) && value.length === 0)

    if (isEmpty) {
      errors.push(__(`{0} is mandatory`, [__(field.label)]))
    }
  })

  // Additional custom validations
  if (lead.doc.annual_revenue) {
    if (typeof lead.doc.annual_revenue === 'string') {
      lead.doc.annual_revenue = lead.doc.annual_revenue.replace(/,/g, '')
    } else if (isNaN(lead.doc.annual_revenue)) {
      errors.push(__('Annual Revenue should be a number'))
    }
  }

  if (lead.doc.mobile_no && isNaN(lead.doc.mobile_no.replace(/[-+() ]/g, ''))) {
    errors.push(__('Mobile No should be a number'))
  }

  if (lead.doc.email && !lead.doc.email.includes('@')) {
    errors.push(__('Invalid Email'))
  }

  if (errors.length > 0) {
    error.value = errors.join('\n')
    return error.value
  }

  return null
}

function evaluateDependsOn(expression) {
  if (!expression) return true
  if (expression.startsWith('eval:')) {
    try {
      const code = expression.substring(5)
      const func = new Function('doc', `return ${code}`)
      return func(lead.doc)
    } catch (e) {
      console.error('Error evaluating depends_on:', e)
      return true
    }
  }
  return !!lead.doc[expression]
}

function evaluateMandatoryDependsOn(expression) {
  if (!expression) return false
  if (expression.startsWith('eval:')) {
    try {
      const code = expression.substring(5)
      const func = new Function('doc', `return ${code}`)
      return func(lead.doc)
    } catch (e) {
      console.error('Error evaluating mandatory_depends_on:', e)
      return false
    }
  }
  return !!lead.doc[expression]
}

async function createNewLead() {
  if (lead.doc.website && !lead.doc.website.startsWith('http')) {
    lead.doc.website = 'https://' + lead.doc.website
  }

  await triggerOnBeforeCreate?.()

  createLead.submit(
    {
      doc: {
        doctype: 'CRM Lead',
        ...lead.doc,
      },
    },
    {
      validate() {
        const validationError = validateMandatoryFields()
        if (validationError) {
          return validationError
        }
        if (lead.doc.status && lead.doc.status !== 'New') {
          error.value = __('Leads can only be created with "New" status')
          return error.value
        }
        isLeadCreating.value = true
      },
      onSuccess(data) {
        capture('lead_created')
        isLeadCreating.value = false
        show.value = false
        router.push({ name: 'Lead', params: { leadId: data.name } })
        updateOnboardingStep('create_first_lead', true, false, () => {
          localStorage.setItem('firstLead' + user, data.name)
        })
      },
      onError(err) {
        isLeadCreating.value = false
        if (!err.messages) {
          error.value = err.message
          return
        }
        error.value = err.messages.join('\n')
      },
    },
  )
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Lead' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  lead.doc = { no_of_employees: '1-10' }
  Object.assign(lead.doc, props.defaults)

  if (!lead.doc?.lead_owner) {
    lead.doc.lead_owner = getUser().name
  }
  // Ensure status defaults to 'New' if not set or if invalid status is passed
  if (!lead.doc?.status) {
    // Find 'New' status from available statuses
    const newStatus = leadStatuses.value.find((s) => s.value === 'New')
    lead.doc.status = newStatus?.value || leadStatuses.value[0]?.value || 'New'
  } else if (lead.doc.status !== 'New') {
    // If a non-'New' status is provided, override it to 'New'
    lead.doc.status = 'New'
  }
})
</script>
