import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import Contact


class CustomContact(Contact):
	def validate(self):
		super().validate()
		self.validate_lead_requirement()

	def validate_lead_requirement(self):
		"""Ensure Lead is required for new contacts"""
		if self.is_new() and not self.lead:
			frappe.throw(_("Lead is required to create a Contact"), frappe.MandatoryError)

	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Name',
				'type': 'Data',
				'key': 'full_name',
				'width': '17rem',
			},
			{
				'label': 'Email',
				'type': 'Data',
				'key': 'email_id',
				'width': '12rem',
			},
			{
				'label': 'Phone',
				'type': 'Data',
				'key': 'mobile_no',
				'width': '12rem',
			},
			{
				'label': 'Organization',
				'type': 'Data',
				'key': 'company_name',
				'width': '12rem',
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
			"full_name",
			"company_name",
			"email_id",
			"mobile_no",
			"modified",
			"image",
		]
		return {'columns': columns, 'rows': rows}
