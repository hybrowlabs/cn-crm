# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMLineofBusiness(Document):
	def validate(self):
		"""Validate Line of Business document"""
		self.validate_circular_parent_reference()
		self.validate_unique_lob_code()

	def validate_circular_parent_reference(self):
		"""Prevent circular parent references"""
		if not self.parent_lob:
			return

		if self.parent_lob == self.name:
			frappe.throw(_("Line of Business cannot be its own parent"))

		# Check for circular reference up the hierarchy
		parent = self.parent_lob
		visited = set([self.name])

		while parent:
			if parent in visited:
				frappe.throw(
					_("Circular reference detected in parent LOB hierarchy"),
					title=_("Invalid Parent LOB")
				)

			visited.add(parent)
			parent_doc = frappe.get_cached_value("CRM Line of Business", parent, "parent_lob")
			parent = parent_doc

	def validate_unique_lob_code(self):
		"""Ensure LOB code is unique"""
		if not self.is_new():
			return

		if frappe.db.exists("CRM Line of Business", {"lob_code": self.lob_code, "name": ["!=", self.name]}):
			frappe.throw(
				_("Line of Business with code {0} already exists").format(frappe.bold(self.lob_code)),
				title=_("Duplicate LOB Code")
			)


@frappe.whitelist()
def get_service_engineers(lob_name):
	"""
	Get list of service engineers for a specific Line of Business

	Args:
		lob_name (str): Name/Code of the Line of Business

	Returns:
		list: List of service engineers with their details
	"""
	if not lob_name:
		return []

	try:
		lob = frappe.get_doc("CRM Line of Business", lob_name)

		if not lob.is_active:
			frappe.msgprint(
				_("Line of Business {0} is inactive").format(lob_name),
				indicator="orange",
				alert=True
			)
			return []

		engineers = []
		for row in lob.service_engineers:
			engineers.append({
				"service_engineer": row.service_engineer,
				"is_primary": row.is_primary,
				"expertise_level": row.expertise_level
			})

		return engineers

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Service Engineers Error")
		return []


@frappe.whitelist()
def get_active_lobs():
	"""
	Get list of all active Lines of Business

	Returns:
		list: List of active LOBs with code and name
	"""
	return frappe.get_all(
		"CRM Line of Business",
		filters={"is_active": 1},
		fields=["name", "lob_code", "lob_name", "display_order"],
		order_by="display_order asc, lob_name asc"
	)
