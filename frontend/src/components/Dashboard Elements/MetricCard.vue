<template>
  <div class="bg-white rounded-lg border shadow-sm p-4 hover:shadow-md transition-shadow">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-sm text-gray-600 mb-1">{{ title }}</p>
        <p class="text-2xl font-bold text-gray-900">
          <CountUp 
            :end-val="value" 
            :decimals="decimals"
            :prefix="prefix"
            :suffix="suffix"
          />
        </p>
        <p class="text-xs text-gray-500 mt-1">{{ subtitle }}</p>
      </div>
      <div :class="iconBgClass">
        <component :is="icon" :class="iconClass" />
      </div>
    </div>
    <div class="mt-3 flex items-center text-sm">
      <span :class="growth >= 0 ? 'text-green-600' : 'text-red-600'">
        {{ growth >= 0 ? '+' : '' }}{{ growth }}%
      </span>
      <span class="text-gray-500 ml-1">vs last period</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import CountUp from './CountUp.vue'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: Number, required: true },
  subtitle: { type: String, required: true },
  growth: { type: Number, required: true },
  icon: { type: Object, required: true },
  iconBgColor: { type: String, default: 'bg-blue-100' },
  iconColor: { type: String, default: 'text-blue-600' },
  decimals: { type: Number, default: 0 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' }
})

const iconBgClass = computed(() => `p-3 rounded-full ${props.iconBgColor}`)
const iconClass = computed(() => `w-6 h-6 ${props.iconColor}`)
</script>