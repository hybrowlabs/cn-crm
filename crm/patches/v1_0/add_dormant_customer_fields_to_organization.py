"""
Patch to add dormant customer tracking fields to CRM Organization.

This patch adds:
- is_dormant: Checkbox to indicate if customer is dormant
- last_transaction_date: Last Sales Order date from ERPNext customers

These fields work with the dormant_customers_timespan setting in FCRM Settings.
"""

import frappe


def execute():
	"""Add dormant customer tracking fields to CRM Organization DocType."""

	doctype = "CRM Organization"

	# Check if DocType exists
	if not frappe.db.exists("DocType", doctype):
		print(f"DocType {doctype} does not exist. Skipping patch.")
		return

	# Get the DocType document
	doc = frappe.get_doc("DocType", doctype)

	# Check if fields already exist
	existing_fields = {field.fieldname for field in doc.fields}

	fields_to_add = []

	# Section Break
	if "dormant_customer_section" not in existing_fields:
		fields_to_add.append({
			"fieldname": "dormant_customer_section",
			"fieldtype": "Section Break",
			"label": "Dormant Customer Tracking"
		})

	# Is Dormant checkbox
	if "is_dormant" not in existing_fields:
		fields_to_add.append({
			"fieldname": "is_dormant",
			"fieldtype": "Check",
			"label": "Is Dormant Customer",
			"default": "0",
			"description": "Automatically calculated based on ERPNext customer transaction activity",
			"read_only": 1
		})

	# Column Break
	if "column_break_dormant" not in existing_fields:
		fields_to_add.append({
			"fieldname": "column_break_dormant",
			"fieldtype": "Column Break"
		})

	# Last Transaction Date
	if "last_transaction_date" not in existing_fields:
		fields_to_add.append({
			"fieldname": "last_transaction_date",
			"fieldtype": "Datetime",
			"label": "Last Transaction Date",
			"description": "Last Sales Order date from linked ERPNext customers",
			"read_only": 1
		})

	if not fields_to_add:
		print(f"All dormant customer fields already exist in {doctype}")
		return

	# Add fields
	for field_dict in fields_to_add:
		doc.append("fields", field_dict)
		print(f"Added field '{field_dict['fieldname']}' to {doctype}")

	# Save the DocType
	doc.flags.ignore_validate = True
	doc.save()

	frappe.db.commit()
	print(f"Successfully added dormant customer tracking fields to {doctype}")
