<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ isEditMode ? __('Edit Meeting') : __('Create Meeting') }}
            </h3>
            <p v-if="isEditMode && visitId" class="mt-1 text-sm text-ink-gray-6">
              {{ visitId }}
            </p>
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
          <div v-if="tabs.loading" class="py-8 text-center">
            <span class="text-gray-600">Loading form...</span>
          </div>
          <div v-else-if="tabs.error" class="py-8 text-center text-red-600">
            Error loading form: {{ tabs.error }}
          </div>
          <div v-else-if="tabs.data">
            <FieldLayout 
              :tabs="tabs.data" 
              :data="visit.doc" 
              doctype="CRM Site Visit"
            />
          </div>
          <div v-else class="py-8 text-center text-gray-600">
            No form data available
          </div>
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="isEditMode ? __('Save Changes') : __('Create')"
            :loading="isVisitCreating"
            @click="isEditMode ? saveChanges() : createVisit()"
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
import { createResource, call } from 'frappe-ui'
import { computed, ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
  visitId: String,
  visitData: Object,
})

const emit = defineEmits(['updated'])

const { getUser, isManager } = usersStore()
const { statusOptions } = statusesStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isVisitCreating = ref(false)

// Determine if this is edit mode
const isEditMode = computed(() => !!props.visitId)
const originalDoc = ref({})

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
  // Customer removed - only Lead or Deal allowed
])

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Site Visit'],
  params: { doctype: 'CRM Site Visit', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    if (!_tabs || !Array.isArray(_tabs)) {
      return _tabs
    }
    
    
    // Return the transformed tabs array (fix: forEach was returning undefined)
    return _tabs.map((tab) => {
      return {
        ...tab,
        sections: tab.sections.map((section) => ({
          ...section,
          columns: section.columns.map((column) => ({
            ...column,
            fields: column.fields.map((field) => {
              const transformedField = { ...field }
              
              if (field.fieldname == 'status') {
                transformedField.fieldtype = 'Select'
                transformedField.options = visitStatuses.value
                transformedField.prefix = getStatusColor(visit.doc.status)
              }

              if (field.fieldname == 'visit_type') {
                transformedField.fieldtype = 'Select'
                transformedField.options = visitTypes.value
              }

              if (field.fieldname == 'priority') {
                transformedField.fieldtype = 'Select'
                transformedField.options = priorityOptions.value
              }

              if (field.fieldname == 'reference_type') {
                transformedField.fieldtype = 'Select'
                transformedField.options = referenceTypes.value
              }

              if (field.fieldname == 'visit_purpose') {
                transformedField.fieldtype = 'Small Text'
                transformedField.reqd = 1
                // Set default value if not provided
                if (!visit.doc.visit_purpose) {
                  transformedField.default = 'Site visit scheduled'
                }
              }

              if (field.fieldname == 'reference_name' || field.fieldname == 'reference') {
                // Handle Dynamic Link field for reference_name
                if (field.fieldtype === 'Dynamic Link') {
                  // Keep it as Dynamic Link but ensure it has proper options
                  transformedField.options = field.options || 'reference_type'
                } else {
                  // Convert to Link field if not already Dynamic Link
                  transformedField.fieldtype = 'Link'
                }
                
                // Set the options based on the selected reference_type
                if (visit.doc.reference_type) {
                  if (transformedField.fieldtype === 'Link') {
                    transformedField.options = visit.doc.reference_type
                  }
                  transformedField.read_only = 0
                } else {
                  // If no reference_type, disable the field
                  if (transformedField.fieldtype === 'Link') {
                    transformedField.options = ''
                  }
                  transformedField.read_only = 1
                  }
              }

              if (field.fieldtype === 'Table') {
                if (!visit.doc[field.fieldname]) {
                  visit.doc[field.fieldname] = []
                }
              }
              
              return transformedField
            })
          }))
        }))
      }
    })
  },
})

function getStatusColor(status) {
  const statusObj = visitStatuses.value.find(s => s.value === status)
  return statusObj?.color || 'gray'
}

function validateForm() {
  const missingFields = []
  
  if (tabs.data) {
    tabs.data.forEach(tab => {
      tab.sections?.forEach(section => {
        section.columns?.forEach(column => {
          column.fields?.forEach(field => {
            if (field.reqd && !visit.doc[field.fieldname]) {
              missingFields.push(field.label)
            }
          })
        })
      })
    })
  } else {
    // Fallback if tabs not loaded yet (though button should be disabled ideally)
    if (!visit.doc.visit_date) missingFields.push(__('Visit Date'))
    if (!visit.doc.visit_type) missingFields.push(__('Visit Type'))
    if (!visit.doc.reference_name) missingFields.push(__('Reference'))
    if (!visit.doc.sales_person) missingFields.push(__('Sales Person'))
    if (!visit.doc.visit_purpose) missingFields.push(__('Visit Purpose'))
  }

  if (missingFields.length > 0) {
    error.value = __('Missing mandatory fields: {0}', [missingFields.join(', ')])
    return false
  }
  return true
}

async function createVisit() {
  error.value = null
  
  // Set current date if not provided
  if (!visit.doc.visit_date) {
    visit.doc.visit_date = new Date().toISOString().split('T')[0]
  }

  // Set current user as sales person if not provided
  if (!visit.doc.sales_person) {
    visit.doc.sales_person = getUser().name
  }

  // Pre-validation - check required fields before API call
  if (!validateForm()) return

  // Additional validations
  if (visit.doc.contact_phone && isNaN(visit.doc.contact_phone.replace(/[-+() ]/g, ''))) {
    error.value = __('Contact Phone should be a valid number')
    return
  }

  if (visit.doc.contact_email && !visit.doc.contact_email.includes('@')) {
    error.value = __('Invalid Email')
    return
  }

  if (visit.doc.potential_value && isNaN(visit.doc.potential_value)) {
    error.value = __('Potential Value should be a number')
    return
  }

  if (visit.doc.probability_percentage && (visit.doc.probability_percentage < 0 || visit.doc.probability_percentage > 100)) {
    error.value = __('Success Probability should be between 0 and 100')
    return
  }

  try {
    await triggerOnBeforeCreate?.()

    // Prepare visit data for insertion
    const visitData = {
      doctype: 'CRM Site Visit',
      ...visit.doc,
      // Ensure required fields with defaults are set
      status: visit.doc.status || 'Planned',
      naming_series: visit.doc.naming_series || 'SV-.YYYY.-',
      priority: visit.doc.priority || 'Medium',
      // Ensure visit_purpose is not empty
      visit_purpose: visit.doc.visit_purpose || 'Site visit scheduled'
    }

    isVisitCreating.value = true

    const insertResource = createResource({
      url: 'frappe.client.insert',
      params: { doc: visitData },
      auto: false
    })

    const result = await insertResource.submit()
    capture('site_visit_created')
    isVisitCreating.value = false
    show.value = false
    
    // Navigate to the created visit
    if (result && result.name) {
      router.push({ name: 'Visit', params: { visitId: result.name } })
    }

  } catch (err) {
    isVisitCreating.value = false
    
    // Use global error handler for comprehensive error processing
    handleResourceError(err, 'create Meeting')
    
    // Set specific local error message
    if (err._server_messages) {
      try {
        const messages = JSON.parse(err._server_messages)
        error.value = messages[0]?.message || 'Failed to create Meeting'
      } catch {
        error.value = 'Server error occurred while creating Meeting'
      }
    } else if (err.exception) {
      error.value = 'Please check all required fields and try again'
    } else if (err.exc_type) {
      error.value = err.message || 'Validation error - please check your input'
    } else if (err.messages && Array.isArray(err.messages)) {
      error.value = err.messages.join('\n')
    } else if (err.message) {
      error.value = err.message
    } else {
      error.value = 'Failed to create Meeting. Please try again.'
    }
  }
}

async function saveChanges() {
  error.value = null
  
  if (!validateForm()) return

  try {
    isVisitCreating.value = true
    
    // Get only changed fields
    const changedFields = {}
    Object.keys(visit.doc).forEach(key => {
      if (['modified', 'modified_by', 'creation', 'owner'].includes(key)) return
      if (JSON.stringify(originalDoc.value[key]) !== JSON.stringify(visit.doc[key])) {
        changedFields[key] = visit.doc[key]
      }
    })

    if (Object.keys(changedFields).length > 0) {
      const updateResource = createResource({
        url: 'frappe.client.set_value',
        params: {
          doctype: 'CRM Site Visit',
          name: props.visitId,
          fieldname: changedFields,
        },
        auto: false
      })

      await updateResource.submit()
    }

    isVisitCreating.value = false
    show.value = false
    emit('updated')
    
  } catch (err) {
    isVisitCreating.value = false
    handleResourceError(err, 'update site visit')
    
    if (err._server_messages) {
      try {
        const messages = JSON.parse(err._server_messages)
        error.value = messages[0]?.message || 'Failed to update site visit'
      } catch {
        error.value = 'Server error occurred while updating visit'
      }
    } else if (err.message) {
      error.value = err.message
    } else {
      error.value = 'Failed to update site visit. Please try again.'
    }
  }
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Site Visit' }
  nextTick(() => (show.value = false))
}

// Watch for reference_type changes to update reference_name field options
watch(() => visit.doc.reference_type, (newType, oldType) => {
  if (newType !== oldType) {
    // Clear reference_name if reference_type changes to a different value
    if (oldType && newType !== oldType) {
      visit.doc.reference_name = null
      // Clear autofilled fields when reference type changes
      visit.doc.contact_phone = null
      visit.doc.contact_email = null
      visit.doc.reference_title = null
      visit.doc.potential_value = null
      visit.doc.probability_percentage = null
    }
    // Force tabs to re-transform to update reference_name field options
    nextTick(() => {
      tabs.reload()
    })
  }
}, { 
  immediate: false // Don't trigger on initial mount, only on actual changes
})

// Watch for reference_name changes to autofill data
watch(() => visit.doc.reference_name, async (newName, oldName) => {
  if (newName && newName !== oldName && visit.doc.reference_type) {
    // Only autofill if fields are empty to avoid overwriting user input
    const shouldAutofill = !visit.doc.contact_phone && !visit.doc.contact_email && 
                          !visit.doc.reference_title && !visit.doc.potential_value
    
    if (shouldAutofill) {
      try {
        const autofillData = await call('crm.api.form_controller.auto_populate_form_data', {
          reference_type: visit.doc.reference_type,
          reference_name: newName,
          customer_address: visit.doc.customer_address
        })
        
        if (autofillData) {
          // Only populate empty fields
          if (autofillData.reference_title && !visit.doc.reference_title) {
            visit.doc.reference_title = autofillData.reference_title
          }
          if (autofillData.contact_phone && !visit.doc.contact_phone) {
            visit.doc.contact_phone = autofillData.contact_phone
          }
          if (autofillData.contact_email && !visit.doc.contact_email) {
            visit.doc.contact_email = autofillData.contact_email
          }
          if (autofillData.city && !visit.doc.city) {
            visit.doc.city = autofillData.city
          }
          if (autofillData.state && !visit.doc.state) {
            visit.doc.state = autofillData.state
          }
          if (autofillData.country && !visit.doc.country) {
            visit.doc.country = autofillData.country
          }
          if (autofillData.potential_value && !visit.doc.potential_value) {
            visit.doc.potential_value = autofillData.potential_value
          }
          if (autofillData.probability_percentage !== undefined && !visit.doc.probability_percentage) {
            visit.doc.probability_percentage = autofillData.probability_percentage
          }
          if (autofillData.sales_person && !visit.doc.sales_person) {
            visit.doc.sales_person = autofillData.sales_person
          }
          if (autofillData.organization && !visit.doc.company) {
            visit.doc.company = autofillData.organization
          }
        }
      } catch (err) {
        console.error('Failed to autofill reference data:', err)
        // Don't show error to user, just log it
      }
    }
  }
}, { 
  immediate: false 
})

// Function to apply defaults to visit.doc
function applyDefaults() {
  
  if (isEditMode.value && props.visitData) {
    visit.doc = { ...props.visitData }
    originalDoc.value = { ...props.visitData }
  } else {
    visit.doc = {
      visit_date: new Date().toISOString().split('T')[0],
      visit_type: 'Initial Meeting',
      status: 'Planned',
      priority: 'Medium',
      naming_series: 'SV-.YYYY.-',
      visit_purpose: 'Site visit scheduled',
      sales_person: getUser().name,
      ...props.defaults
    }
  }
}

// Watch for changes in props.defaults
watch(() => props.defaults, (newDefaults) => {
  if (newDefaults && Object.keys(newDefaults).length > 0) {
    applyDefaults()
    nextTick(() => {
      tabs.reload()
    })
  }
}, { 
  immediate: true,
  deep: true 
})

onMounted(async () => {
  
  applyDefaults()
  await nextTick()
  tabs.reload()
})
</script>