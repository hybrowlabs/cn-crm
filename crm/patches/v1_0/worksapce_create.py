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
            "charts": [
                {
                    "chart_name": "Product-wise Volume (CEO)",
                    "type": "Bar", 
                    "chart_type": "Group By", 
                    "document_type": "CRM Deal",
                    "based_on": "product_type",
                    "value_based_on": "final_volume_kg",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"]])
                },
                {
                    "chart_name": "Pipeline Volume by Stage (CEO)",
                    "type": "Bar", 
                    "chart_type": "Sum", 
                    "document_type": "CRM Deal",
                    "based_on": "status",
                    "value_based_on": "expected_monthly_volume",
                    "filters_json": json.dumps([["CRM Deal", "status", "not in", ["Won", "Lost"]]])
                },
                {
                    "chart_name": "Top Pain Categories (CEO)",
                    "type": "Bar", 
                    "chart_type": "Group By", 
                    "document_type": "CRM Deal",
                    "based_on": "primary_pain_category",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"]])
                }
            ],
            "cards": [
                {
                    "label": "Total Booked Volume",
                    "function": "Sum",
                    "aggregate_function_based_on": "final_volume_kg",
                    "document_type": "CRM Deal",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"]])
                },
                {
                    "label": "Total Revenue",
                    "function": "Sum",
                    "aggregate_function_based_on": "deal_value",
                    "document_type": "CRM Deal",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"]])
                },
                {
                    "label": "Trial Success Rate",
                    "function": "Count",
                    "aggregate_function_based_on": "name",
                    "document_type": "CRM Deal",
                    "filters_json": json.dumps([["CRM Deal", "trial_outcome", "=", "Qualified"]])
                }
            ]
        },
        # 2. Sales Manager Dashboard
        {
            "name": "Sales Manager Dashboard",
            "parent": "Frappe CRM",
            "charts": [
                {
                    "chart_name": "Booked Volume by Rep (Mgr)",
                    "type": "Bar",
                    "chart_type": "Sum",
                    "document_type": "CRM Deal",
                    "based_on": "deal_owner",
                    "value_based_on": "final_volume_kg",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"]])
                },
                {
                    "chart_name": "Pipeline Volume by Rep (Mgr)",
                    "type": "Bar",
                    "chart_type": "Sum",
                    "document_type": "CRM Deal",
                    "based_on": "deal_owner",
                    "value_based_on": "expected_monthly_volume",
                    "filters_json": json.dumps([["CRM Deal", "status", "not in", ["Won", "Lost"]]])
                },
                 {
                    "chart_name": "Win Rate by Rep (Mgr)",
                    "type": "Bar",
                    "chart_type": "Count",
                    "document_type": "CRM Deal",
                    "based_on": "deal_owner",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"]])
                },
                 {
                    "chart_name": "Pain-wise Pipeline (Mgr)",
                    "type": "Bar",
                    "chart_type": "Count",
                    "document_type": "CRM Deal",
                    "based_on": "primary_pain_category",
                    "filters_json": json.dumps([["CRM Deal", "status", "not in", ["Won", "Lost"]]])
                }
            ],
            "cards": []
        },
        # 3. Account Manager Dashboard
        {
            "name": "Account Manager Dashboard",
            "parent": "Frappe CRM",
            "charts": [
                {
                    "chart_name": "My Pipeline Volume",
                    "type": "Bar",
                    "chart_type": "Sum",
                    "document_type": "CRM Deal",
                    "based_on": "status",
                    "value_based_on": "expected_monthly_volume",
                    "filters_json": json.dumps([["CRM Deal", "status", "not in", ["Won", "Lost"]]]),
                    "use_user_filter": 1
                },
                {
                    "chart_name": "My Trial Status",
                    "type": "Donut",
                    "chart_type": "Count",
                    "document_type": "CRM Deal",
                    "based_on": "trial_outcome",
                    "filters_json": json.dumps([]),
                    "use_user_filter": 1
                },
                {
                    "chart_name": "My Pain Mix",
                    "type": "Pie",
                    "chart_type": "Count",
                    "document_type": "CRM Deal",
                    "based_on": "primary_pain_category",
                    "filters_json": json.dumps([]),
                    "use_user_filter": 1
                }
            ],
            "cards": [
                 {
                    "label": "My Booked Volume",
                    "function": "Sum",
                    "aggregate_function_based_on": "final_volume_kg",
                    "document_type": "CRM Deal",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"], ["CRM Deal", "deal_owner", "=", frappe.session.user]])
                }
            ]
        },
        # 4. Peer Comparison Dashboard
        {
            "name": "Peer Comparison Dashboard",
            "parent": "Frappe CRM",
            "charts": [
                {
                    "chart_name": "Booked Volume by Salesperson",
                    "type": "Bar",
                    "chart_type": "Sum",
                    "document_type": "CRM Deal",
                    "based_on": "deal_owner",
                    "value_based_on": "final_volume_kg",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"]])
                },
                 {
                    "chart_name": "Pipeline Volume by Salesperson",
                    "type": "Bar",
                    "chart_type": "Sum",
                    "document_type": "CRM Deal",
                    "based_on": "deal_owner",
                    "value_based_on": "expected_monthly_volume",
                    "filters_json": json.dumps([["CRM Deal", "status", "not in", ["Won", "Lost"]]])
                }
            ],
            "cards": []
        },
        # 5. Repeat Order Dashboard
         {
            "name": "Repeat Order Dashboard",
            "parent": "Frappe CRM",
            "charts": [
               {
                    "chart_name": "Repeat Volume Trend",
                    "type": "Line",
                    "chart_type": "Sum",
                    "document_type": "CRM Deal",
                    "based_on": "order_date",
                    "timeseries": 1,
                    "value_based_on": "final_volume_kg",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"], ["CRM Deal", "source", "=", "Existing Customer"]])
                },
                {
                    "chart_name": "Top Repeat Accounts",
                    "type": "Bar",
                    "chart_type": "Sum",
                    "document_type": "CRM Deal",
                    "based_on": "organization",
                    "value_based_on": "final_volume_kg",
                    "filters_json": json.dumps([["CRM Deal", "status", "=", "Won"], ["CRM Deal", "source", "=", "Existing Customer"]])
                }
            ],
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
    # 1. Create Charts
    chart_refs = []
    for chart_def in config.get("charts", []):
        name = chart_def.pop("chart_name")
        use_user_filter = chart_def.pop("use_user_filter", 0)
        
        if not frappe.db.exists("Dashboard Chart", name):
            doc = frappe.new_doc("Dashboard Chart")
            doc.chart_name = name
            doc.update(chart_def)
            doc.insert(ignore_permissions=True)
        else:
            doc = frappe.get_doc("Dashboard Chart", name)
            doc.update(chart_def)
            doc.save(ignore_permissions=True)
            
        chart_refs.append({"chart": name, "label": name})

    # 2. Create Number Cards
    card_refs = []
    for card_def in config.get("cards", []):
        label = card_def.pop("label")
        if not frappe.db.exists("Number Card", label):
            doc = frappe.new_doc("Number Card")
            doc.label = label
            doc.update(card_def)
            doc.insert(ignore_permissions=True)
        else:
             doc = frappe.get_doc("Number Card", label)
             doc.update(card_def)
             doc.save(ignore_permissions=True)
        card_refs.append({"card": label})

    # 3. Create/Update Workspace
    ws_name = config["name"]
    content = []
    
    # Add Header
    content.append({"type": "header", "data": {"text": ws_name, "col": 12}})
    
    # Add Cards
    if card_refs:
        for card in card_refs:
             content.append({"type": "card", "data": {"card_name": card["card"], "col": 4}})
    
    # Add Charts
    if chart_refs:
        for chart in chart_refs:
            content.append({"type": "chart", "data": {"chart_name": chart["chart"], "col": 12}})

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
