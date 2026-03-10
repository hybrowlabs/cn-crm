<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex items-center gap-2">
        <h1 class="text-xl font-bold text-ink-gray-9">{{ __('Customers') }}</h1>
      </div>
    </template>
  </LayoutHeader>
  
  <div class="flex flex-col flex-1 h-full overflow-hidden">
    <!-- Header with Search -->
    <div class="flex items-center justify-between border-b px-5 py-3 bg-surface-gray-2">
      <div class="w-1/3">
        <FormControl
          type="text"
          :placeholder="__('Search Customers...')"
          v-model="searchQuery"
          @input="handleSearch"
        />
      </div>
    </div>

    <!-- Customer List -->
    <div class="flex flex-col flex-1 overflow-auto">
      <ListView
        :columns="columns"
        :rows="allCustomers || []"
        :options="{
          selectable: false,
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
        <ListRows :rows="allCustomers || []" v-slot="{ idx, column, item, row }" doctype="Customer">
          <ListRowItem :item="item" :align="column.align" @click="openCustomerModal(row)">
              <template #default="{ label }">
                   <div class="truncate text-base">{{ label }}</div>
              </template>
          </ListRowItem>
        </ListRows>
      </ListView>
      <div class="flex items-center justify-between border-t px-5 py-3" v-if="allCustomers && allCustomers.length >= pageLengthCount && !searchQuery">
          <Button
              variant="subtle"
              @click="loadNextPage"
              :loading="loading"
              class="w-full"
          >
              {{ __('Load More') }}
          </Button>
      </div>
    </div>
  </div>

  <CustomerDetailsModal
    v-if="showCustomerModal"
    v-model="showCustomerModal"
    :customerName="selectedCustomerName"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import CustomerDetailsModal from '@/components/Modals/CustomerDetailsModal.vue'
import { ListView, ListHeader, ListHeaderItem, ListRowItem, Button, FormControl, call } from 'frappe-ui'
import { ref, onMounted } from 'vue'

const __ = (window)._ || ((t) => t)

const pageLengthCount = ref(20)
const pageStart = ref(0)
const loading = ref(false)
const allCustomers = ref([])
const searchQuery = ref('')
let searchTimeout = null

const showCustomerModal = ref(false)
const selectedCustomerName = ref('')

function fetchCustomers(reset = false) {
    if (reset) {
      pageStart.value = 0
      allCustomers.value = []
    }
    
    loading.value = true
    call('crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_customers_for_user', {
        limit_start: pageStart.value,
        limit_page_length: pageLengthCount.value,
        search_term: searchQuery.value
    }).then(res => {
        if (res) {
            if (pageStart.value === 0) {
                allCustomers.value = res
            } else {
                allCustomers.value = [...allCustomers.value, ...res]
            }
        }
    }).finally(() => {
        loading.value = false
    })
}

function handleSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchCustomers(true)
  }, 300)
}

function openCustomerModal(row) {
  selectedCustomerName.value = row.name
  showCustomerModal.value = true
}

onMounted(() => {
    fetchCustomers()
})

function loadNextPage() {
    pageStart.value += pageLengthCount.value
    fetchCustomers()
}

const columns = [
  {
    label: __('Customer Name'),
    key: 'customer_name',
    width: '200px',
  },
  {
    label: __('Customer Group'),
    key: 'customer_group',
    width: '150px',
  },
  {
    label: __('Territory'),
    key: 'territory',
    width: '150px',
  },
  {
    label: __('Primary Address'),
    key: 'primary_address',
    width: '300px',
  },
  {
    label: __('Contact No'),
    key: 'mobile_no',
    width: '150px',
  }
]
</script>
