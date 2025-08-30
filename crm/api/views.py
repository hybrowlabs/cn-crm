import frappe
from pypika import Criterion


@frappe.whitelist()
def get_views(doctype):
	filters = [
		["user", "in", ["", None, frappe.session.user]]
	]
	if doctype:
		filters.append(["dt", "=", doctype])
	
	views = frappe.get_all(
		"CRM View Settings",
		filters=filters,
		fields="*"
	)
	return views
