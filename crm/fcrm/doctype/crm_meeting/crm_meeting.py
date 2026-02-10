# Copyright (c) 2026, Precious Alloys and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class CRMMeeting(Document):
    def validate(self):
        self.normalize_datetime_fields()
        self.validate_lead_fields()

    def normalize_datetime_fields(self):
        """Convert datetime fields from human-readable formats to MySQL-compatible format"""
        from dateutil import parser as dateutil_parser

        datetime_fields = ["meeting_date"]
        for field in datetime_fields:
            value = self.get(field)
            if value and isinstance(value, str):
                try:
                    # Try frappe's parser first
                    parsed = get_datetime(value)
                    self.set(field, parsed.strftime("%Y-%m-%d %H:%M:%S"))
                except Exception:
                    try:
                        # Fallback to dateutil for formats like '2026-02-10 3:23 am'
                        parsed = dateutil_parser.parse(value)
                        self.set(field, parsed.strftime("%Y-%m-%d %H:%M:%S"))
                    except Exception:
                        frappe.throw(
                            _("Invalid date/time format for {0}: {1}").format(
                                _(self.meta.get_label(field)), value
                            )
                        )
    
    def validate_lead_fields(self):
        """Validate that the linked Lead has required fields for Meeting creation"""
        if not self.lead:
            return
        
        lead = frappe.get_doc("CRM Lead", self.lead)
        
        errors = []
        if not lead.first_name:
            errors.append(_("Lead must have a Contact Name (first_name)"))
        if not lead.designation:
            errors.append(_("Lead must have a Designation"))
        if not lead.application:
            errors.append(_("Lead must have an Application / Use Case"))
        if not lead.get("customer_segment"):
            errors.append(_("Lead must have a Customer Segment"))
        
        if errors:
            frappe.throw(
                _("Cannot create meeting. The following Lead fields are missing:") + 
                "<br>" + "<br>".join(errors),
                title=_("Lead Not Qualified for Meeting")
            )
    
    def can_create_opportunity(self):
        """Check if this meeting qualifies to create an Opportunity"""
        errors = []
        
        if not self.primary_pain_category:
            errors.append(_("Primary Pain Category is required"))
        if not self.pain_description:
            errors.append(_("Pain Description is required"))
        if not self.volume_range or self.volume_range <= 0:
            errors.append(_("Volume Range must be greater than 0"))
        if self.decision_maker_identified != "Yes":
            errors.append(_("Decision Maker / Buyer must be identified"))
        if self.agrees_to_trial != "Yes":
            errors.append(_("Customer must agree to evaluate trial"))
        
        if errors:
            return False, errors
        return True, []

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Lead",
                "type": "Link",
                "key": "lead",
                "options": "CRM Lead",
                "width": "12rem",
            },
            {
                "label": "Status",
                "type": "Select",
                "key": "status",
                "width": "10rem",
            },
            {
                "label": "Meeting Date & Time",
                "type": "Datetime",
                "key": "meeting_date",
                "width": "12rem",
            },
            {
                "label": "Meeting Type",
                "type": "Link",
                "key": "meeting_type",
                "options": "CRM Meeting Type",
                "width": "10rem",
            },
            {
                "label": "Meeting Owner",
                "type": "Link",
                "key": "meeting_owner",
                "options": "User",
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
            "lead",
            "status",
            "meeting_date",
            "meeting_type",
            "meeting_owner",
            "modified",
            "_assign",
        ]
        return {"columns": columns, "rows": rows}
