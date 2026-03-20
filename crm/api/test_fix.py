import frappe
from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

@frappe.whitelist()
def test_conversion_fix():
    # Create a dummy lead
    lead = frappe.get_doc({
        "doctype": "CRM Lead",
        "first_name": "Test",
        "last_name": "User",
        "organization": "Test Org",
        "status": "Qualified",
        "territory": "All Territories", # Required field
        "product_category": [{"product_category": "Test Category"}] 
    }).insert(ignore_permissions=True)

    print(f"Created Lead: {lead.name}")

    # Convert to Deal
    deal_name = convert_to_deal(lead.name)
    deal = frappe.get_doc("CRM Deal", deal_name)

    print(f"Created Deal: {deal.name}")
    print(f"Deal product_alloy_type: {deal.product_alloy_type}")
    print(f"Deal product_category: {deal.product_category}")

    # Clean up
    frappe.delete_doc("CRM Lead", lead.name)
    frappe.delete_doc("CRM Deal", deal.name)
    frappe.db.commit()
