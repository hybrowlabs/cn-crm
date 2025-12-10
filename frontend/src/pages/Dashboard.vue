<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        :label="__('Dashboard Builder')"
        variant="solid"
        @click="goToBuilder"
      >
        <template #prefix>
          <FeatherIcon name="layout" class="h-4 w-4" />
        </template>
      </Button>
    </template>
  </LayoutHeader>
  <SpancoWidget />
</template>

<script setup>
import { useRouter } from 'vue-router'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, Button, FeatherIcon } from 'frappe-ui'
import SpancoWidget from '@/components/Dashboard Elements/SpancoWidget.vue'

const router = useRouter()
let title = 'Dashboard'
const breadcrumbs = [{ label: title, route: { name: 'Dashboard' } }]

function goToBuilder() {
  router.push({ name: 'Dashboard Builder' })
}
</script>
