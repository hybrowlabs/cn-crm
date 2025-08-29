# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMFormScript(Document):
	def validate(self):
		in_user_env = not (
			frappe.flags.in_install
			or frappe.flags.in_patch
			or frappe.flags.in_test
			or frappe.flags.in_fixtures
		)
		if in_user_env and not self.is_new() and self.is_standard and not frappe.conf.developer_mode:
			# only enabled can be changed for standard form scripts
			if self.has_value_changed("enabled"):
				enabled_value = self.enabled
				self.reload()
				self.enabled = enabled_value
			else:
				frappe.throw(_("You need to be in developer mode to edit a Standard Form Script"))
	
	def on_update(self):
		self.clear_cache()
	
	def on_trash(self):
		self.clear_cache()
	
	def clear_cache(self):
		"""Clear cache for this form script"""
		cache_key = f"form_script:{self.dt}:{self.view}"
		frappe.cache().delete_value(cache_key)

def get_form_script(dt, view="Form"):
	"""Returns the form script for the given doctype"""
	# Create cache key
	cache_key = f"form_script:{dt}:{view}"
	
	# Try to get from cache first
	cached_result = frappe.cache().get_value(cache_key)
	if cached_result is not None:
		return cached_result
	
	FormScript = frappe.qb.DocType("CRM Form Script")
	query = (
		frappe.qb.from_(FormScript)
		.select("script")
		.where(FormScript.dt == dt)
		.where(FormScript.view == view)
		.where(FormScript.enabled == 1)
	)

	doc = query.run(as_dict=True)
	result = None
	if doc:
		result = [d.script for d in doc] if len(doc) > 1 else doc[0].script
	
	# Cache the result for 10 minutes (600 seconds)
	frappe.cache().set_value(cache_key, result, expires_in_sec=600)
	
	return result
