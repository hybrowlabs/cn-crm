# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.document import Document

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)
from crm.api.territory_permissions import has_permission as territory_has_permission


class CRMDeal(Document):
	def before_validate(self):
		self.set_sla()

	def validate(self):
		self.validate_lead_requirement()
		self.validate_eligible_contacts_organizations()
		self.set_primary_contact()
		self.set_primary_email_mobile_no()
		self.validate_territory_access()
		self.auto_set_territory_if_empty()
		self.inherit_lob_from_lead()
		if not self.is_new() and self.has_value_changed("deal_owner") and self.deal_owner:
			self.share_with_agent(self.deal_owner)
			self.assign_agent(self.deal_owner)
		if self.has_value_changed("status"):
			add_status_change_log(self)
		self.validate_forcasting_fields()
		self.validate_lost_reason()

	def validate_lead_requirement(self):
		"""Ensure Lead is required for Deal"""
		if not self.lead:
			frappe.throw(_("Lead is required to create a Deal"), frappe.MandatoryError)

	def validate_eligible_contacts_organizations(self):
		"""Ensure contacts and organization are linked to the same Lead"""
		if not self.lead:
			return

		# Validate organization is linked to the Lead
		if self.organization:
			org_lead = frappe.db.get_value("CRM Organization", self.organization, "lead")
			if org_lead != self.lead:
				frappe.throw(
					_("Organization {0} is not linked to Lead {1}").format(
						frappe.bold(self.organization), frappe.bold(self.lead)
					),
					frappe.ValidationError,
				)

		# Validate contacts are linked to the Lead
		if self.contacts:
			for contact_row in self.contacts:
				if contact_row.contact:
					contact_lead = frappe.db.get_value("Contact", contact_row.contact, "lead")
					if contact_lead != self.lead:
						frappe.throw(
							_("Contact {0} is not linked to Lead {1}").format(
								frappe.bold(contact_row.contact), frappe.bold(self.lead)
							),
							frappe.ValidationError,
						)

	def after_insert(self):
		if self.deal_owner:
			self.assign_agent(self.deal_owner)

	def before_save(self):
		self.apply_sla()

	def set_primary_contact(self, contact=None):
		if not self.contacts:
			return

		if not contact and len(self.contacts) == 1:
			self.contacts[0].is_primary = 1
		elif contact:
			for d in self.contacts:
				if d.contact == contact:
					d.is_primary = 1
				else:
					d.is_primary = 0

	def set_primary_email_mobile_no(self):
		if not self.contacts:
			self.email = ""
			self.mobile_no = ""
			self.phone = ""
			return

		if len([contact for contact in self.contacts if contact.is_primary]) > 1:
			frappe.throw(_("Only one {0} can be set as primary.").format(frappe.bold("Contact")))

		primary_contact_exists = False
		for d in self.contacts:
			if d.is_primary == 1:
				primary_contact_exists = True
				self.email = d.email.strip() if d.email else ""
				self.mobile_no = d.mobile_no.strip() if d.mobile_no else ""
				self.phone = d.phone.strip() if d.phone else ""
				break

		if not primary_contact_exists:
			self.email = ""
			self.mobile_no = ""
			self.phone = ""

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "CRM Deal", "name": self.name}, ignore_permissions=True)

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.share.remove(self.doctype, self.name, user)

	def set_sla(self):
		"""
		Find an SLA to apply to the deal.
		"""
		if self.sla:
			return

		sla = get_sla(self)
		if not sla:
			self.first_responded_on = None
			self.first_response_time = None
			return
		self.sla = sla.name

	def apply_sla(self):
		"""
		Apply SLA if set.
		"""
		if not self.sla:
			return
		sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
		if sla:
			sla.apply(self)

	def update_close_date(self):
		"""
		Update the close date based on the "Won" status.
		"""
		if self.status == "Won" and not self.close_date:
			self.close_date = frappe.utils.nowdate()

	def update_default_probability(self):
		"""
		Update the default probability based on the status.
		"""
		if not self.probability or self.probability == 0:
			self.probability = frappe.db.get_value("CRM Deal Status", self.status, "probability") or 0

	def validate_forcasting_fields(self):
		self.update_close_date()
		self.update_default_probability()
		if frappe.db.get_single_value("FCRM Settings", "enable_forecasting"):
			if not self.deal_value or self.deal_value == 0:
				frappe.throw(_("Deal Value is required."), frappe.MandatoryError)
			if not self.close_date:
				frappe.throw(_("Close Date is required."), frappe.MandatoryError)

	def validate_lost_reason(self):
		"""
		Validate the lost reason if the status is set to "Lost".
		"""
		if self.status == "Lost":
			if not self.lost_reason:
				frappe.throw(_("Please specify a reason for losing the deal."), frappe.ValidationError)
			elif self.lost_reason == "Other" and not self.lost_notes:
				frappe.throw(_("Please specify the reason for losing the deal."), frappe.ValidationError)

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Organization",
				"type": "Link",
				"key": "organization",
				"options": "CRM Organization",
				"width": "11rem",
			},
			{
				"label": "Annual Revenue",
				"type": "Currency",
				"key": "annual_revenue",
				"align": "right",
				"width": "9rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "10rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email",
				"width": "12rem",
			},
			{
				"label": "Mobile No",
				"type": "Data",
				"key": "mobile_no",
				"width": "11rem",
			},
			{
				"label": "Assigned To",
				"type": "Text",
				"key": "_assign",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"organization",
			"annual_revenue",
			"status",
			"email",
			"currency",
			"mobile_no",
			"deal_owner",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"modified",
			"_assign",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "organization",
			"kanban_fields": '["annual_revenue", "email", "mobile_no", "_assign", "modified"]',
		}

	def validate_territory_access(self):
		"""
		Validate that current user has access to the assigned territory.
		"""
		if not self.territory:
			return

		# Skip validation for System Manager or during data import
		if (frappe.session.user == "Administrator" or
			"System Manager" in frappe.get_roles() or
			self.flags.ignore_permissions):
			return

		# Check if user has access to this territory
		if not territory_has_permission(self, frappe.session.user):
			frappe.throw(
				_("You do not have permission to access territory {0}").format(
					frappe.bold(self.territory)
				),
				frappe.PermissionError
			)

	def auto_set_territory_if_empty(self):
		"""
		Auto-assign territory to the deal based on user's primary territory if empty.
		Inherit from lead if available, otherwise use user's territory.
		"""
		if self.territory or self.flags.ignore_permissions:
			return

		# First try to inherit territory from lead
		if self.lead:
			lead_territory = frappe.db.get_value("CRM Lead", self.lead, "territory")
			if lead_territory:
				self.territory = lead_territory
				return

		# Get user's territories as fallback
		from crm.api.territory_permissions import get_user_territories
		user_territories = get_user_territories(frappe.session.user)

		if user_territories:
			# Assign first territory (primary territory)
			self.territory = user_territories[0]

	def inherit_lob_from_lead(self):
		"""
		Inherit Line of Business from linked Lead if not already set.
		Ensures LoB consistency across Lead-Deal relationship.
		"""
		if not self.lead:
			return

		# If LoB is already set, don't override
		if self.line_of_business:
			return

		try:
			# Get LoB from linked lead
			lead_lob = frappe.db.get_value("CRM Lead", self.lead, "line_of_business")
			if lead_lob:
				self.line_of_business = lead_lob
				frappe.logger().info(f"Deal {self.name}: Inherited LoB '{lead_lob}' from Lead {self.lead}")
			else:
				frappe.logger().info(f"Deal {self.name}: Lead {self.lead} has no LoB to inherit")

		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error inheriting LoB from Lead {self.lead} to Deal {self.name}"
			)
			# Don't throw error - just log it and continue

	def has_permission(self, user=None, permission_type=None):
		"""
		Custom permission check for CRM Deal based on territory.
		"""
		return territory_has_permission(self, user, permission_type)


@frappe.whitelist()
def add_contact(deal, contact):
	if not frappe.has_permission("CRM Deal", "write", deal):
		frappe.throw(_("Not allowed to add contact to Deal"), frappe.PermissionError)

	deal = frappe.get_cached_doc("CRM Deal", deal)
	deal.append("contacts", {"contact": contact})
	deal.save()
	return True


@frappe.whitelist()
def remove_contact(deal, contact):
	if not frappe.has_permission("CRM Deal", "write", deal):
		frappe.throw(_("Not allowed to remove contact from Deal"), frappe.PermissionError)

	deal = frappe.get_cached_doc("CRM Deal", deal)
	deal.contacts = [d for d in deal.contacts if d.contact != contact]
	deal.save()
	return True


@frappe.whitelist()
def set_primary_contact(deal, contact):
	if not frappe.has_permission("CRM Deal", "write", deal):
		frappe.throw(_("Not allowed to set primary contact for Deal"), frappe.PermissionError)

	deal = frappe.get_cached_doc("CRM Deal", deal)
	deal.set_primary_contact(contact)
	deal.save()
	return True


def create_organization(doc):
	if not doc.get("organization_name"):
		return

	existing_organization = frappe.db.exists(
		"CRM Organization", {"organization_name": doc.get("organization_name")}
	)
	if existing_organization:
		return existing_organization

	organization = frappe.new_doc("CRM Organization")
	org_data = {
		"organization_name": doc.get("organization_name"),
		"website": doc.get("website"),
		"territory": doc.get("territory"),
		"industry": doc.get("industry"),
		"annual_revenue": doc.get("annual_revenue"),
	}
	
	# Add lead if provided
	if doc.get("lead"):
		org_data["lead"] = doc.get("lead")
	
	organization.update(org_data)
	organization.insert(ignore_permissions=True)
	return organization.name


def contact_exists(doc):
	email_exist = frappe.db.exists("Contact Email", {"email_id": doc.get("email")})
	mobile_exist = frappe.db.exists("Contact Phone", {"phone": doc.get("mobile_no")})

	doctype = "Contact Email" if email_exist else "Contact Phone"
	name = email_exist or mobile_exist

	if name:
		return frappe.db.get_value(doctype, name, "parent")

	return False


def create_contact(doc):
	existing_contact = contact_exists(doc)
	if existing_contact:
		return existing_contact

	contact = frappe.new_doc("Contact")
	contact_data = {
		"first_name": doc.get("first_name"),
		"last_name": doc.get("last_name"),
		"salutation": doc.get("salutation"),
		"company_name": doc.get("organization") or doc.get("organization_name"),
	}
	
	# Add lead if provided
	if doc.get("lead"):
		contact_data["lead"] = doc.get("lead")
	
	contact.update(contact_data)

	if doc.get("email"):
		contact.append("email_ids", {"email_id": doc.get("email"), "is_primary": 1})

	if doc.get("mobile_no"):
		contact.append("phone_nos", {"phone": doc.get("mobile_no"), "is_primary_mobile_no": 1})

	contact.insert(ignore_permissions=True)
	contact.reload()  # load changes by hooks on contact

	return contact.name


@frappe.whitelist()
def create_deal(args):
	deal = frappe.new_doc("CRM Deal")

	# Validate lead is provided
	if not args.get("lead"):
		frappe.throw(_("Lead is required to create a Deal"), frappe.MandatoryError)

	lead = args.get("lead")

	contact = args.get("contact")
	if not contact and (
		args.get("first_name") or args.get("last_name") or args.get("email") or args.get("mobile_no")
	):
		# Create contact with lead reference
		contact_args = args.copy()
		contact_args["lead"] = lead
		contact = create_contact(contact_args)

	# Validate organization is eligible (linked to lead)
	organization = args.get("organization")
	if organization:
		org_lead = frappe.db.get_value("CRM Organization", organization, "lead")
		if org_lead != lead:
			frappe.throw(
				_("Organization {0} is not linked to Lead {1}").format(
					frappe.bold(organization), frappe.bold(lead)
				),
				frappe.ValidationError,
			)
	else:
		# Create organization with lead reference
		org_args = args.copy()
		org_args["lead"] = lead
		organization = create_organization(org_args)

	# Validate contact is eligible (linked to lead)
	if contact:
		contact_lead = frappe.db.get_value("Contact", contact, "lead")
		if contact_lead != lead:
			frappe.throw(
				_("Contact {0} is not linked to Lead {1}").format(
					frappe.bold(contact), frappe.bold(lead)
				),
				frappe.ValidationError,
			)

	deal.update(
		{
			"lead": lead,
			"organization": organization,
			"contacts": [{"contact": contact, "is_primary": 1}] if contact else [],
		}
	)

	args.pop("organization", None)

	deal.update(args)

	deal.insert(ignore_permissions=True)
	return deal.name


@frappe.whitelist()
def get_deals_data():
	return frappe.get_all(
		"CRM Deal",
		fields=["status", "annual_revenue"],
		filters={}
	)