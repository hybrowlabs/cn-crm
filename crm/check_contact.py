import frappe

def run():
    contact = "Alik Laha-2"
    lead = frappe.db.get_value("Contact", contact, "lead")
    print(f"Contact {contact} is linked to Lead: {lead}")

if __name__ == "__main__":
    run()
