
import frappe

def fix_territory():
    territory_name = "All Territories"
    if not frappe.db.exists("Territory", territory_name):
        print(f"Creating missing Territory: {territory_name}")
        t = frappe.new_doc("Territory")
        t.territory_name = territory_name
        t.is_group = 1
        t.parent_territory = "" 
        t.insert(ignore_permissions=True)
        print("Created successfully.")
    else:
        print(f"Territory '{territory_name}' already exists.")

if __name__ == "__main__":
    fix_territory()
    frappe.db.commit()
