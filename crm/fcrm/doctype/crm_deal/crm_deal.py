# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, today, getdate
from frappe.desk.form.assign_to import add as assign
from frappe.model.document import Document

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)


class CRMDeal(Document):
	def before_validate(self):
		self.set_sla()

	def validate(self):
		self.set_primary_contact()
		self.set_primary_email_mobile_no()
		if not self.is_new() and self.has_value_changed("deal_owner") and self.deal_owner:
			self.share_with_agent(self.deal_owner)
			self.assign_agent(self.deal_owner)
		if self.has_value_changed("status"):
			add_status_change_log(self)

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
	organization.update(
		{
			"organization_name": doc.get("organization_name"),
			"website": doc.get("website"),
			"territory": doc.get("territory"),
			"industry": doc.get("industry"),
			"annual_revenue": doc.get("annual_revenue"),
		}
	)
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
	contact.update(
		{
			"first_name": doc.get("first_name"),
			"last_name": doc.get("last_name"),
			"salutation": doc.get("salutation"),
			"company_name": doc.get("organization") or doc.get("organization_name"),
		}
	)

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

	contact = args.get("contact")
	if not contact and (
		args.get("first_name") or args.get("last_name") or args.get("email") or args.get("mobile_no")
	):
		contact = create_contact(args)

	deal.update(
		{
			"organization": args.get("organization") or create_organization(args),
			"contacts": [{"contact": contact, "is_primary": 1}] if contact else [],
		}
	)

	args.pop("organization", None)

	deal.update(args)

	deal.insert(ignore_permissions=True)
	return deal.name

import frappe

@frappe.whitelist()
def get_deals_data():
    return frappe.get_all(
        "CRM Deal",
        fields=["*"],
        filters={}
    )
    
@frappe.whitelist()
def get_deals_metrics(period='thisMonth'):
    return {
        "total": 89,
        "growth": 8.3,
        "value": 450000,
        "valueGrowth": 18.2
    }
    
@frappe.whitelist()
def get_sales_funnel(period='thisMonth'):
    return [
        {"stage": "Prospects", "count": 500, "percentage": 100},
        {"stage": "Qualified Leads", "count": 280, "percentage": 56},
        {"stage": "Proposals", "count": 147, "percentage": 29.4},
        {"stage": "Closed Won", "count": 89, "percentage": 17.8}
    ]

    """
    Returns aggregated metrics for CRM Deal over a given time period:
      - total deals
      - counts by status
      - growth placeholder
    """
    filters = { 'docstatus': 0 }
    if period:
        today = getdate(nowdate())
        if period == 'today':
            filters['creation'] = ['>=', today]
        elif period == 'thisWeek':
            start = today.add_days(-today.weekday())
            filters['creation'] = ['>=', start]
        elif period == 'thisMonth':
            filters['creation'] = ['>=', today.replace(day=1)]
        elif period == 'thisQuarter':
            q = ((today.month - 1) // 3) * 3 + 1
            filters['creation'] = ['>=', today.replace(month=q, day=1)]
        elif period == 'thisYear':
            filters['creation'] = ['>=', today.replace(month=1, day=1)]

    deals = frappe.get_all('CRM Deal', fields=['status'], filters=filters)
    total = len(deals)
    status_counts = {}
    for d in deals:
        st = d.get('status') or 'unknown'
        key = st.lower().replace(' ', '_')
        status_counts[key] = status_counts.get(key, 0) + 1

    metrics = {
        'total': total,
        'growth': 0  # placeholder
    }
    metrics.update({ f"{key}_deals": cnt for key, cnt in status_counts.items() })
    return metrics