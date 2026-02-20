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
      <ListFooter>
        <ListPagination
          class="sm:mx-5 mx-3"
          v-if="customers.data"
          @updatePageCount="pageLengthCount = $event"
          :start="customers.data.length ? (customers.page_length_count * (customers.page_length_count > 0 ? (customers.page_length_count / 20) : 0)) + 1 : 0"
          :totalCount="1000"
          :end="customers.data.length"
          :rowCount="customers.data.length"
          @loadMore="customers.reload()"
        />
      </ListFooter>
    </ListView>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import { ListView, ListHeader, ListHeaderItem, ListRowItem, ListFooter, ListPagination, createListResource } from 'frappe-ui'
import { ref, watch } from 'vue'

const pageLengthCount = ref(20)

const customers = createListResource({
  doctype: 'Customer',
  fields: ['name', 'customer_name', 'customer_group', 'territory', 'primary_address', 'mobile_no'],
  getTemplate: 'crm.fcrm.doctype.frequency_log_list.frequency_log_list.get_customers_for_user',
  orderBy: 'creation desc',
  auto: true,
  pageLength: pageLengthCount.value,
  transform(data) {
    return data || []
  }
})

watch(pageLengthCount, (newVal) => {
    customers.limit = newVal
    customers.reload()
})

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
