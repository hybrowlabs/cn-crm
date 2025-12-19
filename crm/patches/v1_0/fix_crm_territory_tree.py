"""
Patch to fix CRM Territory nested set tree structure.

This patch ensures:
1. A root "All Territories" node exists
2. All territories have valid parent references
3. Nested set lft/rgt values are correct
"""

import frappe
from frappe.utils.nestedset import rebuild_tree


def execute():
	"""Fix CRM Territory nested set tree structure."""

	try:
		# Set flags to prevent sync during tree rebuild
		frappe.flags.skip_territory_sync = True
		frappe.flags.skip_crm_territory_sync = True
		frappe.flags.skip_team_member_sync = True

		# Check if root node exists (root has empty/null parent)
		root = frappe.db.exists("CRM Territory", "All Territories")

		if not root:
			print("Creating root 'All Territories' node...")

			# Create new root node using raw SQL to avoid hooks
			frappe.db.sql("""
				INSERT INTO `tabCRM Territory`
				(name, territory_name, is_group, parent_crm_territory, lft, rgt, creation, modified, owner, modified_by, docstatus)
				VALUES ('All Territories', 'All Territories', 1, '', 1, 2, NOW(), NOW(), 'Administrator', 'Administrator', 0)
			""")
			print(f"Created root node: All Territories")
			root = "All Territories"
		else:
			# Ensure All Territories has correct root values
			frappe.db.sql("""
				UPDATE `tabCRM Territory`
				SET parent_crm_territory = '',
					is_group = 1,
					modified = NOW()
				WHERE name = 'All Territories'
			""")
			print("Updated 'All Territories' as root")

		# Get all territories (including those with NULL parent)
		territories = frappe.db.sql("""
			SELECT name, parent_crm_territory
			FROM `tabCRM Territory`
			WHERE name != 'All Territories'
		""", as_dict=True)

		# Fix territories with NULL parent using raw SQL
		for territory in territories:
			if not territory.parent_crm_territory:
				frappe.db.sql("""
					UPDATE `tabCRM Territory`
					SET parent_crm_territory = 'All Territories',
						modified = NOW()
					WHERE name = %s
				""", (territory.name,))
				print(f"Fixed parent for {territory.name} -> All Territories")

		frappe.db.commit()

		# Rebuild the entire tree to fix lft/rgt values
		print("Rebuilding nested set tree...")
		rebuild_tree("CRM Territory", "parent_crm_territory")

		frappe.db.commit()

		print("Successfully fixed CRM Territory tree structure")

	except Exception as e:
		print(f"Error fixing CRM Territory tree: {str(e)}")
		frappe.log_error(
			frappe.get_traceback(),
			"Error fixing CRM Territory tree structure"
		)
		raise

	finally:
		# Clear flags
		frappe.flags.skip_territory_sync = False
		frappe.flags.skip_crm_territory_sync = False
		frappe.flags.skip_team_member_sync = False
