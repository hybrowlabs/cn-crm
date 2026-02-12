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
from crm.api.territory_permissions import has_permission as territory_has_permission


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
		# Note: auto_fetch_gstin_details() removed - GST Portal API now called only during deal conversion
		self.validate_territory_access()
		self.auto_set_territory_if_empty()
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

		# Validate mandatory fields for specific statuses
		if self.status in ["Contacted", "Nurture"]:
			mandatory_fields = [
				("meeting_type", _("Meeting Type")),
				("product_discussed", _("Product Discussed")),
				("volume_rangekg", _("Volume Range (kg)")),
				("primary_pain_category", _("Primary Pain Category")),
				("pain_description", _("Pain Description")),
				("customer_role_type", _("Customer Role Type")),
				("current_supplier", _("Current Supplier")),
				("decision_process", _("Decision Process")),
				("next_action_date", _("Next Action Date"))
			]

			for fieldname, label in mandatory_fields:
				if not self.get(fieldname):
					frappe.throw(
						_("{0} is mandatory for '{1}' status").format(label, self.status),
						title=_("Missing Required Information")
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
		"""Validate GST number format (offline only) and check for duplicates"""
		# Check if gst_applicable field exists (will be added via migration)
		if not hasattr(self, 'gst_applicable'):
			return

		if self.gst_applicable and self.gst_number:
			from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
				validate_gstin_format,
				check_gstin_duplicates
			)

			# Validate GSTIN format offline (no India Compliance API call)
			is_valid, error_message = validate_gstin_format(self.gst_number)

			if not is_valid:
				frappe.throw(
					_(error_message),
					title=_("Invalid GST Number")
				)

			# Check for duplicates (database query only)
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
		Auto-assign territory to the lead based on user's primary territory if empty.
		"""
		if self.territory or self.flags.ignore_permissions:
			return

		# Get user's territories
		from crm.api.territory_permissions import get_user_territories
		user_territories = get_user_territories(frappe.session.user)

		if user_territories:
			# Assign first territory (primary territory)
			self.territory = user_territories[0]

	def has_permission(self, user=None, permission_type=None):
		"""
		Custom permission check for CRM Lead based on territory.
		"""
		return territory_has_permission(self, user, permission_type)

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

	# Initialize deal dict if not provided
	if deal is None:
		deal = {}

	# Validate and fetch GST details using India Compliance API (only during deal conversion)
	gst_address = None
	if hasattr(lead, 'gst_applicable') and lead.gst_applicable and hasattr(lead, 'gst_number') and lead.gst_number:
		gst_address = _validate_and_fetch_gst_for_conversion(lead)

	# Set GST address on deal if fetched from API
	if gst_address:
		deal["gst_address"] = gst_address

	if frappe.db.exists("CRM Lead Status", "Qualified"):
		lead.db_set("status", "Qualified")
	lead.db_set("converted", 1)
	if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
		lead.db_set("communication_status", "Replied")
	contact = lead.create_contact(existing_contact, False)
	organization = lead.create_organization(existing_organization)
	_deal = lead.create_deal(contact, organization, deal)
	return _deal


def _validate_and_fetch_gst_for_conversion(lead):
	"""
	Validate GSTIN using India Compliance API and auto-fetch organization details.
	This is only called during deal conversion, not during lead save.

	Returns:
		str: Formatted GST address from the GST Portal, or None if not available
	"""
	from crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings import (
		validate_deal_gstin,
		fetch_gstin_details
	)

	# Validate GSTIN using India Compliance API
	result = validate_deal_gstin(lead.gst_number)

	if not result['is_valid']:
		frappe.throw(
			_(result['error_message']),
			title=_("Invalid GST Number")
		)

	# Display warning if using basic validation only
	if result.get('warning_message'):
		frappe.msgprint(
			_(result['warning_message']),
			indicator='orange',
			alert=True
		)

	gst_address = None

	# Auto-fetch organization details from GSTIN
	try:
		fetch_result = fetch_gstin_details(lead.gst_number)

		if fetch_result.get("success") and fetch_result.get("data"):
			gstin_data = fetch_result["data"]
			updated_fields = []

			# Auto-populate organization name if empty
			if not lead.organization and gstin_data.get("organization"):
				lead.db_set("organization", gstin_data["organization"])
				updated_fields.append("Organization")

			# Auto-populate company type if empty
			if not lead.company_type and gstin_data.get("company_type"):
				lead.db_set("company_type", gstin_data["company_type"])
				updated_fields.append("Company Type")

			# Build GST address from API response
			gst_address = _format_gst_address(gstin_data)

			if gst_address:
				updated_fields.append("GST Address")

			# Show success message if any fields were updated
			if updated_fields:
				frappe.msgprint(
					_("Auto-filled from GSTIN: {0}").format(", ".join(updated_fields)),
					indicator="green",
					alert=True
				)

	except Exception as e:
		# Don't block conversion if GSTIN fetch fails
		frappe.log_error(
			frappe.get_traceback(),
			f"GST API Fetch Failed during deal conversion for Lead {lead.name}"
		)
		frappe.msgprint(
			_("Could not fetch details from GSTIN API: {0}").format(str(e)),
			indicator="orange",
			alert=True
		)

	return gst_address


def _format_gst_address(gstin_data):
	"""
	Format the GST address from API response into a single string.

	Args:
		gstin_data: Dict containing address fields from GST Portal API

	Returns:
		str: Formatted address string, or None if no address data
	"""
	address_parts = []

	# Add address lines
	if gstin_data.get("address_line1"):
		address_parts.append(gstin_data["address_line1"])

	if gstin_data.get("address_line2"):
		address_parts.append(gstin_data["address_line2"])

	# Add city, state, pincode
	city_state_parts = []
	if gstin_data.get("city"):
		city_state_parts.append(gstin_data["city"])

	if gstin_data.get("state"):
		city_state_parts.append(gstin_data["state"])

	if city_state_parts:
		address_parts.append(", ".join(city_state_parts))

	if gstin_data.get("pincode"):
		address_parts.append(f"PIN: {gstin_data['pincode']}")

	if gstin_data.get("country"):
		address_parts.append(gstin_data["country"])

	if address_parts:
		return "\n".join(address_parts)

	return None

@frappe.whitelist()
def get_leads_data():
    return frappe.get_all(
        "CRM Lead",
        fields=["status", "annual_revenue", "converted"],
        filters={}
    )


@frappe.whitelist()
def check_lead_duplicates(organization=None, email=None, mobile_no=None):
    """
    Check for potential duplicate leads, organizations, contacts, and customers.

    This helps prevent creating duplicate records by checking:
    1. Existing leads (not yet converted to deals) with matching organization, email, or mobile
    2. Existing organizations (from converted leads/deals) with matching name
    3. Existing contacts with matching email or mobile number
    4. Existing customers with matching email or mobile number

    Args:
        organization: Organization name to search for (partial match)
        email: Email address to search for (exact match)
        mobile_no: Mobile number to search for (exact match)

    Returns:
        dict: Contains 'leads', 'organizations', 'contacts', and 'customers' lists with potential duplicates
    """
    duplicates = {
        "leads": [],
        "organizations": [],
        "contacts": [],
        "customers": [],
        "has_duplicates": False
    }

    # Skip if no search criteria provided
    if not organization and not email and not mobile_no:
        return duplicates

    # Build filters for lead search
    lead_filters = [["converted", "=", 0]]  # Only non-converted leads
    lead_or_filters = []

    if organization and len(organization) >= 2:
        # Partial match on organization name (case-insensitive)
        lead_or_filters.append(["organization", "like", f"%{organization}%"])

    if email:
        lead_or_filters.append(["email", "=", email])

    if mobile_no:
        # Normalize mobile number - remove common formatting characters
        normalized_mobile = mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        lead_or_filters.append(["mobile_no", "like", f"%{normalized_mobile[-10:]}%"])

    # Search for existing leads
    if lead_or_filters:
        existing_leads = frappe.get_all(
            "CRM Lead",
            filters=lead_filters,
            or_filters=lead_or_filters,
            fields=[
                "name", "lead_name", "organization", "email",
                "mobile_no", "status", "lead_owner", "first_name", "last_name"
            ],
            limit=10
        )

        for lead in existing_leads:
            match_reasons = []
            if organization and lead.organization and organization.lower() in lead.organization.lower():
                match_reasons.append("organization")
            if email and lead.email and email.lower() == lead.email.lower():
                match_reasons.append("email")
            if mobile_no and lead.mobile_no:
                normalized_search = mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                normalized_lead = lead.mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                if normalized_search[-10:] in normalized_lead or normalized_lead[-10:] in normalized_search:
                    match_reasons.append("mobile")

            duplicates["leads"].append({
                "name": lead.name,
                "lead_name": lead.lead_name or f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
                "organization": lead.organization,
                "email": lead.email,
                "mobile_no": lead.mobile_no,
                "status": lead.status,
                "lead_owner": lead.lead_owner,
                "match_reasons": match_reasons
            })

    # Search for existing organizations (from converted leads)
    if organization and len(organization) >= 2:
        existing_orgs = frappe.get_all(
            "CRM Organization",
            filters=[["organization_name", "like", f"%{organization}%"]],
            fields=["name", "organization_name", "website", "industry", "lead"],
            limit=10
        )

        for org in existing_orgs:
            # Get the associated deal if any
            deal = frappe.db.get_value(
                "CRM Deal",
                {"organization": org.name},
                ["name", "status", "deal_owner"],
                as_dict=True
            )

            duplicates["organizations"].append({
                "name": org.name,
                "organization_name": org.organization_name,
                "website": org.website,
                "industry": org.industry,
                "lead": org.lead,
                "deal": deal.get("name") if deal else None,
                "deal_status": deal.get("status") if deal else None
            })

    # Search for existing contacts by email or mobile
    if email or mobile_no:
        contact_names = set()

        # Search by email
        if email:
            email_contacts = frappe.get_all(
                "Contact Email",
                filters={"email_id": email},
                fields=["parent"],
                limit=10
            )
            for ec in email_contacts:
                contact_names.add(ec.parent)

        # Search by mobile number
        if mobile_no:
            normalized_mobile = mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            # Search for contacts with matching phone numbers
            phone_contacts = frappe.get_all(
                "Contact Phone",
                filters=[["phone", "like", f"%{normalized_mobile[-10:]}%"]],
                fields=["parent"],
                limit=10
            )
            for pc in phone_contacts:
                contact_names.add(pc.parent)

        # Get contact details
        for contact_name in list(contact_names)[:10]:
            contact = frappe.db.get_value(
                "Contact",
                contact_name,
                ["name", "first_name", "last_name", "email_id", "mobile_no", "company_name"],
                as_dict=True
            )
            if contact:
                match_reasons = []

                # Check email match - also check against all email addresses in Contact Email
                if email:
                    # Check primary email
                    if contact.email_id and email.lower() == contact.email_id.lower():
                        match_reasons.append("email")
                    else:
                        # Check all emails in Contact Email child table
                        email_exists = frappe.db.exists(
                            "Contact Email",
                            {"parent": contact_name, "email_id": email}
                        )
                        if email_exists:
                            match_reasons.append("email")

                # Check mobile match - also check against all phones in Contact Phone
                if mobile_no:
                    normalized_search = mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    matched_mobile = False

                    # Check primary mobile
                    if contact.mobile_no:
                        normalized_contact = contact.mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                        if normalized_search[-10:] in normalized_contact or normalized_contact[-10:] in normalized_search:
                            matched_mobile = True

                    # If not matched, check all phones in Contact Phone child table
                    if not matched_mobile:
                        contact_phones = frappe.get_all(
                            "Contact Phone",
                            filters={"parent": contact_name},
                            fields=["phone"]
                        )
                        for cp in contact_phones:
                            if cp.phone:
                                normalized_phone = cp.phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                                if normalized_search[-10:] in normalized_phone or normalized_phone[-10:] in normalized_search:
                                    matched_mobile = True
                                    break

                    if matched_mobile:
                        match_reasons.append("mobile")

                # Only add contacts that have at least one match reason
                if match_reasons:
                    # Get linked lead or deal if any
                    linked_lead = frappe.db.get_value("Contact", contact_name, "lead")
                    linked_deals = frappe.get_all(
                        "CRM Contacts",
                        filters={"contact": contact_name},
                        fields=["parent"],
                        limit=1
                    )

                    # Get the actual email and mobile to display (from child tables if primary is empty)
                    display_email = contact.email_id
                    display_mobile = contact.mobile_no

                    if not display_email:
                        primary_email = frappe.db.get_value(
                            "Contact Email",
                            {"parent": contact_name, "is_primary": 1},
                            "email_id"
                        )
                        display_email = primary_email

                    if not display_mobile:
                        primary_mobile = frappe.db.get_value(
                            "Contact Phone",
                            {"parent": contact_name, "is_primary_mobile_no": 1},
                            "phone"
                        )
                        display_mobile = primary_mobile

                    duplicates["contacts"].append({
                        "name": contact.name,
                        "full_name": f"{contact.first_name or ''} {contact.last_name or ''}".strip() or contact.name,
                        "email": display_email,
                        "mobile_no": display_mobile,
                        "company_name": contact.company_name,
                        "linked_lead": linked_lead,
                        "linked_deal": linked_deals[0].parent if linked_deals else None,
                        "match_reasons": match_reasons
                    })

    # Search for existing customers by email or mobile
    if email or mobile_no:
        customer_or_filters = []

        if email:
            customer_or_filters.append(["email_id", "=", email])

        if mobile_no:
            normalized_mobile = mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            customer_or_filters.append(["mobile_no", "like", f"%{normalized_mobile[-10:]}%"])

        if customer_or_filters:
            existing_customers = frappe.get_all(
                "Customer",
                or_filters=customer_or_filters,
                fields=[
                    "name", "customer_name", "email_id", "mobile_no",
                    "customer_type", "territory", "lead_name"
                ],
                limit=10
            )

            for customer in existing_customers:
                match_reasons = []

                # Check email match
                if email and customer.email_id and email.lower() == customer.email_id.lower():
                    match_reasons.append("email")

                # Check mobile match
                if mobile_no and customer.mobile_no:
                    normalized_search = mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    normalized_customer = customer.mobile_no.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                    if normalized_search[-10:] in normalized_customer or normalized_customer[-10:] in normalized_search:
                        match_reasons.append("mobile")

                if match_reasons:
                    duplicates["customers"].append({
                        "name": customer.name,
                        "customer_name": customer.customer_name,
                        "email": customer.email_id,
                        "mobile_no": customer.mobile_no,
                        "customer_type": customer.customer_type,
                        "territory": customer.territory,
                        "linked_lead": customer.lead_name,
                        "match_reasons": match_reasons
                    })

    duplicates["has_duplicates"] = bool(duplicates["leads"] or duplicates["organizations"] or duplicates["contacts"] or duplicates["customers"])

    return duplicates
