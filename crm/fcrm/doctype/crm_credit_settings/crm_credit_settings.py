# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMCreditSettings(Document):
	def validate(self):
		"""Validate credit settings"""
		if self.enabled:
			self.validate_credit_limits()
			self.validate_approval_limits()
			self.validate_roles()

	def validate_credit_limits(self):
		"""Validate credit limit configurations"""
		if self.default_credit_limit and self.max_credit_limit:
			if self.default_credit_limit > self.max_credit_limit:
				frappe.throw(_("Default Credit Limit cannot be greater than Maximum Credit Limit"))

	def validate_approval_limits(self):
		"""Validate credit approval limit configurations"""
		if self.auto_approval_limit and self.require_approval_above:
			if self.auto_approval_limit >= self.require_approval_above:
				frappe.throw(_("Auto Approval Limit must be less than Require Approval Above limit"))

	def validate_roles(self):
		"""Validate that credit roles exist"""
		if self.credit_manager_role and not frappe.db.exists("Role", self.credit_manager_role):
			frappe.throw(_("Credit Manager Role '{0}' does not exist").format(self.credit_manager_role))

		if self.credit_analyst_role and not frappe.db.exists("Role", self.credit_analyst_role):
			frappe.throw(_("Credit Analyst Role '{0}' does not exist").format(self.credit_analyst_role))

	@frappe.whitelist()
	def create_credit_roles(self):
		"""Create default credit management roles"""
		roles_created = []

		# Create Credit Manager role
		if not frappe.db.exists("Role", "Credit Manager"):
			credit_manager = frappe.get_doc({
				"doctype": "Role",
				"role_name": "Credit Manager",
				"desk_access": 1
			})
			credit_manager.insert()
			roles_created.append("Credit Manager")

		# Create Credit Analyst role
		if not frappe.db.exists("Role", "Credit Analyst"):
			credit_analyst = frappe.get_doc({
				"doctype": "Role",
				"role_name": "Credit Analyst",
				"desk_access": 1
			})
			credit_analyst.insert()
			roles_created.append("Credit Analyst")

		# Set default roles in settings
		if roles_created:
			if "Credit Manager" in roles_created:
				self.credit_manager_role = "Credit Manager"
			if "Credit Analyst" in roles_created:
				self.credit_analyst_role = "Credit Analyst"
			self.save()

		return {
			"success": True,
			"roles_created": roles_created,
			"message": _("Credit roles created successfully: {0}").format(", ".join(roles_created)) if roles_created else _("Credit roles already exist")
		}


@frappe.whitelist()
def get_credit_settings():
	"""Get current credit settings"""
	try:
		settings = frappe.get_single("CRM Credit Settings")
		return {
			"success": True,
			"settings": settings.as_dict() if settings else {},
			"enabled": settings.enabled if settings else False
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error fetching credit settings")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def check_credit_limit_approval_required(credit_limit):
	"""Check if credit limit requires approval based on settings"""
	try:
		settings = frappe.get_single("CRM Credit Settings")
		if not settings or not settings.enabled:
			return {
				"success": True,
				"approval_required": False,
				"message": "Credit management not enabled"
			}

		credit_limit = float(credit_limit or 0)
		require_approval_above = float(settings.require_approval_above or 0)

		approval_required = credit_limit > require_approval_above

		return {
			"success": True,
			"approval_required": approval_required,
			"auto_approval_limit": settings.auto_approval_limit,
			"require_approval_above": settings.require_approval_above,
			"message": "Approval required" if approval_required else "Auto approved"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error checking credit approval requirement")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def validate_user_credit_permissions(user=None):
	"""Check if user has credit management permissions"""
	try:
		if not user:
			user = frappe.session.user

		settings = frappe.get_single("CRM Credit Settings")
		if not settings or not settings.enabled:
			return {
				"success": True,
				"has_credit_manager_role": False,
				"has_credit_analyst_role": False,
				"can_override_credit": False
			}

		user_roles = frappe.get_roles(user)
		has_credit_manager = settings.credit_manager_role in user_roles
		has_credit_analyst = settings.credit_analyst_role in user_roles
		can_override = has_credit_manager and settings.allow_credit_override

		return {
			"success": True,
			"has_credit_manager_role": has_credit_manager,
			"has_credit_analyst_role": has_credit_analyst,
			"can_override_credit": can_override,
			"user_roles": user_roles
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error validating user credit permissions")
		return {
			"success": False,
			"error": str(e)
		}