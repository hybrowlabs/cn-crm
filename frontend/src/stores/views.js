import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

export const viewsStore = defineStore('crm-views', (doctype) => {
  let viewsByName = reactive({})
  let pinnedViews = ref([])
  let publicViews = ref([])
  let standardViews = ref({})
  // Track default views per doctype
  const defaultViews = ref({})
  // Keep a reference to the first default view found (for global/home context)
  const firstDefaultView = ref(null)

  // Views
  const views = createResource({
    url: 'crm.api.views.get_views',
    params: { doctype: doctype || '' },
    cache: 'crm-views',
    initialData: [],
    auto: true,
    transform(views) {
      pinnedViews.value = []
      publicViews.value = []
      defaultViews.value = {}
      firstDefaultView.value = null
      for (let view of views) {
        viewsByName[view.name] = view
        view.type = view.type || 'list'
        if (view.pinned) {
          pinnedViews.value?.push(view)
        }
        if (view.public) {
          publicViews.value?.push(view)
        }
        if (view.is_standard && view.dt) {
          standardViews.value[view.dt + ' ' + view.type] = view
        }
        if (view.is_default && view.dt) {
          // Track default per doctype
          defaultViews.value[view.dt] = view
          // Keep the first default found for global context
          if (!firstDefaultView.value) {
            firstDefaultView.value = view
          }
        }
      }
      return views
    },
  })

  function getDefaultView(dt = null) {
    // If doctype specified, return default for that doctype
    if (dt) {
      return defaultViews.value[dt] || null
    }
    // Otherwise return the first default view (for global/home context)
    return firstDefaultView.value
  }

  function getView(view, type, doctype = null) {
    type = type || 'list'
    if (!view && doctype) {
      return standardViews.value[doctype + ' ' + type] || null
    }
    return viewsByName[view]
  }

  function getPinnedViews() {
    if (!pinnedViews.value?.length) return []
    return pinnedViews.value
  }

  function getPublicViews() {
    if (!publicViews.value?.length) return []
    return publicViews.value
  }

  async function reload() {
    await views.reload()
  }

  return {
    views,
    defaultViews,
    standardViews,
    getDefaultView,
    getPinnedViews,
    getPublicViews,
    reload,
    getView,
  }
})
