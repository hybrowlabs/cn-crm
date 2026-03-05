import { toast } from 'frappe-ui'

/**
 * Global error handler for processing server-side errors and messages
 * Handles _server_messages, exceptions, and various error formats from Frappe backend
 */

/**
 * Parse and display server messages from _server_messages field
 * @param {string|Array} serverMessages - Raw server messages from API response
 */
export function handleServerMessages(serverMessages) {
  if (!serverMessages) return

  let messages = []

  try {
    // Handle string format (most common from Frappe)
    if (typeof serverMessages === 'string') {
      // Parse the JSON string to get array
      const parsed = JSON.parse(serverMessages)

      if (Array.isArray(parsed)) {
        messages = parsed
      } else {
        messages = [parsed]
      }
    }
    // Handle direct array format
    else if (Array.isArray(serverMessages)) {
      messages = serverMessages
    }
    // Handle single object
    else {
      messages = [serverMessages]
    }

    // Process each message in the array
    messages.forEach(messageItem => {
      let parsedMessage = messageItem

      // If messageItem is a JSON string (nested JSON), parse it
      if (typeof messageItem === 'string') {
        try {
          parsedMessage = JSON.parse(messageItem)
        } catch {
          // If parsing fails, treat as plain text message
          parsedMessage = { message: messageItem, indicator: 'red' }
        }
      }

      // Ensure we have a message object with message property
      if (parsedMessage && parsedMessage.message) {
        const messageText = parsedMessage.message
        const indicator = parsedMessage.indicator || 'red'
        const title = parsedMessage.title || 'Message'

        // Show toast based on indicator color
        switch (indicator.toLowerCase()) {
          case 'green':
            toast.success(messageText, { title })
            break
          case 'blue':
          case 'info':
            toast.info(messageText, { title })
            break
          case 'orange':
          case 'yellow':
          case 'warning':
            toast.warning(messageText, { title })
            break
          case 'red':
          case 'error':
          default:
            toast.error(messageText, { title })
            break
        }
      } else {
        // Handle cases where message structure is different
        console.warn('Server message without message property:', parsedMessage)

        // Try to extract message from various possible formats
        const fallbackMessage = parsedMessage.msg ||
          parsedMessage.text ||
          parsedMessage.description ||
          JSON.stringify(parsedMessage)

        toast.error(fallbackMessage)
      }
    })
  } catch (error) {
    console.error('Failed to parse server messages:', error, serverMessages)

    // Enhanced fallback: try to extract any readable text
    let fallbackText = serverMessages
    if (typeof serverMessages === 'string') {
      // Try to find any JSON-like message patterns
      const messageMatch = serverMessages.match(/"message":\s*"([^"]+)"/i)
      if (messageMatch) {
        fallbackText = messageMatch[1]
      }
    }

    toast.error(fallbackText.toString(), { title: 'Server Error' })
  }
}

/**
 * Enhanced error handler for API responses
 * Processes exceptions, server messages, and standard error formats
 * @param {Object} error - Error object from API response
 * @param {Object} options - Configuration options
 */
export function handleApiError(error, options = {}) {
  const {
    showToast = true,
    showDialog = false,
    fallbackMessage = 'An error occurred',
    context = 'API Request'
  } = options

  // Handle _server_messages first (highest priority)
  if (error._server_messages) {
    handleServerMessages(error._server_messages)
    return
  }

  // Handle standard Frappe exceptions
  if (error.exception || error.exc_type) {
    const errorMessage = extractExceptionMessage(error)
    const errorType = error.exc_type || 'Error'

    if (showToast) {
      toast.error(errorMessage, { title: errorType })
    }

    if (showDialog) {
      createErrorDialog(errorMessage, errorType, context)
    }
    return
  }

  // Handle messages array (standard format)
  if (error.messages && Array.isArray(error.messages)) {
    const message = error.messages.join('\n')
    if (showToast) {
      toast.error(message)
    }
    return
  }

  // Handle single message
  if (error.message) {
    if (showToast) {
      toast.error(error.message)
    }
    return
  }

  // Fallback for unknown error formats
  if (showToast) {
    toast.error(fallbackMessage)
  }

  // Log unknown error formats for debugging
  console.error('Unknown error format:', error)
}

/**
 * Extract human-readable message from Frappe exception
 * @param {Object} error - Error object with exception details
 * @returns {string} - Formatted error message
 */
function extractExceptionMessage(error) {
  // Try to extract the main error message from exception
  if (error.exception) {
    const exception = error.exception

    // Common Frappe exception patterns
    const errorPatterns = [
      /frappe\.exceptions\.(\w+):\s*(.+)/,
      /(\w+Error):\s*(.+)/,
      /(.+)$/
    ]

    for (const pattern of errorPatterns) {
      const match = exception.match(pattern)
      if (match) {
        // Return the message part (last capture group)
        return match[match.length - 1].trim()
      }
    }
  }

  // Fallback to exc_type or generic message
  return error.exc_type || error.message || 'An unexpected error occurred'
}

/**
 * Create an error dialog for serious errors that need more attention
 * @param {string} message - Error message
 * @param {string} title - Error title/type
 * @param {string} context - Context where error occurred
 */
function createErrorDialog(message, title, context) {
  // Import createDialog dynamically to avoid circular imports
  import('./dialogs.jsx').then(({ createDialog }) => {
    createDialog({
      title: title || 'Error',
      message: message,
      actions: [
        {
          label: 'OK',
          variant: 'solid',
          theme: 'red',
          onClick: (dialog) => {
            dialog.show = false
          }
        }
      ]
    })
  }).catch(err => {
    // Fallback if dialog import fails
    console.error('Failed to create error dialog:', err)
    toast.error(message, { title: title || 'Error' })
  })
}

/**
 * Global request interceptor to automatically handle errors
 * Should be called in main.js or app initialization
 */
export function setupGlobalErrorHandler() {
  // Suppress unhandled promise rejections — show toast instead of Vite overlay
  window.addEventListener('unhandledrejection', (event) => {
    event.preventDefault() // prevents Vite overlay from activating
    const reason = event.reason
    const message =
      (reason && (reason.message || reason.toString())) ||
      'An unexpected error occurred'
    // Suppress noisy non-actionable errors
    if (
      message.includes('AbortError') ||
      message.includes('NetworkError') ||
      message.includes('Failed to fetch') ||
      message.includes('ValidationError') ||   // Frappe server-side validation (handled by API layer)
      message.includes('OperationalError') ||    // Database/Backend operational errors (often non-actionable)
      message.includes('Invalid namespace') ||  // Socket.io namespace errors
      message.includes('No dashboard found') || // Dashboard missing — handled by empty state UI
      message.includes('Dashboard not found')
    ) {
      console.warn('Suppressed non-actionable error:', message)
      return
    }
    console.error('Unhandled promise rejection:', reason)
    toast.error(message, { title: 'Error' })
  })

  // Suppress uncaught JS errors — show toast instead of Vite overlay
  window.addEventListener('error', (event) => {
    // Only intercept script errors (not resource load errors like missing images/scripts)
    if (event.message) {
      event.preventDefault()
      const msg = event.message
      // Suppress Frappe boot-phase errors (sync.js, desk.js boot sequence)
      // These occur when a Frappe desk widget triggers boot on a page without full boot context
      if (
        msg.includes("Cannot read properties of undefined (reading 'docs')") ||
        msg.includes('load_bootinfo') ||
        msg.includes('sync.js')
      ) {
        console.warn('Suppressed Frappe boot error (non-actionable):', msg)
        return
      }
      console.error('Uncaught error:', event.error || msg)
      toast.error(msg, { title: 'Application Error' })
    }
  })

  // Intercept frappe-ui resource errors
  if (window.frappe && window.frappe.request) {
    const originalRequest = window.frappe.request

    window.frappe.request = function (options) {
      const originalError = options.error

      options.error = function (xhr, status, error) {
        try {
          const response = JSON.parse(xhr.responseText)
          handleApiError(response, {
            showToast: true,
            context: options.url || 'API Request'
          })
        } catch {
          // Fallback for non-JSON responses
          toast.error(error || 'Network error occurred')
        }

        // Call original error handler if provided
        if (originalError) {
          originalError(xhr, status, error)
        }
      }

      return originalRequest.call(this, options)
    }
  }
}

/**
 * Utility function to handle errors in createResource onError callbacks
 * Use this in your Vue components for consistent error handling
 * @param {Object} error - Error from createResource
 * @param {string} context - Optional context for the error
 */
export function handleResourceError(error, context = '') {
  handleApiError(error, {
    showToast: true,
    context: context,
    fallbackMessage: `Failed to ${context.toLowerCase()}`
  })
}

/**
 * Enhanced createResource wrapper with automatic error handling
 * Use this to automatically handle _server_messages and other server errors
 * @param {Object} options - createResource options
 * @param {string} context - Context for error messages
 * @returns {Function} - Function that creates resource with error handling
 */
export function createResourceWithErrorHandling(options, context = '') {
  return (createResource) => {
    const originalOnError = options.onError

    // Wrap the onError callback
    options.onError = (error) => {
      // Always use our enhanced error handler
      handleResourceError(error, context)

      // Call original onError if provided (for component-specific handling)
      if (originalOnError) {
        originalOnError(error)
      }
    }

    return createResource(options)
  }
}

/**
 * Enhanced error boundaries for Vue components
 * @param {Object} error - Vue error object
 * @param {Object} instance - Vue component instance
 * @param {string} info - Error info
 */
export function handleVueError(error, instance, info) {
  console.error('Vue Error:', error, info)

  // Show user-friendly error message
  toast.error('An unexpected error occurred in the application', {
    title: 'Application Error'
  })

  // Could integrate with error reporting service here
  // e.g., Sentry, LogRocket, etc.
}

/**
 * Patches frappe desk globals to prevent "Page crm not found" DOM injection.
 *
 * When the CRM Vue app navigates (e.g. back from a report), Frappe desk JS can
 * fire frappe.msgprint / frappe.show_alert with a "Page ... not found" message,
 * which injects an HTML element into document.body and shifts the UI upward.
 *
 * Call this AFTER frappe globals are available (i.e. after boot in main.js).
 */
export function patchFrappeDesk() {
  // Retry with a short delay to ensure frappe globals are initialised
  const _patch = () => {
    if (!window.frappe) return

    // ── Intercept frappe.msgprint ──────────────────────────────────────────
    const _originalMsgprint = window.frappe.msgprint
    window.frappe.msgprint = function (message, title) {
      const text = (typeof message === 'string' ? message : message?.message || '') +
        (title || '')
      // Block "page not found" messages — they are useless inside the Vue SPA
      if (
        /page.*not found/i.test(text) ||
        /not found.*page/i.test(text) ||
        /resource.*not available/i.test(text)
      ) {
        console.warn('[CRM] Suppressed frappe.msgprint (page-not-found):', text)
        return
      }
      return _originalMsgprint && _originalMsgprint.apply(this, arguments)
    }

    // ── Intercept frappe.show_alert ────────────────────────────────────────
    const _originalShowAlert = window.frappe.show_alert
    window.frappe.show_alert = function (message) {
      const text = typeof message === 'string' ? message : (message?.message || '')
      if (/page.*not found/i.test(text) || /not found.*page/i.test(text)) {
        console.warn('[CRM] Suppressed frappe.show_alert (page-not-found):', text)
        return
      }
      return _originalShowAlert && _originalShowAlert.apply(this, arguments)
    }

    // ── Intercept frappe.set_route to prevent desk navigation from firing ──
    // When going back from a report, Frappe desk may call set_route('crm')
    // which fails because 'crm' is not a valid desk page.
    const _originalSetRoute = window.frappe.set_route
    window.frappe.set_route = function (...args) {
      const routeArg = args[0]
      // If the dest looks like our Vue app root, just silently ignore
      if (routeArg === 'crm' || routeArg === '/crm') {
        console.warn('[CRM] Suppressed frappe.set_route("crm") — handled by Vue router')
        return Promise.resolve()
      }
      return _originalSetRoute && _originalSetRoute.apply(this, args)
    }

    // ── Remove any already-injected "page not found" DOM nodes ─────────────
    const removePageNotFoundNodes = () => {
      document.querySelectorAll('.msgprint-dialog, .page-container').forEach((el) => {
        if (el.textContent && /page.*not found/i.test(el.textContent)) {
          el.remove()
          console.warn('[CRM] Removed stale page-not-found DOM node')
        }
      })
    }
    removePageNotFoundNodes()

    console.log('[CRM] frappe desk patched (msgprint / set_route intercepted)')
  }

  // Run immediately and also after a short delay for late init
  _patch()
  setTimeout(_patch, 500)
  setTimeout(_patch, 2000)
}