<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Import Prospects'),
      size: 'xl',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-2">
            <div class="flex justify-between items-center">
                <div class="text-p-base text-ink-gray-5">
                    {{ __('Upload a CSV file to import prospects.') }}
                </div>
                <Button :label="__('Download Template')" @click="downloadTemplate">
                    <template #prefix>
                        <FeatherIcon name="download" class="h-4 w-4" />
                    </template>
                </Button>
            </div>
            <div class="text-sm text-ink-gray-5">
                {{ __('The CSV should have headers: Name, Organization, Email, Mobile.') }}
            </div>
        </div>
        
        <div class="flex flex-col gap-2">
            <input 
                type="file" 
                accept=".csv" 
                ref="fileInput" 
                class="block w-full text-sm text-slate-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-violet-50 file:text-violet-700
                  hover:file:bg-violet-100"
                @change="handleFileUpload"
            />
        </div>

        <div v-if="error" class="text-red-500 text-sm">
            {{ error }}
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="cancel" />
        <Button
          variant="solid"
          :label="__('Import')"
          :loading="loading"
          :disabled="!csvContent"
          @click="importProspects"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, toast, FeatherIcon } from 'frappe-ui'
import { ref, watch } from 'vue'
import { call } from 'frappe-ui'

const show = defineModel()
const emit = defineEmits(['success'])

const fileInput = ref(null)
const csvContent = ref(null)
const loading = ref(false)
const error = ref('')

function handleFileUpload(event) {
    const file = event.target.files[0]
    error.value = ''
    csvContent.value = null

    if (!file) return

    if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        error.value = 'Please upload a valid CSV file.'
        return
    }

    const reader = new FileReader()
    reader.onload = (e) => {
        csvContent.value = e.target.result
    }
    reader.onerror = () => {
        error.value = 'Error reading file.'
    }
    reader.readAsText(file)
}

function cancel() {
    show.value = false
    csvContent.value = null
    error.value = ''
    if(fileInput.value) fileInput.value.value = ''
}

async function importProspects() {
    if (!csvContent.value) return

    loading.value = true
    error.value = ''

    try {
        const result = await call('crm.fcrm.doctype.prospects.prospects.import_prospects_csv', {
            csv_content: csvContent.value
        })

        if (result.created_count > 0) {
            toast.success(`Successfully imported ${result.created_count} prospects.`)
            emit('success')
            cancel()
        } else {
            toast.error('No prospects imported.')
        }

        if (result.errors && result.errors.length > 0) {
            console.error('Import Errors:', result.errors)
            error.value = `Imported with errors. Check console for details.`
        }

    } catch (e) {
        error.value = e.message || 'Error importing prospects.'
    } finally {
        loading.value = false
    }
}

function downloadTemplate() {
    const headers = ['Name', 'Organization', 'Email', 'Mobile']
    const csvContent = headers.join(',') + '\n'
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob)
        link.setAttribute('href', url)
        link.setAttribute('download', 'prospects_import_template.csv')
        link.style.visibility = 'hidden'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    }
}
</script>
