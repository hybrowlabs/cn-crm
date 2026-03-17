<script setup>
import {
  TextEditor,
  FormControl,
  Switch,
  toast,
  call,
  createResource,
  Button,
  ErrorMessage
} from 'frappe-ui'
import { computed, inject, onMounted, ref } from 'vue'
import { isMobileView } from '@/composables/settings'

const props = defineProps({
  templateData: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['updateStep'])
const errorMessage = ref('')

const template = ref({
  name: '',
  reference_doctype: '',
  subject: '',
  response_html: '',
  response: '',
  use_html: false,
  enabled: false,
})

const templates = inject('templates')

const dirty = computed(() => {
  return (
    template.value.name !== props.templateData.name ||
    template.value.reference_doctype !== props.templateData.reference_doctype ||
    template.value.subject !== props.templateData.subject ||
    template.value.response_html !== props.templateData.response_html ||
    template.value.response !== props.templateData.response ||
    template.value.use_html !== props.templateData.use_html ||
    template.value.enabled !== (props.templateData.enabled ? true : false)
  )
})

const updateTemplate = async () => {
  errorMessage.value = ''
  if (!template.value.name) {
    errorMessage.value = __('Name is required')
    return
  }
  if (!template.value.subject) {
    errorMessage.value = __('Subject is required')
    return
  }
  if (template.value.content_type === 'Rich Text' && !template.value.response) {
    errorMessage.value = __('Content is required')
    return
  }
  if (template.value.content_type === 'HTML' && !template.value.response_html) {
    errorMessage.value = __('Content is required')
    return
  }

  if (template.value.name !== props.templateData.name) {
    await renameDoc.submit()
  }

  templates.setValue.submit(
    {
      name: template.value.name,
      ...template.value,
      enabled: template.value.enabled ? 1 : 0,
    },
    {
      onSuccess: () => {
        emit('updateStep', 'template-list')
        toast.success(__('Template updated successfully'))
      },
      onError: (error) => {
        errorMessage.value =
          error.messages[0] || __('Failed to update template')
      },
    },
  )
}

const renameDoc = createResource({
  url: 'frappe.client.rename_doc',
  params: {
    doctype: 'CRM Email Template',
    old_name: props.templateData.name,
    new_name: template.value.name,
  },
  onSuccess: (data) => {
    template.value.name = data
  },
})

onMounted(() => {
  if (props.templateData?.name) {
    Object.assign(template.value, props.templateData)
    template.value.enabled = props.templateData.enabled ? true : false
  }
})
</script>

<template>
  <div
    class="flex h-full flex-col gap-6 text-ink-gray-8"
    :class="isMobileView ? 'p-4' : 'p-8'"
  >
    <!-- Header -->
    <div class="flex justify-between items-center px-1">
      <div class="flex gap-2 items-center min-w-0">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          size="md"
          @click="() => emit('updateStep', 'template-list')"
          class="!p-1 hover:bg-surface-gray-2"
        />
        <h2 class="text-xl font-semibold truncate leading-none mt-1">
          {{ __(template.name) }}
        </h2>
      </div>
      <div class="flex items-center space-x-2 shrink-0">
        <Button
          :label="__('Update')"
          variant="solid"
          :disabled="!dirty"
          :loading="renameDoc.loading || templates.setValue.loading"
          @click="updateTemplate"
        />
      </div>
    </div>

    <!-- Fields -->
    <div class="flex flex-1 flex-col gap-4 overflow-y-auto">
      <div
        class="flex justify-between items-center cursor-pointer border-b py-3 px-1 hover:bg-surface-gray-1 transition-colors rounded"
        @click="() => (template.enabled = !template.enabled)"
      >
        <div class="text-base text-ink-gray-7">{{ __('Enabled') }}</div>
        <Switch v-model="template.enabled" @click.stop />
      </div>
      <div class="flex sm:flex-row flex-col gap-4">
        <div class="flex-1">
          <FormControl
            size="md"
            v-model="template.name"
            :placeholder="__('Payment Reminder')"
            :label="__('Name')"
            :required="true"
          />
        </div>
        <div class="flex-1">
          <FormControl
            type="select"
            size="md"
            v-model="template.reference_doctype"
            :label="__('For')"
            :options="[
              {
                label: __('Deal'),
                value: 'CRM Deal',
              },
              {
                label: __('Lead'),
                value: 'CRM Lead',
              },
            ]"
            :placeholder="__('Deal')"
          />
        </div>
      </div>
      <div>
        <FormControl
          ref="subjectRef"
          size="md"
          v-model="template.subject"
          :label="__('Subject')"
          :placeholder="__('Payment Reminder from Frappé - (#{{ name }})')"
          :required="true"
        />
      </div>
      <div class="border-t pt-4">
        <FormControl
          type="select"
          size="md"
          v-model="template.content_type"
          :label="__('Content Type')"
          default="Rich Text"
          :options="['Rich Text', 'HTML']"
          :placeholder="__('Rich Text')"
        />
      </div>
      <div>
        <FormControl
          v-if="template.content_type === 'HTML'"
          size="md"
          type="textarea"
          :label="__('Content')"
          :required="true"
          ref="content"
          :rows="10"
          v-model="template.response_html"
          :placeholder="
            __(
              '<p>Dear {{ lead_name }},</p>\n\n<p>This is a reminder for the payment of {{ grand_total }}.</p>\n\n<p>Thanks,</p>\n<p>Frappé</p>',
            )
          "
        />
        <div v-else>
          <div class="mb-1.5 text-base text-ink-gray-5">
            {{ __('Content') }}
            <span class="text-ink-red-3">*</span>
          </div>
          <TextEditor
            ref="content"
            editor-class="!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="template.response"
            @change="(val) => (template.response = val)"
            :placeholder="
              __(
                'Dear {{ lead_name }}, \n\nThis is a reminder for the payment of {{ grand_total }}. \n\nThanks, \nFrappé',
              )
            "
          />
        </div>
      </div>
    </div>
    <div v-if="errorMessage" class="px-1">
      <ErrorMessage :message="__(errorMessage)" />
    </div>
  </div>
</template>
