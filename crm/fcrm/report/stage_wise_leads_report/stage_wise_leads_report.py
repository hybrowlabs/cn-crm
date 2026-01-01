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
    chart = get_chart_data(data)
    summary = get_summary_data(data)

    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Lead Count"),
            "fieldname": "lead_count",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Percentage"),
            "fieldname": "percentage",
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "label": _("Converted"),
            "fieldname": "converted_count",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Conversion Rate"),
            "fieldname": "conversion_rate",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Avg Days in Stage"),
            "fieldname": "avg_days_in_stage",
            "fieldtype": "Float",
            "width": 120,
            "precision": 1
        },
        {
            "label": _("Total Value"),
            "fieldname": "total_value",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Top Territory"),
            "fieldname": "top_territory",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Top Owner"),
            "fieldname": "top_owner",
            "fieldtype": "Data",
            "width": 120
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    # Get all leads with territory filtering applied
    leads_data = frappe.db.sql(f"""
        SELECT
            name, status, territory, lead_owner, converted, creation, modified,
            COALESCE(annual_revenue, 0) as annual_revenue
        FROM `tabCRM Lead`
        WHERE docstatus < 2 {conditions}
        ORDER BY status, creation DESC
    """, as_dict=1)

    # Apply territory-based filtering for current user
    from crm.api.territory_permissions import has_permission as territory_has_permission
    filtered_leads = []

    for lead in leads_data:
        # Create a mock object for territory permission checking
        mock_doc = frappe._dict({
            'territory': lead.get('territory'),
            'doctype': 'CRM Lead'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_leads.append(lead)

    # Group leads by status for analysis
    status_wise_data = {}
    total_leads = len(filtered_leads)

    for lead in filtered_leads:
        status = lead.status or "No Status"

        if status not in status_wise_data:
            status_wise_data[status] = {
                'leads': [],
                'converted_count': 0,
                'total_value': 0,
                'territories': {},
                'owners': {}
            }

        status_wise_data[status]['leads'].append(lead)

        if lead.converted:
            status_wise_data[status]['converted_count'] += 1

        status_wise_data[status]['total_value'] += lead.annual_revenue

        # Track territories and owners
        territory = lead.territory or "No Territory"
        owner = lead.lead_owner or "Unassigned"

        status_wise_data[status]['territories'][territory] = status_wise_data[status]['territories'].get(territory, 0) + 1
        status_wise_data[status]['owners'][owner] = status_wise_data[status]['owners'].get(owner, 0) + 1

    # Build report data
    report_data = []
    for status, info in status_wise_data.items():
        lead_count = len(info['leads'])
        percentage = (lead_count / total_leads * 100) if total_leads > 0 else 0
        conversion_rate = (info['converted_count'] / lead_count * 100) if lead_count > 0 else 0

        # Calculate average days in stage
        total_days = 0
        for lead in info['leads']:
            days_diff = (getdate() - getdate(lead.creation)).days
            total_days += days_diff

        avg_days = total_days / lead_count if lead_count > 0 else 0

        # Get top territory and owner
        top_territory = max(info['territories'].items(), key=lambda x: x[1])[0] if info['territories'] else "None"
        top_owner = max(info['owners'].items(), key=lambda x: x[1])[0] if info['owners'] else "None"

        report_data.append({
            'status': status,
            'lead_count': lead_count,
            'percentage': percentage,
            'converted_count': info['converted_count'],
            'conversion_rate': conversion_rate,
            'avg_days_in_stage': avg_days,
            'total_value': info['total_value'],
            'top_territory': top_territory,
            'top_owner': top_owner
        })

    # Sort by lead count descending
    report_data.sort(key=lambda x: x['lead_count'], reverse=True)

    return report_data


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

    if filters.get("territory"):
        conditions += f" AND territory = '{filters.get('territory')}'"

    if filters.get("line_of_business"):
        conditions += f" AND line_of_business = '{filters.get('line_of_business')}'"

    if filters.get("converted") is not None:
        conditions += f" AND converted = {1 if filters.get('converted') else 0}"

    return conditions


def get_chart_data(data):
    if not data:
        return None

    # Create pie chart data for status distribution
    labels = [row['status'] for row in data]
    values = [row['lead_count'] for row in data]

    return {
        "data": {
            "labels": labels,
            "datasets": [{
                "name": "Leads by Status",
                "values": values
            }]
        },
        "type": "pie",
        "height": 300,
        "colors": ["#28a745", "#ffc107", "#dc3545", "#6c757d", "#17a2b8", "#6f42c1", "#fd7e14", "#20c997"]
    }


def get_summary_data(data):
    if not data:
        return []

    total_leads = sum([row['lead_count'] for row in data])
    total_converted = sum([row['converted_count'] for row in data])
    total_value = sum([row['total_value'] for row in data])

    overall_conversion_rate = (total_converted / total_leads * 100) if total_leads > 0 else 0

    # Find best performing stage
    best_conversion_stage = max(data, key=lambda x: x['conversion_rate']) if data else None
    worst_conversion_stage = min(data, key=lambda x: x['conversion_rate']) if data else None

    # Find stage with most leads
    busiest_stage = max(data, key=lambda x: x['lead_count']) if data else None

    # Find fastest moving stage
    fastest_stage = min(data, key=lambda x: x['avg_days_in_stage']) if data else None

    return [
        {
            "value": total_leads,
            "label": "Total Leads",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": len(data),
            "label": "Active Stages",
            "indicator": "Gray",
            "datatype": "Int"
        },
        {
            "value": f"{overall_conversion_rate:.1f}%",
            "label": "Overall Conversion Rate",
            "indicator": "Green" if overall_conversion_rate >= 20 else "Orange" if overall_conversion_rate >= 10 else "Red",
            "datatype": "Data"
        },
        {
            "value": total_converted,
            "label": "Total Converted",
            "indicator": "Green",
            "datatype": "Int"
        },
        {
            "value": total_value,
            "label": "Total Pipeline Value",
            "indicator": "Blue",
            "datatype": "Currency"
        },
        {
            "value": f"{best_conversion_stage['status']} ({best_conversion_stage['conversion_rate']:.1f}%)" if best_conversion_stage else "None",
            "label": "Best Converting Stage",
            "indicator": "Green",
            "datatype": "Data"
        },
        {
            "value": f"{busiest_stage['status']} ({busiest_stage['lead_count']})" if busiest_stage else "None",
            "label": "Busiest Stage",
            "indicator": "Orange",
            "datatype": "Data"
        },
        {
            "value": f"{fastest_stage['status']} ({fastest_stage['avg_days_in_stage']:.1f}d)" if fastest_stage else "None",
            "label": "Fastest Moving Stage",
            "indicator": "Purple",
            "datatype": "Data"
        }
    ]