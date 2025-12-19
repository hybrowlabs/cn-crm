"""
Patch to add 'Dormant Customers time span' field to FCRM Settings.

This patch adds a new integer field after the 'enable_forecasting' field
to configure the time span for identifying dormant customers.
"""

import frappe


def execute():
	"""Add dormant_customers_timespan field to FCRM Settings DocType."""

	doctype = "FCRM Settings"

	# Check if DocType exists
	if not frappe.db.exists("DocType", doctype):
		print(f"DocType {doctype} does not exist. Skipping patch.")
		return

	# Get the DocType document
	doc = frappe.get_doc("DocType", doctype)

	# Check if field already exists
	existing_field = None
	for field in doc.fields:
		if field.fieldname == "dormant_customers_timespan":
			existing_field = field
			break

	if existing_field:
		print(f"Field 'dormant_customers_timespan' already exists in {doctype}")
		return

	# Find the position after 'enable_forecasting'
	insert_index = None
	for idx, field in enumerate(doc.fields):
		if field.fieldname == "enable_forecasting":
			insert_index = idx + 1
			break

	if insert_index is None:
		print("Could not find 'enable_forecasting' field. Adding field at the end.")
		insert_index = len(doc.fields)

	# Create the new field dictionary
	new_field_dict = {
		"fieldname": "dormant_customers_timespan",
		"fieldtype": "Int",
		"label": "Dormant Customers time span",
		"description": "Number of days after which a customer is considered dormant (no activity)",
		"default": "90"
	}

	# Add the field to the fields list
	doc.append("fields", new_field_dict)

	# Reorder fields to put the new field after enable_forecasting
	fields_list = list(doc.fields)
	new_field_obj = fields_list.pop()  # Remove the newly added field from the end
	fields_list.insert(insert_index, new_field_obj)  # Insert at correct position
	doc.fields = fields_list

	# Save the DocType (this will trigger rebuild of the table structure)
	doc.flags.ignore_validate = True
	doc.save()

	frappe.db.commit()
	print(f"Successfully added 'dormant_customers_timespan' field to {doctype}")
