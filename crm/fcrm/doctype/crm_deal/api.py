import frappe

from crm.api.doc import get_assigned_users, get_fields_meta
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script


@frappe.whitelist()
def get_deal(name):
	deal = frappe.get_doc("CRM Deal", name)
	deal.check_permission("read")

	deal = deal.as_dict()

	deal["fields_meta"] = get_fields_meta("CRM Deal")
	deal["_form_script"] = get_form_script("CRM Deal")
	return deal

@frappe.whitelist()
def get_deal_contacts(name):
	contacts = frappe.get_all(
		"CRM Contacts",
		filters={"parenttype": "CRM Deal", "parent": name},
		fields=["contact", "is_primary"],
		distinct=True,
	)
	deal_contacts = []
	for contact in contacts:
		if not contact.contact:
			continue

		is_primary = contact.is_primary
		contact = frappe.get_doc("Contact", contact.contact).as_dict()

		def get_primary_email(contact):
			for email in contact.email_ids:
				if email.is_primary:
					return email.email_id
			return contact.email_ids[0].email_id if contact.email_ids else ""

		def get_primary_mobile_no(contact):
			for phone in contact.phone_nos:
				if phone.is_primary:
					return phone.phone
			return contact.phone_nos[0].phone if contact.phone_nos else ""

		_contact = {
			"name": contact.name,
			"image": contact.image,
			"full_name": contact.full_name,
			"email": get_primary_email(contact),
			"mobile_no": get_primary_mobile_no(contact),
			"is_primary": is_primary,
		}
		deal_contacts.append(_contact)
	return deal_contacts

@frappe.whitelist()
def get_linked_quotations(args):
	"""
	Get linked quotations for a deal.
	"""
	if not args.get("dealId"):
		return []

	quotations = frappe.get_all(
		"Quotation",
		filters={
      "quotation_to": "CRM Deal",
      "crm_deal": args.get("dealId")
      },
		fields=["*"],
	)

	# for quotation in quotations:
	# 	quotation["quotation_to"] = frappe.bold(quotation["quotation_to"])
	# 	quotation["customer"] = frappe.bold(quotation["customer"])

	return quotations

@frappe.whitelist()
def get_deal_visits(name):
	"""
	Get linked site visits for a deal.
	"""
	if not name:
		return []

	visits = frappe.get_all(
		"CRM Site Visit",
		filters={
			"reference_type": "CRM Deal",
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
def send_trial_request(name):
	"""
	Sets is_approved_by_tech_team to 1 for the specified deal,
	creates a Technical Team Request, and auto-assigns it.
	"""
	deal = frappe.get_doc("CRM Deal", name)
	deal.check_permission("write")

	# Create Technical Team Request
	ttr = frappe.get_doc({
		"doctype": "Technical Team Request",
		"deal": deal.name,
		"product_category": deal.product_alloy_type,
		"commercial_pain_category": deal.primary_pain_category,
		"technical_pain_category": deal.technical_pain_category,
		"notes_by_sales_team": deal.notes,
	})
	ttr.insert(ignore_permissions=True)

	# Assignment Logic
	assignee = None
	if deal.territory:
		territory = frappe.get_doc("Territory", deal.territory)

		# Filter technical team map for matching product category
		tech_team_entries = [
			entry for entry in (territory.custom_technical_team_map or [])
			if entry.product_category == deal.product_alloy_type
		]

		if len(tech_team_entries) == 1:
			assignee = tech_team_entries[0].technical_team_name
		else:
			# If more than one or none, fall back to technical manager
			assignee = territory.custom_technical_manager

	if assignee:
		# Get User ID from Sales Person via Employee link
		from frappe.desk.form.assign_to import add
		
		# Sales Person -> Employee -> User ID
		employee = frappe.db.get_value("Sales Person", assignee, "employee")
		user_id = None
		if employee:
			user_id = frappe.db.get_value("Employee", employee, "user_id")
		
		# If not found via employee, try direct check if Sales Person has user_id (not standard but possible)
		if not user_id:
			try:
				user_id = frappe.db.get_value("Sales Person", assignee, "user_id")
			except Exception:
				user_id = None

		if user_id:
			add({
				"assign_to": [user_id],
				"doctype": "Technical Team Request",
				"name": ttr.name,
				"description": f"Technical Team Request for Deal {deal.name}",
			})

	deal.is_approved_by_tech_team = 1
	deal.save()
	return True

