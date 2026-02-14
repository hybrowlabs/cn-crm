import frappe
import json

def execute():
    create_dashboards()

def create_dashboards():
    dashboards = [
        # 1. CEO Dashboard
        {
            "name": "CEO Dashboard",
            "parent": "Frappe CRM",
            "charts": [],
            "cards": []
        },
        # 2. Sales Manager Dashboard
        {
            "name": "Sales Manager Dashboard",
            "parent": "Frappe CRM",
            "charts": [],
            "cards": []
        },
        # 3. Account Manager Dashboard
        {
            "name": "Account Manager Dashboard",
            "parent": "Frappe CRM",
            "charts": [],
            "cards": []
        },
        # 4. Peer Comparison Dashboard
        {
            "name": "Peer Comparison Dashboard",
            "parent": "Frappe CRM",
            "charts": [],
            "cards": []
        },
        # 5. Repeat Order Dashboard
         {
            "name": "Repeat Order Dashboard",
            "parent": "Frappe CRM",
            "charts": [],
            "cards": []
        },
        # 6. Inactive Customer Dashboard
        {
            "name": "Inactive Customer Dashboard",
            "parent": "Frappe CRM",
            "charts": [],
            "cards": [],
            "shortcuts": [
                {
                    "label": "Inactive Accounts (>60 Days)",
                    "type": "Report",
                    "link_to": "CRM Organization",
                    "url": "/app/crm-organization?status=Inactive"
                }
            ]
        }
    ]

    for db_config in dashboards:
        create_dashboard_workspace(db_config)

def create_dashboard_workspace(config):
    # 3. Create/Update Workspace
    ws_name = config["name"]
    content = []
    
    # Add Header
    content.append({"type": "header", "data": {"text": ws_name, "col": 12}})
    
    # Add Shortcuts/Links if any
    if config.get("shortcuts"):
         content.append({"type": "spacer", "data": {"col": 12}})
         content.append({"type": "header", "data": {"text": "Lists & Reports", "col": 12}})
         for sc in config.get("shortcuts"):
             pass 

    if not frappe.db.exists("Workspace", ws_name):
        ws = frappe.new_doc("Workspace")
        ws.label = ws_name
        ws.name = ws_name
        ws.title = ws_name # Added Title
        ws.public = 1
        ws.parent_page = config.get("parent", "")
        ws.content = json.dumps(content)
        ws.insert(ignore_permissions=True)
    else:
        # Update existing
        ws = frappe.get_doc("Workspace", ws_name)
        ws.title = ws_name # Added Title update just in case
        ws.parent_page = config.get("parent", "")
        ws.content = json.dumps(content)
        ws.save(ignore_permissions=True)

    frappe.db.commit()
