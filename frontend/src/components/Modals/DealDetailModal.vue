<template>
  <Dialog
    v-model="show"
    :options="{
      size: 'xl',
      actions: [
        {
          label: __('Convert'),
          variant: 'solid',
          onClick: convertToDeal,
        },
      ],
    }"
  >
    <template #body-header>
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Deal Details') }}
          </h3>
        </div>
        <div class="flex items-center gap-1">
          <Button icon="x" variant="ghost" @click="show = false" />
        </div>
      </div>
    </template>
    <template #body-content>
      <div class="space-y-6">
        <div v-for="field in fields" :key="field.fieldname">
          <Field :field="field" />
        </div>
        <ErrorMessage v-if="error" :message="error" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, provide } from 'vue'
import { Dialog, call, ErrorMessage } from 'frappe-ui'
import Field from '@/components/FieldLayout/Field.vue'
import { useDocument } from '@/data/document'
import { capture } from '@/telemetry'
import { sessionStore } from '@/stores/session'
import { useOnboarding } from 'frappe-ui/frappe'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: {
    type: Object,
    required: true,
  },
  deal: {
    type: Object,
    required: true,
  },
  existingContact: String,
  existingOrganization: String,
})

const show = defineModel()
const router = useRouter()
const { user } = sessionStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const error = ref('')

const { triggerConvertToDeal } = useDocument('CRM Lead', props.lead.name)

// Provide data to Field component
const data = ref(props.deal)
provide('data', data)
provide('doctype', 'CRM Deal')
provide('preview', ref(false))
provide('isGridRow', false)

const fields = [
  {
    fieldname: 'primary_pain_category',
    label: 'Primary Pain Category',
    fieldtype: 'Link',
    options: 'CRM Pain Category',
    reqd: 1,
    visible: true,
  },
  {
    fieldname: 'product_alloy_type',
    label: 'Product /Alloy type',
    fieldtype: 'Link',
    options: 'CRM Product',
    reqd: 1,
    visible: true,
  },
  {
    fieldname: 'first_order_volume',
    label: 'First Order Volume',
    fieldtype: 'Float',
    reqd: 1,
    visible: true,
  },
  {
    fieldname: 'expected_monthly_volume',
    label: 'Expected monthly volume',
    fieldtype: 'Float',
    reqd: 1,
    visible: true,
  },
  {
    fieldname: 'decision_criteria',
    label: 'Decision Criteria',
    fieldtype: 'Table MultiSelect',
    options: 'CRM Decision Criteria Multi select',
    reqd: 1,
    visible: true,
  },
  {
    fieldname: 'economic_buyer_name',
    label: 'Economic Buyer Name',
    fieldtype: 'Data',
    reqd: 1,
    visible: true,
  },
  {
    fieldname: 'custom_formulation_required',
    label: 'Custom Formulation Required',
    fieldtype: 'Select',
    options: 'Yes\nNo',
    reqd: 1,
    visible: true,
  },
  {
    fieldname: 'decision_timeline',
    label: 'Decision Timeline',
    fieldtype: 'Date',
    reqd: 1,
    visible: true,
  },
]

async function convertToDeal() {
  error.value = ''

  // Validate mandatory fields
  for (const field of fields) {
    if (field.reqd && !data.value[field.fieldname]) {
      error.value = __('{0} is required', [__(field.label)])
      return
    }
    if (field.fieldtype === 'Table MultiSelect' && (!data.value[field.fieldname] || data.value[field.fieldname].length === 0)) {
       error.value = __('{0} is required', [__(field.label)])
       return
    }
  }

  await triggerConvertToDeal?.(props.lead, data.value, () => (show.value = false))

  const _deal = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
    lead: props.lead.name,
    deal: data.value,
    existing_contact: props.existingContact,
    existing_organization: props.existingOrganization,
  }).catch((err) => {
    error.value = __('Error converting to deal: {0}', [err.messages?.[0] || err.message])
  })

  if (_deal) {
    show.value = false
    error.value = ''
    updateOnboardingStep('convert_lead_to_deal', true, false, () => {
      localStorage.setItem('firstDeal' + user, _deal)
    })
    capture('convert_lead_to_deal')
    router.push({ name: 'Deal', params: { dealId: _deal } })
  }
}
</script>
