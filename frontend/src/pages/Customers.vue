<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex items-center gap-2">
        <h1 class="text-xl font-bold text-ink-gray-9">{{ __('Customers') }}</h1>
      </div>
    </template>
  </LayoutHeader>
  
  <div class="flex h-full flex-col overflow-auto">
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
        <ListRowItem :item="item" :align="column.align">
            <template #default="{ label }">
                 <div class="truncate text-base">{{ label }}</div>
            </template>
        </ListRowItem>
      </ListRows>
    </ListView>
    <div class="flex items-center justify-between border-t px-5 py-3" v-if="allCustomers && allCustomers.length >= pageLengthCount">
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
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import { ListView, ListHeader, ListHeaderItem, ListRowItem, Button, call } from 'frappe-ui'
import { ref, onMounted } from 'vue'

const pageLengthCount = ref(20)
const pageStart = ref(0)
const loading = ref(false)
const allCustomers = ref([])

function fetchCustomers() {
    loading.value = true
    call('crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_customers_for_user', {
        limit_start: pageStart.value,
        limit_page_length: pageLengthCount.value
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
