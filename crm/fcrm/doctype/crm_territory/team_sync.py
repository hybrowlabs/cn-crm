# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Helper functions for syncing territory team members between ERPNext and CRM.

This module supports Section 4.1 (Territory-Based Sales Teams) by integrating
the sales_team_members child table with the existing Territory Synchronization.
"""

import frappe
from frappe import _


def sync_territory_manager_to_team_members(crm_territory_doc, territory_manager_sales_person):
	"""
	Sync ERPNext Territory's territory_manager to CRM Territory's sales_team_members table.

	Args:
		crm_territory_doc: CRM Territory document
		territory_manager_sales_person: Sales Person name from ERPNext Territory
	"""
	try:
		# Skip if sales_team_members field doesn't exist
		if not hasattr(crm_territory_doc, "sales_team_members"):
			return

		# Convert Sales Person to User
		if territory_manager_sales_person:
			user = frappe.db.get_value("Sales Person", territory_manager_sales_person, "user")
			if user and user != crm_territory_doc.territory_manager:
				# Update territory_manager field
				crm_territory_doc.territory_manager = user

			# Check if this user already exists in team members
			existing_member = None
			for member in crm_territory_doc.sales_team_members:
				if member.user == user:
					existing_member = member
					break

			if not existing_member and user:
				# Add territory manager to team members with "Territory Manager" role
				crm_territory_doc.append("sales_team_members", {
					"user": user,
					"role": "Territory Manager",
					"is_active": 1
				})
				frappe.logger().info(
					f"Added territory manager {user} to {crm_territory_doc.name} team members"
				)

	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error syncing territory manager to team members for {crm_territory_doc.name}: {str(e)}"
		)


def get_team_members_from_user_permissions(territory_name):
	"""
	Get list of users who have User Permissions for a specific territory.

	Args:
		territory_name: Name of the CRM Territory

	Returns:
		List of dicts with user and role information
	"""
	try:
		# Get all User Permissions for this territory
		permissions = frappe.get_all("User Permission",
			filters={
				"allow": "CRM Territory",
				"for_value": territory_name
			},
			fields=["user", "auto_created_from_territory"]
		)

		team_members = []
		for perm in permissions:
			# Try to determine role from user's roles
			user_roles = frappe.get_roles(perm.user)

			role = "Sales Executive"  # Default
			if "Sales Manager" in user_roles:
				role = "Sales Manager"
			elif "Territory Manager" in user_roles:
				role = "Territory Manager"

			team_members.append({
				"user": perm.user,
				"role": role,
				"is_active": 1,
				"auto_created": perm.auto_created_from_territory
			})

		return team_members

	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error getting team members from User Permissions for {territory_name}: {str(e)}"
		)
		return []
