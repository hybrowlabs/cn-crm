<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-header>
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Create Meeting') }}
          </h3>
          <p class="text-sm text-ink-gray-5 mt-1">
            {{ __('Schedule a discovery meeting for') }} {{ lead.lead_name || lead.name }}
          </p>
        </div>
        <Button icon="x" variant="ghost" @click="show = false" />
      </div>
    </template>

    <template #body-content>
      <div class="max-h-[60vh] overflow-y-auto pr-2">
        <!-- Meeting Details Section -->
        <div class="mb-6">
          <h4 class="text-sm font-medium text-ink-gray-9 mb-4 flex items-center gap-2">
            <CalendarIcon class="h-4 w-4" />
            {{ __('Meeting Details') }}
          </h4>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Meeting Type') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="link"
                :value="meetingData.meeting_type"
                @change="(val) => meetingData.meeting_type = val"
                :link="{
                  doctype: 'CRM Meeting Type',
                  filters: {},
                }"
                class="w-full"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Meeting Date & Time') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="datetime"
                :value="meetingData.meeting_date"
                @change="(val) => meetingData.meeting_date = val"
                class="w-full"
              />
            </div>
          </div>
        </div>
        
        <!-- Discovery Information Section -->
        <div class="mb-6 border-t pt-6">
          <h4 class="text-sm font-medium text-ink-gray-9 mb-4 flex items-center gap-2">
            <DetailsIcon class="h-4 w-4" />
            {{ __('Discovery Information') }}
          </h4>
          
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Product Discussed') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="link"
                :value="meetingData.product_discussed"
                @change="(val) => meetingData.product_discussed = val"
                :link="{
                  doctype: 'CRM Product',
                  filters: {},
                }"
                class="w-full"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Volume Range (kg)') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="float"
                :value="meetingData.volume_range"
                @change="(val) => meetingData.volume_range = parseFloat(val) || 0"
                class="w-full"
              />
            </div>
          </div>
          
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Primary Pain Category') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="link"
                :value="meetingData.primary_pain_category"
                @change="(val) => meetingData.primary_pain_category = val"
                :link="{
                  doctype: 'CRM Pain Catagory',
                  filters: {},
                }"
                class="w-full"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Customer Role') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="link"
                :value="meetingData.customer_role_type"
                @change="(val) => meetingData.customer_role_type = val"
                :link="{
                  doctype: 'CRM Customer Role',
                  filters: {},
                }"
                class="w-full"
              />
            </div>
          </div>
          
          <div class="mb-4">
            <label class="block text-sm font-medium text-ink-gray-7 mb-1">
              {{ __('Pain Description') }}
            </label>
            <FormControl
              type="textarea"
              :value="meetingData.pain_description"
              @change="(val) => meetingData.pain_description = val"
              :rows="3"
              class="w-full"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-ink-gray-7 mb-1">
              {{ __('Current Supplier') }}
            </label>
            <FormControl
              type="text"
              :value="meetingData.current_supplier"
              @change="(val) => meetingData.current_supplier = val"
              class="w-full"
            />
          </div>
        </div>
        
        <!-- Qualification Section -->
        <div class="mb-6 border-t pt-6">
          <h4 class="text-sm font-medium text-ink-gray-9 mb-4 flex items-center gap-2">
            <TaskIcon class="h-4 w-4" />
            {{ __('Qualification') }}
          </h4>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Decision Maker Identified?') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="select"
                :value="meetingData.decision_maker_identified"
                @change="(val) => meetingData.decision_maker_identified = val"
                :options="[
                  { label: __('Yes'), value: 'Yes' },
                  { label: __('No'), value: 'No' },
                ]"
                class="w-full"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-ink-gray-7 mb-1">
                {{ __('Agrees to Trial?') }} <span class="text-red-500">*</span>
              </label>
              <FormControl
                type="select"
                :value="meetingData.agrees_to_trial"
                @change="(val) => meetingData.agrees_to_trial = val"
                :options="[
                  { label: __('Yes'), value: 'Yes' },
                  { label: __('No'), value: 'No' },
                ]"
                class="w-full"
              />
            </div>
          </div>
        </div>
      </div>
      
      <ErrorMessage class="mt-4" :message="error" />
    </template>

    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" variant="outline" @click="show = false" />
        <Button
          :label="__('Create Meeting')"
          variant="solid"
          @click="createMeeting"
          :loading="loading"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import { Dialog, FormControl, ErrorMessage, call, toast } from 'frappe-ui'
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: {
    type: Object,
    required: true,
  },
})

const show = defineModel()
const router = useRouter()

const loading = ref(false)
const error = ref('')

const meetingData = ref({
  lead: '',
  meeting_type: '',
  meeting_date: '',
  product_discussed: '',
  volume_range: 0,
  primary_pain_category: '',
  pain_description: '',
  customer_role_type: '',
  decision_process: '',
  current_supplier: '',
  next_action_date: '',
  decision_maker_identified: 'No',
  agrees_to_trial: 'No',
})

// Initialize lead when prop changes
watch(() => props.lead, (newLead) => {
  if (newLead?.name) {
    meetingData.value.lead = newLead.name
  }
}, { immediate: true })

async function createMeeting() {
  error.value = ''
  
  // Validation
  if (!meetingData.value.meeting_date) {
    error.value = __('Meeting Date & Time is required')
    return
  }
  if (!meetingData.value.product_discussed) {
    error.value = __('Product Discussed is required')
    return
  }
  if (!meetingData.value.volume_range || meetingData.value.volume_range <= 0) {
    error.value = __('Volume Range must be greater than 0')
    return
  }
  if (!meetingData.value.primary_pain_category) {
    error.value = __('Primary Pain Category is required')
    return
  }
  if (!meetingData.value.customer_role_type) {
    error.value = __('Customer Role is required')
    return
  }
  
  loading.value = true
  
  try {
    const result = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Meeting',
        ...meetingData.value,
      },
    })
    
    toast.success(__('Meeting created successfully'))
    show.value = false
    
    // Optionally navigate to meeting or show success
    // router.push({ name: 'Meeting', params: { meetingId: result.name } })
  } catch (err) {
    if (err.exc_type === 'MandatoryError') {
      const errorMessage = err.messages
        .map((msg) => {
          let arr = msg.split(': ')
          return arr[arr.length - 1].trim()
        })
        .join(', ')
      error.value = __('{0} is required', [errorMessage])
    } else {
      error.value = err.messages?.[0] || __('Error creating meeting')
    }
  } finally {
    loading.value = false
  }
}
</script>
