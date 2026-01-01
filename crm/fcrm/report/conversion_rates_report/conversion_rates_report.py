# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months, formatdate, flt, date_diff
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
            "label": _("Dimension"),
            "fieldname": "dimension_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Dimension Value"),
            "fieldname": "dimension_value",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Total Leads"),
            "fieldname": "total_leads",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Converted Leads"),
            "fieldname": "converted_leads",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Conversion Rate %"),
            "fieldname": "conversion_rate",
            "fieldtype": "Percent",
            "width": 130
        },
        {
            "label": _("Total Deals"),
            "fieldname": "total_deals",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Won Deals"),
            "fieldname": "won_deals",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Deal Win Rate %"),
            "fieldname": "deal_win_rate",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Revenue Generated"),
            "fieldname": "revenue_generated",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Avg Deal Value"),
            "fieldname": "avg_deal_value",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Avg Conversion Time (Days)"),
            "fieldname": "avg_conversion_time",
            "fieldtype": "Float",
            "width": 170,
            "precision": 1
        }
    ]


def get_data(filters):
    # Get leads data with territory filtering
    leads_data = get_leads_data(filters)

    # Get deals data
    deals_data = get_deals_data(filters)

    # Build conversion analysis by different dimensions
    report_data = []

    # Analysis by Lead Owner
    owner_analysis = analyze_by_dimension(leads_data, deals_data, "lead_owner", "Lead Owner")
    report_data.extend(owner_analysis)

    # Analysis by Territory
    territory_analysis = analyze_by_dimension(leads_data, deals_data, "territory", "Territory")
    report_data.extend(territory_analysis)

    # Analysis by Source
    source_analysis = analyze_by_dimension(leads_data, deals_data, "source", "Source")
    report_data.extend(source_analysis)

    # Analysis by Line of Business
    lob_analysis = analyze_by_dimension(leads_data, deals_data, "line_of_business", "Line of Business")
    report_data.extend(lob_analysis)

    # Analysis by Status
    status_analysis = analyze_by_dimension(leads_data, deals_data, "status", "Lead Status")
    report_data.extend(status_analysis)

    return report_data


def get_leads_data(filters):
    conditions = get_conditions(filters, "CRM Lead")

    leads_data = frappe.db.sql(f"""
        SELECT
            name, lead_owner, territory, source, line_of_business, status,
            converted, creation, annual_revenue
        FROM `tabCRM Lead`
        WHERE docstatus < 2 {conditions}
    """, as_dict=1)

    # Apply territory-based filtering
    from crm.api.territory_permissions import has_permission as territory_has_permission
    filtered_leads = []

    for lead in leads_data:
        mock_doc = frappe._dict({
            'territory': lead.get('territory'),
            'doctype': 'CRM Lead'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_leads.append(lead)

    return filtered_leads


def get_deals_data(filters):
    conditions = get_conditions(filters, "CRM Deal")

    deals_data = frappe.db.sql(f"""
        SELECT
            d.name, d.deal_owner, d.deal_value, d.status, d.creation, d.close_date,
            l.lead_owner, l.territory, l.source, l.line_of_business, l.status as lead_status,
            l.creation as lead_creation
        FROM `tabCRM Deal` d
        LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE d.docstatus < 2 {conditions.replace('lead_owner', 'l.lead_owner').replace('territory', 'l.territory').replace('source', 'l.source').replace('line_of_business', 'l.line_of_business')}
    """, as_dict=1)

    # Apply territory-based filtering
    from crm.api.territory_permissions import has_permission as territory_has_permission
    filtered_deals = []

    for deal in deals_data:
        mock_doc = frappe._dict({
            'territory': deal.get('territory'),
            'doctype': 'CRM Deal'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_deals.append(deal)

    return filtered_deals


def analyze_by_dimension(leads_data, deals_data, dimension_field, dimension_name):
    analysis_data = {}

    # Analyze leads by dimension
    for lead in leads_data:
        dim_value = lead.get(dimension_field) or f"No {dimension_name}"

        if dim_value not in analysis_data:
            analysis_data[dim_value] = {
                'total_leads': 0,
                'converted_leads': 0,
                'total_deals': 0,
                'won_deals': 0,
                'total_revenue': 0,
                'conversion_times': []
            }

        analysis_data[dim_value]['total_leads'] += 1
        if lead.get('converted'):
            analysis_data[dim_value]['converted_leads'] += 1

    # Analyze deals by dimension
    for deal in deals_data:
        dim_value = deal.get(dimension_field) or f"No {dimension_name}"

        if dim_value not in analysis_data:
            analysis_data[dim_value] = {
                'total_leads': 0,
                'converted_leads': 0,
                'total_deals': 0,
                'won_deals': 0,
                'total_revenue': 0,
                'conversion_times': []
            }

        analysis_data[dim_value]['total_deals'] += 1

        if deal.get('status') == 'Won':
            analysis_data[dim_value]['won_deals'] += 1
            analysis_data[dim_value]['total_revenue'] += deal.get('deal_value', 0)

        # Calculate conversion time if available
        if deal.get('lead_creation') and deal.get('close_date'):
            conversion_days = date_diff(deal.get('close_date'), deal.get('lead_creation'))
            if conversion_days >= 0:
                analysis_data[dim_value]['conversion_times'].append(conversion_days)

    # Build report rows for this dimension
    report_rows = []
    for dim_value, data in analysis_data.items():
        total_leads = data['total_leads']
        converted_leads = data['converted_leads']
        total_deals = data['total_deals']
        won_deals = data['won_deals']

        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        deal_win_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0
        avg_deal_value = (data['total_revenue'] / won_deals) if won_deals > 0 else 0
        avg_conversion_time = sum(data['conversion_times']) / len(data['conversion_times']) if data['conversion_times'] else 0

        report_rows.append({
            'dimension_name': dimension_name,
            'dimension_value': dim_value,
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'conversion_rate': conversion_rate,
            'total_deals': total_deals,
            'won_deals': won_deals,
            'deal_win_rate': deal_win_rate,
            'revenue_generated': data['total_revenue'],
            'avg_deal_value': avg_deal_value,
            'avg_conversion_time': avg_conversion_time
        })

    # Sort by conversion rate descending
    report_rows.sort(key=lambda x: x['conversion_rate'], reverse=True)

    return report_rows


def get_conditions(filters, doctype):
    conditions = ""

    if filters.get("from_date"):
        conditions += f" AND DATE(creation) >= '{filters.get('from_date')}'"

    if filters.get("to_date"):
        conditions += f" AND DATE(creation) <= '{filters.get('to_date')}'"

    if filters.get("lead_owner"):
        conditions += f" AND lead_owner = '{filters.get('lead_owner')}'"

    if filters.get("territory"):
        conditions += f" AND territory = '{filters.get('territory')}'"

    if filters.get("source"):
        conditions += f" AND source = '{filters.get('source')}'"

    if filters.get("line_of_business"):
        conditions += f" AND line_of_business = '{filters.get('line_of_business')}'"

    return conditions


def get_chart_data(data, filters):
    if not data:
        return None

    # Create chart showing conversion rates by dimension value
    # Group by dimension name for better visualization
    chart_data = {}

    for row in data:
        dim_name = row['dimension_name']
        if dim_name not in chart_data:
            chart_data[dim_name] = {
                'labels': [],
                'values': []
            }

        # Take top 5 performers per dimension to avoid overcrowding
        if len(chart_data[dim_name]['labels']) < 5:
            chart_data[dim_name]['labels'].append(row['dimension_value'])
            chart_data[dim_name]['values'].append(row['conversion_rate'])

    # Create datasets for each dimension
    datasets = []
    colors = ["#28a745", "#ffc107", "#dc3545", "#6c757d", "#17a2b8"]

    for i, (dim_name, chart_info) in enumerate(chart_data.items()):
        datasets.append({
            "name": f"{dim_name} Conversion Rate",
            "values": chart_info['values'],
            "chartType": "bar"
        })

    # Use labels from the first dimension (or combine all unique labels)
    all_labels = []
    for dim_name, chart_info in chart_data.items():
        all_labels.extend(chart_info['labels'])

    unique_labels = list(dict.fromkeys(all_labels))  # Preserve order while removing duplicates

    return {
        "data": {
            "labels": unique_labels[:10],  # Limit to avoid overcrowding
            "datasets": datasets[:2]  # Show max 2 datasets for clarity
        },
        "type": "bar",
        "height": 300,
        "colors": colors
    }


def get_summary_data(data):
    if not data:
        return []

    # Calculate overall metrics
    total_leads = sum([row['total_leads'] for row in data])
    total_converted = sum([row['converted_leads'] for row in data])
    total_deals = sum([row['total_deals'] for row in data])
    total_won = sum([row['won_deals'] for row in data])
    total_revenue = sum([row['revenue_generated'] for row in data])

    overall_conversion_rate = (total_converted / total_leads * 100) if total_leads > 0 else 0
    overall_win_rate = (total_won / total_deals * 100) if total_deals > 0 else 0
    avg_deal_value = (total_revenue / total_won) if total_won > 0 else 0

    # Find best performers
    best_converter = max(data, key=lambda x: x['conversion_rate']) if data else None
    best_deal_closer = max(data, key=lambda x: x['deal_win_rate']) if data else None
    highest_revenue = max(data, key=lambda x: x['revenue_generated']) if data else None

    return [
        {
            "value": f"{overall_conversion_rate:.1f}%",
            "label": "Overall Lead Conversion Rate",
            "indicator": "Green" if overall_conversion_rate >= 20 else "Orange" if overall_conversion_rate >= 10 else "Red",
            "datatype": "Data"
        },
        {
            "value": f"{overall_win_rate:.1f}%",
            "label": "Overall Deal Win Rate",
            "indicator": "Green" if overall_win_rate >= 30 else "Orange" if overall_win_rate >= 20 else "Red",
            "datatype": "Data"
        },
        {
            "value": total_revenue,
            "label": "Total Revenue Generated",
            "indicator": "Blue",
            "datatype": "Currency"
        },
        {
            "value": avg_deal_value,
            "label": "Average Deal Value",
            "indicator": "Purple",
            "datatype": "Currency"
        },
        {
            "value": f"{best_converter['dimension_value']} ({best_converter['conversion_rate']:.1f}%)" if best_converter else "None",
            "label": "Best Lead Converter",
            "indicator": "Green",
            "datatype": "Data"
        },
        {
            "value": f"{best_deal_closer['dimension_value']} ({best_deal_closer['deal_win_rate']:.1f}%)" if best_deal_closer else "None",
            "label": "Best Deal Closer",
            "indicator": "Green",
            "datatype": "Data"
        },
        {
            "value": f"{highest_revenue['dimension_value']}" if highest_revenue else "None",
            "label": "Highest Revenue Generator",
            "indicator": "Blue",
            "datatype": "Data"
        },
        {
            "value": len(set([row['dimension_value'] for row in data if row['dimension_name'] == 'Territory'])),
            "label": "Territories Analyzed",
            "indicator": "Gray",
            "datatype": "Int"
        }
    ]