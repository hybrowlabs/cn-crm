<template>
  <Dialog v-model="show" :options="{
    size: 'xl',
    actions: [
      {
        label: editMode ? __('Update') : __('Create'),
        variant: 'solid',
        onClick: () => updateNote(),
      },
    ],
  }">
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Edit Note') : __('Create Note') }}
        </h3>
        <Button v-if="note.doc?.reference_docname" size="sm" :label="note.doc.reference_doctype == 'CRM Deal'
          ? __('Open Deal')
          : __('Open Lead')
          " @click="redirect()">
          <template #suffix>
            <ArrowUpRightIcon class="w-4 h-4" />
          </template>
        </Button>
      </div>
    </template>
    <template #body-content>
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
            :data="note.doc" 
            doctype="FCRM Note"
          />
        </div>
        <div v-else class="py-8 text-center text-gray-600">
          No form data available
        </div>
        <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { capture } from '@/telemetry'
import { useDocument } from '@/data/document'
import { call, createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  note: {
    type: Object,
    default: {},
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  doc: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const notes = defineModel('reloadNotes')

const emit = defineEmits(['after'])

const router = useRouter()

const { updateOnboardingStep } = useOnboarding('frappecrm')

const error = ref(null)
const editMode = ref(false)

const { document: note } = useDocument('FCRM Note', props.note?.name || '')

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'FCRM Note'],
  params: { doctype: 'FCRM Note', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    if (!_tabs || !Array.isArray(_tabs)) {
      return _tabs
    }
    
    return _tabs.map((tab) => {
      return {
        ...tab,
        sections: tab.sections.map((section) => ({
          ...section,
          columns: section.columns.map((column) => ({
            ...column,
            fields: column.fields.map((field) => {
              const transformedField = { ...field }
              
              // Handle reference_doctype field
              if (field.fieldname === 'reference_doctype') {
                transformedField.fieldtype = 'Select'
                transformedField.options = [
                  { label: 'CRM Lead', value: 'CRM Lead' },
                  { label: 'CRM Deal', value: 'CRM Deal' }
                ]
              }
              
              // Handle reference_docname field - enable/disable based on reference_doctype
              if (field.fieldname === 'reference_docname') {
                if (note.doc.reference_doctype) {
                  transformedField.read_only = 0
                  // Ensure Dynamic Link options are set correctly
                  if (transformedField.fieldtype === 'Dynamic Link') {
                    transformedField.options = 'reference_doctype'
                  }
                } else {
                  transformedField.read_only = 1
                  if (transformedField.fieldtype === 'Dynamic Link') {
                    transformedField.options = ''
                  }
                }
              }
              
              // Ensure content field remains Small Text (multiline)
              if (field.fieldname === 'content') {
                transformedField.fieldtype = 'Small Text'
              }
              
              return transformedField
            })
          }))
        }))
      }
    })
  },
})

async function updateNote() {
  error.value = null
  
  // Validate reference fields
  if (!note.doc.reference_doctype || !note.doc.reference_docname) {
    error.value = __('Reference Type and Reference Name are required')
    return
  }
  
  if (!['CRM Lead', 'CRM Deal'].includes(note.doc.reference_doctype)) {
    error.value = __('Reference Type must be CRM Lead or CRM Deal')
    return
  }
  
  if (note.doc.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'FCRM Note',
      name: note.doc.name,
      fieldname: note.doc,
    })
    if (d.name) {
      notes.value?.reload()
      emit('after', d)
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'FCRM Note',
        ...note.doc,
      },
    }, {
      onError: (err) => {
        if (err.error.exc_type == 'MandatoryError') {
          error.value = __('Title is mandatory')
        } else if (err.messages && Array.isArray(err.messages)) {
          error.value = err.messages.join('\n')
        } else if (err.message) {
          error.value = err.message
        }
      }
    })
    if (d.name) {
      updateOnboardingStep('create_first_note')
      capture('note_created')
      notes.value?.reload()
      emit('after', d, true)
    }
  }
  show.value = false
}

function redirect() {
  if (!note.doc?.reference_docname) return
  let name = note.doc.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: note.doc.reference_docname }
  if (name == 'Deal') {
    params = { dealId: note.doc.reference_docname }
  }
  router.push({ name: name, params: params })
}

// Watch for reference_type changes to update reference_name field options
watch(() => note.doc.reference_doctype, (newType, oldType) => {
  if (newType !== oldType) {
    // Clear reference_docname if reference_doctype changes
    if (oldType && newType !== oldType) {
      note.doc.reference_docname = null
    }
    // Force tabs to re-transform to update reference_docname field options
    nextTick(() => {
      tabs.reload()
    })
  }
}, { 
  immediate: false 
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      // Initialize note document
      if (props.note?.name) {
        // Edit mode - load existing note
        note.doc = { ...props.note }
        editMode.value = true
      } else {
        // Create mode - set defaults
        note.doc = {
          reference_doctype: props.doctype || 'CRM Lead',
          reference_docname: props.doc || '',
          ...props.note
        }
      }
      tabs.reload()
    })
  },
)
</script>
