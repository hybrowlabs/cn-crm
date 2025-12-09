# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMDashboard(Document):
	def validate(self):
		"""Validate dashboard configuration"""
		self.validate_default_dashboard()
		self.validate_widgets()
	
	def validate_default_dashboard(self):
		"""Ensure only one default dashboard per user"""
		if self.is_default:
			# Unset other default dashboards for this user
			frappe.db.sql("""
				UPDATE `tabCRM Dashboard`
				SET is_default = 0
				WHERE owner = %s AND name != %s AND is_default = 1
			""", (frappe.session.user, self.name))
	
	def validate_widgets(self):
		"""Validate widget configurations"""
		for widget in self.widgets:
			if widget.widget_type == 'KPI' and not widget.metric_field:
				frappe.throw(f"Metric Field is required for KPI widget: {widget.widget_title}")
			
			if widget.widget_type == 'Chart':
				if not widget.chart_type:
					frappe.throw(f"Chart Type is required for Chart widget: {widget.widget_title}")
				if not widget.x_axis_field or not widget.y_axis_field:
					frappe.throw(f"X Axis and Y Axis fields are required for Chart widget: {widget.widget_title}")
			
			if widget.widget_type == 'Table' and not widget.table_columns:
				frappe.throw(f"Table Columns are required for Table widget: {widget.widget_title}")

