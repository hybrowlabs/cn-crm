<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Trial Outcome Note') }"
    @close="cancel"
  >
    <template #body-content>
      <div class="-mt-3 mb-4 text-p-base text-ink-gray-7">
        {{ __('Please provide a note for the trial outcome: {0}', [outcome]) }}
      </div>
      <div class="flex flex-col gap-3">
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('Note') }}
            <span class="text-ink-red-2">*</span>
          </div>
          <FormControl
            class="form-control flex-1"
            type="textarea"
            :value="note"
            @change="(e) => (note = e.target.value)"
            :placeholder="__('Enter trial outcome details...')"
          />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between items-center gap-2">
        <div><ErrorMessage :message="error" /></div>
        <div class="flex gap-2">
          <Button :label="__('Cancel')" @click="cancel" />
          <Button variant="solid" :label="__('Save')" @click="save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, FormControl, ErrorMessage, Button } from 'frappe-ui'
import { ref, watch } from 'vue'

const props = defineProps({
  deal: {
    type: Object,
    required: true,
  },
  outcome: {
    type: String,
    required: true,
  },
})

const show = defineModel()
const note = ref(props.deal.doc.trial_outcome_note || '')
const error = ref('')

watch(show, (value) => {
  if (value) {
    note.value = props.deal.doc.trial_outcome_note || ''
    error.value = ''
  }
})

function cancel() {
  show.value = false
  error.value = ''
}

function save() {
  if (!note.value || !note.value.trim()) {
    error.value = __('Note is required')
    return
  }

  error.value = ''
  show.value = false

  props.deal.doc.trial_outcome = props.outcome
  props.deal.doc.trial_outcome_note = note.value
  props.deal.save.submit()
}
</script>
