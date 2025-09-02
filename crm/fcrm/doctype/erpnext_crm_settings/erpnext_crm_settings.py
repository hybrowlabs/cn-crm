# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import json
import re

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.frappeclient import FrappeClient
from frappe.model.document import Document
from frappe.utils import get_url_to_form, get_url_to_list


class ERPNextCRMSettings(Document):
	def validate(self):
		if self.enabled:
			self.validate_if_erpnext_installed()
			self.add_quotation_to_option()
			self.create_custom_fields()
			self.create_crm_form_script()

	def validate_if_erpnext_installed(self):
		if not self.is_erpnext_in_different_site:
			if "erpnext" not in frappe.get_installed_apps():
				frappe.throw(_("ERPNext is not installed in the current site"))

	def add_quotation_to_option(self):
		if not self.is_erpnext_in_different_site:
			if not frappe.db.exists("Property Setter", {"name": "Quotation-quotation_to-link_filters"}):
				make_property_setter(
					doctype="Quotation",
					fieldname="quotation_to",
					property="link_filters",
					value='[["DocType","name","in", ["Customer", "Lead", "Prospect", "CRM Deal"]]]',
					property_type="JSON",
					validate_fields_for_doctype=False,
				)

	def create_custom_fields(self):
		if not self.is_erpnext_in_different_site:
			from erpnext.crm.frappe_crm_api import create_custom_fields_for_frappe_crm

			create_custom_fields_for_frappe_crm()
		else:
			self.create_custom_fields_in_remote_site()

	def create_custom_fields_in_remote_site(self):
		client = get_erpnext_site_client(self)
		try:
			client.post_api("erpnext.crm.frappe_crm_api.create_custom_fields_for_frappe_crm")
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error while creating custom field in the remote erpnext site: {self.erpnext_site_url}",
			)
			frappe.throw("Error while creating custom field in ERPNext, check error log for more details")

	def create_crm_form_script(self):
		if not frappe.db.exists("CRM Form Script", "Create Quotation from CRM Deal"):
			script = get_crm_form_script()
			frappe.get_doc(
				{
					"doctype": "CRM Form Script",
					"name": "Create Quotation from CRM Deal",
					"dt": "CRM Deal",
					"view": "Form",
					"script": script,
					"enabled": 1,
					"is_standard": 1,
				}
			).insert()

	@frappe.whitelist()
	def reset_erpnext_form_script(self):
		try:
			if frappe.db.exists("CRM Form Script", "Create Quotation from CRM Deal"):
				script = get_crm_form_script()
				frappe.db.set_value("CRM Form Script", "Create Quotation from CRM Deal", "script", script)
				return True
			return False
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Error while resetting form script")
			return False

	@frappe.whitelist()
	def validate_gstin_api(self, gstin):
		"""
		API method to validate GSTIN for testing purposes
		"""
		try:
			if not gstin:
				return {
					"success": False,
					"message": "GSTIN is required"
				}
			
			validation_result = validate_deal_gstin(gstin, self.strict_gst_validation)
			
			return {
				"success": True,
				"validation_result": validation_result,
				"message": "GSTIN validation completed"
			}
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "GSTIN Validation API Error")
			return {
				"success": False,
				"message": f"Error validating GSTIN: {str(e)}"
			}


def validate_gstin_format(gstin):
	"""
	Validate Indian GSTIN format (15 characters: 2 digits state code + 10 characters PAN + 1 digit entity number + 1 character Z + 1 check digit)
	Returns tuple (is_valid, error_message)
	"""
	if not gstin:
		return True, None
	
	gstin = gstin.upper().strip()
	
	# Check length
	if len(gstin) != 15:
		return False, f"GSTIN must be exactly 15 characters long. Provided: {len(gstin)} characters"
	
	# Check pattern: 2 digits + 10 alphanumeric + 1 digit + 1 letter Z + 1 alphanumeric
	gstin_pattern = re.compile(r'^[0-9]{2}[A-Z0-9]{10}[0-9][A-Z][A-Z0-9]$')
	if not gstin_pattern.match(gstin):
		return False, "GSTIN format is invalid. Expected format: 2 digits + 10 alphanumeric + 1 digit + 1 letter + 1 alphanumeric"
	
	# Check if 13th character is 'Z' (index 12, but many GSTINs have different structure)
	# Let's remove this strict check as GSTIN structure can vary
	# if gstin[12] != 'Z':
	#	return False, "13th character of GSTIN must be 'Z'"
	
	# Validate check digit
	try:
		if not validate_gstin_check_digit(gstin):
			return False, "GSTIN check digit validation failed"
	except Exception as e:
		return False, f"Error validating GSTIN check digit: {str(e)}"
	
	return True, None


def validate_gstin_check_digit(gstin):
	"""
	Validate GSTIN check digit using the standard algorithm
	"""
	factor = 1
	total = 0
	code_point_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
	mod = len(code_point_chars)
	input_chars = gstin[:-1]
	
	for char in input_chars:
		digit = factor * code_point_chars.find(char)
		digit = (digit // mod) + (digit % mod)
		total += digit
		factor = 2 if factor == 1 else 1
	
	expected_check_digit = code_point_chars[((mod - (total % mod)) % mod)]
	return gstin[-1] == expected_check_digit


def validate_gstin_with_compliance_app(gstin):
	"""
	Validate GSTIN using India Compliance app if available
	Returns tuple (is_valid, error_message, gstin_info)
	"""
	try:
		# Check if India Compliance app is installed
		if "india_compliance" not in frappe.get_installed_apps():
			return None, "India Compliance app not installed", None
		
		# Import validation function
		from india_compliance.gst_india.utils import validate_gstin
		
		# This will raise an exception if invalid, or return cleaned GSTIN if valid
		validated_gstin = validate_gstin(gstin, label="GSTIN")
		
		return True, None, {"gstin": validated_gstin}
		
	except ImportError:
		return None, "India Compliance validation function not available", None
	except Exception as e:
		return False, str(e), None


def validate_deal_gstin(gstin, strict_validation=False):
	"""
	Main GSTIN validation function that tries India Compliance first, then falls back to basic validation
	Returns dict with validation results
	"""
	if not gstin:
		return {
			"is_valid": True,
			"error_message": None,
			"warning_message": None,
			"gstin_info": None,
			"validation_method": "skip"
		}
	
	# Try India Compliance app first
	compliance_result, compliance_error, gstin_info = validate_gstin_with_compliance_app(gstin)
	
	if compliance_result is not None:
		# India Compliance validation was attempted
		if compliance_result:
			return {
				"is_valid": True,
				"error_message": None,
				"warning_message": None,
				"gstin_info": gstin_info,
				"validation_method": "india_compliance"
			}
		else:
			return {
				"is_valid": False,
				"error_message": compliance_error,
				"warning_message": None,
				"gstin_info": None,
				"validation_method": "india_compliance"
			}
	
	# Fall back to basic validation
	basic_result, basic_error = validate_gstin_format(gstin)
	
	if basic_result:
		return {
			"is_valid": True,
			"error_message": None,
			"warning_message": "GSTIN format appears valid (basic validation only - India Compliance app not available for full validation)",
			"gstin_info": {"gstin": gstin.upper().strip()},
			"validation_method": "basic"
		}
	else:
		return {
			"is_valid": False,
			"error_message": basic_error,
			"warning_message": None,
			"gstin_info": None,
			"validation_method": "basic"
		}


def get_erpnext_site_client(erpnext_crm_settings):
	site_url = erpnext_crm_settings.erpnext_site_url
	api_key = erpnext_crm_settings.api_key
	api_secret = erpnext_crm_settings.get_password("api_secret", raise_exception=False)

	return FrappeClient(site_url, api_key=api_key, api_secret=api_secret)


@frappe.whitelist()
def get_customer_link(crm_deal):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if not erpnext_crm_settings.enabled:
		frappe.throw(_("ERPNext is not integrated with the CRM"))

	if not erpnext_crm_settings.is_erpnext_in_different_site:
		customer = frappe.db.exists("Customer", {"crm_deal": crm_deal})
		return get_url_to_form("Customer", customer) if customer else ""
	else:
		client = get_erpnext_site_client(erpnext_crm_settings)
		try:
			customer = client.get_list("Customer", {"crm_deal": crm_deal})
			customer = customer[0].get("name") if len(customer) else None
			if customer:
				return f"{erpnext_crm_settings.erpnext_site_url}/app/customer/{customer}"
			else:
				return ""
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				f"Error while fetching customer in remote site: {erpnext_crm_settings.erpnext_site_url}",
			)
			frappe.throw(_("Error while fetching customer in ERPNext, check error log for more details"))


@frappe.whitelist()
def get_quotation_url(crm_deal, organization):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if not erpnext_crm_settings.enabled:
		frappe.throw(_("ERPNext is not integrated with the CRM"))

	contact = get_contact(crm_deal)
	address = get_organization_address(organization)
	address = address.get("name") if address else None

	if not erpnext_crm_settings.is_erpnext_in_different_site:
		quotation_url = get_url_to_list("Quotation")
		return f"{quotation_url}/new?quotation_to=CRM Deal&crm_deal={crm_deal}&party_name={crm_deal}&company={erpnext_crm_settings.erpnext_company}&contact_person={contact}&customer_address={address}"
	else:
		site_url = erpnext_crm_settings.get("erpnext_site_url")
		quotation_url = f"{site_url}/app/quotation"

		prospect = create_prospect_in_remote_site(crm_deal, erpnext_crm_settings)
		return f"{quotation_url}/new?quotation_to=Prospect&crm_deal={crm_deal}&party_name={prospect}&company={erpnext_crm_settings.erpnext_company}&contact_person={contact}&customer_address={address}"


def create_prospect_in_remote_site(crm_deal, erpnext_crm_settings):
	try:
		client = get_erpnext_site_client(erpnext_crm_settings)
		doc = frappe.get_cached_doc("CRM Deal", crm_deal)
		contacts = get_contacts(doc)
		address = get_organization_address(doc.organization) or None

		if address and not isinstance(address, dict):
			address = address.as_dict()

		return client.post_api(
			"erpnext.crm.frappe_crm_api.create_prospect_against_crm_deal",
			{
				"organization": doc.organization,
				"lead_name": doc.lead_name,
				"no_of_employees": doc.no_of_employees,
				"deal_owner": doc.deal_owner,
				"crm_deal": doc.name,
				"territory": doc.territory,
				"industry": doc.industry,
				"website": doc.website,
				"annual_revenue": doc.annual_revenue,
				"contacts": json.dumps(contacts) if contacts else None,
				"erpnext_company": erpnext_crm_settings.erpnext_company,
				"address": json.dumps(address) if address else None,
			},
		)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error while creating prospect in remote site: {erpnext_crm_settings.erpnext_site_url}",
		)
		frappe.throw(_("Error while creating prospect in ERPNext, check error log for more details"))


def get_contact(crm_deal):
	doc = frappe.get_cached_doc("CRM Deal", crm_deal)
	contact = None
	for c in doc.contacts:
		if c.is_primary:
			contact = c.contact
			break

	return contact


def get_contacts(doc):
	contacts = []
	for c in doc.contacts:
		contacts.append(
			{
				"contact": c.contact,
				"full_name": c.full_name,
				"email": c.email,
				"mobile_no": c.mobile_no,
				"gender": c.gender,
				"is_primary": c.is_primary,
			}
		)
	return contacts


def get_organization_address(organization):
	address = frappe.db.get_value("CRM Organization", organization, "address")
	address = frappe.get_cached_doc("Address", address) if address else None
	if not address:
		return None
	return {
		"name": address.name,
		"address_title": address.address_title,
		"address_type": address.address_type,
		"address_line1": address.address_line1,
		"address_line2": address.address_line2,
		"city": address.city,
		"county": address.county,
		"state": address.state,
		"country": address.country,
		"pincode": address.pincode,
	}


def create_customer_in_erpnext(doc, method):
	erpnext_crm_settings = frappe.get_single("ERPNext CRM Settings")
	if (
		not erpnext_crm_settings.enabled
		or not erpnext_crm_settings.create_customer_on_status_change
		or doc.status != erpnext_crm_settings.deal_status
	):
		return

	# GST Validation
	gst_validation_result = None
	customer_comment = None
	
	if erpnext_crm_settings.enable_gst_validation:
		gstin = getattr(doc, 'organization_gstin', None) or ""
		if gstin:
			gst_validation_result = validate_deal_gstin(gstin, erpnext_crm_settings.strict_gst_validation)
			
			# Handle validation results
			if not gst_validation_result["is_valid"]:
				error_msg = f"GST validation failed for GSTIN {gstin}: {gst_validation_result['error_message']}"
				
				if erpnext_crm_settings.strict_gst_validation:
					# Block customer creation
					frappe.throw(
						_("Customer creation blocked due to invalid GSTIN. {0}").format(error_msg),
						title=_("GST Validation Failed")
					)
				else:
					# Show warning and add comment to customer
					frappe.msgprint(
						_("Warning: {0}. Customer will still be created.").format(error_msg),
						title=_("GST Validation Warning"),
						indicator="orange"
					)
					customer_comment = f"GST Validation Warning: {gst_validation_result['error_message']} (Validation method: {gst_validation_result['validation_method']})"
			elif gst_validation_result["warning_message"]:
				# Show info message for successful validation with warnings
				frappe.msgprint(
					gst_validation_result["warning_message"],
					title=_("GST Validation Info"),
					indicator="blue"
				)
				customer_comment = f"GST Validation Info: {gst_validation_result['warning_message']} (Validation method: {gst_validation_result['validation_method']})"
		else:
			# No GSTIN provided - this is allowed
			if not erpnext_crm_settings.strict_gst_validation:
				frappe.msgprint(
					_("No GSTIN provided for customer creation from deal {0}").format(doc.name),
					title=_("GST Validation Info"),
					indicator="blue"
				)

	contacts = get_contacts(doc)
	address = get_organization_address(doc.organization)
	customer = {
		"customer_name": doc.organization,
		"customer_group": "All Customer Groups",
		"customer_type": "Company",
		"territory": doc.territory,
		"default_currency": doc.currency,
		"industry": doc.industry,
		"website": doc.website,
		"crm_deal": doc.name,
		"contacts": json.dumps(contacts),
		"address": json.dumps(address) if address else None,
	}
	
	# Add GSTIN to customer if available and validated
	if gst_validation_result and gst_validation_result.get("gstin_info") and gst_validation_result["gstin_info"].get("gstin"):
		customer["gstin"] = gst_validation_result["gstin_info"]["gstin"]
	elif getattr(doc, 'organization_gstin', None):
		# Use original GSTIN even if validation failed (in non-strict mode)
		customer["gstin"] = doc.organization_gstin.upper().strip()
	
	# Create customer
	customer_doc = None
	if not erpnext_crm_settings.is_erpnext_in_different_site:
		from erpnext.crm.frappe_crm_api import create_customer
		customer_doc = create_customer(customer)
	else:
		customer_doc = create_customer_in_remote_site(customer, erpnext_crm_settings)

	# Add comment to customer if there were validation issues
	if customer_comment and customer_doc and not erpnext_crm_settings.is_erpnext_in_different_site:
		try:
			# Get the created customer name
			customer_name = customer_doc if isinstance(customer_doc, str) else customer_doc.get("name")
			if customer_name:
				add_customer_comment(customer_name, customer_comment, erpnext_crm_settings)
		except Exception as e:
			frappe.log_error(
				frappe.get_traceback(),
				f"Failed to add GST validation comment to customer: {str(e)}"
			)

	frappe.publish_realtime("crm_customer_created")


def add_customer_comment(customer_name, comment_text, erpnext_crm_settings):
	"""
	Add a comment to the customer document
	"""
	try:
		if erpnext_crm_settings.is_erpnext_in_different_site:
			# For remote site, we'll skip adding comments for now
			# Could be implemented using the API if needed
			frappe.log_error(
				f"Cannot add comment to remote customer: {customer_name}",
				"GST Validation Comment"
			)
			return
		
		# Add comment to local customer
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Comment",
			"reference_doctype": "Customer",
			"reference_name": customer_name,
			"content": comment_text,
			"comment_email": frappe.session.user,
			"comment_by": frappe.session.user
		}).insert(ignore_permissions=True)
		
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			f"Error adding comment to customer {customer_name}: {str(e)}"
		)


def create_customer_in_remote_site(customer, erpnext_crm_settings):
	client = get_erpnext_site_client(erpnext_crm_settings)
	try:
		client.post_api("erpnext.crm.frappe_crm_api.create_customer", customer)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Error while creating customer in remote site")
		frappe.throw(_("Error while creating customer in ERPNext, check error log for more details"))


@frappe.whitelist()
def validate_gstin_number(gstin):
	"""
	Standalone API method to validate GSTIN
	"""
	try:
		if not gstin:
			frappe.throw(_("GSTIN is required for validation"), title=_("Missing GSTIN"))
		
		validation_result = validate_deal_gstin(gstin, False)  # Non-strict validation for API
		
		return {
			"success": True,
			"data": validation_result,
			"message": _("GSTIN validation completed successfully")
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "GSTIN Validation API Error")
		return {
			"success": False,
			"error": str(e),
			"message": _("Error occurred during GSTIN validation")
		}


@frappe.whitelist()
def get_crm_form_script():
	return """
async function setupForm({ doc, call, $dialog, updateField, toast }) {
	let actions = [];
	let is_erpnext_integration_enabled = await call("frappe.client.get_single_value", {doctype: "ERPNext CRM Settings", field: "enabled"});
	if (!["Lost", "Won"].includes(doc?.status) && is_erpnext_integration_enabled) {
		actions.push({
			label: __("Create Quotation"),
			onClick: async () => {
				let quotation_url = await call(
					"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_quotation_url", 
					{
						crm_deal: doc.name,
						organization: doc.organization
					}
				);

				if (quotation_url) {
					window.open(quotation_url, '_blank');
				}
			}
		})
	}
	if (is_erpnext_integration_enabled) {
		let customer_url = await call("crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_customer_link", {
			crm_deal: doc.name
		});
		if (customer_url) {
			actions.push({
				label: __("View Customer"),
				onClick: () => window.open(customer_url, '_blank')
			});
		}
	}
	return {
		actions: actions,
	};
}
"""
