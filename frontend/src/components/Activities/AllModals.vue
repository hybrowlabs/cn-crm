<template>
  <TaskModal
    v-model="showTaskModal"
    v-model:reloadTasks="activities"
    :task="task"
    :doctype="doctype"
    :doc="doc.data?.name"
    @after="redirect('tasks')"
  />
  <NoteModal
    v-model="showNoteModal"
    v-model:reloadNotes="activities"
    :note="note"
    :doctype="doctype"
    :doc="doc.data?.name"
    @after="redirect('notes')"
  />
  <CallLogModal
    v-if="showCallLogModal"
    v-model="showCallLogModal"
    :data="callLog"
    :referenceDoc="referenceDoc"
    :options="{ afterInsert: () => activities.reload() }"
  />
  <VisitModal
    v-model="showVisitModal"
    :defaults="visit"
    :options="{ afterInsert: () => { activities.reload(); emit('reloadVisits'); redirect('visits'); } }"
  />
</template>
<script setup>
import TaskModal from '@/components/Modals/TaskModal.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import CallLogModal from '@/components/Modals/CallLogModal.vue'
import VisitModal from '@/components/Modals/VisitModal.vue'
import { call } from 'frappe-ui'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  doctype: String,
})

const emit = defineEmits(['reloadVisits'])

const activities = defineModel()
const doc = defineModel('doc')

// Tasks
const showTaskModal = ref(false)
const task = ref({})

function showTask(t) {
  // Tasks can only reference CRM Lead
  let docname = doc.value.data?.name
  
  // If doctype is not CRM Lead, we need to get the lead from the deal
  if (props.doctype === 'CRM Deal' && docname) {
    // Get lead from deal
    call('frappe.client.get_value', {
      doctype: 'CRM Deal',
      fieldname: 'lead',
      filters: { name: docname }
    }).then((result) => {
      docname = result.message.lead
    })
  }
  
  task.value = t || {
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    priority: 'Low',
    status: 'Backlog',
    reference_doctype: 'CRM Lead', // Always CRM Lead
    reference_docname: docname,
  }
  showTaskModal.value = true
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Task',
    name,
  })
  activities.value.reload()
}

function updateTaskStatus(status, task) {
  call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: 'status',
    value: status,
  }).then(() => {
    activities.value.reload()
  })
}

// Notes
const showNoteModal = ref(false)
const note = ref({})

function showNote(n) {
  // Notes can only reference CRM Lead
  let docname = doc.value.data?.name
  
  // If doctype is not CRM Lead, we need to get the lead from the deal
  if (props.doctype === 'CRM Deal' && docname) {
    // Get lead from deal
    call('frappe.client.get_value', {
      doctype: 'CRM Deal',
      fieldname: 'lead',
      filters: { name: docname }
    }).then((result) => {
      docname = result.message.lead
    })
  }
  
  note.value = n || {
    title: '',
    content: '',
    reference_doctype: 'CRM Lead', // Always CRM Lead
    reference_docname: docname,
  }
  showNoteModal.value = true
}

// Call Logs
const showCallLogModal = ref(false)
const callLog = ref({})
const referenceDoc = ref({})

// Visits
const showVisitModal = ref(false)
const visit = ref({})

function createCallLog() {
  // Call Logs can only reference CRM Lead
  let docname = doc.value.data?.name
  
  // If doctype is not CRM Lead, we need to get the lead from the deal
  if (props.doctype === 'CRM Deal' && docname) {
    // Get lead from deal
    call('frappe.client.get_value', {
      doctype: 'CRM Deal',
      fieldname: 'lead',
      filters: { name: docname }
    }).then((result) => {
      docname = result.message.lead
      referenceDoc.value = { ...doc.value.data }
      callLog.value = {
        reference_doctype: 'CRM Lead', // Always CRM Lead
        reference_docname: docname,
      }
      showCallLogModal.value = true
    })
  } else {
    referenceDoc.value = { ...doc.value.data }
    callLog.value = {
      reference_doctype: 'CRM Lead', // Always CRM Lead
      reference_docname: docname,
    }
    showCallLogModal.value = true
  }
}

function showVisit() {
  let doctype = props.doctype
  let docname = doc.value.data?.name
  
  // Visits can reference CRM Lead or CRM Deal (but Deal must have Lead)
  // If doctype is not CRM Lead or CRM Deal, default to CRM Lead
  if (doctype !== 'CRM Lead' && doctype !== 'CRM Deal') {
    doctype = 'CRM Lead'
  }
  
  // Clear previous defaults first
  visit.value = {}
  
  // Ensure we have valid reference data before showing the modal
  if (doctype && docname) {
    visit.value = {
      reference_type: doctype,
      reference_name: docname,
      visit_date: new Date().toISOString().split('T')[0],
      visit_type: 'Initial Meeting',
      status: 'Planned',
      priority: 'Medium'
    }
  } else {
    // If no reference available, just set basic defaults
    visit.value = {
      visit_date: new Date().toISOString().split('T')[0],
      visit_type: 'Initial Meeting',
      status: 'Planned',
      priority: 'Medium'
    }
  }
  
  // Open the modal
  showVisitModal.value = true
}

// common
const route = useRoute()
const router = useRouter()

function redirect(tabName) {
  if (route.name == 'Lead' || route.name == 'Deal') {
    let hash = '#' + tabName
    if (route.hash != hash) {
      router.push({ ...route, hash })
    }
  }
}

defineExpose({
  showTask,
  deleteTask,
  updateTaskStatus,
  showNote,
  createCallLog,
  showVisit,
})
</script>
