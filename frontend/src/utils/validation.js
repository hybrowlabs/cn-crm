import { getMeta } from '@/stores/meta'

export const MANDATORY_FIELDS_BY_STATUS = {
    'CRM Lead': {
        Contacted: ['meeting_type', 'product_discussed', 'volume_rangekg', 'primary_pain_category', 'pain_description', 'customer_role_type', 'current_supplier', 'decision_process', 'next_action_date'],
        Nurture: ['meeting_type', 'product_discussed', 'volume_rangekg', 'primary_pain_category', 'pain_description', 'customer_role_type', 'current_supplier', 'decision_process', 'next_action_date'],
    },
    'CRM Deal': {
        'Demo/Making': ['trial_product', 'trial_volume_kg', 'trial_start_date', 'trial_end_date', 'trial_success_criteria'],
        // 'Proposal/Quotation': ['final_volume_kg', 'final_price__kg', 'approval_authority', 'commercial_acceptance', 'paper_process_status', 'proposal_acknowledged'],
        // 'Negotiation': ['final_volume_kg', 'final_price__kg', 'approval_authority', 'commercial_acceptance', 'paper_process_status', 'proposal_acknowledged'],
        'Won': ['order_date', 'final_volume_kg', 'final_price__kg', 'product_type'],
    }
}

export function getFieldsForValidation(doctype, status) {
    const meta = getMeta(doctype)
    const allFields = meta.getFields()
    if (!allFields || !allFields.length) return []

    const mandatoryFieldnames = MANDATORY_FIELDS_BY_STATUS[doctype]?.[status] || []

    if (!mandatoryFieldnames.length) return []

    return mandatoryFieldnames
        .map((fieldname) => {
            const field = allFields.find((f) => f.fieldname === fieldname)
            if (field) {
                return {
                    ...field,
                    visible: true,
                    read_only: 0,
                    hidden: 0,
                    reqd: 1,
                }
            }
            return null
        })
        .filter(Boolean)
}
