# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def sync_territory_to_crm(doc, method):
	"""Hook function to sync Territory to CRM Territory"""
	try:
		# Skip sync if this update was triggered by CRM Territory sync
		if frappe.flags.get("skip_territory_sync"):
			return
		
		# Check if ERPNext CRM integration is enabled
		if not frappe.db.exists("DocType", "ERPNext CRM Settings"):
			return
		
		erpnext_settings = frappe.get_single("ERPNext CRM Settings")
		if not erpnext_settings.enabled or not erpnext_settings.enable_territory_sync:
			return
		
		from crm.fcrm.doctype.crm_territory.field_mapping import map_territory_to_crm_data, update_doc_with_mapped_data
		
		# Set flag to prevent infinite loop
		frappe.flags.skip_crm_territory_sync = True
		
		# Check if CRM Territory already exists
		territory_name = doc.territory_name
		crm_territory = frappe.db.exists("CRM Territory", territory_name)
		
		# Map Territory data to CRM Territory format
		crm_territory_data = map_territory_to_crm_data(doc)
		
		if crm_territory:
			# Update existing CRM territory
			crm_territory_doc = frappe.get_doc("CRM Territory", crm_territory)
			updated_fields = update_doc_with_mapped_data(crm_territory_doc, crm_territory_data)
			if updated_fields:
				crm_territory_doc.save()
				frappe.logger().info(f"Updated CRM Territory {territory_name} fields: {updated_fields}")
		else:
			# Create new CRM territory
			crm_territory_doc = frappe.get_doc({
				"doctype": "CRM Territory",
				**crm_territory_data
			})
			crm_territory_doc.insert()
			frappe.logger().info(f"Created new CRM Territory {territory_name}")
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error syncing Territory {doc.name} to CRM Territory: {str(e)}"
		)
	finally:
		# Clear the flag
		frappe.flags.skip_crm_territory_sync = False


def delete_territory_from_crm(doc, method):
	"""Hook function to delete Territory from CRM Territory"""
	try:
		# Skip sync if this delete was triggered by CRM Territory delete
		if frappe.flags.get("skip_territory_sync"):
			return
		
		# Check if ERPNext CRM integration is enabled
		if not frappe.db.exists("DocType", "ERPNext CRM Settings"):
			return
		
		erpnext_settings = frappe.get_single("ERPNext CRM Settings")
		if not erpnext_settings.enabled or not erpnext_settings.enable_territory_sync:
			return
		
		crm_territory = frappe.db.exists("CRM Territory", doc.territory_name)
		if crm_territory:
			frappe.flags.skip_crm_territory_sync = True
			frappe.delete_doc("CRM Territory", crm_territory)
			frappe.flags.skip_crm_territory_sync = False
			
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error deleting CRM Territory for Territory {doc.name}: {str(e)}"
		)
