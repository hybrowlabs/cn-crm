<template>
  <span>{{ displayValue }}</span>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const props = defineProps({
  endVal: { type: Number, required: true },
  duration: { type: Number, default: 1500 },
  decimals: { type: Number, default: 0 },
  format: { type: Boolean, default: false },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' }
})

const current = ref(0)
const isAnimating = ref(false)

const displayValue = computed(() => {
  let value = current.value
  
  if (props.decimals > 0) {
    value = value.toFixed(props.decimals)
  } else {
    value = Math.round(value)
  }
  
  if (props.format) {
    value = Number(value).toLocaleString()
  }
  
  return `${props.prefix}${value}${props.suffix}`
})

const startAnimation = () => {
  if (isAnimating.value) return
  
  isAnimating.value = true
  const startTime = performance.now()
  const startValue = current.value
  const targetValue = props.endVal || 0

  const animate = (currentTime) => {
    if (!isAnimating.value) return

    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / props.duration, 1)
    const easeProgress = 1 - Math.pow(1 - progress, 3)

    current.value = startValue + (targetValue - startValue) * easeProgress

    if (progress < 1) {
      requestAnimationFrame(animate)
    } else {
      isAnimating.value = false
      current.value = targetValue
    }
  }

  requestAnimationFrame(animate)
}

watch(() => props.endVal, () => {
  startAnimation()
}, { immediate: true })

onMounted(() => {
  startAnimation()
})
</script>