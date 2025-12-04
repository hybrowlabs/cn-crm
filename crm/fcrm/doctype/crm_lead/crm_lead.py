# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.document import Document
from frappe.utils import has_gravatar, validate_email_address

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)


class CRMLead(Document):
	def before_validate(self):
		self.set_sla()

	def validate(self):
		self.validate_mandatory_fields()
		self.set_full_name()
		self.set_lead_name()
		self.set_title()
		self.validate_email()
		self.validate_gst_number()
		self.auto_fetch_gstin_details()
		if not self.is_new() and self.has_value_changed("lead_owner") and self.lead_owner:
			self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)
		if self.has_value_changed("status"):
			add_status_change_log(self)

	def validate_mandatory_fields(self):
		"""Explicitly validate mandatory fields to ensure they are not bypassed"""
		# Validate first_name: either first_name OR organization OR email must be present
		if not self.first_name and not self.organization and not self.email:
			frappe.throw(
				_("Please provide either First Name, Organization, or Email"),
				title=_("Missing Required Information")
			)

		# Validate status: must always be present
		if not self.status:
			frappe.throw(
				_("Status is mandatory"),
				title=_("Missing Status")
			)

		# Validate GST Number when GST Applicable is checked
		if hasattr(self, 'gst_applicable') and self.gst_applicable:
			if not hasattr(self, 'gst_number') or not self.gst_number:
				frappe.throw(
					_("GST Number is mandatory when GST Applicable is checked"),
					title=_("Missing GST Number")
				)

		# Validate lead_owner if set in meta
		if hasattr(self.meta, 'get_field') and self.meta.get_field('lead_owner'):
			if self.meta.get_field('lead_owner').reqd and not self.lead_owner:
				frappe.throw(
					_("Lead Owner is mandatory"),
					title=_("Missing Lead Owner")
				)

	def after_insert(self):
		if self.lead_owner:
			self.assign_agent(self.lead_owner)

	def before_save(self):
		self.apply_sla()

	def set_full_name(self):
		if self.first_name:
			self.lead_name = " ".join(
				filter(
					None,
					[
						self.salutation,
						self.first_name,
						self.middle_name,
						self.last_name,
					],
				)
			)

	def set_lead_name(self):
		if not self.lead_name:
			# Check for leads being created through data import
			if not self.organization and not self.email and not self.flags.ignore_mandatory:
				frappe.throw(_("A Lead requires either a person's name or an organization's name"))
			elif self.organization:
				self.lead_name = self.organization
			elif self.email:
				self.lead_name = self.email.split("@")[0]
			else:
				self.lead_name = "Unnamed Lead"

	def set_title(self):
		self.title = self.organization or self.lead_name

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email)

	def validate_gst_number(self):
		"""Validate GST number format and check for duplicates"""
		# Check if gst_applicable field exists (will be added via migration)
		if not hasattr(self, 'gst_applicable'):
			return

		if self.gst_applicable and self.gst_number:
			from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
				validate_deal_gstin,
				check_gstin_duplicates
			)

			# Validate GSTIN format and check digit
			result = validate_deal_gstin(self.gst_number)

			if not result['is_valid']:
				frappe.throw(
					_(result['error_message']),
					title=_("Invalid GST Number")
				)

			# Display warning if using basic validation only
			if result['warning_message']:
				frappe.msgprint(
					_(result['warning_message']),
					indicator='orange',
					alert=True
				)

			# Check for duplicates
			duplicates = check_gstin_duplicates(
				self.gst_number,
				exclude_doctype="CRM Lead",
				exclude_name=self.name
			)

			if duplicates:
				# Format duplicate message
				dup_list = "\n".join([
					f"- {d['doctype']}: {d['name']} ({d['display_name']})"
					for d in duplicates
				])

				frappe.throw(
					_(f"GST Number {self.gst_number} already exists in:\n{dup_list}"),
					title=_("Duplicate GST Number Found")
				)

	def auto_fetch_gstin_details(self):
		"""Automatically fetch and populate organization details from GSTIN"""
		# Only fetch if GST is applicable and GST number is provided
		if not hasattr(self, 'gst_applicable') or not self.gst_applicable:
			return

		if not hasattr(self, 'gst_number') or not self.gst_number:
			return

		# Check if GST number has changed
		if not self.is_new():
			old_doc = self.get_doc_before_save()
			if old_doc and old_doc.gst_number == self.gst_number:
				# GST number hasn't changed, skip fetch
				return

		try:
			from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import fetch_gstin_details

			result = fetch_gstin_details(self.gst_number)

			if result.get("success") and result.get("data"):
				gstin_data = result["data"]
				updated_fields = []

				# Auto-populate organization name if empty
				if not self.organization and gstin_data.get("organization"):
					self.organization = gstin_data["organization"]
					updated_fields.append("Organization")

				# Auto-populate company type if empty
				if not self.company_type and gstin_data.get("company_type"):
					self.company_type = gstin_data["company_type"]
					updated_fields.append("Company Type")

				# Show success message if any fields were updated
				if updated_fields:
					frappe.msgprint(
						_("Auto-filled from GSTIN: {0}").format(", ".join(updated_fields)),
						indicator="green",
						alert=True
					)

		except Exception as e:
			# Don't block save if GSTIN fetch fails
			frappe.log_error(
				frappe.get_traceback(),
				f"Auto GSTIN Fetch Failed for Lead {self.name}"
			)
			# Show warning but don't throw
			frappe.msgprint(
				_("Could not fetch details from GSTIN: {0}").format(str(e)),
				indicator="orange",
				alert=True
			)

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "CRM Lead", "name": self.name})

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

	def create_contact(self, existing_contact=None, throw=True):
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		existing_contact = existing_contact or self.contact_exists(throw)
		if existing_contact:
			self.update_lead_contact(existing_contact)
			return existing_contact

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"salutation": self.salutation,
				"gender": self.gender,
				"designation": self.job_title,
				"company_name": self.organization,
				"image": self.image or "",
				"lead": self.name,
			}
		)

		if self.email:
			contact.append("email_ids", {"email_id": self.email, "is_primary": 1})

		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		contact.reload()  # load changes by hooks on contact

		return contact.name

	def create_organization(self, existing_organization=None):
		if not self.organization and not existing_organization:
			return

		existing_organization = existing_organization or frappe.db.exists(
			"CRM Organization", {"organization_name": self.organization}
		)
		if existing_organization:
			self.db_set("organization", existing_organization)
			return existing_organization

		organization = frappe.new_doc("CRM Organization")
		org_data = {
			"organization_name": self.organization,
			"website": self.website,
			"territory": self.territory,
			"industry": self.industry,
			"annual_revenue": self.annual_revenue,
			"lead": self.name,
		}

		# Copy GST information if available
		if hasattr(self, 'gst_applicable') and self.gst_applicable and hasattr(self, 'gst_number') and self.gst_number:
			org_data["custom_gstin"] = self.gst_number

		organization.update(org_data)
		organization.insert(ignore_permissions=True)
		return organization.name

	def update_lead_contact(self, contact):
		contact = frappe.get_cached_doc("Contact", contact)
		frappe.db.set_value(
			"CRM Lead",
			self.name,
			{
				"salutation": contact.salutation,
				"first_name": contact.first_name,
				"last_name": contact.last_name,
				"email": contact.email_id,
				"mobile_no": contact.mobile_no,
			},
		)

	def contact_exists(self, throw=True):
		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email})
		phone_exist = frappe.db.exists("Contact Phone", {"phone": self.phone})
		mobile_exist = frappe.db.exists("Contact Phone", {"phone": self.mobile_no})

		doctype = "Contact Email" if email_exist else "Contact Phone"
		name = email_exist or phone_exist or mobile_exist

		if name:
			text = "Email" if email_exist else "Phone" if phone_exist else "Mobile No"
			data = self.email if email_exist else self.phone if phone_exist else self.mobile_no

			value = "{0}: {1}".format(text, data)

			contact = frappe.db.get_value(doctype, name, "parent")

			if throw:
				frappe.throw(
					_("Contact already exists with {0}").format(value),
					title=_("Contact Already Exists"),
				)
			return contact

		return False

	def create_deal(self, contact, organization, deal=None):
		new_deal = frappe.new_doc("CRM Deal")

		lead_deal_map = {
			"lead_owner": "deal_owner",
			"gst_number": "organization_gstin",
		}

		restricted_fieldtypes = [
			"Tab Break",
			"Section Break",
			"Column Break",
			"HTML",
			"Button",
			"Attach",
		]
		restricted_map_fields = [
			"name",
			"naming_series",
			"creation",
			"owner",
			"modified",
			"modified_by",
			"idx",
			"docstatus",
			"status",
			"email",
			"mobile_no",
			"phone",
			"sla",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"communication_status",
			"sla_creation",
			"status_change_log",
		]

		for field in self.meta.fields:
			if field.fieldtype in restricted_fieldtypes:
				continue
			if field.fieldname in restricted_map_fields:
				continue

			fieldname = field.fieldname
			if field.fieldname in lead_deal_map:
				fieldname = lead_deal_map[field.fieldname]

			if hasattr(new_deal, fieldname):
				if fieldname == "organization":
					new_deal.update({fieldname: organization})
				else:
					new_deal.update({fieldname: self.get(field.fieldname)})

		new_deal.update(
			{
				"lead": self.name,
				"contacts": [{"contact": contact}],
			}
		)

		if self.first_responded_on:
			new_deal.update(
				{
					"sla_creation": self.sla_creation,
					"response_by": self.response_by,
					"sla_status": self.sla_status,
					"communication_status": self.communication_status,
					"first_response_time": self.first_response_time,
					"first_responded_on": self.first_responded_on,
				}
			)

		if deal:
			new_deal.update(deal)

		new_deal.insert(ignore_permissions=True)
		return new_deal.name

	def set_sla(self):
		"""
		Find an SLA to apply to the lead.
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

	def convert_to_deal(self, deal=None):
		return convert_to_deal(lead=self.name, doc=self, deal=deal)

	@staticmethod
	def get_non_filterable_fields():
		return ["converted"]

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "lead_name",
				"width": "12rem",
			},
			{
				"label": "Organization",
				"type": "Link",
				"key": "organization",
				"options": "CRM Organization",
				"width": "10rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "8rem",
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
			"lead_name",
			"organization",
			"status",
			"email",
			"mobile_no",
			"lead_owner",
			"first_name",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"modified",
			"_assign",
			"image",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "lead_name",
			"kanban_fields": '["organization", "email", "mobile_no", "_assign", "modified"]',
		}


@frappe.whitelist()
def fetch_and_populate_gstin_details(lead_name, gstin):
	"""
	Fetch GSTIN details and auto-populate organization fields in CRM Lead
	"""
	try:
		if not gstin:
			return {
				"success": False,
				"error": "GSTIN is required"
			}

		# Fetch GSTIN details from India Compliance
		from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import fetch_gstin_details

		result = fetch_gstin_details(gstin)

		if not result.get("success"):
			return result

		# Get the lead document
		lead = frappe.get_doc("CRM Lead", lead_name)

		# Auto-populate fields from GSTIN data
		gstin_data = result.get("data", {})

		update_fields = {}

		# Map GSTIN data to lead fields
		if gstin_data.get("organization"):
			update_fields["organization"] = gstin_data["organization"]

		if gstin_data.get("company_type"):
			update_fields["company_type"] = gstin_data["company_type"]

		# Update the lead document
		if update_fields:
			for field, value in update_fields.items():
				setattr(lead, field, value)

			lead.save(ignore_permissions=True)

		return {
			"success": True,
			"data": gstin_data,
			"message": "Organization details populated successfully",
			"updated_fields": update_fields,
			"debug": result
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "GSTIN Auto-populate Error")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def convert_to_deal(lead, doc=None, deal=None, existing_contact=None, existing_organization=None):
	if not (doc and doc.flags.get("ignore_permissions")) and not frappe.has_permission(
		"CRM Lead", "write", lead
	):
		frappe.throw(_("Not allowed to convert Lead to Deal"), frappe.PermissionError)

	lead = frappe.get_cached_doc("CRM Lead", lead)
	if frappe.db.exists("CRM Lead Status", "Qualified"):
		lead.db_set("status", "Qualified")
	lead.db_set("converted", 1)
	if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
		lead.db_set("communication_status", "Replied")
	contact = lead.create_contact(existing_contact, False)
	organization = lead.create_organization(existing_organization)
	_deal = lead.create_deal(contact, organization, deal)
	return _deal

@frappe.whitelist()
def get_leads_data():
    return frappe.get_all(
        "CRM Lead",
        fields=["status", "annual_revenue", "converted"],
        filters={}
    )
