import frappe
import json

def run():
    layout_name = "CRM Deal-Qualified Data"
    if frappe.db.exists("CRM Fields Layout", layout_name):
        frappe.delete_doc("CRM Fields Layout", layout_name)
    
    layout_data = [
        {
            "name": "first_tab",
            "sections": [
                {
                    "label": "Qualified Details",
                    "name": "qualified_details_section",
                    "opened": True,
                    "columns": [
                        {
                            "name": "column_qualified_1",
                            "fields": [
                                "primary_pain_category",
                                "technical_pain_category",
                                "first_order_volume",
                                "product_alloy_type",
                                "expected_monthly_volume"
                            ]
                        },
                        {
                            "name": "column_qualified_2",
                            "fields": [
                                "decision_criteria",
                                "economic_buyer_name",
                                "decision_timeline",
                                "notes"
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    doc = frappe.new_doc("CRM Fields Layout")
    doc.name = layout_name
    doc.type = "Qualified Data"
    doc.dt = "CRM Deal"
    doc.layout = json.dumps(layout_data)
    doc.insert()
    frappe.db.commit()
    print(f"Created layout: {layout_name}")
