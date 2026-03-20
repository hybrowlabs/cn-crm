import frappe
from frappe import _

@frappe.whitelist()
def get_requests():
    """
    Fetch pending Technical Team Requests assigned to the current user.
    """
    user = frappe.session.user
    
    # Check if user is Administrator or has 'System Manager' role
    is_admin = user == "Administrator" or "System Manager" in frappe.get_roles()
    
    query = """
        SELECT 
            name, deal, product_category, commercial_pain_category, 
            technical_pain_category, notes_by_sales_team, modified
        FROM `tabTechnical Team Request`
        WHERE approved = 0
        AND rejected = 0
    """
    params = {}
    
    if not is_admin:
        query += " AND _assign LIKE %(user_pattern)s"
        params["user_pattern"] = f"%%{user}%%"
        
    query += " ORDER BY modified DESC"
    
    requests = frappe.db.sql(query, params, as_dict=True)
    
    # Enrich with Deal info
    for req in requests:
        if req.deal:
            req.organization = frappe.db.get_value("CRM Deal", req.deal, "organization")
            
    return requests

@frappe.whitelist()
def act_on_request(request_name, action, products, description=None):
    """
    Approve or Reject a Technical Team Request.
    """
    if not request_name or not action:
        frappe.throw(_("Missing mandatory parameters"))
        
    ttr = frappe.get_doc("Technical Team Request", request_name)
    deal = frappe.get_doc("CRM Deal", ttr.deal)
    
    
    # Correctly handle Table MultiSelect products (input is JSON string of list or actual list)
    import json
    if isinstance(products, str):
        product_list = json.loads(products) if products else []
    else:
        product_list = products if products else []
    
    # Validation for approval: mandatory products
    if action == 'approve' and not product_list:
        frappe.throw("At least one product must be selected for approval.")
        
    ttr.set("products", [])
    for p in product_list:
        ttr.append("products", {"product": p})
        
    if description:
        ttr.description = description
        
    if action == "approve":
        ttr.approved = 1
        ttr.rejected = 0
        
        deal.is_approved_by_tech_team = 1
        deal.approved_by_tech_team = 1
        deal.tech_team_notes = description
        
        # Sync products to CRM Deal
        deal.set("products_selected_by_technical_team", [])
        for p in product_list:
            deal.append("products_selected_by_technical_team", {"product": p})
            
        deal.save(ignore_permissions=True)
        
    elif action == "reject":
        ttr.approved = 0
        ttr.rejected = 1
        
        deal.is_suspended_by_tech_team = 1
        deal.save(ignore_permissions=True)
    
    ttr.save(ignore_permissions=True)
    frappe.db.commit()
    
    return True

@frappe.whitelist()
def get_products():
    """
    Get options for Product Discussed Multi Select.
    """
    return frappe.get_all("CRM Product", fields=["name", "product_name", "product_category"], filters={"disabled": 0})
