<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Bulk Import Leads'),
      size: '3xl',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-6 min-h-[400px]">
        <!-- Step Indicator -->
        <div class="flex items-center justify-between px-4 py-2 bg-gray-50 rounded-lg">
          <div
            v-for="(step, index) in steps"
            :key="index"
            class="flex items-center gap-2"
            :class="currentStep >= index ? 'text-blue-600' : 'text-gray-400'"
          >
            <div
              class="flex items-center justify-center w-6 h-6 rounded-full border text-xs font-bold"
              :class="currentStep >= index ? 'border-blue-600 bg-blue-50' : 'border-gray-300'"
            >
              {{ index + 1 }}
            </div>
            <span class="text-sm font-medium">{{ step }}</span>
            <div v-if="index < steps.length - 1" class="w-8 h-px bg-gray-300 mx-2"></div>
          </div>
        </div>

        <!-- Step 1: Field Selection -->
        <div v-if="currentStep === 0" class="flex flex-col gap-4">
          <div class="text-base font-medium text-ink-gray-9">
            {{ __('Select fields you want to import') }}
          </div>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3 overflow-y-auto max-h-[300px] p-1">
            <div
              v-for="field in importableFields.data"
              :key="field.fieldname"
              class="flex items-center gap-2 p-2 rounded border hover:bg-gray-50 cursor-pointer"
              @click="toggleField(field)"
            >
              <Checkbox
                :modelValue="selectedFields.includes(field.fieldname)"
                :disabled="field.reqd"
                @update:modelValue="toggleField(field)"
              />
              <div class="flex flex-col truncate">
                <span class="text-sm truncate" :class="field.reqd ? 'font-bold' : ''">
                  {{ field.label }}
                  <span v-if="field.reqd" class="text-red-500">*</span>
                </span>
                <span class="text-xs text-ink-gray-5 truncate">{{ field.fieldname }}</span>
              </div>
            </div>
          </div>
          <div class="flex justify-between items-center mt-2">
            <div class="text-xs text-ink-gray-5 italic">
              * {{ __('Mandatory fields are auto-selected') }}
            </div>
            <Button
              :label="__('Select All')"
              variant="ghost"
              size="sm"
              @click="selectAllFields"
            />
          </div>
        </div>

        <!-- Step 2: Template & Upload -->
        <div v-if="currentStep === 1" class="flex flex-col gap-6">
          <div class="flex flex-col gap-4 p-4 border rounded-lg bg-blue-50">
            <div class="text-base font-medium text-blue-900">
              {{ __('1. Download Template') }}
            </div>
            <div class="text-sm text-blue-800">
              {{ __('Download the template based on your selected fields, fill in the data, and then upload it back.') }}
            </div>
            <div class="flex gap-3">
              <Button
                :label="__('Download CSV Template')"
                @click="downloadTemplate('csv')"
                :loading="downloading"
              >
                <template #prefix><FeatherIcon name="download" class="h-4 w-4" /></template>
              </Button>
              <Button
                :label="__('Download Excel Template')"
                @click="downloadTemplate('excel')"
                :loading="downloading"
              >
                <template #prefix><FeatherIcon name="download" class="h-4 w-4" /></template>
              </Button>
            </div>
          </div>

          <div class="flex flex-col gap-4 p-4 border rounded-lg">
            <div class="text-base font-medium text-ink-gray-9">
              {{ __('2. Upload Filled Template') }}
            </div>
            <input
              type="file"
              accept=".csv, .xlsx, .xls"
              ref="fileInput"
              class="block w-full text-sm text-slate-500
                file:mr-4 file:py-2 file:px-4
                file:rounded file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
              @change="handleFileUpload"
            />
            <div v-if="file" class="flex items-center gap-2 text-sm text-green-600">
              <FeatherIcon name="check-circle" class="h-4 w-4" />
              <span>{{ file.name }} {{ __('selected') }}</span>
            </div>
            <div v-if="fileError" class="text-sm text-red-500">
              {{ fileError }}
            </div>
          </div>
        </div>

        <!-- Step 3: Review & Import -->
        <div v-if="currentStep === 2" class="flex flex-col gap-4">
          <div v-if="importing" class="flex flex-col items-center justify-center gap-4 py-12">
            <LoadingIndicator class="h-8 w-8" />
            <div class="text-lg font-medium text-ink-gray-9">{{ __('Importing leads...') }}</div>
            <div class="text-sm text-ink-gray-5">{{ __('Please do not close this modal.') }}</div>
          </div>
          <div v-else-if="importResult" class="flex flex-col gap-4">
            <div class="flex items-center gap-3 p-4 rounded-lg" :class="importResult.error_count > 0 ? 'bg-orange-50 border border-orange-200' : 'bg-green-50 border border-green-200'">
              <div
                class="flex items-center justify-center w-12 h-12 rounded-full"
                :class="importResult.error_count > 0 ? 'bg-orange-100 text-orange-600' : 'bg-green-100 text-green-600'"
              >
                <FeatherIcon :name="importResult.error_count > 0 ? 'alert-triangle' : 'check-circle'" class="h-6 w-6" />
              </div>
              <div class="flex flex-col">
                <div class="text-lg font-bold" :class="importResult.error_count > 0 ? 'text-orange-900' : 'text-green-900'">
                  {{ importResult.created_count }} {{ __('Leads imported successfully') }}
                </div>
                <div v-if="importResult.error_count > 0" class="text-sm text-orange-800">
                  {{ importResult.error_count }} {{ __('failed to import') }}
                </div>
              </div>
            </div>

            <div v-if="importResult.errors && importResult.errors.length > 0" class="flex flex-col gap-2">
              <div class="text-sm font-semibold text-ink-gray-9">{{ __('Errors (First 10):') }}</div>
              <div class="max-h-[200px] overflow-y-auto border rounded divide-y">
                <div v-for="(err, idx) in importResult.errors" :key="idx" class="p-2 text-xs">
                  <div class="font-medium text-red-600">{{ err.error }}</div>
                  <div class="text-gray-500 mt-1 truncate">{{ JSON.stringify(err.row) }}</div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="flex flex-col gap-4 py-8 items-center text-center">
             <div class="text-lg font-medium text-ink-gray-9">{{ __('Ready to import') }}</div>
             <div class="text-sm text-ink-gray-5 max-w-sm">
               {{ __('Click "Import Now" to start the process. We will create {0} leads from your file.', [parsedRows.length]) }}
             </div>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between w-full">
        <div>
          <Button
            v-if="currentStep > 0 && !importing && !importResult"
            :label="__('Back')"
            @click="currentStep--"
          />
        </div>
        <div class="flex gap-2">
          <Button
            :label="importResult ? __('Close') : __('Cancel')"
            @click="close"
          />
          <Button
            v-if="currentStep === 0"
            variant="solid"
            :label="__('Next: Template & Upload')"
            :disabled="selectedFields.length === 0"
            @click="currentStep = 1"
          />
          <Button
            v-if="currentStep === 1"
            variant="solid"
            :label="__('Next: Review')"
            :disabled="!file || !!fileError"
            @click="prepareReview"
          />
          <Button
            v-if="currentStep === 2 && !importResult"
            variant="solid"
            :label="__('Import Now')"
            :loading="importing"
            @click="performImport"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Dialog,
  Button,
  Checkbox,
  LoadingIndicator,
  toast,
  FeatherIcon,
  createResource,
  call
} from 'frappe-ui'
import { ref, computed, onMounted, watch } from 'vue'

const show = defineModel()
const emit = defineEmits(['success'])
const __ = window.__ || ((s, ...args) => s)

const steps = [
  __('Field Selection'),
  __('Template & Upload'),
  __('Import')
]
const currentStep = ref(0)
const selectedFields = ref([])
const downloading = ref(false)
const uploading = ref(false)
const importing = ref(false)
const fileInput = ref(null)
const file = ref(null)
const fileError = ref('')
const parsedRows = ref([])
const importResult = ref(null)

const importableFields = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_importable_fields',
  params: { doctype: 'CRM Lead' },
  auto: true,
  onSuccess: (data) => {
    // Auto select mandatory fields
    selectedFields.value = data
      .filter(f => f.reqd)
      .map(f => f.fieldname)
  }
})

function toggleField(field) {
  if (field.reqd) return // Cannot unselect mandatory fields
  const index = selectedFields.value.indexOf(field.fieldname)
  if (index > -1) {
    selectedFields.value.splice(index, 1)
  } else {
    selectedFields.value.push(field.fieldname)
  }
}

function selectAllFields() {
  selectedFields.value = importableFields.data.map(f => f.fieldname)
}

async function downloadTemplate(type) {
  downloading.value = true
  try {
    const response = await fetch(`/api/method/crm.fcrm.doctype.crm_lead.api.download_lead_import_template?fields=${JSON.stringify(selectedFields.value)}&file_type=${type}`)
    
    if (!response.ok) throw new Error('Download failed')
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `lead_import_template.${type === 'excel' ? 'xlsx' : 'csv'}`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
  } catch (error) {
    toast.error(__('Failed to download template'))
    console.error(error)
  } finally {
    downloading.value = false
  }
}

function handleFileUpload(event) {
  const selectedFile = event.target.files[0]
  fileError.value = ''
  file.value = null
  parsedRows.value = []
  
  if (!selectedFile) return
  
  const ext = selectedFile.name.split('.').pop().toLowerCase()
  if (!['csv', 'xlsx', 'xls'].includes(ext)) {
    fileError.value = __('Please upload a CSV or Excel file.')
    return
  }
  
  file.value = selectedFile
}

async function prepareReview() {
  if (!file.value) return
  
  parsedRows.value = []
  const ext = file.value.name.split('.').pop().toLowerCase()
  const reader = new FileReader()
  
  reader.onload = async (e) => {
    const base64Data = e.target.result
    try {
      const rows = await call('crm.fcrm.doctype.crm_lead.api.parse_import_file', {
        file: base64Data,
        file_type: ext === 'csv' ? 'csv' : 'excel'
      })
      parsedRows.value = rows
      currentStep.value = 2
    } catch (error) {
      toast.error(error.message || __('Failed to parse file'))
    }
  }
  reader.readAsDataURL(file.value)
}


async function performImport() {
  importing.value = true
  importResult.value = null
  
  try {
    if (parsedRows.value.length === 0) {
      toast.error(__('No data to import'))
      importing.value = false
      return
    }

    const result = await call('crm.fcrm.doctype.crm_lead.api.bulk_import_leads', {
      data: parsedRows.value
    })
    
    importResult.value = result
    if (result.created_count > 0) {
      emit('success')
    }
  } catch (error) {
    toast.error(error.message || __('Import failed'))
  } finally {
    importing.value = false
  }
}

function close() {
  if (importResult.value && importResult.value.created_count > 0) {
    emit('success')
  }
  show.value = false
}

function reset() {
  currentStep.value = 0
  file.value = null
  fileError.value = ''
  parsedRows.value = []
  importResult.value = null
}

watch(show, (val) => {
  if (!val) reset()
})
</script>
