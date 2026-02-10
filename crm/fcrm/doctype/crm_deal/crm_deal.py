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
		# Lead is optional - deals can be created directly without a lead
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
		self.validate_stage_gates()

	def validate_stage_gates(self):
		"""
		Enforce qualification gates between stages.
		"""
		# Gate 1: Meeting -> Application (Opportunity)
		# Enforce when entering Qualification stage or later, IF a lead is linked
		# (Deals can be created without leads, but if lead exists, gate applies)
		if self.lead and self.status not in ["Lost"]:
			self.validate_meeting_to_opportunity_gate()

		# Gate 2: Opportunity -> Trial
		if self.status == "Demo/Making":
			self.validate_opportunity_to_trial_gate()

		# Gate 3: Trial -> Proposal
		# Enforced when moving to Proposal or later stages
		if self.status in ["Proposal/Quotation", "Negotiation", "Ready to Close", "Won"]:
			# Ensure we passed the trial gate if we were previously in trial or just enforce if fields are missing?
			# The requirement is "Proposal allowed only if: Trial completed, Outcome documented, Outcome = Pass"
			# This implies we must have had a trial.
			# But what if we skip trial? "No proposal without trial" is a rule.
			self.validate_trial_to_proposal_gate()

	def validate_meeting_to_opportunity_gate(self):
		"""
		Meeting -> Qualified Opportunity Gate:
		Opportunity can be created only if ALL are true:
		- Pain category selected (on meeting)
		- Pain clearly described (on meeting)
		- Volume range entered (on meeting)
		- Customer Role Type is 'Decision Maker' or 'Purchaser' (on meeting)
		"""
		# Find at least one valid meeting
		meetings = frappe.get_all(
			"CRM Site Visit",
			filters={
				"reference_type": "CRM Lead",
				"reference_name": self.lead,
				"docstatus": 1, # Submitted/Completed? Or just saved? Let's assume saved (0 or 1)
			},
			fields=[
				"primary_pain_category",
				"pain_description",
				"volume_rangekg",
				"customer_role_type"
			]
		)

		valid_meeting_found = False
		for m in meetings:
			if (m.primary_pain_category and
				m.pain_description and
				m.volume_rangekg and
				m.customer_role_type in ["Decision Maker", "Purchaser"]):
				valid_meeting_found = True
				break

		# If no meeting found at all, strictly block?
		# Blueprint says: "Meeting -> Qualified Opportunity (Gate)... Opportunity can be created only if..."
		if not meetings:
			# If no meetings at all, we can't have passed the gate
			# Allow exemption if manually created without lead? No, logic above checks self.lead
			frappe.throw(
				_("Cannot create Opportunity. No Site Visit found for Lead {0}.").format(
					frappe.bold(self.lead)
				),
				frappe.ValidationError
			)

		if not valid_meeting_found:
			frappe.throw(
				_("Cannot create Opportunity. No valid Site Visit found with required qualification criteria (Pain, Volume, Decision Maker/Purchaser role)."),
				frappe.ValidationError
			)

	def validate_opportunity_to_trial_gate(self):
		"""
		Opportunity -> Trial Gate:
		Trial allowed only if:
		- Product selected
		- Trial volume defined
		- Trial success criteria agreed
		- Trial timeline agreed
		"""
		missing = []
		if not self.product_alloy_type: missing.append(_("Product / Alloy Type"))
		if not self.trial_volume: missing.append(_("Trial Volume"))
		if not self.trial_success_criteria: missing.append(_("Trial Success Criteria"))
		if not self.trial_start_date: missing.append(_("Trial Start Date"))
		if not self.trial_end_date: missing.append(_("Trial End Date"))

		if missing:
			frappe.throw(
				_("Cannot move to Trial stage. Missing mandatory fields: {0}").format(
					", ".join(missing)
				),
				frappe.ValidationError
			)

	def validate_trial_to_proposal_gate(self):
		"""
		Trial -> Proposal Gate:
		Proposal allowed only if:
		- Trial completed
		- Outcome documented
		- Outcome = Pass
		"""
		# If we are effectively skipping trial stage in the UI, we might not have these filled.
		# But the rule "No proposal without trial" enforces this.
		
		# Check if outcome is filled
		if not self.trial_outcome:
			frappe.throw(
				_("Cannot move to Proposal. Trial Outcome must be documented."),
				frappe.ValidationError
			)

		if not self.trial_outcome_notes:
			frappe.throw(
				_("Cannot move to Proposal. Trial Outcome Notes are required."),
				frappe.ValidationError
			)

		if self.trial_outcome != "Pass":
			frappe.throw(
				_("Cannot move to Proposal. Trial Outcome must be 'Pass'."),
				frappe.ValidationError
			)

	def validate_eligible_contacts_organizations(self):
		"""Ensure contacts and organization are linked to the same Lead (if lead is provided)"""
		# Skip validation if no lead is linked - deals can exist without leads
		if not self.lead:
			return

		# Validate organization is linked to the Lead
		if self.organization:
			org_lead = frappe.db.get_value("CRM Organization", self.organization, "lead")
			if org_lead and org_lead != self.lead:
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
					if contact_lead and contact_lead != self.lead:
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

	# Lead is optional - deals can be created without a lead
	lead = args.get("lead")

	contact = args.get("contact")
	if not contact and (
		args.get("first_name") or args.get("last_name") or args.get("email") or args.get("mobile_no")
	):
		# Create contact (with lead reference if provided)
		contact_args = args.copy()
		if lead:
			contact_args["lead"] = lead
		contact = create_contact(contact_args)

	# Get or create organization
	organization = args.get("organization")
	if organization and lead:
		# Validate organization is linked to lead (only if both are provided)
		org_lead = frappe.db.get_value("CRM Organization", organization, "lead")
		if org_lead and org_lead != lead:
			frappe.throw(
				_("Organization {0} is not linked to Lead {1}").format(
					frappe.bold(organization), frappe.bold(lead)
				),
				frappe.ValidationError,
			)
	elif not organization:
		# Create organization (with lead reference if provided)
		org_args = args.copy()
		if lead:
			org_args["lead"] = lead
		organization = create_organization(org_args)

	# Validate contact is linked to lead (only if both are provided)
	if contact and lead:
		contact_lead = frappe.db.get_value("Contact", contact, "lead")
		if contact_lead and contact_lead != lead:
			frappe.throw(
				_("Contact {0} is not linked to Lead {1}").format(
					frappe.bold(contact), frappe.bold(lead)
				),
				frappe.ValidationError,
			)

	deal_data = {
		"organization": organization,
		"contacts": [{"contact": contact, "is_primary": 1}] if contact else [],
	}

	# Only set lead if provided
	if lead:
		deal_data["lead"] = lead

	deal.update(deal_data)

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