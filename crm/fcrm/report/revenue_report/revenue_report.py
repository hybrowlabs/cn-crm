# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months, formatdate, flt, date_diff, cint
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
            "label": _("Period"),
            "fieldname": "period",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Won Deals"),
            "fieldname": "won_deals",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Total Revenue"),
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Average Deal Value"),
            "fieldname": "avg_deal_value",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Pipeline Value"),
            "fieldname": "pipeline_value",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Pipeline Count"),
            "fieldname": "pipeline_count",
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
            "label": _("Top Territory"),
            "fieldname": "top_territory",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Top Deal Owner"),
            "fieldname": "top_deal_owner",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Growth %"),
            "fieldname": "growth_rate",
            "fieldtype": "Percent",
            "width": 100
        }
    ]


def get_data(filters):
    # Determine grouping period
    group_by = filters.get("group_by", "Monthly")

    # Get deals data with territory filtering
    deals_data = get_deals_data(filters)

    if group_by == "Daily":
        return get_daily_revenue_data(deals_data)
    elif group_by == "Weekly":
        return get_weekly_revenue_data(deals_data)
    elif group_by == "Monthly":
        return get_monthly_revenue_data(deals_data)
    elif group_by == "Quarterly":
        return get_quarterly_revenue_data(deals_data)
    else:
        return get_monthly_revenue_data(deals_data)


def get_deals_data(filters):
    conditions = get_conditions(filters)

    # Get deals with lead information for territory
    deals_data = frappe.db.sql(f"""
        SELECT
            d.name, d.deal_value, d.status, d.deal_owner, d.creation, d.close_date, d.probability,
            l.territory, l.lead_owner, l.organization
        FROM `tabCRM Deal` d
        LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE d.docstatus < 2 {conditions}
        ORDER BY d.creation DESC
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


def get_monthly_revenue_data(deals_data):
    monthly_data = {}

    for deal in deals_data:
        # Use close_date for won deals, creation date for others
        if deal.status == "Won" and deal.close_date:
            period_date = getdate(deal.close_date)
        else:
            period_date = getdate(deal.creation)

        period_key = period_date.strftime("%Y-%m")
        period_label = period_date.strftime("%b %Y")

        if period_key not in monthly_data:
            monthly_data[period_key] = {
                'period': period_label,
                'won_deals': [],
                'pipeline_deals': [],
                'territories': {},
                'deal_owners': {}
            }

        # Categorize deals
        if deal.status == "Won":
            monthly_data[period_key]['won_deals'].append(deal)
        elif deal.status not in ["Lost", "Closed"]:
            monthly_data[period_key]['pipeline_deals'].append(deal)

        # Track territories and owners
        territory = deal.territory or "No Territory"
        owner = deal.deal_owner or "Unassigned"

        monthly_data[period_key]['territories'][territory] = monthly_data[period_key]['territories'].get(territory, 0) + (deal.deal_value or 0)
        monthly_data[period_key]['deal_owners'][owner] = monthly_data[period_key]['deal_owners'].get(owner, 0) + (deal.deal_value or 0)

    # Process the data
    report_data = []
    previous_revenue = 0

    for period_key in sorted(monthly_data.keys()):
        data = monthly_data[period_key]

        won_deals_count = len(data['won_deals'])
        total_revenue = sum([deal.deal_value or 0 for deal in data['won_deals']])
        avg_deal_value = total_revenue / won_deals_count if won_deals_count > 0 else 0

        pipeline_count = len(data['pipeline_deals'])
        pipeline_value = sum([deal.deal_value or 0 for deal in data['pipeline_deals']])

        total_deals_period = won_deals_count + pipeline_count
        conversion_rate = (won_deals_count / total_deals_period * 100) if total_deals_period > 0 else 0

        # Find top territory and owner
        top_territory = max(data['territories'].items(), key=lambda x: x[1])[0] if data['territories'] else "None"
        top_deal_owner = max(data['deal_owners'].items(), key=lambda x: x[1])[0] if data['deal_owners'] else "None"

        # Calculate growth rate
        growth_rate = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0

        report_data.append({
            'period': data['period'],
            'won_deals': won_deals_count,
            'total_revenue': total_revenue,
            'avg_deal_value': avg_deal_value,
            'pipeline_value': pipeline_value,
            'pipeline_count': pipeline_count,
            'conversion_rate': conversion_rate,
            'top_territory': top_territory,
            'top_deal_owner': top_deal_owner,
            'growth_rate': growth_rate
        })

        previous_revenue = total_revenue

    return report_data


def get_quarterly_revenue_data(deals_data):
    quarterly_data = {}

    for deal in deals_data:
        if deal.status == "Won" and deal.close_date:
            period_date = getdate(deal.close_date)
        else:
            period_date = getdate(deal.creation)

        quarter = (period_date.month - 1) // 3 + 1
        period_key = f"{period_date.year}-Q{quarter}"
        period_label = f"Q{quarter} {period_date.year}"

        if period_key not in quarterly_data:
            quarterly_data[period_key] = {
                'period': period_label,
                'won_deals': [],
                'pipeline_deals': [],
                'territories': {},
                'deal_owners': {}
            }

        if deal.status == "Won":
            quarterly_data[period_key]['won_deals'].append(deal)
        elif deal.status not in ["Lost", "Closed"]:
            quarterly_data[period_key]['pipeline_deals'].append(deal)

        territory = deal.territory or "No Territory"
        owner = deal.deal_owner or "Unassigned"

        quarterly_data[period_key]['territories'][territory] = quarterly_data[period_key]['territories'].get(territory, 0) + (deal.deal_value or 0)
        quarterly_data[period_key]['deal_owners'][owner] = quarterly_data[period_key]['deal_owners'].get(owner, 0) + (deal.deal_value or 0)

    # Process quarterly data similar to monthly
    report_data = []
    previous_revenue = 0

    for period_key in sorted(quarterly_data.keys()):
        data = quarterly_data[period_key]

        won_deals_count = len(data['won_deals'])
        total_revenue = sum([deal.deal_value or 0 for deal in data['won_deals']])
        avg_deal_value = total_revenue / won_deals_count if won_deals_count > 0 else 0

        pipeline_count = len(data['pipeline_deals'])
        pipeline_value = sum([deal.deal_value or 0 for deal in data['pipeline_deals']])

        total_deals_period = won_deals_count + pipeline_count
        conversion_rate = (won_deals_count / total_deals_period * 100) if total_deals_period > 0 else 0

        top_territory = max(data['territories'].items(), key=lambda x: x[1])[0] if data['territories'] else "None"
        top_deal_owner = max(data['deal_owners'].items(), key=lambda x: x[1])[0] if data['deal_owners'] else "None"

        growth_rate = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0

        report_data.append({
            'period': data['period'],
            'won_deals': won_deals_count,
            'total_revenue': total_revenue,
            'avg_deal_value': avg_deal_value,
            'pipeline_value': pipeline_value,
            'pipeline_count': pipeline_count,
            'conversion_rate': conversion_rate,
            'top_territory': top_territory,
            'top_deal_owner': top_deal_owner,
            'growth_rate': growth_rate
        })

        previous_revenue = total_revenue

    return report_data


def get_conditions(filters):
    conditions = ""

    if filters.get("from_date"):
        conditions += f" AND DATE(d.creation) >= '{filters.get('from_date')}'"

    if filters.get("to_date"):
        conditions += f" AND DATE(d.creation) <= '{filters.get('to_date')}'"

    if filters.get("deal_owner"):
        conditions += f" AND d.deal_owner = '{filters.get('deal_owner')}'"

    if filters.get("status"):
        if isinstance(filters.get("status"), list):
            status_list = "', '".join(filters.get("status"))
            conditions += f" AND d.status IN ('{status_list}')"
        else:
            conditions += f" AND d.status = '{filters.get('status')}'"

    if filters.get("territory"):
        conditions += f" AND l.territory = '{filters.get('territory')}'"

    if filters.get("line_of_business"):
        conditions += f" AND l.line_of_business = '{filters.get('line_of_business')}'"

    return conditions


def get_chart_data(data, filters):
    if not data:
        return None

    labels = [row['period'] for row in data]
    revenue_values = [row['total_revenue'] for row in data]
    pipeline_values = [row['pipeline_value'] for row in data]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Revenue (Won)",
                    "values": revenue_values,
                    "chartType": "bar"
                },
                {
                    "name": "Pipeline Value",
                    "values": pipeline_values,
                    "chartType": "line"
                }
            ]
        },
        "type": "line",
        "height": 300,
        "colors": ["#28a745", "#ffc107"]
    }


def get_summary_data(data):
    if not data:
        return []

    total_revenue = sum([row['total_revenue'] for row in data])
    total_won_deals = sum([row['won_deals'] for row in data])
    total_pipeline_value = sum([row['pipeline_value'] for row in data])
    total_pipeline_count = sum([row['pipeline_count'] for row in data])

    avg_deal_value = total_revenue / total_won_deals if total_won_deals > 0 else 0

    # Calculate overall conversion rate
    total_deals = total_won_deals + total_pipeline_count
    overall_conversion_rate = (total_won_deals / total_deals * 100) if total_deals > 0 else 0

    # Find best performing period
    best_period = max(data, key=lambda x: x['total_revenue']) if data else None
    best_growth_period = max(data, key=lambda x: x['growth_rate']) if data else None

    # Calculate average monthly growth
    growth_rates = [row['growth_rate'] for row in data if row['growth_rate'] != 0]
    avg_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0

    return [
        {
            "value": total_revenue,
            "label": "Total Revenue",
            "indicator": "Green",
            "datatype": "Currency"
        },
        {
            "value": total_won_deals,
            "label": "Total Won Deals",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": avg_deal_value,
            "label": "Average Deal Value",
            "indicator": "Purple",
            "datatype": "Currency"
        },
        {
            "value": total_pipeline_value,
            "label": "Total Pipeline Value",
            "indicator": "Orange",
            "datatype": "Currency"
        },
        {
            "value": f"{overall_conversion_rate:.1f}%",
            "label": "Overall Conversion Rate",
            "indicator": "Green" if overall_conversion_rate >= 30 else "Orange" if overall_conversion_rate >= 20 else "Red",
            "datatype": "Data"
        },
        {
            "value": f"{best_period['period']} ({best_period['total_revenue']:,.0f})" if best_period else "None",
            "label": "Best Revenue Period",
            "indicator": "Green",
            "datatype": "Data"
        },
        {
            "value": f"{avg_growth_rate:.1f}%",
            "label": "Average Growth Rate",
            "indicator": "Green" if avg_growth_rate >= 10 else "Orange" if avg_growth_rate >= 5 else "Red",
            "datatype": "Data"
        },
        {
            "value": len(data),
            "label": "Periods Analyzed",
            "indicator": "Gray",
            "datatype": "Int"
        }
    ]