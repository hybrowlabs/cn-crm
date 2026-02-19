# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import csv
import io

class Prospects(Document):
	pass

@frappe.whitelist()
def mark_prospect_converted(prospect_id):
	prospect = frappe.get_doc("Prospects", prospect_id)
	prospect.status = "Converted"
	prospect.save(ignore_permissions=True)

@frappe.whitelist()
def import_prospects_csv(csv_content):
    if not csv_content:
        frappe.throw("Empty CSV content")

    # Read CSV content
    f = io.StringIO(csv_content)
    reader = csv.DictReader(f)
    
    created_count = 0
    errors = []

    for row in reader:
        try:
            # Map CSV columns to DocType fields
            # Assumes CSV headers: Customer Name, Organization, Email, Mobile
            # Or simplified: Name, Organization, Email, Mobile
            
            # Normalize keys to lowercase and strip whitespace
            clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            
            customer_name = clean_row.get("customer name") or clean_row.get("name") or clean_row.get("full name")
            organization = clean_row.get("organization") or clean_row.get("company")
            email = clean_row.get("email")
            mobile_no = clean_row.get("mobile") or clean_row.get("mobile no") or clean_row.get("phone")
            
            if not customer_name:
                continue

            doc = frappe.new_doc("Prospects")
            doc.customer_name = customer_name
            doc.organization = organization
            doc.email = email
            doc.mobile_no = mobile_no
            doc.status = "Open"
            doc.insert()
            created_count += 1
            
        except Exception as e:
            errors.append(f"Error importing row {row}: {str(e)}")

    return {
        "created_count": created_count,
        "errors": errors
    }

def check_prospect_data():
    try:
        # Check if column exists
        db = frappe.db
        if not db.has_column("Prospects", "status"):
            print("Status column missing in Prospects table.")
            return

        # Fetch all prospects
        prospects = frappe.get_all("Prospects", fields=["name", "customer_name", "status", "mobile_no", "organization"])
        print(f"Total Prospects: {len(prospects)}")
        for p in prospects:
            print(f"Prospect: {p.name}, Status: {p.status}")
            
            # Fix if status is missing
            if not p.status:
                frappe.db.set_value("Prospects", p.name, "status", "Open")
                print(f"Updated status for {p.name} to Open")
        
        frappe.db.commit()
        print("Data check completed.")

    except Exception as e:
        print(f"Error: {e}")
