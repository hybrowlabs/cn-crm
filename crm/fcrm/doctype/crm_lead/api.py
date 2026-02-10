import frappe

from crm.api.doc import get_assigned_users, get_fields_meta
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_lead(name):
	lead = frappe.get_doc("CRM Lead", name)
	lead.check_permission("read")

	lead = lead.as_dict()

	lead["fields_meta"] = get_fields_meta("CRM Lead")
	lead["_form_script"] = get_form_script("CRM Lead")
	lead["linked_visits"] = get_lead_visits(name)
	return lead

@frappe.whitelist()
def get_lead_visits(name):
	"""
	Get linked site visits for a lead.
	"""
	if not name:
		return []

	visits = frappe.get_all(
		"CRM Site Visit",
		filters={
			"reference_type": "CRM Lead",
			"reference_name": name
		},
		fields=[
			"name",
			"visit_date",
			"visit_type", 
			"status",
			"priority",
			"sales_person",
			"visit_purpose",
			"visit_summary",
			"planned_start_time",
			"planned_end_time",
			"check_in_time",
			"check_out_time",
			"total_duration",
			"lead_quality",
			"feedback",
			"next_steps",
			"follow_up_required",
			"follow_up_date",
			"potential_value",
			"probability_percentage"
		],
		order_by="visit_date desc"
	)

	return visits
