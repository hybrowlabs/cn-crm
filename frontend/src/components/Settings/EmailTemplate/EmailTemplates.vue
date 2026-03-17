<script setup>
import { TemplateOption } from '@/utils'
import {
  TextInput,
  FormControl,
  Switch,
  Dropdown,
  FeatherIcon,
  toast,
  Badge,
  Button,
} from 'frappe-ui'
import { ref, computed, inject } from 'vue'
import { isMobileView } from '@/composables/settings'

const emit = defineEmits(['updateStep'])

const templates = inject('templates')

const search = ref('')
const currentDoctype = ref('All')
const confirmDelete = ref(false)

const templatesList = computed(() => {
  let list = templates.data || []
  if (search.value) {
    list = list.filter(
      (template) =>
        template.name.toLowerCase().includes(search.value.toLowerCase()) ||
        template.subject.toLowerCase().includes(search.value.toLowerCase()),
    )
  }
  if (currentDoctype.value !== 'All') {
    list = list.filter(
      (template) => template.reference_doctype === currentDoctype.value,
    )
  }
  return list
})

function toggleEmailTemplate(template) {
  templates.setValue.submit(
    {
      name: template.name,
      enabled: template.enabled ? 1 : 0,
    },
    {
      onSuccess: () => {
        toast.success(
          template.enabled
            ? __('Template enabled successfully')
            : __('Template disabled successfully'),
        )
      },
      onError: (error) => {
        toast.error(error.messages[0] || __('Failed to update template'))
        // Revert the change if there was an error
        template.enabled = !template.enabled
      },
    },
  )
}

function deleteTemplate(template) {
  confirmDelete.value = false
  templates.delete.submit(template.name, {
    onSuccess: () => {
      toast.success(__('Template deleted successfully'))
    },
    onError: (error) => {
      toast.error(error.messages[0] || __('Failed to delete template'))
    },
  })
}

function getDropdownOptions(template) {
  let options = [
    {
      label: __('Duplicate'),
      component: (props) =>
        TemplateOption({
          option: __('Duplicate'),
          icon: 'copy',
          active: props.active,
          onClick: () => emit('updateStep', 'new-template', { ...template }),
        }),
    },
    {
      label: __('Delete'),
      component: (props) =>
        TemplateOption({
          option: __('Delete'),
          icon: 'trash-2',
          active: props.active,
          onClick: (e) => {
            e.preventDefault()
            e.stopPropagation()
            confirmDelete.value = true
          },
        }),
      condition: () => !confirmDelete.value,
    },
    {
      label: __('Confirm Delete'),
      component: (props) =>
        TemplateOption({
          option: __('Confirm Delete'),
          icon: 'trash-2',
          active: props.active,
          theme: 'danger',
          onClick: () => deleteTemplate(template),
        }),
      condition: () => confirmDelete.value,
    },
  ]

  return options.filter((option) => option.condition?.() || true)
}
</script>

<template>
  <div
    class="flex h-full flex-col gap-6 text-ink-gray-8"
    :class="isMobileView ? 'p-4' : 'p-6'"
  >
    <!-- Header -->
    <div
      class="flex gap-4 px-2 pt-2"
      :class="isMobileView ? 'flex-col items-start' : 'justify-between'"
    >
      <div class="flex flex-col gap-1 flex-1 min-w-0">
        <h2 class="flex gap-2 text-xl font-semibold leading-none">
          {{ __('Email templates') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Add, edit, and manage email templates for various CRM communications',
            )
          }}
        </p>
      </div>
      <div
        class="flex item-center shrink-0"
        :class="isMobileView ? 'w-full' : 'w-auto justify-end'"
      >
        <Button
          :label="__('New')"
          icon-left="plus"
          variant="solid"
          class="w-full sm:w-auto"
          @click="emit('updateStep', 'new-template')"
        />
      </div>
    </div>

    <!-- loading state -->
    <div
      v-if="templates.loading"
      class="flex mt-28 justify-center w-full h-full"
    >
      <Button :loading="true" variant="ghost" class="w-full" size="2xl" />
    </div>

    <!-- Empty State -->
    <div
      v-if="!templates.loading && !templates.data?.length"
      class="flex justify-between w-full h-full"
    >
      <div
        class="text-ink-gray-4 border border-dashed rounded w-full flex items-center justify-center p-8 text-center"
      >
        {{ __('No email templates found') }}
      </div>
    </div>

    <!-- Email template list -->
    <div
      class="flex flex-col overflow-hidden"
      v-if="!templates.loading && templates.data?.length"
    >
      <div
        class="flex items-center justify-between mb-4 px-2 pt-0.5"
        :class="isMobileView ? 'flex-col gap-4 items-stretch' : 'gap-4'"
      >
        <TextInput
          ref="searchRef"
          v-model="search"
          :placeholder="__('Search template')"
          :class="isMobileView ? 'w-full' : 'w-1/3'"
          :debounce="300"
        >
          <template #prefix>
            <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-6" />
          </template>
        </TextInput>
        <FormControl
          type="select"
          v-model="currentDoctype"
          class="sm:w-48"
          :options="[
            { label: __('All Type'), value: 'All' },
            { label: __('Lead'), value: 'CRM Lead' },
            { label: __('Deal'), value: 'CRM Deal' },
          ]"
        />
      </div>

      <!-- Desktop Header -->
      <div
        v-if="!isMobileView"
        class="flex items-center py-2 px-4 text-sm text-ink-gray-5 border-b border-outline-gray-modals"
      >
        <div class="flex-1">{{ __('Template name') }}</div>
        <div class="w-24 px-4">{{ __('For') }}</div>
        <div class="w-24 text-center">{{ __('Enabled') }}</div>
        <div class="w-10"></div>
      </div>

      <ul class="overflow-y-auto px-2 space-y-2 mt-2">
        <template v-for="(template, i) in templatesList" :key="template.name">
          <!-- Mobile Card Layout -->
          <li
            v-if="isMobileView"
            class="flex flex-col gap-3 p-4 bg-surface-menu-bar rounded-lg border border-outline-gray-modals"
            @click="() => emit('updateStep', 'edit-template', { ...template })"
          >
            <div class="flex justify-between items-start gap-2">
              <div class="flex flex-col flex-1 min-w-0">
                <div class="text-base font-medium text-ink-gray-7 truncate">
                  {{ template.name }}
                </div>
                <div class="text-sm text-ink-gray-5 truncate">
                  {{ template.subject }}
                </div>
              </div>
              <Dropdown
                :options="getDropdownOptions(template)"
                placement="bottom-end"
                :button="{
                  icon: 'more-vertical',
                  variant: 'ghost',
                }"
                @click.stop
              />
            </div>
            <div class="flex justify-between items-center gap-2 pt-2 border-t mt-1">
              <Badge
                variant="subtle"
                :label="template.reference_doctype.replace('CRM ', '')"
              />
              <div class="flex items-center gap-2">
                <span class="text-xs text-ink-gray-5">{{ __('Enabled') }}</span>
                <Switch
                  size="sm"
                  v-model="template.enabled"
                  @update:model-value="toggleEmailTemplate(template)"
                  @click.stop
                />
              </div>
            </div>
          </li>

          <!-- Desktop Row Layout -->
          <li
            v-else
            class="flex items-center p-3 cursor-pointer hover:bg-surface-menu-bar rounded transition-colors"
            @click="() => emit('updateStep', 'edit-template', { ...template })"
          >
            <div class="flex flex-col flex-1 min-w-0 pr-5">
              <div class="text-base font-medium text-ink-gray-7 truncate">
                {{ template.name }}
              </div>
              <div class="text-p-base text-ink-gray-5 truncate">
                {{ template.subject }}
              </div>
            </div>
            <div class="w-24 px-4 text-sm text-ink-gray-6 whitespace-nowrap">
              {{ template.reference_doctype.replace('CRM ', '') }}
            </div>
            <div class="w-24 flex justify-center">
              <Switch
                size="sm"
                v-model="template.enabled"
                @update:model-value="toggleEmailTemplate(template)"
                @click.stop
              />
            </div>
            <div class="w-10 flex justify-end">
              <Dropdown
                :options="getDropdownOptions(template)"
                placement="bottom-end"
                :button="{
                  icon: 'more-vertical',
                  variant: 'ghost',
                }"
                @click.stop
              />
            </div>
          </li>
        </template>
        <!-- Load More Button -->
        <div
          v-if="!templates.loading && templates.hasNextPage"
          class="flex justify-center pt-4 pb-2"
        >
          <Button
            class="p-2"
            @click="() => templates.next()"
            :loading="templates.loading"
            :label="__('Load More')"
            icon-left="refresh-cw"
          />
        </div>
      </ul>
    </div>
  </div>
</template>
