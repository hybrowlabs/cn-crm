import frappe

def test_fetch_from():
    lead_name = frappe.db.get_value("CRM Lead", {"status": "Qualified"}, "name")
    if not lead_name:
        print("No qualified lead found.")
        return
        
    print(f"Testing with Lead: {lead_name}")
    new_deal = frappe.new_doc("CRM Deal")
    
    # Set a value for product_alloy_type
    cat = frappe.db.get_value("CRM Product Category", {}, "name")
    new_deal.product_alloy_type = cat
    print(f"Set product_alloy_type to: {new_deal.product_alloy_type}")
    
    # Now set lead, which has fetch_from configured for product_alloy_type
    new_deal.lead = lead_name
    print(f"Set lead to: {new_deal.lead}")
    
    # Check value before insert
    print(f"Value before insert: {new_deal.product_alloy_type}")
    
    try:
        new_deal.insert(ignore_permissions=True)
        print(f"Value after insert: {new_deal.product_alloy_type}")
    except Exception as e:
        print(f"Error during insert: {e}")

if __name__ == "__main__":
    test_fetch_from()
