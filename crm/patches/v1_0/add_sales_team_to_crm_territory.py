"""
Patch to add Sales Team Members table to CRM Territory.

This patch adds:
- sales_team_members: Child table for managing team members per territory
- Section break for better UI organization

These fields enable Section 4.1.1 (Configure Territory-Based Sales Teams)
"""

import frappe


def execute():
	"""Add sales team members field to CRM Territory DocType."""

	doctype = "CRM Territory"

	# Check if DocType exists
	if not frappe.db.exists("DocType", doctype):
		print(f"DocType {doctype} does not exist. Skipping patch.")
		return

	# Get the DocType document
	doc = frappe.get_doc("DocType", doctype)

	# Check if fields already exist
	existing_fields = {field.fieldname for field in doc.fields}

	fields_to_add = []

	# Section Break for Sales Team
	if "sales_team_section" not in existing_fields:
		fields_to_add.append({
			"fieldname": "sales_team_section",
			"fieldtype": "Section Break",
			"label": "Sales Team Members",
			"collapsible": 1
		})

	# Sales Team Members Table
	if "sales_team_members" not in existing_fields:
		fields_to_add.append({
			"fieldname": "sales_team_members",
			"fieldtype": "Table",
			"label": "Team Members",
			"options": "CRM Territory Team Member",
			"description": "Add sales team members for this territory. User Permissions will be auto-created."
		})

	if not fields_to_add:
		print(f"Sales team fields already exist in {doctype}")
		return

	# Add fields
	for field_dict in fields_to_add:
		doc.append("fields", field_dict)
		print(f"Added field '{field_dict['fieldname']}' to {doctype}")

	# Save the DocType
	doc.flags.ignore_validate = True
	doc.save()

	frappe.db.commit()
	print(f"Successfully added sales team fields to {doctype}")
