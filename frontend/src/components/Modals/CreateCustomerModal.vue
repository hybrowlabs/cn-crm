<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Enter Customer Details') }"
    @close="cancel"
  >
    <template #body-content>
      <div class="flex flex-col gap-3 sm:min-w-[400px] w-full">
        <div>
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('Customer Name') }}
            <span class="text-ink-red-2">*</span>
          </div>
          <FormControl
            class="form-control flex-1 truncate"
            type="text"
            :value="organizationName"
            @change="(e) => (organizationName = e.target.value)"
          />
        </div>

        <div>
          <div class="mb-2 text-sm text-ink-gray-5">
            {{ __('GSTIN') }}
          </div>
          <div class="flex gap-2 mb-2">
            <FormControl
              class="form-control flex-1 truncate"
              type="text"
              :value="gstin"
              @change="(e) => (gstin = e.target.value)"
              @blur="fetchGstinDetails"
            />
            <Button
              :loading="isFetching"
              icon="refresh-cw"
              @click="fetchGstinDetails"
              :disabled="gstin.length !== 15"
            />
          </div>
        </div>

        <div class="w-full h-px bg-outline-gray-2 my-1"></div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <div class="mb-2 text-sm text-ink-gray-5">{{ __('Territory') }}</div>
            <Link
              class="form-control"
              doctype="Territory"
              v-model="territory"
            />
          </div>
          <div>
            <div class="mb-2 text-sm text-ink-gray-5">{{ __('Customer Type') }}</div>
            <Autocomplete
              class="form-control"
              :options="[
                { label: 'Company', value: 'Company' },
                { label: 'Individual', value: 'Individual' },
                { label: 'Partnership', value: 'Partnership' }
              ]"
              v-model="customerType"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <div class="mb-2 text-sm text-ink-gray-5">{{ __('Default Currency') }}</div>
            <Link
              class="form-control"
              doctype="Currency"
              v-model="defaultCurrency"
            />
          </div>
          <div>
            <div class="mb-2 text-sm text-ink-gray-5">{{ __('Credit Limit') }}</div>
            <FormControl
              class="form-control"
              type="number"
              :value="creditLimit"
              @change="(e) => (creditLimit = e.target.value)"
            />
          </div>
        </div>

        <div>
          <div class="mb-2 text-sm text-ink-gray-5">{{ __('GST Category') }}</div>
          <Autocomplete
            class="form-control w-full sm:w-1/2"
            :options="[
              { label: 'Registered Regular', value: 'Registered Regular' },
              { label: 'Registered Composition', value: 'Registered Composition' },
              { label: 'Unregistered', value: 'Unregistered' },
              { label: 'SEZ', value: 'SEZ' },
              { label: 'Overseas', value: 'Overseas' },
              { label: 'Deemed Export', value: 'Deemed Export' },
              { label: 'UIN Holders', value: 'UIN Holders' },
              { label: 'Tax Deductor', value: 'Tax Deductor' },
              { label: 'Tax Collector', value: 'Tax Collector' },
              { label: 'Input Service Distributor', value: 'Input Service Distributor' }
            ]"
            v-model="gstCategory"
          />
        </div>

        <div class="w-full h-px bg-outline-gray-2 my-1"></div>

        <div class="flex flex-col gap-3">
          <div class="text-sm font-semibold text-ink-gray-7">{{ __('Primary Address') }}</div>
          <FormControl
            class="form-control"
            type="text"
            placeholder="Address Line 1"
            :value="addressLine1"
            @change="(e) => (addressLine1 = e.target.value)"
          />
          <FormControl
            class="form-control"
            type="text"
            placeholder="Address Line 2"
            :value="addressLine2"
            @change="(e) => (addressLine2 = e.target.value)"
          />
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormControl
              class="form-control"
              type="text"
              placeholder="City"
              :value="city"
              @change="(e) => (city = e.target.value)"
            />
            <FormControl
              class="form-control"
              type="text"
              placeholder="State"
              :value="state"
              @change="(e) => (state = e.target.value)"
            />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <FormControl
              class="form-control"
              type="text"
              placeholder="Pincode"
              :value="pincode"
              @change="(e) => (pincode = e.target.value)"
            />
            <FormControl
              class="form-control"
              type="text"
              placeholder="Country"
              :value="country"
              @change="(e) => (country = e.target.value)"
            />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between items-center gap-2 w-full">
        <div><ErrorMessage :message="error" /></div>
        <div class="flex gap-2">
           <Button :label="__('Cancel')" @click="cancel" />
           <Button variant="solid" :label="__('Create')" :loading="isCreating" @click="createCustomer" />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { Dialog, FormControl, Button, ErrorMessage, toast, Autocomplete } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import { ref, watch, onMounted } from 'vue'

const __ = (window)._ || ((t) => t)

const props = defineProps({
  deal: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['success'])

const show = defineModel()

const organizationName = ref(props.deal.data?.organization || '')
const gstin = ref(props.deal.data?.organization_gstin || '')
const territory = ref(props.deal.data?.territory || '')
const customerType = ref('Company')
const defaultCurrency = ref(props.deal.data?.currency || '')
const creditLimit = ref(0)
const gstCategory = ref('')
const addressLine1 = ref('')
const addressLine2 = ref('')
const city = ref('')
const state = ref('')
const country = ref('')
const pincode = ref('')

const error = ref('')
const isCreating = ref(false)
const isFetching = ref(false)

watch(() => props.deal.data?.organization, (newVal) => {
  if (newVal) organizationName.value = newVal
})

watch(() => props.deal.data?.organization_gstin, (newVal) => {
  if (newVal) gstin.value = newVal
})

onMounted(() => {
  if (gstin.value && gstin.value.length === 15) {
    fetchGstinDetails()
  }
})

function cancel() {
  show.value = false
  error.value = ''
  organizationName.value = props.deal.data?.organization || ''
  gstin.value = props.deal.data?.organization_gstin || ''
  territory.value = props.deal.data?.territory || ''
  customerType.value = 'Company'
  defaultCurrency.value = props.deal.data?.currency || ''
  creditLimit.value = 0
  gstCategory.value = ''
  addressLine1.value = ''
  addressLine2.value = ''
  city.value = ''
  state.value = ''
  country.value = ''
  pincode.value = ''
}

function fetchGstinDetails() {
  if (!gstin.value || gstin.value.length !== 15) return
  
  isFetching.value = true
  frappe.call({
    method: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.fetch_gstin_details',
    args: { gstin: gstin.value },
    callback: function(r) {
      isFetching.value = false
      if (r.message && r.message.success) {
        const data = r.message.data
        if (data.organization) organizationName.value = data.organization
        if (data.company_type) customerType.value = data.company_type
        if (data.address_line1) addressLine1.value = data.address_line1
        if (data.address_line2) addressLine2.value = data.address_line2
        if (data.city) city.value = data.city
        if (data.state) state.value = data.state
        if (data.country) country.value = data.country
        if (data.pincode) pincode.value = data.pincode
        toast.success(__('GST details fetched successfully'))
      } else if (r.message && !r.message.success) {
        toast.error(r.message.error || __('Failed to fetch GST details'))
      }
    }
  })
}

function createCustomer() {
  if (!organizationName.value) {
    error.value = __('Organization Name is required')
    return
  }

  error.value = ''
  isCreating.value = true

  frappe.call({
    method: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.create_customer_from_deal',
    args: {
      crm_deal: props.deal.data?.name,
      customer_data: {
        organization: organizationName.value,
        gstin: gstin.value,
        territory: territory.value,
        customer_type: customerType.value ? (typeof customerType.value === 'object' ? customerType.value.value : customerType.value) : 'Company',
        default_currency: defaultCurrency.value,
        credit_limit: creditLimit.value,
        gst_category: (gstCategory.value && typeof gstCategory.value === 'object') ? gstCategory.value.value : (gstCategory.value || ''),
        address_line1: addressLine1.value,
        address_line2: addressLine2.value,
        city: city.value,
        state: state.value,
        country: country.value,
        pincode: pincode.value
      }
    },
    callback: function(r) {
      isCreating.value = false
      if (!r.exc && r.message && r.message.success) {
        show.value = false
        emit('success')
      } else {
        error.value = (r.message && r.message.error) ? r.message.error : __('Failed to create customer')
        toast.error(error.value)
      }
    }
  })
}
</script>
