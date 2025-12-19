# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.nestedset import get_root_of


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
			"rgt": "rgt"
			# Note: old_parent is excluded - it's only used internally by NestedSet during moves
		},
		# Territory -> CRM Territory
		"territory_to_crm": {
			"territory_name": "territory_name",
			"parent_territory": "parent_crm_territory",
			"is_group": "is_group",
			"territory_manager": "territory_manager",  # Sales Person -> User (needs conversion)
			"lft": "lft",
			"rgt": "rgt"
			# Note: old_parent is excluded - it's only used internally by NestedSet during moves
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
			# Special handling for parent_territory to prevent self-reference
			elif territory_field == "parent_territory":
				root_territory = get_root_of("Territory")
				crm_root_territory = get_root_of("CRM Territory")

				# Handle root territory (only root itself should have empty parent)
				if territory_doc.territory_name == root_territory:
					# This IS the root, set empty parent
					crm_data[crm_field] = ""
				# Prevent a territory from being its own parent
				elif value == territory_doc.territory_name or value == territory_doc.name:
					# Self-reference detected, set to root
					frappe.logger().warning(
						f"Territory {territory_doc.territory_name} has self-reference in parent_territory, setting parent to {crm_root_territory}"
					)
					crm_data[crm_field] = crm_root_territory
				elif not value:
					# NULL parent but not root itself - set to root
					crm_data[crm_field] = crm_root_territory
				else:
					# Normal case - parent is different from territory
					crm_data[crm_field] = value
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
			# Special handling for parent_crm_territory to prevent self-reference
			elif crm_field == "parent_crm_territory":
				crm_root_territory = get_root_of("CRM Territory")
				root_territory = get_root_of("Territory")

				# Handle root territory - it should have NULL parent in ERPNext
				if crm_territory_doc.territory_name == crm_root_territory:
					# Root territory - set to None (NULL in ERPNext)
					territory_data[territory_field] = None
				# Handle empty parent
				elif not value or value == "":
					# If this territory name matches the ERPNext root, set to None
					# Otherwise set to root (but only if it won't create self-reference)
					if crm_territory_doc.territory_name == root_territory:
						territory_data[territory_field] = None
					else:
						territory_data[territory_field] = root_territory
				# Prevent a territory from being its own parent
				elif value == crm_territory_doc.territory_name or value == crm_territory_doc.name:
					# Self-reference detected, set to None if it's the root, else set to root
					if crm_territory_doc.territory_name == root_territory:
						territory_data[territory_field] = None
					else:
						frappe.logger().warning(
							f"CRM Territory {crm_territory_doc.territory_name} has self-reference in parent, setting parent to {root_territory}"
						)
						territory_data[territory_field] = root_territory
				else:
					# Normal case - parent is different from territory
					territory_data[territory_field] = value
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








