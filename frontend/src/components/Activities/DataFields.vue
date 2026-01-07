<template>
  <div
    class="my-3 flex items-center justify-between text-lg font-medium sm:mb-4 sm:mt-8"
  >
    <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
      {{ __('Data') }}
      <Badge
        v-if="document.isDirty"
        class="ml-3"
        :label="'Not Saved'"
        theme="orange"
      />
    </div>
    <div class="flex gap-1">
      <Button
        v-if="isManager() && !isMobileView"
        @click="showDataFieldsModal = true"
      >
        <template #icon>
          <EditIcon />
        </template>
      </Button>
      <Button
        label="Save"
        :disabled="!document.isDirty"
        variant="solid"
        :loading="document.save.loading"
        @click="saveChanges"
      />
    </div>
  </div>
  <div
    v-if="document.get.loading"
    class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-ink-gray-6"
  >
    <LoadingIndicator class="h-6 w-6" />
    <span>{{ __('Loading...') }}</span>
  </div>
  <div v-else class="pb-8 overflow-y-auto" style="max-height: calc(100vh - 300px);">
    <FieldLayout
      v-if="tabs.data"
      :tabs="tabs.data"
      :data="document.doc"
      :doctype="doctype"
    />
  </div>
  <DataFieldsModal
    v-if="showDataFieldsModal"
    v-model="showDataFieldsModal"
    :doctype="doctype"
    @reload="
      () => {
        tabs.reload()
        document.reload()
      }
    "
  />
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import DataFieldsModal from '@/components/Modals/DataFieldsModal.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { Badge, createResource } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { usersStore } from '@/stores/users'
import { useDocument } from '@/data/document'
import { isMobileView } from '@/composables/settings'
import { ref, watch, getCurrentInstance } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['beforeSave', 'afterSave'])

const { isManager } = usersStore()

const instance = getCurrentInstance()
const attrs = instance?.vnode?.props ?? {}

const showDataFieldsModal = ref(false)

const { document } = useDocument(props.doctype, props.docname)

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['DataFields', props.doctype],
  params: { doctype: props.doctype, type: 'Data Fields' },
  auto: true,
})

function saveChanges() {
  console.log('=== SAVE CHANGES CALLED ===')
  console.log('document.isDirty:', document.isDirty)
  
  if (!document.isDirty) return

  console.log('Document object structure:', document)
  console.log('Available methods on document:', Object.keys(document))
  console.log('document.save:', document.save)
  console.log('document.setValue:', document.setValue)

  const updatedDoc = { ...document.doc }
  const oldDoc = { ...document.originalDoc || {} }

  const changes = Object.keys(updatedDoc).reduce((acc, key) => {
    if (JSON.stringify(updatedDoc[key]) !== JSON.stringify(oldDoc[key])) {
      acc[key] = updatedDoc[key]
    }
    return acc
  }, {})

  console.log('Changes to save:', changes)
  console.log('Has onBeforeSave listener:', attrs['onBeforeSave'] !== undefined)

  // Force direct save instead of emitting beforeSave event
  console.log('Proceeding with direct save (bypassing beforeSave event)')
  
  // Try multiple approaches to save
  if (document.setValue && typeof document.setValue.submit === 'function') {
    console.log('Using document.setValue.submit approach')
    document.setValue.submit(changes, {
      onSuccess: () => {
        console.log('document.setValue.submit SUCCESS')
        document.isDirty = false
        emit('afterSave', changes)
      },
      onError: (error) => {
        console.error('document.setValue.submit FAILED:', error)
      }
    })
  } else if (document.save && typeof document.save.submit === 'function') {
    console.log('Falling back to document.save.submit approach')
    document.save.submit({
      onSuccess: () => {
        console.log('document.save.submit SUCCESS')
        document.isDirty = false
        emit('afterSave', changes)
      },
      onError: (error) => {
        console.error('document.save.submit FAILED:', error)
      }
    })
  } else {
    console.error('No available save method found!')
    console.error('document.save:', document.save)
    console.error('document.setValue:', document.setValue)
  }
}

watch(
  () => document.doc,
  (newValue, oldValue) => {
    if (!oldValue) return
    if (newValue && oldValue) {
      const isDirty =
        JSON.stringify(newValue) !== JSON.stringify(document.originalDoc)
      document.isDirty = isDirty
      if (isDirty) {
        document.save.loading = false
      }
    }
  },
  { deep: true },
)
</script>
