# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
import click
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from crm.fcrm.doctype.crm_products.crm_products import create_product_details_script


def before_install():
	pass


def cleanup_legacy_views():
	"""Remove legacy views that shouldn't exist"""
	# Delete view labeled "Lead" (but NOT "Lead Stage")
	# Explicitly check that label is exactly "Lead" and not "Lead Stage"
	lead_view = frappe.db.get_value(
		"CRM View Settings",
		{"label": "Lead", "dt": "CRM Lead"},
		"name"
	)
	if lead_view:
		# Double-check that it's not "Lead Stage" before deleting
		view_doc = frappe.get_doc("CRM View Settings", lead_view)
		if view_doc.label == "Lead" and view_doc.label != "Lead Stage":
			frappe.delete_doc("CRM View Settings", lead_view, force=True)


def after_install(force=False):
	cleanup_legacy_views()
	add_default_lead_statuses()
	add_default_deal_statuses()
	add_default_communication_statuses()
	add_default_fields_layout(force)
	add_property_setter()
	add_email_template_custom_fields()
	add_contact_lead_field()
	add_default_industries()
	add_default_lead_sources()
	add_default_lost_reasons()
	add_standard_dropdown_items()
	add_default_scripts()
	add_default_spanco_views()
	frappe.db.commit()


def add_default_lead_statuses():
	statuses = {
		"New": {
			"color": "orange",
			"position": 1,
		},
		"Contacted": {
			"color": "orange",
			"position": 2,
		},
		"Nurture": {
			"color": "blue",
			"position": 3,
		},
		"Qualified": {
			"color": "green",
			"position": 4,
		},
		"Unqualified": {
			"color": "red",
			"position": 5,
		},
		"Junk": {
			"color": "purple",
			"position": 6,
		},
	}

	for status, values in statuses.items():
		existing = frappe.db.exists("CRM Lead Status", status)
		if existing:
			# Ensure existing records align with desired color/position
			frappe.db.set_value("CRM Lead Status", status, {
				"color": values["color"],
				"position": values["position"],
			})
			continue

		doc = frappe.new_doc("CRM Lead Status")
		doc.lead_status = status
		doc.color = values["color"]
		doc.position = values["position"]
		doc.insert()


def add_default_deal_statuses():
	statuses = {
		"Qualification": {
			"color": "gray",
			"probability": 10,
			"position": 1,
		},
		"Demo/Making": {
			"color": "orange",
			"probability": 25,
			"position": 2,
		},
		"Proposal/Quotation": {
			"color": "blue",
			"probability": 50,
			"position": 3,
		},
		"Negotiation": {
			"color": "yellow",
			"probability": 70,
			"position": 4,
		},
		"Won": {
			"color": "green",
			"probability": 100,
			"position": 5,
		},
		"Lost": {
			"color": "red",
			"probability": 0,
			"position": 6,
		},
	}

	for status, values in statuses.items():
		existing = frappe.db.exists("CRM Deal Status", status)
		if existing:
			# Keep existing records in sync with desired color/position/probability
			frappe.db.set_value("CRM Deal Status", status, {
				"color": values["color"],
				"probability": values["probability"],
				"position": values["position"],
			})
			continue

		doc = frappe.new_doc("CRM Deal Status")
		doc.deal_status = status
		doc.color = values["color"]
		doc.probability = values["probability"]
		doc.position = values["position"]
		doc.insert()


def add_default_communication_statuses():
	statuses = ["Open", "Replied"]

	for status in statuses:
		if frappe.db.exists("CRM Communication Status", status):
			continue

		doc = frappe.new_doc("CRM Communication Status")
		doc.status = status
		doc.insert()


def add_default_fields_layout(force=False):
	quick_entry_layouts = {
		"CRM Lead-Quick Entry": {
			"doctype": "CRM Lead",
			"layout": '[{"name":"first_tab","sections":[{"name":"person_section","columns":[{"name":"column_5jrk","fields":["salutation","email"]},{"name":"column_5CPV","fields":["first_name","mobile_no"]},{"name":"column_gXOy","fields":["last_name","designation"]}]},{"name":"organization_section","columns":[{"name":"column_GHfX","fields":["organization","engagement_type"]},{"name":"column_hXjS","fields":["website","annual_revenue","product_interested"]},{"name":"column_RDNA","fields":["source","industry","applicationusage"]}]},{"name":"lead_section","columns":[{"name":"column_EO1H","fields":["status"]},{"name":"column_RWBe","fields":["lead_owner"]}]}]}]',
		},
		"CRM Deal-Quick Entry": {
			"doctype": "CRM Deal",
			"layout": '[{"name": "organization_section", "hidden": true, "editable": false, "columns": [{"name": "column_GpMP", "fields": ["organization"]}, {"name": "column_FPTn", "fields": []}]}, {"name": "organization_details_section", "editable": false, "columns": [{"name": "column_S3tQ", "fields": ["organization_name", "territory"]}, {"name": "column_KqV1", "fields": ["website", "annual_revenue"]}, {"name": "column_1r67", "fields": ["no_of_employees", "industry"]}]}, {"name": "contact_section", "hidden": true, "editable": false, "columns": [{"name": "column_CeXr", "fields": ["contact"]}, {"name": "column_yHbk", "fields": []}]}, {"name": "contact_details_section", "editable": false, "columns": [{"name": "column_ZTWr", "fields": ["salutation", "email"]}, {"name": "column_tabr", "fields": ["first_name", "mobile_no"]}, {"name": "column_Qjdx", "fields": ["last_name", "gender"]}]}, {"name": "deal_section", "columns": [{"name": "column_mdps", "fields": ["status"]}, {"name": "column_H40H", "fields": ["deal_owner"]}]}]',
		},
		"Contact-Quick Entry": {
			"doctype": "Contact",
			"layout": '[{"name": "salutation_section", "columns": [{"name": "column_eXks", "fields": ["salutation"]}]}, {"name": "full_name_section", "hideBorder": true, "columns": [{"name": "column_cSxf", "fields": ["first_name"]}, {"name": "column_yBc7", "fields": ["last_name"]}]}, {"name": "email_section", "hideBorder": true, "columns": [{"name": "column_tH3L", "fields": ["email_id"]}]}, {"name": "mobile_gender_section", "hideBorder": true, "columns": [{"name": "column_lrfI", "fields": ["mobile_no"]}, {"name": "column_Tx3n", "fields": ["gender"]}]}, {"name": "organization_section", "hideBorder": true, "columns": [{"name": "column_S0J8", "fields": ["company_name"]}]}, {"name": "designation_section", "hideBorder": true, "columns": [{"name": "column_bsO8", "fields": ["designation"]}]}, {"name": "address_section", "hideBorder": true, "columns": [{"name": "column_W3VY", "fields": ["address"]}]}]',
		},
		"CRM Organization-Quick Entry": {
			"doctype": "CRM Organization",
			"layout": '[{"name": "organization_section", "columns": [{"name": "column_zOuv", "fields": ["organization_name"]}]}, {"name": "website_revenue_section", "hideBorder": true, "columns": [{"name": "column_I5Dy", "fields": ["website"]}, {"name": "column_Rgss", "fields": ["annual_revenue"]}]}, {"name": "territory_section", "hideBorder": true, "columns": [{"name": "column_w6ap", "fields": ["territory"]}]}, {"name": "employee_industry_section", "hideBorder": true, "columns": [{"name": "column_u5tZ", "fields": ["no_of_employees"]}, {"name": "column_FFrT", "fields": ["industry"]}]}, {"name": "address_section", "hideBorder": true, "columns": [{"name": "column_O2dk", "fields": ["address"]}]}]',
		},
		"Address-Quick Entry": {
			"doctype": "Address",
			"layout": '[{"name": "details_section", "columns": [{"name": "column_uSSG", "fields": ["address_title", "address_type", "address_line1", "address_line2", "city", "state", "country", "pincode"]}]}]',
		},
		"CRM Call Log-Quick Entry": {
			"doctype": "CRM Call Log",
			"layout": '[{"name":"details_section","columns":[{"name":"column_uMSG","fields":["type","from","duration"]},{"name":"column_wiZT","fields":["to","status","caller","receiver"]}]}]',
		},
		"FCRM Note-Quick Entry": {
			"doctype": "FCRM Note",
			"layout": '[{"name":"reference_section","columns":[{"name":"column_ref1","fields":["reference_doctype"]},{"name":"column_ref2","fields":["reference_docname"]}]},{"name":"note_section","columns":[{"name":"column_title","fields":["title"]}]},{"name":"content_section","columns":[{"name":"column_content","fields":["content"]}]}]',
		},
		"CRM Task-Quick Entry": {
			"doctype": "CRM Task",
			"layout": '[{"name":"reference_section","columns":[{"name":"column_ref1","fields":["reference_doctype"]},{"name":"column_ref2","fields":["reference_docname"]}]},{"name":"task_section","columns":[{"name":"column_title","fields":["title"]},{"name":"column_priority","fields":["priority"]}]},{"name":"assignment_section","columns":[{"name":"column_assigned","fields":["assigned_to"]},{"name":"column_status","fields":["status"]}]},{"name":"dates_section","columns":[{"name":"column_start","fields":["start_date"]},{"name":"column_due","fields":["due_date"]}]},{"name":"description_section","columns":[{"name":"column_desc","fields":["description"]}]}]',
		},
	}

	sidebar_fields_layouts = {
		"CRM Lead-Side Panel": {
			"doctype": "CRM Lead",
			"layout": '[{"label": "Details", "name": "details_section", "opened": true, "columns": [{"name": "column_kl92", "fields": ["organization", "website", "territory", "industry", "job_title", "source", "lead_owner"]}]}, {"label": "Person", "name": "person_section", "opened": true, "columns": [{"name": "column_XmW2", "fields": ["salutation", "first_name", "last_name", "email", "mobile_no"]}]}]',
		},
		"CRM Deal-Side Panel": {
			"doctype": "CRM Deal",
			"layout": '[{"label": "Contacts", "name": "contacts_section", "opened": true, "editable": false, "contacts": []}, {"label": "Organization Details", "name": "organization_section", "opened": true, "columns": [{"name": "column_na2Q", "fields": ["organization", "website", "territory", "annual_revenue", "close_date", "probability", "next_step", "deal_owner"]}]}]',
		},
		"Contact-Side Panel": {
			"doctype": "Contact",
			"layout": '[{"label": "Details", "name": "details_section", "opened": true, "columns": [{"name": "column_eIWl", "fields": ["salutation", "first_name", "last_name", "email_id", "mobile_no", "gender", "company_name", "designation", "address"]}]}]',
		},
		"CRM Organization-Side Panel": {
			"doctype": "CRM Organization",
			"layout": '[{"label": "Details", "name": "details_section", "opened": true, "columns": [{"name": "column_IJOV", "fields": ["organization_name", "website", "territory", "industry", "no_of_employees", "address"]}]}]',
		},
	}

	data_fields_layouts = {
		"CRM Lead-Data Fields": {
			"doctype": "CRM Lead",
			"layout": '[{"name":"first_tab","sections":[{"label":"Details","name":"details_section","opened":true,"columns":[{"name":"column_ZgLG","fields":["organization","lead_owner","engagement_type"]},{"name":"column_TbYq","fields":["job_title","industry","product_interested"]},{"name":"column_OKSX","fields":["source","company_type","applicationusage"]}]},{"label":"Person","name":"person_section","opened":true,"columns":[{"name":"column_6c5g","fields":["salutation","email"]},{"name":"column_1n7Q","fields":["first_name","mobile_no"]},{"name":"column_cT6C","fields":["last_name","designation"]}]}]}]',
		},
		"CRM Deal-Data Fields": {
			"doctype": "CRM Deal",
			"layout": '[{"name":"first_tab","sections":[{"label":"Details","name":"details_section","opened":true,"columns":[{"name":"column_z9XL","fields":["organization","next_step","first_order_volume","decision_criteria"]},{"name":"column_gM4w","fields":["close_date","deal_owner","expected_monthly_volume","economic_buyer_name","custom_formulation_required"]},{"name":"column_gWmE","fields":["probability","product_alloy_type","primary_pain_category","decision_timeline"]}]}]}]',
		},
	}

	for layout in quick_entry_layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			if force:
				frappe.delete_doc("CRM Fields Layout", layout)
			else:
				continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Quick Entry"
		doc.dt = quick_entry_layouts[layout]["doctype"]
		doc.layout = quick_entry_layouts[layout]["layout"]
		doc.insert()

	for layout in sidebar_fields_layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			if force:
				frappe.delete_doc("CRM Fields Layout", layout)
			else:
				continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Side Panel"
		doc.dt = sidebar_fields_layouts[layout]["doctype"]
		doc.layout = sidebar_fields_layouts[layout]["layout"]
		doc.insert()

	for layout in data_fields_layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			if force:
				frappe.delete_doc("CRM Fields Layout", layout)
			else:
				continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Data Fields"
		doc.dt = data_fields_layouts[layout]["doctype"]
		doc.layout = data_fields_layouts[layout]["layout"]
		doc.insert()

	side_data_bar_layouts = {
		"CRM Lead-Side Data Bar": {
			"doctype": "CRM Lead",
			"layout": '[{"label": "Meeting Details", "opened": true, "columns": [{"fields": ["meeting_type", "meeting_outcomes", "next_action_date"]}]}, {"label": "Outcome Analysis", "opened": true, "columns": [{"fields": ["decision_process", "pain_description", "primary_pain_category"]}]}, {"label": "Product Context", "opened": true, "columns": [{"fields": ["product_discussed", "product_interested", "volume_rangekg"]}]}]',
		},
		"CRM Deal-Side Data Bar": {
			"doctype": "CRM Deal",
			"layout": '[{"label": "Proposal Details", "opened": true, "columns": [{"fields": ["final_volume_kg", "final_price__kg", "commercial_acceptance", "proposal_acknowledged"]}]}, {"label": "Process Status", "opened": true, "columns": [{"fields": ["approval_authority", "paper_process_status", "order_date", "product_type"]}]}]',
		}
	}

	for layout in side_data_bar_layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			if force:
				frappe.delete_doc("CRM Fields Layout", layout)
			else:
				continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Side Data Bar"
		doc.dt = side_data_bar_layouts[layout]["doctype"]
		doc.layout = side_data_bar_layouts[layout]["layout"]
		doc.insert()

	trial_data_layouts = {
		"CRM Deal-Trial Data": {
			"doctype": "CRM Deal",
			"layout": '[{"name":"first_tab","sections":[{"label":"Trial Details","name":"trial_details_section","opened":true,"columns":[{"name":"column_trial_1","fields":["trial_product","trial_volume_kg","trial_start_date","trial_end_date","trial_success_criteria"]}]}]}]',
		}
	}

	for layout in trial_data_layouts:
		if frappe.db.exists("CRM Fields Layout", layout):
			if force:
				frappe.delete_doc("CRM Fields Layout", layout)
			else:
				continue

		doc = frappe.new_doc("CRM Fields Layout")
		doc.type = "Trial Data"
		doc.dt = trial_data_layouts[layout]["doctype"]
		doc.layout = trial_data_layouts[layout]["layout"]
		doc.insert()


def add_property_setter():
	if not frappe.db.exists("Property Setter", {"name": "Contact-main-search_fields"}):
		doc = frappe.new_doc("Property Setter")
		doc.doctype_or_field = "DocType"
		doc.doc_type = "Contact"
		doc.property = "search_fields"
		doc.property_type = "Data"
		doc.value = "email_id"
		doc.insert()


def add_email_template_custom_fields():
	if not frappe.get_meta("Email Template").has_field("enabled"):
		click.secho("* Installing Custom Fields in Email Template")

		create_custom_fields(
			{
				"Email Template": [
					{
						"default": "0",
						"fieldname": "enabled",
						"fieldtype": "Check",
						"label": "Enabled",
						"insert_after": "",
					},
					{
						"fieldname": "reference_doctype",
						"fieldtype": "Link",
						"label": "Doctype",
						"options": "DocType",
						"insert_after": "enabled",
					},
				]
			}
		)

		frappe.clear_cache(doctype="Email Template")


def add_contact_lead_field():
	"""Add lead field to Contact doctype"""
	if not frappe.get_meta("Contact").has_field("lead"):
		click.secho("* Installing Lead field in Contact")

		create_custom_fields(
			{
				"Contact": [
					{
						"fieldname": "lead",
						"fieldtype": "Link",
						"label": "Lead",
						"options": "CRM Lead",
						"reqd": 1,
						"insert_after": "company_name",
					},
				]
			}
		)

		frappe.clear_cache(doctype="Contact")


def add_default_industries():
	industries = [
		"Jewellery Manufacturing"
	]

	for industry in industries:
		if frappe.db.exists("CRM Industry", industry):
			continue

		doc = frappe.new_doc("CRM Industry")
		doc.industry = industry
		doc.insert()


def add_default_lead_sources():
	lead_sources = [
		"Existing Customer",
		"Reference",
		"Advertisement",
		"Cold Calling",
		"Exhibition",
		"Supplier Reference",
		"Mass Mailing",
		"Customer's Vendor",
		"Campaign",
		"Walk In",
	]

	for source in lead_sources:
		if frappe.db.exists("CRM Lead Source", source):
			continue

		doc = frappe.new_doc("CRM Lead Source")
		doc.source_name = source
		doc.insert()


def add_default_lost_reasons():
	lost_reasons = [
		{
			"reason": "Pricing",
			"description": "The prospect found the pricing to be too high or not competitive.",
		},
		{"reason": "Competition", "description": "The prospect chose a competitor's product or service."},
		{
			"reason": "Budget Constraints",
			"description": "The prospect did not have the budget to proceed with the purchase.",
		},
		{
			"reason": "Missing Features",
			"description": "The prospect felt that the product or service was missing key features they needed.",
		},
		{
			"reason": "Long Sales Cycle",
			"description": "The sales process took too long, leading to loss of interest.",
		},
		{
			"reason": "No Decision-Maker",
			"description": "The prospect was not the decision-maker and could not proceed.",
		},
		{"reason": "Unresponsive Prospect", "description": "The prospect did not respond to follow-ups."},
		{"reason": "Poor Fit", "description": "The prospect was not a good fit for the product or service."},
		{"reason": "Other", "description": ""},
	]

	for reason in lost_reasons:
		if frappe.db.exists("CRM Lost Reason", reason["reason"]):
			continue

		doc = frappe.new_doc("CRM Lost Reason")
		doc.lost_reason = reason["reason"]
		doc.description = reason["description"]
		doc.insert()


def add_standard_dropdown_items():
	crm_settings = frappe.get_single("FCRM Settings")

	# don't add dropdown items if they're already present
	if crm_settings.dropdown_items:
		return

	crm_settings.dropdown_items = []

	for item in frappe.get_hooks("standard_dropdown_items"):
		crm_settings.append("dropdown_items", item)

	crm_settings.save()


def add_default_scripts():
	from crm.fcrm.doctype.fcrm_settings.fcrm_settings import create_forecasting_script

	for doctype in ["CRM Lead", "CRM Deal"]:
		create_product_details_script(doctype)
	create_forecasting_script()


def add_default_spanco_views():
	"""Ensure LMOTPO pipeline views exist (legacy SPANCO renamed) and wire FCRM Settings."""

	lmotpo_views = {
		"lead": {
			"label": "Lead Stage",
			"dt": "CRM Lead",
			"filters": '{"status": "New"}',
			"route_name": "Leads",
		},
		"meetings": {
			"label": "Meetings Stage",
			"dt": "CRM Lead",
			"filters": '{"status": ["in", ["Contacted", "Nurture"]]}',
			"route_name": "Leads",
		},
		"opportunities": {
			"label": "Opportunities Stage",
			"dt": "CRM Deal",
			"filters": '{"status": ["in", ["Qualification"]]}',
			"route_name": "Deals",
		},
		"trial": {
			"label": "Trial Stage",
			"dt": "CRM Deal",
			"filters": '{"status": ["in", ["Demo/Making"]]}',
			"route_name": "Deals",
		},
		"pricing": {
			"label": "Pricing Discussion Stage",
			"dt": "CRM Deal",
			"filters": '{"status": ["in", ["Negotiation"]]}',
			"route_name": "Deals",
		},
		"proposal": {
			"label": "Proposal Stage",
			"dt": "CRM Deal",
			"filters": '{"status": ["in", ["Proposal/Quotation"]]}',
			"route_name": "Deals",
		},
		"orderbooking": {
			"label": "Order Booking Stage",
			"dt": "CRM Deal",
			"filters": '{"status": ["in", ["Won"]]}',
			"route_name": "Deals",
		},
	}

	# Map old labels to new labels (handles both legacy SPANCO and Configure-prefixed labels)
	rename_map = [
		(["Suspects", "Configure Lead Stage"], "Lead Stage", "lead"),
		(["Prospects", "Configure Meetings Stage"], "Meetings Stage", "meetings"),
		(["Analysis", "Configure Opportunities Stage"], "Opportunities Stage", "opportunities"),
		(["Commitment", "Configure Trial Stage"], "Trial Stage", "trial"),
		(["Negotiation", "Configure Pricing Discussion Stage"], "Pricing Discussion Stage", "pricing"),
		(["Order", "Configure Order Booking Stage"], "Order Booking Stage", "orderbooking"),
	]

	view_ids = {}

	# Rename legacy SPANCO labels in place to preserve filters, route and flags
	for old_labels, new_label, key in rename_map:
		# Check if new label already exists
		existing_new = frappe.db.get_value("CRM View Settings", {"label": new_label}, "name")
		if existing_new:
			view_ids[key] = existing_new
			continue

		# Check each old label variant and rename the first one found
		for old_label in old_labels:
			existing_old = frappe.db.get_value("CRM View Settings", {"label": old_label}, "name")
			if existing_old:
				doc = frappe.get_doc("CRM View Settings", existing_old)
				doc.label = new_label
				doc.save()
				view_ids[key] = doc.name
				break

	# Create or Update LMOTPO views
	for key, config in lmotpo_views.items():
		doc_name = view_ids.get(key)

		if not doc_name:
			doc_name = frappe.db.get_value(
				"CRM View Settings",
				{"label": config["label"], "dt": config["dt"]},
				"name",
			)

		if doc_name:
			doc = frappe.get_doc("CRM View Settings", doc_name)
			if doc.filters != config["filters"]:
				doc.filters = config["filters"]
				doc.save()
			view_ids[key] = doc.name
		else:
			doc = frappe.new_doc("CRM View Settings")
			doc.label = config["label"]
			doc.dt = config["dt"]
			doc.type = "list"
			doc.route_name = config["route_name"]
			doc.filters = config["filters"]
			doc.is_standard = 1
			doc.public = 1
			doc.insert()
			view_ids[key] = doc.name

	# Update FCRM Settings with the view references
	fcrm_settings = frappe.get_single("FCRM Settings")

	if view_ids.get("lead"):
		fcrm_settings.suspects = view_ids["lead"]
	if view_ids.get("meetings"):
		fcrm_settings.prospects = view_ids["meetings"]
	if view_ids.get("opportunities"):
		fcrm_settings.analysis = view_ids["opportunities"]
	if view_ids.get("trial"):
		fcrm_settings.negotiation = view_ids["trial"]
	if view_ids.get("proposal"):
		fcrm_settings.proposal = view_ids["proposal"]
	if view_ids.get("pricing"):
		fcrm_settings.closed = view_ids["pricing"]
	if view_ids.get("orderbooking"):
		fcrm_settings.order = view_ids["orderbooking"]

	fcrm_settings.save()
