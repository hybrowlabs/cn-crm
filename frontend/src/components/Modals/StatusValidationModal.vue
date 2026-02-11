<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Information Required'),
      size: 'md',
      actions: [
        {
          label: __('Save & Proceed'),
          variant: 'solid',
          onClick: onSave,
          loading: loading,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="space-y-4">
        <p class="text-base text-ink-gray-7">
          {{
            __('Please provide the following details to move to the {0} stage:', [
              targetStatus,
            ])
          }}
        </p>
        <div class="space-y-5">
          <Field
            v-for="field in fields"
            :key="field.fieldname"
            :field="field"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Field from '@/components/FieldLayout/Field.vue'
import { Dialog } from 'frappe-ui'
import { ref, provide, computed } from 'vue'

const props = defineProps({
  fields: {
    type: Array,
    required: true,
  },
  targetStatus: {
    type: String,
    required: true,
  },
  doc: {
    type: Object,
    required: true,
  },
})

const show = defineModel()
const emit = defineEmits(['proceed'])
const loading = ref(false)

// Provide context for Field.vue
provide('data', computed(() => props.doc))
provide('doctype', 'CRM Lead')
provide('preview', ref(false))
provide('isGridRow', false)

async function onSave() {
  loading.value = true
  try {
    await emit('proceed')
  } finally {
    loading.value = false
  }
}
</script>
