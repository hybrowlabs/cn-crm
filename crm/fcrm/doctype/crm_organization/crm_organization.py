# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMOrganization(Document):
	def validate(self):
		self.auto_fetch_gstin_details()

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
