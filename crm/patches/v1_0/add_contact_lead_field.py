import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	"""
	Ensure Contact has the `lead` Link field to CRM Lead.

	This patch is idempotent and will:
	- Create the custom field if it doesn't exist.
	- If the field exists but the DB column is missing, add the column.
	"""
	doctype = "Contact"
	fieldname = "lead"

	# If column already exists, nothing to do.
	if frappe.db.has_column(doctype, fieldname):
		return

	# Create the custom field if it's not defined.
	if not frappe.get_meta(doctype).has_field(fieldname):
		create_custom_fields(
			{
				doctype: [
					{
						"fieldname": fieldname,
						"fieldtype": "Link",
						"label": "Lead",
						"options": "CRM Lead",
						"reqd": 1,
						"insert_after": "company_name",
					},
				]
			}
		)
		frappe.clear_cache(doctype=doctype)
		return

	# Field exists in metadata but column is missing: add it explicitly.
	frappe.db.add_column(doctype, fieldname, "varchar(140)")
	frappe.clear_cache(doctype=doctype)
