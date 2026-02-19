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
          <!-- Duplicate Warning Banner -->
          <div
            v-if="duplicateWarning.show"
            ref="duplicateWarningRef"
            class="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 sm:p-4"
          >
            <!-- Header -->
            <div class="flex items-start gap-2 sm:gap-3">
              <FeatherIcon
                name="alert-triangle"
                class="size-5 text-amber-600 shrink-0 mt-0.5"
              />
              <div class="flex-1 min-w-0">
                <h4 class="text-sm font-medium text-amber-800">
                  {{ __('Potential Duplicates Found') }}
                </h4>
                <p class="mt-1 text-xs sm:text-sm text-amber-700">
                  {{ __('Similar records already exist. Please review before creating.') }}
                </p>
              </div>
              <button
                @click="duplicateWarning.show = false"
                class="text-amber-600 hover:text-amber-800 p-1 -m-1"
              >
                <FeatherIcon name="x" class="size-5 sm:size-4" />
              </button>
            </div>

            <!-- Existing Leads -->
            <div v-if="duplicateWarning.leads.length > 0" class="mt-3">
              <p class="text-xs font-medium text-amber-800 uppercase tracking-wide mb-2">
                {{ __('Existing Leads') }}
              </p>
              <div class="space-y-2">
                <div
                  v-for="dup in duplicateWarning.leads"
                  :key="dup.name"
                  class="bg-white rounded-md p-3 border border-amber-200"
                >
                  <!-- Mobile: Stacked layout -->
                  <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-ink-gray-9 break-words">
                        {{ dup.lead_name || dup.organization || dup.email }}
                      </p>
                      <!-- Mobile: Stack details vertically -->
                      <div class="mt-1 text-xs text-ink-gray-5 space-y-0.5 sm:space-y-0">
                        <p v-if="dup.organization" class="sm:inline">
                          {{ dup.organization }}
                          <span class="hidden sm:inline"> · </span>
                        </p>
                        <p v-if="dup.email" class="sm:inline break-all">
                          {{ dup.email }}
                          <span class="hidden sm:inline" v-if="dup.mobile_no"> · </span>
                        </p>
                        <p v-if="dup.mobile_no" class="sm:inline">
                          {{ dup.mobile_no }}
                        </p>
                      </div>
                      <p class="text-xs text-amber-600 mt-1">
                        {{ __('Matched by:') }} {{ dup.match_reasons.join(', ') }}
                      </p>
                    </div>
                    <!-- Mobile: Full-width action row -->
                    <div class="flex items-center justify-between sm:justify-end gap-2 pt-2 sm:pt-0 border-t border-amber-100 sm:border-0 sm:ml-3">
                      <Badge :label="dup.status" variant="subtle" theme="orange" />
                      <Button
                        variant="outline"
                        size="sm"
                        :label="__('View Lead')"
                        class="flex-1 sm:flex-initial"
                        @click="openLeadInNewTab(dup.name)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Existing Organizations -->
            <div v-if="duplicateWarning.organizations.length > 0" class="mt-3">
              <p class="text-xs font-medium text-amber-800 uppercase tracking-wide mb-2">
                {{ __('Existing Organizations') }}
              </p>
              <div class="space-y-2">
                <div
                  v-for="org in duplicateWarning.organizations"
                  :key="org.name"
                  class="bg-white rounded-md p-3 border border-amber-200"
                >
                  <!-- Mobile: Stacked layout -->
                  <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-ink-gray-9 break-words">
                        {{ org.organization_name }}
                      </p>
                      <div class="mt-1 text-xs text-ink-gray-5 space-y-0.5 sm:space-y-0">
                        <p v-if="org.industry" class="sm:inline">
                          {{ org.industry }}
                          <span class="hidden sm:inline" v-if="org.deal"> · </span>
                        </p>
                        <p v-if="org.deal" class="sm:inline">
                          {{ __('Deal') }}: {{ org.deal }}
                          <span v-if="org.deal_status"> ({{ org.deal_status }})</span>
                        </p>
                      </div>
                    </div>
                    <!-- Mobile: Full-width action row -->
                    <div class="flex items-center justify-between sm:justify-end gap-2 pt-2 sm:pt-0 border-t border-amber-100 sm:border-0 sm:ml-3">
                      <Badge
                        v-if="org.deal"
                        :label="__('Has Deal')"
                        variant="subtle"
                        theme="blue"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        :label="__('View Org')"
                        class="flex-1 sm:flex-initial"
                        @click="openOrganizationInNewTab(org.name)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Existing Contacts -->
            <div v-if="duplicateWarning.contacts.length > 0" class="mt-3">
              <p class="text-xs font-medium text-amber-800 uppercase tracking-wide mb-2">
                {{ __('Existing Contacts') }}
              </p>
              <div class="space-y-2">
                <div
                  v-for="contact in duplicateWarning.contacts"
                  :key="contact.name"
                  class="bg-white rounded-md p-3 border border-amber-200"
                >
                  <!-- Mobile: Stacked layout -->
                  <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-ink-gray-9 break-words">
                        {{ contact.full_name }}
                      </p>
                      <div class="mt-1 text-xs text-ink-gray-5 space-y-0.5 sm:space-y-0">
                        <p v-if="contact.company_name" class="sm:inline">
                          {{ contact.company_name }}
                          <span class="hidden sm:inline" v-if="contact.email || contact.mobile_no"> · </span>
                        </p>
                        <p v-if="contact.email" class="sm:inline break-all">
                          {{ contact.email }}
                          <span class="hidden sm:inline" v-if="contact.mobile_no"> · </span>
                        </p>
                        <p v-if="contact.mobile_no" class="sm:inline">
                          {{ contact.mobile_no }}
                        </p>
                      </div>
                      <p class="text-xs text-amber-600 mt-1">
                        {{ __('Matched by:') }} {{ contact.match_reasons.join(', ') }}
                        <span v-if="contact.linked_deal" class="text-ink-gray-5">
                          · {{ __('Linked to Deal') }}: {{ contact.linked_deal }}
                        </span>
                      </p>
                    </div>
                    <!-- Mobile: Full-width action row -->
                    <div class="flex items-center justify-between sm:justify-end gap-2 pt-2 sm:pt-0 border-t border-amber-100 sm:border-0 sm:ml-3">
                      <Badge
                        v-if="contact.linked_deal"
                        :label="__('Has Deal')"
                        variant="subtle"
                        theme="green"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        :label="__('View Contact')"
                        class="flex-1 sm:flex-initial"
                        @click="openContactInNewTab(contact.name)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Existing Customers -->
            <div v-if="duplicateWarning.customers.length > 0" class="mt-3">
              <p class="text-xs font-medium text-amber-800 uppercase tracking-wide mb-2">
                {{ __('Existing Customers') }}
              </p>
              <div class="space-y-2">
                <div
                  v-for="customer in duplicateWarning.customers"
                  :key="customer.name"
                  class="bg-white rounded-md p-3 border border-amber-200"
                >
                  <!-- Mobile: Stacked layout -->
                  <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-ink-gray-9 break-words">
                        {{ customer.customer_name }}
                      </p>
                      <div class="mt-1 text-xs text-ink-gray-5 space-y-0.5 sm:space-y-0">
                        <p v-if="customer.customer_type" class="sm:inline">
                          {{ customer.customer_type }}
                          <span class="hidden sm:inline" v-if="customer.email || customer.mobile_no"> · </span>
                        </p>
                        <p v-if="customer.email" class="sm:inline break-all">
                          {{ customer.email }}
                          <span class="hidden sm:inline" v-if="customer.mobile_no"> · </span>
                        </p>
                        <p v-if="customer.mobile_no" class="sm:inline">
                          {{ customer.mobile_no }}
                        </p>
                      </div>
                      <p class="text-xs text-amber-600 mt-1">
                        {{ __('Matched by:') }} {{ customer.match_reasons.join(', ') }}
                        <span v-if="customer.territory" class="text-ink-gray-5">
                          · {{ customer.territory }}
                        </span>
                      </p>
                    </div>
                    <!-- Mobile: Full-width action row -->
                    <div class="flex items-center justify-between sm:justify-end gap-2 pt-2 sm:pt-0 border-t border-amber-100 sm:border-0 sm:ml-3">
                      <Badge
                        :label="__('Customer')"
                        variant="subtle"
                        theme="purple"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        :label="__('View Customer')"
                        class="flex-1 sm:flex-initial"
                        @click="openCustomerInNewTab(customer.name)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <p class="mt-3 text-xs text-amber-600 italic text-center sm:text-left">
              {{ __('You can still create this lead if it is not a duplicate.') }}
            </p>
          </div>

          <FieldLayout
            v-if="tabs.data"
            :tabs="tabs.data"
            :data="lead.doc"
          />
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
import { createResource, Badge } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { user } = sessionStore()
const { getUser, isManager } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel()
const emit = defineEmits(['success'])
const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)

const { document: lead, triggerOnBeforeCreate } = useDocument('CRM Lead')

// Ref for duplicate warning banner (for scrolling on mobile)
const duplicateWarningRef = ref(null)

// Duplicate detection state
const duplicateWarning = reactive({
  show: false,
  leads: [],
  organizations: [],
  contacts: [],
  customers: [],
})

// Debounce timer for duplicate checking
let duplicateCheckTimer = null

// Resource for checking duplicates
const checkDuplicates = createResource({
  url: 'crm.fcrm.doctype.crm_lead.crm_lead.check_lead_duplicates',
  onSuccess(data) {
    if (data.has_duplicates) {
      duplicateWarning.leads = data.leads || []
      duplicateWarning.organizations = data.organizations || []
      duplicateWarning.contacts = data.contacts || []
      duplicateWarning.customers = data.customers || []
      duplicateWarning.show = true

      // On mobile, scroll to the warning banner so user sees it
      if (isMobileView.value) {
        nextTick(() => {
          duplicateWarningRef.value?.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
          })
        })
      }
    } else {
      duplicateWarning.show = false
      duplicateWarning.leads = []
      duplicateWarning.organizations = []
      duplicateWarning.contacts = []
      duplicateWarning.customers = []
    }
  },
})

// Debounced duplicate check function
function debouncedDuplicateCheck() {
  if (duplicateCheckTimer) {
    clearTimeout(duplicateCheckTimer)
  }

  duplicateCheckTimer = setTimeout(() => {
    const org = lead.doc.organization
    const email = lead.doc.email

    // Only check if at least one field has meaningful content
    if ((org && org.length >= 2) || email) {
      checkDuplicates.submit({
        organization: org || null,
        email: email || null,
      })
    } else {
      // Clear warnings if no search criteria
      duplicateWarning.show = false
      duplicateWarning.leads = []
      duplicateWarning.organizations = []
      duplicateWarning.contacts = []
      duplicateWarning.customers = []
    }
  }, 500) // 500ms debounce
}

// Watch for changes to lead.doc fields that should trigger duplicate checking
watch(
  () => [lead.doc.organization, lead.doc.email],
  () => {
    debouncedDuplicateCheck()
  },
  { deep: true }
)

// Helper functions for opening records in new tabs
function openLeadInNewTab(leadName) {
  const url = router.resolve({ name: 'Lead', params: { leadId: leadName } })
  window.open(url.href, '_blank')
}

function openOrganizationInNewTab(orgName) {
  const url = router.resolve({ name: 'Organization', params: { organizationId: orgName } })
  window.open(url.href, '_blank')
}

function openContactInNewTab(contactName) {
  // Open contact in Frappe desk since contacts may not have a dedicated CRM page
  window.open(`/app/contact/${contactName}`, '_blank')
}

function openCustomerInNewTab(customerName) {
  // Open customer in Frappe desk
  window.open(`/app/customer/${customerName}`, '_blank')
}

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
        emit('success', data)
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
