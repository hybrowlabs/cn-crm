"""
Migration patch to update SPANCO views to LMOTPO views.

This patch:
1. Updates existing SPANCO view labels to LMOTPO labels
2. Creates new LMOTPO views if they don't exist
3. Updates FCRM Settings to reference the correct views
4. Removes old SPANCO views that are no longer needed

Based on: CRM_Non_Blocking_Tasks - Section 2: SPANCO to LMOTPO Sales Pipeline Stages
"""

import frappe
from frappe import _


def execute():
	"""Execute the migration from SPANCO to LMOTPO views."""

	# Mapping of old SPANCO labels to new LMOTPO labels
	spanco_to_lmotpo_mapping = {
		"Suspects": "Lead",
		"Prospects": "Meetings",
		"Analysis": "Opportunities",
		"Negotiations": "Trial",
		"Negotiation": "Trial",  # Handle both variants
		"Commitment": "Price Discussion",
		# Order remains the same
	}

	# Update existing views with old SPANCO labels to new LMOTPO labels
	for old_label, new_label in spanco_to_lmotpo_mapping.items():
		existing_views = frappe.get_all(
			"CRM View Settings",
			filters={"label": old_label},
			fields=["name", "label", "dt"]
		)

		for view in existing_views:
			frappe.db.set_value("CRM View Settings", view.name, "label", new_label)
			frappe.db.commit()
			print(f"Updated view label: {old_label} -> {new_label}")

	# Now ensure all LMOTPO views exist with correct configurations
	lmotpo_views = {
		"Lead": {
			"label": "Lead",
			"dt": "CRM Lead",
			"filters": '{"status": "New"}',
			"route_name": "Leads",
		},
		"Meetings": {
			"label": "Meetings",
			"dt": "CRM Lead",
			"filters": '{"status": ["in", ["Contacted", "Nurture"]]}',
			"route_name": "Leads",
		},
		"Opportunities": {
			"label": "Opportunities",
			"dt": "CRM Deal",
			"filters": '{"status": ["in", ["Qualification", "Demo/Making"]]}',
			"route_name": "Deals",
		},
		"Trial": {
			"label": "Trial",
			"dt": "CRM Deal",
			"filters": '{"status": "Proposal/Quotation"}',
			"route_name": "Deals",
		},
		"Price Discussion": {
			"label": "Price Discussion",
			"dt": "CRM Deal",
			"filters": '{"status": "Negotiation"}',
			"route_name": "Deals",
		},
		"Order": {
			"label": "Order",
			"dt": "CRM Deal",
			"filters": '{"status": ["in", ["Ready to Close", "Won"]]}',
			"route_name": "Deals",
		}
	}

	view_ids = {}

	# Create or update each LMOTPO view
	for view_name, config in lmotpo_views.items():
		# Check if view with this label and doctype already exists
		existing_views = frappe.get_all(
			"CRM View Settings",
			filters={"label": config["label"], "dt": config["dt"]},
			fields=["name"],
			order_by="creation"
		)

		if existing_views:
			# Use the first (oldest) view and update it
			primary_view = existing_views[0].name
			doc = frappe.get_doc("CRM View Settings", primary_view)
			doc.filters = config["filters"]
			doc.route_name = config["route_name"]
			doc.type = "list"
			doc.is_standard = 1
			doc.public = 1
			doc.save()
			view_ids[view_name.lower().replace(" ", "_")] = doc.name
			print(f"Updated existing view: {view_name}")

			# Delete duplicate views with the same label and doctype
			if len(existing_views) > 1:
				for duplicate in existing_views[1:]:
					try:
						frappe.delete_doc("CRM View Settings", duplicate.name, force=True)
						print(f"Deleted duplicate view: {duplicate.name}")
					except Exception as e:
						print(f"Could not delete duplicate view {duplicate.name}: {str(e)}")
		else:
			# Create new view
			doc = frappe.new_doc("CRM View Settings")
			doc.label = config["label"]
			doc.dt = config["dt"]
			doc.type = "list"
			doc.route_name = config["route_name"]
			doc.filters = config["filters"]
			doc.is_standard = 1
			doc.public = 1
			doc.insert(ignore_permissions=True)
			view_ids[view_name.lower().replace(" ", "_")] = doc.name
			print(f"Created new view: {view_name}")

	# Update FCRM Settings with the view references
	if frappe.db.exists("FCRM Settings"):
		fcrm_settings = frappe.get_single("FCRM Settings")

		# Map LMOTPO views to existing field names in FCRM Settings
		if view_ids.get("lead"):
			fcrm_settings.suspects = view_ids["lead"]  # L - Lead
		if view_ids.get("meetings"):
			fcrm_settings.prospects = view_ids["meetings"]  # M - Meetings
		if view_ids.get("opportunities"):
			fcrm_settings.analysis = view_ids["opportunities"]  # O - Opportunities
		if view_ids.get("trial"):
			fcrm_settings.negotiation = view_ids["trial"]  # T - Trial
		if view_ids.get("price_discussion"):
			fcrm_settings.closed = view_ids["price_discussion"]  # P - Price Discussion
		if view_ids.get("order"):
			fcrm_settings.order = view_ids["order"]  # O - Order

		fcrm_settings.save()
		print("Updated FCRM Settings with LMOTPO view references")

	frappe.db.commit()
	print("SPANCO to LMOTPO migration completed successfully")
