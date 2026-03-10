<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Customer Details') }"
  >
    <template #body-content>
      <div v-if="loading" class="flex justify-center p-5">
        <LoadingIndicator class="h-6 w-6 text-ink-gray-5" />
      </div>
      <div v-else-if="customer" class="flex flex-col gap-4 sm:min-w-[500px] w-full">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <div class="text-xs text-ink-gray-5 mb-1">{{ __('Customer Name') }}</div>
            <div class="font-medium truncate text-ink-gray-9">{{ customer.customer_name }}</div>
          </div>
          <div>
            <div class="text-xs text-ink-gray-5 mb-1">{{ __('Customer Group') }}</div>
            <div class="font-medium truncate text-ink-gray-9">{{ customer.customer_group }}</div>
          </div>
          <div>
            <div class="text-xs text-ink-gray-5 mb-1">{{ __('Customer Type') }}</div>
            <div class="font-medium truncate text-ink-gray-9">{{ customer.customer_type || '-' }}</div>
          </div>
          <div>
            <div class="text-xs text-ink-gray-5 mb-1">{{ __('Territory') }}</div>
            <div class="font-medium truncate text-ink-gray-9">{{ customer.territory || '-' }}</div>
          </div>
          <div>
            <div class="text-xs text-ink-gray-5 mb-1">{{ __('Default Currency') }}</div>
            <div class="font-medium truncate text-ink-gray-9">{{ customer.default_currency || '-' }}</div>
          </div>
        </div>

        <div class="w-full h-px bg-outline-gray-2 my-2"></div>

        <div>
          <div class="text-sm font-semibold text-ink-gray-7">{{ __('Address & Contact') }}</div>
          <div v-if="customer.primary_address" class="text-sm mt-1 text-ink-gray-9" v-html="customer.primary_address.replace(/\n/g, '<br>')"></div>
          <div v-else class="text-sm mt-1 text-ink-gray-5">{{ __('No primary address set') }}</div>
          
          <div v-if="customer.mobile_no" class="text-sm mt-2 text-ink-gray-9">
            <span class="text-ink-gray-5">{{ __('Mobile') }}:</span> {{ customer.mobile_no }}
          </div>
          <div v-if="customer.email_id" class="text-sm mt-1 text-ink-gray-9">
            <span class="text-ink-gray-5">{{ __('Email') }}:</span> {{ customer.email_id }}
          </div>
        </div>

        <div class="w-full h-px bg-outline-gray-2 my-2"></div>

        <div>
          <div class="text-sm font-semibold text-ink-gray-7 mb-2">{{ __('Sales Team') }}</div>
          <div v-if="customer.sales_team && customer.sales_team.length > 0" class="border rounded-md divide-y overflow-hidden max-h-[150px] overflow-y-auto">
             <div class="grid grid-cols-2 bg-surface-gray-2 p-2 text-xs font-semibold text-ink-gray-5">
               <div>{{ __('Sales Person') }}</div>
               <div>{{ __('Contribution (%)') }}</div>
             </div>
             <div v-for="member in customer.sales_team" :key="member.name" class="grid grid-cols-2 p-2 text-sm text-ink-gray-9 items-center">
               <div class="truncate">{{ member.sales_person }}</div>
               <div>{{ member.allocated_percentage || 0 }}%</div>
             </div>
          </div>
          <div v-else class="text-sm text-ink-gray-5 italic">{{ __('No sales team assigned') }}</div>
        </div>
      </div>
      <div v-else class="text-center p-5 text-ink-red-3">
         {{ __('Failed to load customer details') }}
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end w-full">
         <Button :label="__('Close')" @click="show = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, call } from 'frappe-ui'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { ref, watch, onMounted } from 'vue'

const __ = (window)._ || ((t) => t)

const props = defineProps({
  customerName: {
    type: String,
    required: true
  }
})

const show = defineModel()
const loading = ref(true)
const customer = ref(null)

function fetchCustomerDetails() {
  if (!props.customerName) return
  loading.value = true
  
  call('frappe.client.get', {
    doctype: 'Customer',
    name: props.customerName
  })
  .then(res => {
    if (res) {
      customer.value = res
    }
  })
  .finally(() => {
    loading.value = false
  })
}

watch(() => props.customerName, (newVal) => {
  if (show.value && newVal) {
    fetchCustomerDetails()
  }
})

onMounted(() => {
  if (props.customerName) {
    fetchCustomerDetails()
  }
})
</script>
