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
      :rows="customers.data || []"
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
      <ListRows :rows="customers.data || []" v-slot="{ idx, column, item, row }" doctype="Customer">
        <ListRowItem :item="item" :align="column.align">
            <template #default="{ label }">
                 <div class="truncate text-base">{{ label }}</div>
            </template>
        </ListRowItem>
      </ListRows>
    </ListView>
    <div class="flex items-center justify-between border-t px-5 py-3" v-if="customers.data && customers.data.length >= pageLengthCount">
        <Button
            variant="subtle"
            @click="loadNextPage"
            :loading="customers.loading"
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
import { ListView, ListHeader, ListHeaderItem, ListRowItem, createListResource, Button } from 'frappe-ui'
import { ref } from 'vue'

const pageLengthCount = ref(20)
const pageStart = ref(0)
const allCustomers = ref([])

const customers = createListResource({
  doctype: 'Customer',
  fields: ['name', 'customer_name', 'customer_group', 'territory', 'primary_address', 'mobile_no'],
  getTemplate: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_customers_for_user',
  orderBy: 'creation desc',
  auto: true,
  makeParams() {
    return {
        limit_start: pageStart.value,
        limit_page_length: pageLengthCount.value
    }
  },
  onSuccess(data) {
     if (pageStart.value === 0) {
        allCustomers.value = data || []
     } else if (data && data.length) {
        allCustomers.value = [...allCustomers.value, ...data]
     }
  },
  transform(data) {
    return allCustomers.value || []
  }
})

function loadNextPage() {
    pageStart.value += pageLengthCount.value
    customers.reload()
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
