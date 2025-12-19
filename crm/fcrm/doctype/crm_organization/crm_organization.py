# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, get_datetime


class CRMOrganization(Document):
	def validate(self):
		self.validate_lead_requirement()
		self.auto_fetch_gstin_details()

	def validate_lead_requirement(self):
		"""Ensure Lead is required for new organizations"""
		if self.is_new() and not self.lead:
			frappe.throw(_("Lead is required to create an Organization"), frappe.MandatoryError)

	def auto_fetch_gstin_details(self):
		"""Automatically fetch and populate organization details from GSTIN"""
		# Only fetch if GSTIN is provided and changed
		if not self.custom_gstin:
			return

		# Check if GSTIN has changed
		if not self.is_new():
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.custom_gstin == self.custom_gstin:
				# GSTIN hasn't changed, skip fetch
				return

		try:
			from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import fetch_gstin_details

			result = fetch_gstin_details(self.custom_gstin)

			if result.get("success") and result.get("data"):
				gstin_data = result["data"]

				# Auto-populate organization name if empty
				if not self.organization_name and gstin_data.get("organization"):
					self.organization_name = gstin_data["organization"]
					frappe.msgprint(
						_("Organization name auto-filled from GSTIN: {0}").format(self.organization_name),
						indicator="green",
						alert=True
					)

				# Note: We don't have company_type field in CRM Organization
				# If needed, it can be added as a custom field

		except Exception as e:
			# Don't block save if GSTIN fetch fails
			frappe.log_error(
				frappe.get_traceback(),
				f"Auto GSTIN Fetch Failed for {self.name}"
			)
			# Show warning but don't throw
			frappe.msgprint(
				_("Could not fetch details from GSTIN: {0}").format(str(e)),
				indicator="orange",
				alert=True
			)

	@staticmethod
	def default_list_data():
			columns = [
				{
					'label': 'Organization',
					'type': 'Data',
					'key': 'organization_name',
					'width': '16rem',
				},
				{
					'label': 'GSTIN',
					'type': 'Data',
					'key': 'custom_gstin',
					'width': '14rem',
				},
				{
					'label': 'Industry',
					'type': 'Link',
					'key': 'industry',
					'options': 'CRM Industry',
					'width': '14rem',
				},
				{
					'label': 'Annual Revenue',
					'type': 'Currency',
					'key': 'annual_revenue',
					'width': '14rem',
				},
				{
					'label': 'Last Modified',
					'type': 'Datetime',
					'key': 'modified',
					'width': '8rem',
				},
			]
			rows = [
				"name",
				"custom_gstin",
				"organization_name",
				"organization_logo",
				"website",
				"industry",
				"currency",
				"annual_revenue",
				"modified",
			]
			return {'columns': columns, 'rows': rows}

	def update_dormancy_status(self):
		"""
		Update the dormancy status based on ERPNext customer transactions.

		Logic:
		1. Find all CRM Deals linked to this organization
		2. Find all ERPNext Customers created from those deals
		3. Check last Sales Order date for each customer
		4. Mark as dormant if no SO in last X days (from FCRM Settings)
		"""
		try:
			# Get dormant timespan from FCRM Settings
			fcrm_settings = frappe.get_single("FCRM Settings")
			dormant_days = fcrm_settings.dormant_customers_timespan or 90

			# Calculate cutoff date
			cutoff_date = add_days(now_datetime(), -dormant_days)

			# Get all deals for this organization
			deals = frappe.get_all(
				"CRM Deal",
				filters={"organization": self.name},
				pluck="name"
			)

			if not deals:
				# No deals, cannot determine dormancy
				self.is_dormant = 0
				self.last_transaction_date = None
				return

			# Check if ERPNext is installed
			if "erpnext" not in frappe.get_installed_apps():
				# ERPNext not installed, cannot check transactions
				return

			# Get all customers created from these deals
			customers = frappe.get_all(
				"Customer",
				filters={"crm_deal": ["in", deals]},
				pluck="name"
			)

			if not customers:
				# No customers created yet, not dormant
				self.is_dormant = 0
				self.last_transaction_date = None
				return

			# Find the latest Sales Order for these customers
			latest_so = frappe.db.sql("""
				SELECT
					MAX(transaction_date) as last_order_date
				FROM `tabSales Order`
				WHERE customer IN %(customers)s
				AND docstatus = 0
			""", {"customers": customers}, as_dict=True)

			last_order_date = latest_so[0].last_order_date if latest_so and latest_so[0].last_order_date else None

			if last_order_date:
				self.last_transaction_date = get_datetime(last_order_date)
				# Check if customer is dormant
				if get_datetime(last_order_date) < cutoff_date:
					self.is_dormant = 1
				else:
					self.is_dormant = 0
			else:
				# No sales orders found, mark as dormant
				self.is_dormant = 1
				self.last_transaction_date = None

		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error updating dormancy status for {self.name}"
			)


@frappe.whitelist()
def update_dormancy_status_for_organization(organization_name):
	"""
	API method to manually update dormancy status for a specific organization.
	"""
	try:
		org = frappe.get_doc("CRM Organization", organization_name)
		org.update_dormancy_status()
		org.save(ignore_permissions=True)

		frappe.db.commit()

		return {
			"success": True,
			"is_dormant": org.is_dormant,
			"last_transaction_date": org.last_transaction_date,
			"message": _("Dormancy status updated successfully")
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Update Dormancy Status Error")
		return {
			"success": False,
			"message": str(e)
		}


def update_all_organizations_dormancy_status():
	"""
	Background job to update dormancy status for all organizations.
	This should be run daily via scheduler.
	"""
	organizations = frappe.get_all("CRM Organization", pluck="name")

	success_count = 0
	error_count = 0

	for org_name in organizations:
		try:
			org = frappe.get_doc("CRM Organization", org_name)
			org.update_dormancy_status()
			org.save(ignore_permissions=True)
			frappe.db.commit()
			success_count += 1
		except Exception as e:
			error_count += 1
			frappe.log_error(
				frappe.get_traceback(),
				f"Dormancy Update Failed for {org_name}"
			)

	frappe.logger().info(
		f"Dormancy status updated: {success_count} successful, {error_count} failed"
	)
