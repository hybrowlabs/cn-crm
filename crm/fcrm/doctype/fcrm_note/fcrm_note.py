# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FCRMNote(Document):
	def validate(self):
		self.validate_lead_reference()

	def validate_lead_reference(self):
		"""Ensure Note only references CRM Lead"""
		if self.reference_doctype and self.reference_doctype != "CRM Lead":
			frappe.throw(
				_("Note can only reference CRM Lead. Current reference: {0}").format(
					frappe.bold(self.reference_doctype)
				),
				frappe.ValidationError,
			)
	@staticmethod
	def default_list_data():
		rows = [
			"name",
			"title",
			"content",
			"reference_doctype",
			"reference_docname",
			"owner",
			"modified",
		]
		return {'columns': [], 'rows': rows}
