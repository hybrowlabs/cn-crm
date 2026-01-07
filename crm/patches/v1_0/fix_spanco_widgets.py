# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from crm.patches.v1_0.create_default_dashboards import add_lmotpo_widget


def execute():
	"""Add LMOTPO widget to Spanco Dashboard if it doesn't have any widgets"""
	dashboard_name = "Spanco Dashboard"
	
	if not frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		frappe.log_error(f"Dashboard '{dashboard_name}' does not exist", "Fix Spanco Widgets")
		return
	
	# Check if widgets exist with proper parent linkage
	widget_count = frappe.db.count("CRM Dashboard Widget", {"parent": dashboard_name})
	
	# Check for orphaned widgets (widgets with name starting with dashboard name but NULL or wrong parent)
	orphaned_widgets = frappe.db.get_all(
		"CRM Dashboard Widget",
		filters={
			"name": ["like", f"{dashboard_name}-%"],
			"parent": ["in", [None, "", dashboard_name]]
		},
		fields=["name", "parent"]
	)
	
	# Fix orphaned widgets by updating their parent, or delete and recreate
	for widget in orphaned_widgets:
		if widget.parent != dashboard_name:
			try:
				# Try to update the parent first
				frappe.db.set_value("CRM Dashboard Widget", widget.name, {
					"parent": dashboard_name,
					"parenttype": "CRM Dashboard",
					"parentfield": "widgets"
				})
				frappe.db.commit()
			except Exception as e:
				# If update fails (e.g., duplicate), delete and recreate
				try:
					frappe.delete_doc("CRM Dashboard Widget", widget.name, force=True, ignore_permissions=True)
					frappe.db.commit()
				except Exception as e2:
					frappe.log_error(f"Error fixing orphaned widget {widget.name}: {str(e2)}", "Fix Spanco Widgets")
	
	# Re-check widget count after fixing orphans
	widget_count = frappe.db.count("CRM Dashboard Widget", {"parent": dashboard_name})
	
	if widget_count == 0:
		# No widgets found. Add LMOTPO widget
		dashboard = frappe.get_doc("CRM Dashboard", dashboard_name)
		add_lmotpo_widget(dashboard)
		dashboard.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.log_error(f"Added LMOTPO widget to {dashboard_name}", "Fix Spanco Widgets")
	else:
		frappe.log_error(f"Dashboard already has {widget_count} widget(s)", "Fix Spanco Widgets")
