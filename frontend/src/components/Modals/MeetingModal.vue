<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Meeting') }}
            </h3>
            <p v-if="lead" class="text-sm text-ink-gray-5 mt-1">
              {{ __('Schedule a discovery meeting for') }} {{ lead.lead_name || lead.name }}
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
          <FieldLayout
            v-if="tabs.data"
            :tabs="tabs.data"
            :data="meeting.doc"
            doctype="CRM Meeting"
          />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isMeetingCreating"
            @click="createNewMeeting"
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
import { sessionStore } from '@/stores/session'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: {
    type: Object,
    default: null,
  },
  defaults: Object,
})

const { user } = sessionStore()
const { getUser, isManager } = usersStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isMeetingCreating = ref(false)

const { document: meeting, triggerOnBeforeCreate } = useDocument('CRM Meeting')

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Meeting'],
  params: { doctype: 'CRM Meeting', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    _tabs.forEach((tab) => {
      if (!tab.sections) return
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            // Initialize table fields
            if (field.fieldtype === 'Table') {
              meeting.doc[field.fieldname] = []
            }
          })
        })
      })
    })
    return _tabs
  },
})

const createMeeting = createResource({
  url: 'frappe.client.insert',
})

function validateMandatoryFields() {
  error.value = null
  const errors = []

  // Get all fields from tabs
  const allFields = []
  if (tabs.data) {
    tabs.data.forEach(tab => {
      if (!tab.sections) return
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
    const value = meeting.doc[field.fieldname]
    const isEmpty = value === null || value === undefined || value === '' ||
                    (Array.isArray(value) && value.length === 0)

    if (isEmpty) {
      errors.push(__(`{0} is mandatory`, [__(field.label)]))
    }
  })

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
      return func(meeting.doc)
    } catch (e) {
      console.error('Error evaluating depends_on:', e)
      return true
    }
  }
  return !!meeting.doc[expression]
}

function evaluateMandatoryDependsOn(expression) {
  if (!expression) return false
  if (expression.startsWith('eval:')) {
    try {
      const code = expression.substring(5)
      const func = new Function('doc', `return ${code}`)
      return func(meeting.doc)
    } catch (e) {
      console.error('Error evaluating mandatory_depends_on:', e)
      return false
    }
  }
  return !!meeting.doc[expression]
}

async function createNewMeeting() {
  await triggerOnBeforeCreate?.()

  createMeeting.submit(
    {
      doc: {
        doctype: 'CRM Meeting',
        ...meeting.doc,
      },
    },
    {
      validate() {
        const validationError = validateMandatoryFields()
        if (validationError) {
          return validationError
        }
        isMeetingCreating.value = true
      },
      onSuccess(data) {
        capture('meeting_created')
        isMeetingCreating.value = false
        show.value = false
        // Optionally navigate to meeting page or stay on lead
        // router.push({ name: 'Meeting', params: { meetingId: data.name } })
      },
      onError(err) {
        isMeetingCreating.value = false
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
  quickEntryProps.value = { doctype: 'CRM Meeting' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  meeting.doc = {}
  Object.assign(meeting.doc, props.defaults)

  // Set the lead reference if provided
  if (props.lead?.name) {
    meeting.doc.lead = props.lead.name
  }

  // Set default meeting owner
  if (!meeting.doc?.meeting_owner) {
    meeting.doc.meeting_owner = getUser().name
  }

  // Set default status
  if (!meeting.doc?.status) {
    meeting.doc.status = 'Open'
  }
})
</script>
