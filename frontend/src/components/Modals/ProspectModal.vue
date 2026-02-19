<template>
  <Dialog v-model="show" :options="{ size: '2xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Prospect') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button variant="ghost" class="w-7" @click="show = false">
              <template #icon>
                <FeatherIcon name="x" class="size-4" />
              </template>
            </Button>
          </div>
        </div>
        
        <div class="space-y-4">
            <FormControl
                v-model="prospect.customer_name"
                :label="__('Customer Name')"
                required
            />
            <FormControl
                v-model="prospect.organization"
                :label="__('Organization Name')"
            />
            <FormControl
                v-model="prospect.mobile_no"
                :label="__('Mobile Number')"
            />
            <FormControl
                v-model="prospect.email"
                :label="__('Email')"
                type="email"
            />
        </div>

        <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isCreating"
            @click="createProspect"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { capture } from '@/telemetry'
import { createResource, FormControl, ErrorMessage } from 'frappe-ui'
import { ref, reactive } from 'vue'

const show = defineModel()
const error = ref(null)
const isCreating = ref(false)

const prospect = reactive({
  customer_name: '',
  organization: '',
  mobile_no: '',
  email: ''
})

const createResourceInstance = createResource({
  url: 'frappe.client.insert',
})

function validate() {
  if (!prospect.customer_name) {
    return __('Customer Name is required');
  }
  return null;
}

function createProspect() {
  const validationError = validate();
  if (validationError) {
    error.value = validationError;
    return;
  }
  
  isCreating.value = true;
  error.value = null;

  createResourceInstance.submit(
    {
      doc: {
        doctype: 'Prospects',
        ...prospect,
      },
    },
    {
      onSuccess(data) {
        capture('prospect_created');
        isCreating.value = false;
        show.value = false;
        // Optionally emit an event to refresh the list
      },
      onError(err) {
        isCreating.value = false;
        if (err.messages) {
           error.value = err.messages.join('\n');
        } else {
           error.value = err.message;
        }
      },
    }
  );
}
</script>
