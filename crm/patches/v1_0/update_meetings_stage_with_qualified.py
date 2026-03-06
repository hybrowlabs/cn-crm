import frappe


def execute():
	"""Add 'Qualified' status to the Meetings Stage view filter."""
	meetings_view = frappe.db.get_value(
		"CRM View Settings",
		{"label": "Meetings Stage", "dt": "CRM Lead"},
		"name",
	)

	if not meetings_view:
		return

	doc = frappe.get_doc("CRM View Settings", meetings_view)
	new_filters = '{"status": ["in", ["Contacted", "Nurture", "Qualified"]]}'

	if doc.filters != new_filters:
		doc.filters = new_filters
		doc.save()
		frappe.db.commit()
