import { handleApiError, handleServerMessages } from './errorHandler'

/**
 * Test utilities for validating error handling functionality
 * These functions can be used to simulate various error scenarios
 */

/**
 * Simulate the specific error scenario provided by the user
 * This tests _server_messages handling for email configuration errors
 */
export function testEmailConfigError() {
  const mockError = {
    "exception": "frappe.exceptions.OutgoingEmailError: Unable to send mail because of a missing email account. Please setup default Email Account from Settings > Email Account",
    "exc_type": "OutgoingEmailError", 
    "exc": "[\"Traceback (most recent call last):\\n  File \\\"apps/frappe/frappe/app.py\\\", line 115, in application\\n    response = frappe.api.handle(request)\\n  File \\\"apps/frappe/frappe/api/__init__.py\\\", line 49, in handle\\n    data = endpoint(**arguments)\\n  File \\\"apps/frappe/frappe/api/v1.py\\\", line 36, in handle_rpc_call\\n    return frappe.handler.handle()\\n  File \\\"apps/frappe/frappe/handler.py\\\", line 51, in handle\\n    data = execute_cmd(cmd)\\n  File \\\"apps/frappe/frappe/handler.py\\\", line 84, in execute_cmd\\n    return frappe.call(method, **frappe.form_dict)\\n  File \\\"apps/frappe/frappe/__init__.py\\\", line 1742, in call\\n    return fn(*args, **newargs)\\n  File \\\"apps/frappe/frappe/utils/typing_validations.py\\\", line 31, in wrapper\\n    return func(*args, **kwargs)\\n  File \\\"apps/frappe/frappe/core/doctype/communication/email.py\\\", line 84, in make\\n    return _make(\\n  File \\\"apps/frappe/frappe/core/doctype/communication/email.py\\\", line 178, in _make\\n    frappe.throw(\\n  File \\\"apps/frappe/frappe/__init__.py\\\", line 609, in throw\\n    msgprint(\\n  File \\\"apps/frappe/frappe/__init__.py\\\", line 574, in msgprint\\n    _raise_exception()\\n  File \\\"apps/frappe/frappe/__init__.py\\\", line 525, in _raise_exception\\n    raise exc\\nfrappe.exceptions.OutgoingEmailError: Unable to send mail because of a missing email account. Please setup default Email Account from Settings > Email Account\\n\"]",
    "_server_messages": "[\"{\\\"message\\\": \\\"Unable to send mail because of a missing email account. Please setup default Email Account from Settings > Email Account\\\", \\\"title\\\": \\\"Message\\\", \\\"indicator\\\": \\\"red\\\", \\\"raise_exception\\\": 1, \\\"__frappe_exc_id\\\": \\\"67fffd15aaaa220e6c27f19457f02c8f7d24cd037d542557596d0f9f\\\"}\"]"
  }

  console.log('🧪 Testing Email Configuration Error...')
  console.log('Raw _server_messages:', mockError._server_messages)
  
  // This should show a red toast with title "Message" and the email configuration error message
  handleApiError(mockError, { context: 'Email Configuration Test' })
}

/**
 * Test various server message formats
 */
export function testServerMessageFormats() {
  console.log('🧪 Testing Different Server Message Formats...')

  // Test 1: Direct array format (how Frappe usually sends _server_messages)
  const frappeFormat = '["{\\"message\\": \\"Document saved successfully\\", \\"title\\": \\"Success\\", \\"indicator\\": \\"green\\"}"]'
  console.log('Testing Frappe format (_server_messages):', frappeFormat)
  handleServerMessages(frappeFormat)

  setTimeout(() => {
    // Test 2: Multiple messages in Frappe format
    const multipleFrappeFormat = '["{\\"message\\": \\"First validation error\\", \\"title\\": \\"Validation Error\\", \\"indicator\\": \\"red\\"}", "{\\"message\\": \\"Second validation warning\\", \\"title\\": \\"Warning\\", \\"indicator\\": \\"yellow\\"}"]'
    console.log('Testing multiple Frappe format messages:', multipleFrappeFormat)
    handleServerMessages(multipleFrappeFormat)
  }, 2000)

  setTimeout(() => {
    // Test 3: Direct array of objects (alternative format)
    const directArrayFormat = [
      {
        message: "This action may affect other documents",
        title: "Warning", 
        indicator: "orange"
      }
    ]
    console.log('Testing direct array format:', directArrayFormat)
    handleServerMessages(directArrayFormat)
  }, 4000)

  setTimeout(() => {
    // Test 4: Info message in Frappe format
    const infoFrappeFormat = '["{\\"message\\": \\"Please review the changes before proceeding\\", \\"title\\": \\"Information\\", \\"indicator\\": \\"blue\\"}"]'
    console.log('Testing info message in Frappe format:', infoFrappeFormat)
    handleServerMessages(infoFrappeFormat)
  }, 6000)

  setTimeout(() => {
    // Test 5: Message without title (should default to "Message")
    const noTitleFormat = '["{\\"message\\": \\"This is a message without title\\", \\"indicator\\": \\"red\\"}"]'
    console.log('Testing message without title:', noTitleFormat)
    handleServerMessages(noTitleFormat)
  }, 8000)
}

/**
 * Test different exception types
 */
export function testExceptionTypes() {
  console.log('🧪 Testing Different Exception Types...')

  // Test 1: Permission Error
  setTimeout(() => {
    const permissionError = {
      exception: "frappe.exceptions.PermissionError: You do not have permission to access this document",
      exc_type: "PermissionError"
    }
    handleApiError(permissionError, { context: 'Permission Test' })
  }, 1000)

  // Test 2: Validation Error
  setTimeout(() => {
    const validationError = {
      exception: "frappe.exceptions.ValidationError: Email field is required",
      exc_type: "ValidationError"
    }
    handleApiError(validationError, { context: 'Validation Test' })
  }, 2500)

  // Test 3: Duplicate Error
  setTimeout(() => {
    const duplicateError = {
      exception: "frappe.exceptions.DuplicateEntryError: Document with this name already exists",
      exc_type: "DuplicateEntryError"
    }
    handleApiError(duplicateError, { context: 'Duplicate Test' })
  }, 4000)
}

/**
 * Test legacy error formats (messages array)
 */
export function testLegacyErrorFormats() {
  console.log('🧪 Testing Legacy Error Formats...')

  // Test 1: Messages array
  const messagesError = {
    messages: [
      "Field 'Customer Name' is mandatory",
      "Email format is invalid", 
      "Phone number must be 10 digits"
    ]
  }
  handleApiError(messagesError, { context: 'Legacy Messages Test' })

  setTimeout(() => {
    // Test 2: Single message
    const singleMessageError = {
      message: "Network connection failed"
    }
    handleApiError(singleMessageError, { context: 'Single Message Test' })
  }, 2000)
}

/**
 * Test error handling with dialog option
 */
export function testErrorDialog() {
  console.log('🧪 Testing Error Dialog...')
  
  const criticalError = {
    exception: "frappe.exceptions.CriticalError: System configuration is invalid",
    exc_type: "CriticalError"
  }
  
  handleApiError(criticalError, { 
    context: 'Critical System Error',
    showDialog: true,
    showToast: true
  })
}

/**
 * Test specifically _server_messages array parsing
 */
export function testServerMessagesArrayParsing() {
  console.log('🧪 Testing _server_messages Array Parsing...')

  // Test the exact format from your example
  const exactFormat = "[\"{\\\"message\\\": \\\"Unable to send mail because of a missing email account. Please setup default Email Account from Settings > Email Account\\\", \\\"title\\\": \\\"Message\\\", \\\"indicator\\\": \\\"red\\\", \\\"raise_exception\\\": 1, \\\"__frappe_exc_id\\\": \\\"67fffd15aaaa220e6c27f19457f02c8f7d24cd037d542557596d0f9f\\\"}\"]"
  
  console.log('🎯 Testing exact user-provided format:')
  console.log('Raw input:', exactFormat)
  
  // Parse step by step for debugging
  try {
    const step1 = JSON.parse(exactFormat) // Should get array of JSON strings
    console.log('Step 1 - Parsed array:', step1)
    
    const step2 = step1.map(item => JSON.parse(item)) // Parse each JSON string
    console.log('Step 2 - Parsed messages:', step2)
    
    step2.forEach((msg, index) => {
      console.log(`Message ${index + 1}:`, {
        message: msg.message,
        title: msg.title,
        indicator: msg.indicator
      })
    })
  } catch (error) {
    console.error('Manual parsing error:', error)
  }
  
  // Now test with our handler
  console.log('🧪 Testing with handleServerMessages...')
  handleServerMessages(exactFormat)

  setTimeout(() => {
    // Test with multiple server messages
    const multipleServerMessages = "[\"{\\\"message\\\": \\\"First error message\\\\nWith line break\\\", \\\"title\\\": \\\"Error 1\\\", \\\"indicator\\\": \\\"red\\\"}\", \"{\\\"message\\\": \\\"Second warning message\\\", \\\"title\\\": \\\"Warning\\\", \\\"indicator\\\": \\\"orange\\\"}\"]"
    
    console.log('🎯 Testing multiple server messages:')
    console.log('Raw input:', multipleServerMessages)
    handleServerMessages(multipleServerMessages)
  }, 3000)
}

/**
 * Comprehensive test suite - runs all tests in sequence
 */
export function runAllErrorTests() {
  console.log('🚀 Starting Comprehensive Error Handling Tests...')
  
  testEmailConfigError()
  
  setTimeout(() => testServerMessagesArrayParsing(), 3000)
  setTimeout(() => testServerMessageFormats(), 8000)
  setTimeout(() => testExceptionTypes(), 16000)
  setTimeout(() => testLegacyErrorFormats(), 22000)
  setTimeout(() => testErrorDialog(), 26000)
  
  setTimeout(() => {
    console.log('✅ All Error Handling Tests Completed!')
  }, 30000)
}

// Export for browser console testing
if (typeof window !== 'undefined') {
  window.errorTests = {
    testEmailConfigError,
    testServerMessageFormats,
    testExceptionTypes,
    testLegacyErrorFormats,
    testErrorDialog,
    testServerMessagesArrayParsing,
    runAllErrorTests
  }
}