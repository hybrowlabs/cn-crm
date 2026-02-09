import frappe
from frappe import _


@frappe.whitelist()
def create_meeting_from_lead(lead, meeting_data):
    """Create CRM Meeting from Lead with validation
    
    Args:
        lead: CRM Lead name
        meeting_data: dict containing meeting fields
        
    Returns:
        Meeting name
    """
    if isinstance(meeting_data, str):
        import json
        meeting_data = json.loads(meeting_data)
    
    # Validate lead exists
    if not frappe.db.exists("CRM Lead", lead):
        frappe.throw(_("Lead {0} does not exist").format(lead))
    
    lead_doc = frappe.get_doc("CRM Lead", lead)
    
    # Optional: Validate lead qualification (can be enabled later)
    # errors = validate_lead_for_meeting(lead_doc)
    # if errors:
    #     frappe.throw("<br>".join(errors), title=_("Lead Not Qualified"))
    
    # Create meeting
    meeting = frappe.new_doc("Meeting")
    
    # Set fields from meeting_data
    for field, value in meeting_data.items():
        if hasattr(meeting, field):
            setattr(meeting, field, value)
    
    # Ensure lead is linked
    meeting.lead = lead
    
    meeting.insert(ignore_permissions=True)
    frappe.db.commit()
    
    return meeting.name


@frappe.whitelist()
def create_deal_from_meeting(meeting_name, deal_data=None):
    """Create CRM Deal (Opportunity) from Meeting with validation
    
    Args:
        meeting_name: Meeting docname
        deal_data: optional dict containing additional deal fields
        
    Returns:
        Deal name
    """
    if deal_data and isinstance(deal_data, str):
        import json
        deal_data = json.loads(deal_data)
    
    meeting = frappe.get_doc("Meeting", meeting_name)
    
    # Gate validation: Meeting → Opportunity
    errors = []
    if not meeting.primary_pain_category:
        errors.append(_("Primary Pain Category is required"))
    if not meeting.volume_range or meeting.volume_range <= 0:
        errors.append(_("Volume Range must be greater than 0"))
    if meeting.decision_maker_identified != "Yes":
        errors.append(_("Decision maker must be identified"))
    if meeting.agrees_to_trial != "Yes":
        errors.append(_("Customer must agree to trial"))
    
    if errors:
        frappe.throw("<br>".join(errors), title=_("Cannot Create Opportunity"))
    
    # Get lead data
    lead_doc = frappe.get_doc("CRM Lead", meeting.lead)
    
    # Create deal
    deal = frappe.new_doc("CRM Deal")
    
    if deal_data:
        for field, value in deal_data.items():
            if hasattr(deal, field):
                setattr(deal, field, value)
    
    # Copy data from lead and meeting
    deal.lead = meeting.lead
    deal.organization = lead_doc.organization
    deal.lead_name = lead_doc.lead_name
    deal.email = lead_doc.email
    deal.mobile_no = lead_doc.mobile_no
    
    # Copy discovery data from meeting
    if hasattr(deal, 'primary_pain'):
        deal.primary_pain = meeting.primary_pain_category
    if hasattr(deal, 'expected_monthly_volume'):
        deal.expected_monthly_volume = meeting.volume_range
    if hasattr(deal, 'product_alloy_type'):
        deal.product_alloy_type = meeting.product_discussed
    
    deal.insert(ignore_permissions=True)
    
    # Link meeting to deal
    frappe.db.set_value("Meeting", meeting_name, "deal", deal.name)
    frappe.db.commit()
    
    return deal.name


@frappe.whitelist()
def get_meeting(meeting_name):
    """Get meeting details
    
    Args:
        meeting_name: Meeting docname
        
    Returns:
        Meeting document as dict
    """
    if not frappe.db.exists("Meeting", meeting_name):
        frappe.throw(_("Meeting {0} does not exist").format(meeting_name))
    
    meeting = frappe.get_doc("Meeting", meeting_name)
    return meeting.as_dict()


def validate_lead_for_meeting(lead_doc):
    """Validate lead qualification for meeting creation
    
    Args:
        lead_doc: CRM Lead document
        
    Returns:
        list of error messages, empty if valid
    """
    errors = []
    
    # These validations can be customized based on requirements
    # if not lead_doc.contact_role:
    #     errors.append(_("Contact Role must be set on the lead"))
    # if lead_doc.customer_engaged != "Yes":
    #     errors.append(_("Customer must be engaged"))
    # if not lead_doc.next_action_date:
    #     errors.append(_("Next Action Date must be set"))
    
    return errors


@frappe.whitelist()
def get_meetings_for_lead(lead):
    """Get all meetings for a lead
    
    Args:
        lead: CRM Lead name
        
    Returns:
        list of meetings
    """
    meetings = frappe.get_all(
        "Meeting",
        filters={"lead": lead},
        fields=[
            "name", "meeting_date", "meeting_type", 
            "product_discussed", "volume_range",
            "primary_pain_category", "decision_maker_identified",
            "agrees_to_trial", "deal", "creation"
        ],
        order_by="creation desc"
    )
    return meetings
