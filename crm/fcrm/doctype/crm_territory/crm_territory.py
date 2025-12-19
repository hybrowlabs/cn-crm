# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.nestedset import NestedSet, get_root_of


class CRMTerritory(NestedSet):
	nsm_parent_field = "parent_crm_territory"
	
	def validate(self):
		# For root territory "All Territories", keep parent empty
		root_name = get_root_of("CRM Territory")
		if self.name == root_name or self.territory_name == root_name:
			self.parent_crm_territory = ""
		elif not self.parent_crm_territory:
			self.parent_crm_territory = root_name

		# Validate that we're not creating a loop in the territory hierarchy
		if self.parent_crm_territory and self.parent_crm_territory == self.name:
			frappe.throw(_("A territory cannot be its own parent"))
	
	def on_update(self):
		super().on_update()
		self.validate_one_root()
		# Sync to ERPNext Territory if integration is enabled
		self.sync_to_erpnext_territory()
		# Sync sales team members to User Permissions (Section 4.1)
		# This runs after nested set operations are complete
		if not frappe.flags.get("skip_team_member_sync"):
			self.sync_team_members_to_user_permissions()
	
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

			# Set flags to prevent infinite loop (both directions)
			frappe.flags.skip_crm_territory_sync = True
			frappe.flags.skip_territory_sync = True

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
			# Clear the flags
			frappe.flags.skip_crm_territory_sync = False
			frappe.flags.skip_territory_sync = False
	
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

			# TODO: Re-enable ERPNext Territory deletion after fixing bidirectional sync
			# For now, only allow CRM Territory deletion without affecting ERPNext
			# ERPNext Territory is the source of truth and should not be deleted from CRM side
			frappe.logger().info(f"Skipping ERPNext Territory deletion for {self.territory_name} (one-way sync enabled)")

			# if not erpnext_settings.is_erpnext_in_different_site:
			# 	# Same site - direct delete
			# 	if "erpnext" in frappe.get_installed_apps():
			# 		territory = frappe.db.exists("Territory", self.territory_name)
			# 		if territory:
			# 			frappe.flags.skip_crm_territory_sync = True
			# 			frappe.delete_doc("Territory", territory)
			# 			frappe.flags.skip_crm_territory_sync = False
			# else:
			# 	# Different site - API delete
			# 	from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import get_erpnext_site_client
			# 	client = get_erpnext_site_client(erpnext_settings)
			#
			# 	try:
			# 		existing_territories = client.get_list("Territory", {"territory_name": self.territory_name})
			# 		if existing_territories:
			# 			client.delete("Territory", existing_territories[0]["name"])
			# 	except Exception as e:
			# 		frappe.log_error(
			# 			frappe.get_traceback(),
			# 			f"Error deleting Territory {self.territory_name} from remote ERPNext site: {str(e)}"
			# 		)

		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error deleting ERPNext Territory for CRM Territory {self.name}: {str(e)}"
			)

	def sync_team_members_to_user_permissions(self):
		"""
		Sync sales team members to User Permissions (Section 4.1.1 & 4.1.2)

		This method:
		1. Deletes existing auto-created User Permissions for this territory
		2. Creates new User Permissions from sales_team_members child table
		3. Enables territory-based visibility for sales teams
		"""
		try:
			# Skip if sales_team_members field doesn't exist (not yet migrated)
			if not hasattr(self, "sales_team_members"):
				return

			# Delete existing auto-created User Permissions for this territory
			frappe.db.delete("User Permission", {
				"allow": "CRM Territory",
				"for_value": self.name,
				"auto_created_from_territory": 1
			})

			# Create User Permissions from sales_team_members table
			for member in self.sales_team_members:
				if member.user and member.is_active:
					# Check if permission already exists
					existing = frappe.db.exists("User Permission", {
						"user": member.user,
						"allow": "CRM Territory",
						"for_value": self.name,
						"auto_created_from_territory": 1
					})

					if existing:
						continue

					# Create new User Permission
					user_permission = frappe.get_doc({
						"doctype": "User Permission",
						"user": member.user,
						"allow": "CRM Territory",
						"for_value": self.name,
						"apply_to_all_doctypes": 1,  # Filter across all doctypes
						"hide_descendants": 0,  # Allow access to child territories
						"auto_created_from_territory": 1  # Flag to track auto-created permissions
					})
					user_permission.insert(ignore_permissions=True)
					frappe.logger().info(
						f"Created User Permission: {member.user} → {self.name}"
					)

			# Note: Do not commit here - let the parent transaction handle it

		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error syncing team members to User Permissions for {self.name}: {str(e)}"
			)

