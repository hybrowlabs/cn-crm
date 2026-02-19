<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex items-center gap-2">
        <h1 class="text-xl font-bold text-ink-gray-9">{{ __('Prospects') }}</h1>
      </div>
    </template>
    <template #right-header>
      <Button
        variant="outline"
        :label="__('Import')"
        @click="showImportModal = true"
        class="mr-2"
      >
        <template #prefix><FeatherIcon name="upload" class="h-4" /></template>
      </Button>
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showProspectModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  
  <div class="flex h-full flex-col overflow-auto">
    <ListView
      :columns="columns"
      :rows="prospects.data || []"
      :options="{
        selectable: true,
        showTooltip: true,
        resizeColumn: true,
      }"
      row-key="name"
    >
      <ListHeader class="sm:mx-5 mx-3">
        <ListHeaderItem
            v-for="column in columns"
            :key="column.key"
            :item="column"
        />
      </ListHeader>
      <ListRows :rows="prospects.data || []" v-slot="{ idx, column, item, row }" doctype="Prospects">
        <ListRowItem :item="item" :align="column.align">
            <template #default="{ label }">
                 <div v-if="column.key === 'actions'" class="flex justify-end">
                    <Button
                        variant="ghost"
                        :label="__('Convert to Lead')"
                        @click.stop="convertToLead(row)"
                    >
                        <template #prefix>
                            <FeatherIcon name="corner-up-right" class="h-4 w-4" />
                        </template>
                    </Button>
                 </div>
                 <div v-else class="truncate text-base">{{ label }}</div>
            </template>
        </ListRowItem>
      </ListRows>
    </ListView>
  </div>

  <ProspectModal v-if="showProspectModal" v-model="showProspectModal" />
  <ProspectImportModal
    v-if="showImportModal"
    v-model="showImportModal"
    @success="prospects.reload()"
  />
  <LeadModal
    v-if="showLeadModal"
    v-model="showLeadModal"
    :defaults="leadDefaults"
    @success="handleLeadCreated"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ProspectModal from '@/components/Modals/ProspectModal.vue'
import ProspectImportModal from '@/components/Modals/ProspectImportModal.vue'
import LeadModal from '@/components/Modals/LeadModal.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import { ListView, ListHeader, ListHeaderItem, ListRowItem, createListResource, Button, FeatherIcon, call } from 'frappe-ui'
import { ref } from 'vue'

const showProspectModal = ref(false)
const showLeadModal = ref(false)
const showImportModal = ref(false)
const leadDefaults = ref({})
const currentProspectId = ref(null)

const prospects = createListResource({
  doctype: 'Prospects',
  fields: ['name', 'customer_name', 'organization', 'mobile_no', 'email', 'status'],
  filters: {
    status: ['!=', 'Converted']
  },
  orderBy: 'creation desc',
  auto: true,
})

const columns = [
  {
    label: __('Customer Name'),
    key: 'customer_name',
    width: '200px',
  },
  {
    label: __('Organization'),
    key: 'organization',
    width: '200px',
  },
  {
    label: __('Mobile'),
    key: 'mobile_no',
    width: '150px',
  },
  {
    label: __('Email'),
    key: 'email',
    width: '200px',
  },
  {
    label: '',
    key: 'actions',
    width: '150px',
    align: 'right',
  }
]

function convertToLead(row) {
    currentProspectId.value = row.name
    leadDefaults.value = {
        first_name: row.customer_name,
        organization: row.organization,
        mobile_no: row.mobile_no,
        email: row.email
    }
    showLeadModal.value = true
}

function handleLeadCreated() {
    if (currentProspectId.value) {
        call('crm.fcrm.doctype.prospects.prospects.mark_prospect_converted', { prospect_id: currentProspectId.value })
            .then(() => {
                prospects.reload()
                currentProspectId.value = null
            })
    }
}
</script>
