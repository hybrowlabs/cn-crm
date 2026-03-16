import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { capture } from '@/telemetry'
import { parseColor } from '@/utils'
import { defineStore } from 'pinia'
import { createListResource } from 'frappe-ui'
import { reactive, h } from 'vue'

export const statusesStore = defineStore('crm-statuses', () => {
  let leadStatusesByName = reactive({})
  let dealStatusesByName = reactive({})
  let communicationStatusesByName = reactive({})

  const leadStatuses = createListResource({
    doctype: 'CRM Lead Status',
    fields: ['name', 'color', 'position'],
    orderBy: 'position asc',
    cache: 'lead-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        status.color = parseColor(status.color)
        leadStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  const dealStatuses = createListResource({
    doctype: 'CRM Deal Status',
    fields: ['name', 'color', 'position'],
    orderBy: 'position asc',
    cache: 'deal-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        status.color = parseColor(status.color)
        dealStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  const communicationStatuses = createListResource({
    doctype: 'CRM Communication Status',
    fields: ['name'],
    cache: 'communication-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        communicationStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  function getLeadStatus(name) {
    if (!name) {
      name = leadStatuses.data?.[0]?.name
    }
    return leadStatusesByName[name] || { name: name || '', color: 'text-ink-gray-5' }
  }

  function getDealStatus(name) {
    if (!name) {
      name = dealStatuses.data?.[0]?.name
    }
    return dealStatusesByName[name] || { name: name || '', color: 'text-ink-gray-5' }
  }

  function getCommunicationStatus(name) {
    if (!name) {
      name = communicationStatuses.data?.[0]?.name
    }
    return communicationStatusesByName[name] || { name: name || '', color: 'text-ink-gray-5' }
  }

  function statusOptions(
    doctype,
    statuses = [],
    triggerStatusChange = null,
    currentStatus = null,
    visibilityMap = null,
    doc = null,
  ) {
    const defaultVisibilityMaps = {
      deal: {
        'Unqualified': [
          'Unqualified',
          'Meeting',
          'Lost',
        ],
        'Meeting': [
          'Meeting',
          'Qualified',
          'Lost'
        ],
        'Qualified': [
          'Qualified',
          'Trial',
          'Lost',
        ],
        'Trial': [
          'Trial',
          'Proposal/Quotation',
          'Lost',
        ],
        'Proposal/Quotation': [
          'Proposal/Quotation',
          'Won',
          'Lost',
        ],
      },
      lead: {},
    }

    if (!visibilityMap && defaultVisibilityMaps[doctype]) {
      visibilityMap = defaultVisibilityMaps[doctype]
    }

    let statusesByName =
      doctype == 'deal' ? dealStatusesByName : leadStatusesByName

    if (statuses?.length) {
      statusesByName = statuses.reduce((acc, status) => {
        acc[status] = statusesByName[status]
        return acc
      }, {})
    }

    if (currentStatus && visibilityMap?.[currentStatus]) {
      let allowedStatuses = [...visibilityMap[currentStatus]]

      if (
        doctype === 'deal' &&
        currentStatus !== 'Unqualified'
      ) {
        allowedStatuses = allowedStatuses.filter(
          (s) => s !== 'Unqualified',
        )
      }

      if (
        doctype === 'deal' &&
        currentStatus === 'Trial' &&
        doc?.trial_outcome !== 'Qualified'
      ) {
        allowedStatuses = allowedStatuses.filter(
          (s) => !['Proposal/Quotation'].includes(s),
        )
      }

      statusesByName = Object.keys(statusesByName).reduce((acc, status) => {
        if (allowedStatuses.includes(status)) {
          acc[status] = statusesByName[status]
        }
        return acc
      }, {})
    }

    let options = []
    for (const status in statusesByName) {
      options.push({
        label: statusesByName[status]?.name,
        value: statusesByName[status]?.name,
        icon: () => h(IndicatorIcon, { class: statusesByName[status]?.color }),
        onClick: async () => {
          await triggerStatusChange?.(statusesByName[status]?.name)
          capture('status_changed', { doctype, status })
        },
      })
    }
    return options
  }

  return {
    leadStatuses,
    dealStatuses,
    communicationStatuses,
    getLeadStatus,
    getDealStatus,
    getCommunicationStatus,
    statusOptions,
  }
})
