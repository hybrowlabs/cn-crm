# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_territory_field_mapping():
	"""
	Define field mapping between Territory and CRM Territory
	Returns dict with mapping and field existence checks
	"""
	
	# Get field lists for both doctypes
	territory_fields = get_doctype_fields("Territory")
	crm_territory_fields = get_doctype_fields("CRM Territory")
	
	# Define the field mapping
	field_mapping = {
		# CRM Territory -> Territory
		"crm_to_territory": {
			"territory_name": "territory_name",
			"parent_crm_territory": "parent_territory", 
			"is_group": "is_group",
			"territory_manager": "territory_manager",  # User -> Sales Person (needs conversion)
			"lft": "lft",
			"rgt": "rgt",
			"old_parent": "old_parent"
		},
		# Territory -> CRM Territory  
		"territory_to_crm": {
			"territory_name": "territory_name",
			"parent_territory": "parent_crm_territory",
			"is_group": "is_group", 
			"territory_manager": "territory_manager",  # Sales Person -> User (needs conversion)
			"lft": "lft",
			"rgt": "rgt",
			"old_parent": "old_parent"
		}
	}
	
	# Filter mappings to only include fields that exist in both doctypes
	filtered_mapping = {
		"crm_to_territory": {},
		"territory_to_crm": {}
	}
	
	for direction, mapping in field_mapping.items():
		source_fields = crm_territory_fields if direction == "crm_to_territory" else territory_fields
		target_fields = territory_fields if direction == "crm_to_territory" else crm_territory_fields
		
		for source_field, target_field in mapping.items():
			if source_field in source_fields and target_field in target_fields:
				filtered_mapping[direction][source_field] = target_field
			else:
				frappe.logger().debug(f"Skipping field mapping {source_field} -> {target_field} (field not found)")
	
	return filtered_mapping


def get_doctype_fields(doctype):
	"""Get list of all fields for a doctype"""
	try:
		meta = frappe.get_meta(doctype)
		return [field.fieldname for field in meta.fields if field.fieldname]
	except Exception:
		frappe.logger().warning(f"Could not get fields for doctype {doctype}")
		return []


def map_territory_to_crm_data(territory_doc):
	"""
	Map Territory document data to CRM Territory format
	"""
	mapping = get_territory_field_mapping()["territory_to_crm"]
	
	crm_data = {}
	
	for territory_field, crm_field in mapping.items():
		if hasattr(territory_doc, territory_field):
			value = getattr(territory_doc, territory_field)
			
			# Special handling for territory_manager (Sales Person -> User)
			if territory_field == "territory_manager" and value:
				user = frappe.db.get_value("Sales Person", value, "user")
				crm_data[crm_field] = user if user else None
			else:
				crm_data[crm_field] = value
	
	return crm_data


def map_crm_to_territory_data(crm_territory_doc):
	"""
	Map CRM Territory document data to Territory format
	"""
	mapping = get_territory_field_mapping()["crm_to_territory"]
	
	territory_data = {}
	
	for crm_field, territory_field in mapping.items():
		if hasattr(crm_territory_doc, crm_field):
			value = getattr(crm_territory_doc, crm_field)
			
			# Special handling for territory_manager (User -> Sales Person)
			if crm_field == "territory_manager" and value:
				sales_person = frappe.db.get_value("Sales Person", {"user": value}, "name")
				territory_data[territory_field] = sales_person if sales_person else None
			else:
				territory_data[territory_field] = value
	
	return territory_data


def get_safe_field_value(doc, fieldname, default=None):
	"""
	Safely get field value from document, return default if field doesn't exist
	"""
	try:
		if hasattr(doc, fieldname):
			return getattr(doc, fieldname, default)
		return default
	except Exception:
		return default


def update_doc_with_mapped_data(doc, mapped_data):
	"""
	Update document with mapped data, only updating fields that exist
	"""
	updated_fields = []
	
	for fieldname, value in mapped_data.items():
		if hasattr(doc, fieldname):
			try:
				setattr(doc, fieldname, value)
				updated_fields.append(fieldname)
			except Exception as e:
				frappe.logger().warning(f"Could not set field {fieldname} to {value}: {str(e)}")
	
	return updated_fields








