# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def sync_all_territories():
	"""Sync all existing territories between ERPNext and CRM"""
	try:
		# Check if ERPNext integration is enabled
		erpnext_settings = frappe.get_single("ERPNext CRM Settings")
		if not erpnext_settings.enabled:
			frappe.throw(_("ERPNext CRM integration is not enabled"))
		
		if not erpnext_settings.is_erpnext_in_different_site:
			# Same site - sync both ways
			sync_erpnext_to_crm()
			sync_crm_to_erpnext()
		else:
			# Different site - only sync CRM to remote ERPNext
			sync_crm_to_remote_erpnext(erpnext_settings)
		
		frappe.msgprint(_("Territory synchronization completed successfully"))
		
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error during territory synchronization: {str(e)}"
		)
		frappe.throw(_("Error during territory synchronization. Check error log for details."))


def sync_erpnext_to_crm():
	"""Sync ERPNext Territories to CRM Territories"""
	if "erpnext" not in frappe.get_installed_apps():
		return
	
	from crm.fcrm.doctype.crm_territory.field_mapping import get_territory_field_mapping, map_territory_to_crm_data, update_doc_with_mapped_data
	
	# Set flag to prevent infinite loop
	frappe.flags.skip_territory_sync = True
	
	try:
		# Get all available fields for Territory
		mapping = get_territory_field_mapping()
		territory_fields = list(mapping["territory_to_crm"].keys())
		
		territories = frappe.get_all("Territory", fields=["name"] + territory_fields)
		
		for territory_data in territories:
			territory_doc = frappe.get_doc("Territory", territory_data.name)
			
			# Check if CRM Territory already exists
			crm_territory = frappe.db.exists("CRM Territory", territory_doc.territory_name)
			
			# Map Territory data to CRM Territory format
			crm_territory_data = map_territory_to_crm_data(territory_doc)
			
			if crm_territory:
				# Update existing CRM territory
				crm_territory_doc = frappe.get_doc("CRM Territory", crm_territory)
				updated_fields = update_doc_with_mapped_data(crm_territory_doc, crm_territory_data)
				if updated_fields:
					crm_territory_doc.save()
					frappe.logger().info(f"Bulk sync: Updated CRM Territory {territory_doc.territory_name} fields: {updated_fields}")
			else:
				# Create new CRM territory
				crm_territory_doc = frappe.get_doc({
					"doctype": "CRM Territory",
					**crm_territory_data
				})
				crm_territory_doc.insert()
				frappe.logger().info(f"Bulk sync: Created new CRM Territory {territory_doc.territory_name}")
		
		frappe.db.commit()
		
	finally:
		frappe.flags.skip_territory_sync = False


def sync_crm_to_erpnext():
	"""Sync CRM Territories to ERPNext Territories"""
	if "erpnext" not in frappe.get_installed_apps():
		return
	
	from crm.fcrm.doctype.crm_territory.field_mapping import get_territory_field_mapping, map_crm_to_territory_data, update_doc_with_mapped_data
	
	# Set flag to prevent infinite loop
	frappe.flags.skip_crm_territory_sync = True
	
	try:
		# Get all available fields for CRM Territory
		mapping = get_territory_field_mapping()
		crm_territory_fields = list(mapping["crm_to_territory"].keys())
		
		crm_territories = frappe.get_all("CRM Territory", fields=["name"] + crm_territory_fields)
		
		for crm_territory_data in crm_territories:
			crm_territory_doc = frappe.get_doc("CRM Territory", crm_territory_data.name)
			
			# Check if Territory already exists
			territory = frappe.db.exists("Territory", crm_territory_doc.territory_name)
			
			# Map CRM Territory data to Territory format
			territory_data = map_crm_to_territory_data(crm_territory_doc)
			
			if territory:
				# Update existing territory
				territory_doc = frappe.get_doc("Territory", territory)
				updated_fields = update_doc_with_mapped_data(territory_doc, territory_data)
				if updated_fields:
					territory_doc.save()
					frappe.logger().info(f"Bulk sync: Updated Territory {crm_territory_doc.territory_name} fields: {updated_fields}")
			else:
				# Create new territory
				territory_doc = frappe.get_doc({
					"doctype": "Territory",
					**territory_data
				})
				territory_doc.insert()
				frappe.logger().info(f"Bulk sync: Created new Territory {crm_territory_doc.territory_name}")
		
		frappe.db.commit()
		
	finally:
		frappe.flags.skip_crm_territory_sync = False


def sync_crm_to_remote_erpnext(erpnext_settings):
	"""Sync CRM Territories to remote ERPNext site"""
	from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_erpnext_site_client
	from crm.fcrm.doctype.crm_territory.field_mapping import get_territory_field_mapping, map_crm_to_territory_data
	
	client = get_erpnext_site_client(erpnext_settings)
	
	try:
		# Get all available fields for CRM Territory
		mapping = get_territory_field_mapping()
		crm_territory_fields = list(mapping["crm_to_territory"].keys())
		
		crm_territories = frappe.get_all("CRM Territory", fields=["name"] + crm_territory_fields)
		
		for crm_territory_data in crm_territories:
			crm_territory_doc = frappe.get_doc("CRM Territory", crm_territory_data.name)
			
			# Map CRM Territory data to Territory format
			territory_data = map_crm_to_territory_data(crm_territory_doc)
			
			# For remote sync, we can't convert User to Sales Person, so remove territory_manager
			if "territory_manager" in territory_data:
				territory_data["territory_manager"] = None
			
			try:
				# Check if territory exists remotely
				existing_territories = client.get_list("Territory", {"territory_name": crm_territory_doc.territory_name})
				
				if existing_territories:
					# Update existing territory
					client.update("Territory", existing_territories[0]["name"], territory_data)
					frappe.logger().info(f"Remote bulk sync: Updated Territory {crm_territory_doc.territory_name}")
				else:
					# Create new territory
					client.insert("Territory", territory_data)
					frappe.logger().info(f"Remote bulk sync: Created Territory {crm_territory_doc.territory_name}")
					
			except Exception as e:
				frappe.log_error(
					frappe.get_traceback(),
					f"Error syncing CRM Territory {crm_territory_doc.name} to remote ERPNext site: {str(e)}"
				)
				
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error during remote territory synchronization: {str(e)}"
		)
		raise
