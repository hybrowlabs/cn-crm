<template>
  <Dialog
    v-model="show"
    :options="{
      size: 'xl',
      actions: [
        {
          label: editMode ? __('Update') : __('Create'),
          variant: 'solid',
          onClick: () => updateTask(),
        },
      ],
    }"
  >
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Edit Task') : __('Create Task') }}
        </h3>
        <Button
          v-if="task.doc?.reference_docname"
          size="sm"
          :label="
            task.doc.reference_doctype == 'CRM Deal'
              ? __('Open Deal')
              : __('Open Lead')
          "
          @click="redirect()"
        >
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
            :data="task.doc" 
            doctype="CRM Task"
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
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { taskStatusOptions, taskPriorityOptions, getFormat } from '@/utils'
import { usersStore } from '@/stores/users'
import { capture } from '@/telemetry'
import { useDocument } from '@/data/document'
import { call, createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, watch, nextTick, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  task: {
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
const tasks = defineModel('reloadTasks')

const emit = defineEmits(['updateTask', 'after'])

const router = useRouter()
const { users, getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const error = ref(null)
const editMode = ref(false)

const { document: task } = useDocument('CRM Task', props.task?.name || '')

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Task'],
  params: { doctype: 'CRM Task', type: 'Quick Entry' },
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
                if (task.doc.reference_doctype) {
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
              
              // Handle status field
              if (field.fieldname === 'status') {
                transformedField.fieldtype = 'Select'
                transformedField.options = [
                  { label: 'Backlog', value: 'Backlog' },
                  { label: 'Todo', value: 'Todo' },
                  { label: 'In Progress', value: 'In Progress' },
                  { label: 'Done', value: 'Done' },
                  { label: 'Canceled', value: 'Canceled' }
                ]
              }
              
              // Handle priority field
              if (field.fieldname === 'priority') {
                transformedField.fieldtype = 'Select'
                transformedField.options = [
                  { label: 'Low', value: 'Low' },
                  { label: 'Medium', value: 'Medium' },
                  { label: 'High', value: 'High' }
                ]
              }
              
              // Ensure description field remains Text Editor
              if (field.fieldname === 'description') {
                transformedField.fieldtype = 'Text Editor'
              }
              
              return transformedField
            })
          }))
        }))
      }
    })
  },
})

function redirect() {
  if (!task.doc?.reference_docname) return
  let name = task.doc.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: task.doc.reference_docname }
  if (name == 'Deal') {
    params = { dealId: task.doc.reference_docname }
  }
  router.push({ name: name, params: params })
}

// Watch for reference_doctype changes to update reference_docname field options
watch(() => task.doc.reference_doctype, (newType, oldType) => {
  if (newType !== oldType) {
    // Clear reference_docname if reference_doctype changes
    if (oldType && newType !== oldType) {
      task.doc.reference_docname = null
    }
    // Force tabs to re-transform to update reference_docname field options
    nextTick(() => {
      tabs.reload()
    })
  }
}, { 
  immediate: false 
})

async function updateTask() {
  error.value = null
  
  // Validate reference fields
  if (!task.doc.reference_doctype || !task.doc.reference_docname) {
    error.value = __('Reference Type and Reference Name are required')
    return
  }
  
  if (!['CRM Lead', 'CRM Deal'].includes(task.doc.reference_doctype)) {
    error.value = __('Reference Type must be CRM Lead or CRM Deal')
    return
  }
  
  if (!task.doc.assigned_to) {
    task.doc.assigned_to = getUser().name
  }
  
  if (task.doc.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Task',
      name: task.doc.name,
      fieldname: task.doc,
    })
    if (d.name) {
      tasks.value?.reload()
      emit('after', d)
    }
  } else {
    let d = await call(
      'frappe.client.insert',
      {
        doc: {
          doctype: 'CRM Task',
          ...task.doc,
        },
      },
      {
        onError: (err) => {
          if (err.error.exc_type == 'MandatoryError') {
            error.value = __('Title is mandatory')
          } else if (err.messages && Array.isArray(err.messages)) {
            error.value = err.messages.join('\n')
          } else if (err.message) {
            error.value = err.message
          }
        },
      },
    )
    if (d.name) {
      updateOnboardingStep('create_first_task')
      capture('task_created')
      tasks.value?.reload()
      emit('after', d, true)
    }
  }
  show.value = false
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
  editMode.value = false
  nextTick(() => {
      // Initialize task document
      if (props.task?.name) {
        // Edit mode - load existing task
        task.doc = { ...props.task }
      editMode.value = true
      } else {
        // Create mode - set defaults
        task.doc = {
          reference_doctype: props.doctype || 'CRM Lead',
          reference_docname: props.doc || null,
          status: 'Backlog',
          priority: 'Low',
          ...props.task
        }
      }
      tabs.reload()
})
  },
)
</script>

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
