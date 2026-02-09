# Copyright (c) 2026, Precious Alloys and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMMeeting(Document):
    def validate(self):
        self.validate_lead_fields()
    
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
