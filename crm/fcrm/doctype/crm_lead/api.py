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

@frappe.whitelist()
def get_meeting_data_sections(doctype):
	if not frappe.db.exists("CRM Fields Layout", {"dt": doctype, "type": "Side Data Bar"}):
		return []
	layout = frappe.get_doc("CRM Fields Layout", {"dt": doctype, "type": "Side Data Bar"}).layout

	if not layout:
		return []

	import json
	from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_field_obj, handle_perm_level_restrictions

	layout = json.loads(layout)

	not_allowed_fieldtypes = [
		"Tab Break",
		"Section Break",
		"Column Break",
	]

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in not_allowed_fieldtypes]

	for section in layout:
		section["name"] = section.get("name") or section.get("label")
		for column in section.get("columns") if section.get("columns") else []:
			for field in column.get("fields") if column.get("fields") else []:
				field_obj = next((f for f in fields if f.fieldname == field), None)
				if field_obj:
					field_obj = field_obj.as_dict()
					handle_perm_level_restrictions(field_obj, doctype)
					column["fields"][column.get("fields").index(field)] = get_field_obj(field_obj)

	return layout
