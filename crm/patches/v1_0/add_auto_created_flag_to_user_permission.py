"""
Patch to add auto_created_from_territory flag to User Permission.

This custom field helps track which User Permissions were auto-created
from CRM Territory team members vs manually created by admins.
"""

import frappe


def execute():
	"""Add auto_created_from_territory custom field to User Permission DocType."""

	doctype = "User Permission"

	# Check if DocType exists
	if not frappe.db.exists("DocType", doctype):
		print(f"DocType {doctype} does not exist. Skipping patch.")
		return

	# Check if custom field already exists
	if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": "auto_created_from_territory"}):
		print(f"Custom field 'auto_created_from_territory' already exists in {doctype}")
		return

	# Create custom field
	custom_field = frappe.get_doc({
		"doctype": "Custom Field",
		"dt": doctype,
		"fieldname": "auto_created_from_territory",
		"label": "Auto Created From Territory",
		"fieldtype": "Check",
		"default": "0",
		"insert_after": "hide_descendants",
		"hidden": 1,
		"read_only": 1,
		"description": "Indicates this permission was auto-created from CRM Territory team members"
	})

	custom_field.insert(ignore_permissions=True)
	frappe.db.commit()

	print(f"Successfully added 'auto_created_from_territory' custom field to {doctype}")
