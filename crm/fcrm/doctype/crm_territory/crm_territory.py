# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.nestedset import NestedSet, get_root_of


class CRMTerritory(NestedSet):
	nsm_parent_field = "parent_crm_territory"
	
	def validate(self):
		if not self.parent_crm_territory:
			self.parent_crm_territory = get_root_of("CRM Territory")
	
	def on_update(self):
		super().on_update()
		self.validate_one_root()
		# Sync to ERPNext Territory if integration is enabled
		self.sync_to_erpnext_territory()
	
	def on_trash(self):
		super().on_trash()
		# Delete corresponding ERPNext Territory if integration is enabled
		self.delete_erpnext_territory()
	
	def sync_to_erpnext_territory(self):
		"""Sync CRM Territory to ERPNext Territory"""
		try:
			# Check if ERPNext integration is enabled
			erpnext_settings = frappe.get_single("ERPNext CRM Settings")
			if not erpnext_settings.enabled or not erpnext_settings.enable_territory_sync:
				return
			
			# Skip sync if this update was triggered by ERPNext Territory sync
			if frappe.flags.get("skip_territory_sync"):
				return
			
			# Set flag to prevent infinite loop
			frappe.flags.skip_crm_territory_sync = True
			
			if not erpnext_settings.is_erpnext_in_different_site:
				# Same site - direct sync
				self._sync_to_local_territory()
			else:
				# Different site - API sync
				self._sync_to_remote_territory(erpnext_settings)
				
		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error syncing CRM Territory {self.name} to ERPNext Territory: {str(e)}"
			)
		finally:
			# Clear the flag
			frappe.flags.skip_crm_territory_sync = False
	
	def _sync_to_local_territory(self):
		"""Sync to local ERPNext Territory"""
		if "erpnext" not in frappe.get_installed_apps():
			return
		
		from crm.fcrm.doctype.crm_territory.field_mapping import map_crm_to_territory_data, update_doc_with_mapped_data
		
		# Check if Territory already exists
		territory_name = self.territory_name
		territory = frappe.db.exists("Territory", territory_name)
		
		# Map CRM Territory data to Territory format
		territory_data = map_crm_to_territory_data(self)
		
		if territory:
			# Update existing territory
			territory_doc = frappe.get_doc("Territory", territory)
			updated_fields = update_doc_with_mapped_data(territory_doc, territory_data)
			if updated_fields:
				territory_doc.save()
				frappe.logger().info(f"Updated Territory {territory_name} fields: {updated_fields}")
		else:
			# Create new territory
			territory_doc = frappe.get_doc({
				"doctype": "Territory",
				**territory_data
			})
			territory_doc.insert()
			frappe.logger().info(f"Created new Territory {territory_name}")
		
		frappe.db.commit()
	
	def _sync_to_remote_territory(self, erpnext_settings):
		"""Sync to remote ERPNext Territory via API"""
		from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_erpnext_site_client
		from crm.fcrm.doctype.crm_territory.field_mapping import map_crm_to_territory_data
		
		client = get_erpnext_site_client(erpnext_settings)
		
		# Map CRM Territory data to Territory format
		territory_data = map_crm_to_territory_data(self)
		
		# For remote sync, we can't convert User to Sales Person, so remove territory_manager
		if "territory_manager" in territory_data:
			territory_data["territory_manager"] = None
		
		try:
			# Check if territory exists remotely
			existing_territories = client.get_list("Territory", {"territory_name": self.territory_name})
			
			if existing_territories:
				# Update existing territory
				client.update("Territory", existing_territories[0]["name"], territory_data)
				frappe.logger().info(f"Updated remote Territory {self.territory_name}")
			else:
				# Create new territory
				client.insert("Territory", territory_data)
				frappe.logger().info(f"Created remote Territory {self.territory_name}")
				
		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error syncing CRM Territory {self.name} to remote ERPNext site: {str(e)}"
			)
	
	def delete_erpnext_territory(self):
		"""Delete corresponding ERPNext Territory"""
		try:
			# Check if ERPNext integration is enabled
			erpnext_settings = frappe.get_single("ERPNext CRM Settings")
			if not erpnext_settings.enabled or not erpnext_settings.enable_territory_sync:
				return
			
			# Skip sync if this delete was triggered by ERPNext Territory delete
			if frappe.flags.get("skip_territory_sync"):
				return
			
			if not erpnext_settings.is_erpnext_in_different_site:
				# Same site - direct delete
				if "erpnext" in frappe.get_installed_apps():
					territory = frappe.db.exists("Territory", self.territory_name)
					if territory:
						frappe.flags.skip_crm_territory_sync = True
						frappe.delete_doc("Territory", territory)
						frappe.flags.skip_crm_territory_sync = False
			else:
				# Different site - API delete
				from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_erpnext_site_client
				client = get_erpnext_site_client(erpnext_settings)
				
				try:
					existing_territories = client.get_list("Territory", {"territory_name": self.territory_name})
					if existing_territories:
						client.delete("Territory", existing_territories[0]["name"])
				except Exception as e:
					frappe.log_error(
						frappe.get_traceback(),
						f"Error deleting Territory {self.territory_name} from remote ERPNext site: {str(e)}"
					)
					
		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error deleting ERPNext Territory for CRM Territory {self.name}: {str(e)}"
			)

