<template>
  <div v-if="isDev" class="fixed bottom-4 right-4 z-50 bg-red-50 border border-red-200 rounded-lg p-4 shadow-lg">
    <h4 class="text-sm font-semibold text-red-800 mb-2">🧪 Error Handler Test</h4>
    <div class="space-y-2">
      <Button
        size="sm"
        variant="outline"
        theme="red"
        @click="testEmailError"
      >
        Test Email Error
      </Button>
      <Button
        size="sm"
        variant="outline"
        theme="orange"
        @click="testServerMessages"
      >
        Test Server Messages
      </Button>
      <Button
        size="sm"
        variant="outline"
        theme="purple"
        @click="testArrayParsing"
      >
        Test Array Parsing
      </Button>
      <Button
        size="sm"
        variant="outline"
        theme="blue"
        @click="testExceptions"
      >
        Test Exceptions
      </Button>
      <Button
        size="sm"
        variant="outline"
        theme="green"
        @click="runAllTests"
      >
        Run All Tests
      </Button>
    </div>
    <Button
      size="sm"
      variant="ghost"
      class="mt-2 w-full text-xs"
      @click="hide"
    >
      Hide Tester
    </Button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  testEmailConfigError,
  testServerMessageFormats,
  testExceptionTypes,
  testServerMessagesArrayParsing,
  runAllErrorTests
} from '@/utils/errorTestUtils'

const isDev = ref(false)

onMounted(() => {
  // Only show in development mode
  isDev.value = import.meta.env.DEV
})

function testEmailError() {
  testEmailConfigError()
}

function testServerMessages() {
  testServerMessageFormats()
}

function testArrayParsing() {
  testServerMessagesArrayParsing()
}

function testExceptions() {
  testExceptionTypes()
}

function runAllTests() {
  runAllErrorTests()
}

function hide() {
  isDev.value = false
}
</script>