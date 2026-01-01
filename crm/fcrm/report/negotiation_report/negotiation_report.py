# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, formatdate, flt, date_diff
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
            "label": _("Deal ID"),
            "fieldname": "deal_id",
            "fieldtype": "Link",
            "options": "CRM Deal",
            "width": 120
        },
        {
            "label": _("Deal Name"),
            "fieldname": "deal_name",
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
            "label": _("Deal Value"),
            "fieldname": "deal_value",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Current Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Deal Owner"),
            "fieldname": "deal_owner",
            "fieldtype": "Link",
            "options": "User",
            "width": 150
        },
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 120
        },
        {
            "label": _("Negotiation Stage"),
            "fieldname": "negotiation_stage",
            "fieldtype": "Data",
            "width": 130
        },
        {
            "label": _("Days in Negotiation"),
            "fieldname": "days_in_negotiation",
            "fieldtype": "Int",
            "width": 140
        },
        {
            "label": _("Proposal Count"),
            "fieldname": "proposal_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Last Activity"),
            "fieldname": "last_activity_date",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Days Since Activity"),
            "fieldname": "days_since_activity",
            "fieldtype": "Int",
            "width": 140
        },
        {
            "label": _("Negotiation Score"),
            "fieldname": "negotiation_score",
            "fieldtype": "Float",
            "width": 130,
            "precision": 1
        },
        {
            "label": _("Risk Level"),
            "fieldname": "risk_level",
            "fieldtype": "Data",
            "width": 100
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    # Get deals in negotiation phases
    deals = frappe.db.sql(f"""
        SELECT d.name, d.deal_name, d.organization, d.deal_value, d.status,
               d.deal_owner, l.territory, d.creation, d.modified
        FROM `tabCRM Deal` d
        LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE d.docstatus < 2
        AND d.status IN ('Proposal', 'Negotiation', 'Qualified', 'Decision Pending')
        {conditions}
        ORDER BY d.deal_value DESC
    """, as_dict=1)

    # Apply territory filtering
    filtered_deals = []
    from crm.api.territory_permissions import has_permission as territory_has_permission

    for deal in deals:
        # Create a mock document for permission checking
        mock_doc = frappe._dict({
            'territory': deal.get('territory'),
            'doctype': 'CRM Deal'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_deals.append(deal)

    report_data = []

    for deal in filtered_deals:
        # Get negotiation metrics
        negotiation_data = get_negotiation_metrics(deal)

        # Calculate negotiation score and risk
        score = calculate_negotiation_score(negotiation_data)
        risk_level = determine_risk_level(negotiation_data, score)

        row = {
            'deal_id': deal.name,
            'deal_name': deal.deal_name,
            'organization': deal.organization or '-',
            'deal_value': deal.deal_value or 0,
            'status': deal.status,
            'deal_owner': deal.deal_owner,
            'territory': deal.territory,
            'negotiation_stage': negotiation_data['stage'],
            'days_in_negotiation': negotiation_data['days_in_negotiation'],
            'proposal_count': negotiation_data['proposal_count'],
            'last_activity_date': negotiation_data['last_activity_date'],
            'days_since_activity': negotiation_data['days_since_activity'],
            'negotiation_score': score,
            'risk_level': risk_level
        }

        report_data.append(row)

    return report_data


def get_negotiation_metrics(deal):
    """Calculate detailed negotiation metrics for a deal"""

    # Get proposal/quotation count
    proposal_count = frappe.db.count("CRM Quotation", {
        "deal": deal.name,
        "docstatus": ["<", 2]
    })

    # Get timeline activities related to negotiation
    negotiation_activities = frappe.db.sql("""
        SELECT timeline_content, creation
        FROM `tabCRM Note`
        WHERE reference_doctype = 'CRM Deal'
        AND reference_name = %s
        AND (
            timeline_content LIKE '%proposal%'
            OR timeline_content LIKE '%negotiation%'
            OR timeline_content LIKE '%price%'
            OR timeline_content LIKE '%discount%'
            OR timeline_content LIKE '%terms%'
        )
        ORDER BY creation DESC
        LIMIT 1
    """, (deal.name,), as_dict=1)

    # Calculate days in negotiation
    negotiation_start_date = get_negotiation_start_date(deal.name)
    days_in_negotiation = 0
    if negotiation_start_date:
        days_in_negotiation = date_diff(frappe.utils.nowdate(), negotiation_start_date)

    # Get last activity date
    last_activity = frappe.db.sql("""
        SELECT MAX(creation) as last_activity
        FROM `tabCRM Note`
        WHERE reference_doctype = 'CRM Deal'
        AND reference_name = %s
        AND note_type = 'Activity Timeline'
    """, (deal.name,), as_dict=1)

    last_activity_date = None
    days_since_activity = 0

    if last_activity and last_activity[0].get('last_activity'):
        last_activity_date = last_activity[0]['last_activity'].date()
        days_since_activity = date_diff(frappe.utils.nowdate(), last_activity_date)

    # Determine negotiation stage
    stage = determine_negotiation_stage(deal, negotiation_activities)

    return {
        'stage': stage,
        'days_in_negotiation': max(days_in_negotiation, 0),
        'proposal_count': proposal_count,
        'last_activity_date': last_activity_date,
        'days_since_activity': max(days_since_activity, 0),
        'deal_value': deal.deal_value or 0
    }


def get_negotiation_start_date(deal_name):
    """Find when negotiation phase started"""

    # Look for status changes to negotiation-related statuses
    negotiation_statuses = ['Proposal', 'Negotiation', 'Qualified']

    negotiation_activity = frappe.db.sql("""
        SELECT creation
        FROM `tabCRM Note`
        WHERE reference_doctype = 'CRM Deal'
        AND reference_name = %s
        AND note_type = 'Activity Timeline'
        AND (timeline_content LIKE '%Proposal%' OR timeline_content LIKE '%Qualified%')
        ORDER BY creation ASC
        LIMIT 1
    """, (deal_name,), as_dict=1)

    if negotiation_activity:
        return negotiation_activity[0]['creation'].date()

    # Fallback to deal creation date
    return frappe.db.get_value("CRM Deal", deal_name, "creation")


def determine_negotiation_stage(deal, activities):
    """Determine current negotiation stage"""

    # Check for recent negotiation keywords in activities
    if activities:
        content = activities[0].get('timeline_content', '').lower()
        if 'price' in content or 'discount' in content:
            return "Price Negotiation"
        elif 'terms' in content:
            return "Terms Discussion"
        elif 'proposal' in content:
            return "Proposal Sent"

    # Fallback to deal status
    status_mapping = {
        'Proposal': 'Proposal Sent',
        'Negotiation': 'Active Negotiation',
        'Qualified': 'Initial Discussion',
        'Decision Pending': 'Awaiting Decision'
    }

    return status_mapping.get(deal.status, 'Initial Discussion')


def calculate_negotiation_score(metrics):
    """Calculate weighted negotiation score"""
    score = 50  # Base score

    # Deal value impact (20% of score)
    if metrics['deal_value'] > 100000:
        score += 15
    elif metrics['deal_value'] > 50000:
        score += 10
    elif metrics['deal_value'] > 10000:
        score += 5

    # Activity recency (30% of score)
    days_since_activity = metrics['days_since_activity']
    if days_since_activity <= 3:
        score += 20
    elif days_since_activity <= 7:
        score += 15
    elif days_since_activity <= 14:
        score += 5
    else:
        score -= 10

    # Negotiation duration (25% of score)
    days_in_negotiation = metrics['days_in_negotiation']
    if days_in_negotiation <= 7:
        score += 15
    elif days_in_negotiation <= 30:
        score += 10
    elif days_in_negotiation <= 60:
        score += 0
    else:
        score -= 15

    # Proposal count (25% of score)
    proposal_count = metrics['proposal_count']
    if proposal_count == 1:
        score += 10
    elif proposal_count == 2:
        score += 5
    elif proposal_count >= 3:
        score -= 5

    return max(0, min(100, score))


def determine_risk_level(metrics, score):
    """Determine risk level based on metrics"""

    if score >= 70:
        return "Low"
    elif score >= 50:
        if metrics['days_since_activity'] > 14:
            return "High"
        return "Medium"
    else:
        return "High"


def get_conditions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += f" AND DATE(d.creation) >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        conditions += f" AND DATE(d.creation) <= '{filters.get('to_date')}'"
    if filters.get("deal_owner"):
        conditions += f" AND d.deal_owner = '{filters.get('deal_owner')}'"
    if filters.get("territory"):
        conditions += f" AND l.territory = '{filters.get('territory')}'"
    return conditions


def get_chart_data(data):
    if not data:
        return None

    # Negotiation stages distribution
    stage_counts = {}
    for row in data:
        stage = row['negotiation_stage']
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    labels = list(stage_counts.keys())
    values = list(stage_counts.values())

    return {
        "data": {
            "labels": labels,
            "datasets": [{
                "name": "Deals by Negotiation Stage",
                "values": values
            }]
        },
        "type": "pie",
        "height": 300,
        "colors": ["#28a745", "#17a2b8", "#ffc107", "#dc3545", "#6f42c1"]
    }


def get_summary_data(data):
    if not data:
        return []

    total_deals = len(data)
    total_value = sum([row['deal_value'] for row in data])
    avg_negotiation_days = sum([row['days_in_negotiation'] for row in data]) / total_deals if total_deals > 0 else 0

    # Risk distribution
    risk_counts = {'Low': 0, 'Medium': 0, 'High': 0}
    for row in data:
        risk_level = row['risk_level']
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

    # Stale deals (no activity > 14 days)
    stale_deals = len([row for row in data if row['days_since_activity'] > 14])

    # High-value deals (>$50k)
    high_value_deals = len([row for row in data if row['deal_value'] > 50000])

    # Top negotiation score
    top_score = max([row['negotiation_score'] for row in data]) if data else 0

    return [
        {
            "value": total_deals,
            "label": "Deals in Negotiation",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": total_value,
            "label": "Total Pipeline Value",
            "indicator": "Green",
            "datatype": "Currency"
        },
        {
            "value": f"{avg_negotiation_days:.1f}",
            "label": "Avg Days in Negotiation",
            "indicator": "Gray",
            "datatype": "Data"
        },
        {
            "value": risk_counts['High'],
            "label": "High Risk Deals",
            "indicator": "Red",
            "datatype": "Int"
        },
        {
            "value": stale_deals,
            "label": "Stale Deals (>14 days)",
            "indicator": "Orange",
            "datatype": "Int"
        },
        {
            "value": high_value_deals,
            "label": "High Value Deals (>$50k)",
            "indicator": "Purple",
            "datatype": "Int"
        },
        {
            "value": f"{top_score:.1f}",
            "label": "Highest Negotiation Score",
            "indicator": "Green",
            "datatype": "Data"
        }
    ]