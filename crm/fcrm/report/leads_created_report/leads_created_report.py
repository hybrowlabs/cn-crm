# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, formatdate, flt
from datetime import datetime, timedelta
import json


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    summary = get_summary_data(data)

    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Lead"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "CRM Lead",
            "width": 120
        },
        {
            "label": _("Lead Name"),
            "fieldname": "lead_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Organization"),
            "fieldname": "organization",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Lead Owner"),
            "fieldname": "lead_owner",
            "fieldtype": "Link",
            "options": "User",
            "width": 120
        },
        {
            "label": _("Source"),
            "fieldname": "source",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 100
        },
        {
            "label": _("Line of Business"),
            "fieldname": "line_of_business",
            "fieldtype": "Link",
            "options": "CRM Line of Business",
            "width": 120
        },
        {
            "label": _("Email"),
            "fieldname": "email",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Mobile"),
            "fieldname": "mobile_no",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Converted"),
            "fieldname": "converted",
            "fieldtype": "Check",
            "width": 80
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql(f"""
        SELECT
            DATE(creation) as date,
            name,
            lead_name,
            organization,
            status,
            lead_owner,
            source,
            territory,
            line_of_business,
            email,
            mobile_no,
            converted,
            creation
        FROM `tabCRM Lead`
        WHERE docstatus < 2 {conditions}
        ORDER BY creation DESC
    """, as_dict=1)

    # Apply territory-based filtering for current user
    from crm.api.territory_permissions import has_permission as territory_has_permission
    filtered_data = []

    for row in data:
        # Create a mock object for territory permission checking
        mock_doc = frappe._dict({
            'territory': row.get('territory'),
            'doctype': 'CRM Lead'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_data.append(row)

    return filtered_data


def get_conditions(filters):
    conditions = ""

    if filters.get("from_date"):
        conditions += f" AND DATE(creation) >= '{filters.get('from_date')}'"

    if filters.get("to_date"):
        conditions += f" AND DATE(creation) <= '{filters.get('to_date')}'"

    if filters.get("lead_owner"):
        conditions += f" AND lead_owner = '{filters.get('lead_owner')}'"

    if filters.get("status"):
        if isinstance(filters.get("status"), list):
            status_list = "', '".join(filters.get("status"))
            conditions += f" AND status IN ('{status_list}')"
        else:
            conditions += f" AND status = '{filters.get('status')}'"

    if filters.get("source"):
        conditions += f" AND source = '{filters.get('source')}'"

    if filters.get("territory"):
        conditions += f" AND territory = '{filters.get('territory')}'"

    if filters.get("line_of_business"):
        conditions += f" AND line_of_business = '{filters.get('line_of_business')}'"

    if filters.get("converted") is not None:
        conditions += f" AND converted = {1 if filters.get('converted') else 0}"

    return conditions


def get_chart_data(data, filters):
    if not data:
        return None

    # Group data by date for chart
    date_wise_data = {}

    for row in data:
        date_str = formatdate(row.date)
        if date_str not in date_wise_data:
            date_wise_data[date_str] = 0
        date_wise_data[date_str] += 1

    # Sort dates
    sorted_dates = sorted(date_wise_data.keys(), key=lambda x: getdate(x))

    return {
        "data": {
            "labels": sorted_dates,
            "datasets": [{
                "name": "Leads Created",
                "values": [date_wise_data[date] for date in sorted_dates]
            }]
        },
        "type": "line",
        "height": 300,
        "colors": ["#28a745"]
    }


def get_summary_data(data):
    if not data:
        return []

    total_leads = len(data)
    converted_leads = len([d for d in data if d.converted])
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

    # Weekly and monthly analysis
    today = getdate()
    week_ago = add_days(today, -7)
    month_ago = add_days(today, -30)

    this_week_leads = len([d for d in data if getdate(d.date) >= week_ago])
    this_month_leads = len([d for d in data if getdate(d.date) >= month_ago])

    # Status breakdown
    status_counts = {}
    for row in data:
        status = row.status or "No Status"
        status_counts[status] = status_counts.get(status, 0) + 1

    # Top status
    top_status = max(status_counts.items(), key=lambda x: x[1]) if status_counts else ("None", 0)

    # Lead owners breakdown
    owner_counts = {}
    for row in data:
        owner = row.lead_owner or "Unassigned"
        owner_counts[owner] = owner_counts.get(owner, 0) + 1

    top_performer = max(owner_counts.items(), key=lambda x: x[1]) if owner_counts else ("None", 0)

    return [
        {
            "value": total_leads,
            "label": "Total Leads",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": this_week_leads,
            "label": "This Week",
            "indicator": "Green",
            "datatype": "Int"
        },
        {
            "value": this_month_leads,
            "label": "This Month",
            "indicator": "Orange",
            "datatype": "Int"
        },
        {
            "value": f"{conversion_rate:.1f}%",
            "label": "Conversion Rate",
            "indicator": "Green" if conversion_rate >= 20 else "Orange" if conversion_rate >= 10 else "Red",
            "datatype": "Data"
        },
        {
            "value": converted_leads,
            "label": "Converted Leads",
            "indicator": "Green",
            "datatype": "Int"
        },
        {
            "value": f"{top_status[0]} ({top_status[1]})",
            "label": "Top Status",
            "indicator": "Blue",
            "datatype": "Data"
        },
        {
            "value": f"{top_performer[1]} leads",
            "label": f"Top Performer: {top_performer[0]}",
            "indicator": "Purple",
            "datatype": "Data"
        },
        {
            "value": len(set([d.territory for d in data if d.territory])),
            "label": "Territories Covered",
            "indicator": "Gray",
            "datatype": "Int"
        }
    ]