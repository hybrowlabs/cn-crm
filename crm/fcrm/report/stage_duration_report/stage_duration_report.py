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
            "label": _("Lead ID"),
            "fieldname": "lead_id",
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
            "label": _("Current Status"),
            "fieldname": "current_status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Lead Owner"),
            "fieldname": "lead_owner",
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
            "label": _("Created Date"),
            "fieldname": "creation",
            "fieldtype": "Date",
            "width": 120
        },
        {
            "label": _("Days in New"),
            "fieldname": "days_in_new",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Days in Qualified"),
            "fieldname": "days_in_qualified",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Days in Interested"),
            "fieldname": "days_in_interested",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Days in Proposal"),
            "fieldname": "days_in_proposal",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Total Days"),
            "fieldname": "total_days",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Stage Velocity"),
            "fieldname": "stage_velocity",
            "fieldtype": "Data",
            "width": 120
        }
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    # Get all leads with their current data
    leads = frappe.db.sql(f"""
        SELECT name, lead_name, organization, status, lead_owner, territory, creation
        FROM `tabCRM Lead`
        WHERE docstatus < 2 {conditions}
        ORDER BY creation DESC
    """, as_dict=1)

    # Apply territory filtering
    filtered_leads = []
    from crm.api.territory_permissions import has_permission as territory_has_permission

    for lead in leads:
        # Create a mock document for permission checking
        mock_doc = frappe._dict({
            'territory': lead.get('territory'),
            'doctype': 'CRM Lead'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_leads.append(lead)

    report_data = []

    for lead in filtered_leads:
        # Calculate stage durations from activity timeline
        stage_durations = calculate_stage_durations(lead.name)

        total_days = sum(stage_durations.values())
        velocity = calculate_velocity(stage_durations, lead.status)

        row = {
            'lead_id': lead.name,
            'lead_name': lead.lead_name,
            'organization': lead.organization or '-',
            'current_status': lead.status or 'New',
            'lead_owner': lead.lead_owner,
            'territory': lead.territory,
            'creation': lead.creation,
            'days_in_new': stage_durations.get('New', 0),
            'days_in_qualified': stage_durations.get('Qualified', 0),
            'days_in_interested': stage_durations.get('Interested', 0),
            'days_in_proposal': stage_durations.get('Proposal', 0),
            'total_days': total_days,
            'stage_velocity': velocity
        }

        report_data.append(row)

    return report_data


def calculate_stage_durations(lead_name):
    """Calculate time spent in each stage based on timeline activities"""

    # Get status change activities from timeline
    activities = frappe.db.sql("""
        SELECT reference_name, timeline_content, creation
        FROM `tabCRM Note`
        WHERE reference_doctype = 'CRM Lead'
        AND reference_name = %s
        AND note_type = 'Activity Timeline'
        AND timeline_content LIKE '%status%'
        ORDER BY creation ASC
    """, (lead_name,), as_dict=1)

    # Get lead creation date
    lead_creation = frappe.db.get_value("CRM Lead", lead_name, "creation")

    stage_durations = {
        'New': 0,
        'Qualified': 0,
        'Interested': 0,
        'Proposal': 0
    }

    # If no status change activities found, calculate based on current status
    if not activities:
        current_status = frappe.db.get_value("CRM Lead", lead_name, "status") or "New"
        days_since_creation = date_diff(frappe.utils.nowdate(), lead_creation.date()) if lead_creation else 0
        stage_durations[current_status] = days_since_creation
        return stage_durations

    # Track status changes
    previous_date = lead_creation.date() if lead_creation else frappe.utils.getdate()
    previous_status = "New"

    for activity in activities:
        # Parse status from timeline content
        content = activity.get('timeline_content', '')
        new_status = extract_status_from_content(content)

        if new_status and new_status != previous_status:
            # Calculate days in previous status
            current_date = activity.creation.date() if activity.creation else frappe.utils.getdate()
            days_in_status = date_diff(current_date, previous_date)

            if previous_status in stage_durations:
                stage_durations[previous_status] += max(days_in_status, 0)

            previous_date = current_date
            previous_status = new_status

    # Calculate days in current status
    current_date = frappe.utils.getdate()
    days_in_current = date_diff(current_date, previous_date)
    if previous_status in stage_durations:
        stage_durations[previous_status] += max(days_in_current, 0)

    return stage_durations


def extract_status_from_content(content):
    """Extract status from timeline content"""
    status_keywords = {
        'qualified': 'Qualified',
        'interested': 'Interested',
        'proposal': 'Proposal',
        'converted': 'Converted',
        'lost': 'Lost'
    }

    content_lower = content.lower()
    for keyword, status in status_keywords.items():
        if keyword in content_lower:
            return status

    return None


def calculate_velocity(stage_durations, current_status):
    """Calculate stage progression velocity"""
    total_days = sum(stage_durations.values())

    if total_days == 0:
        return "New"

    # Define stage progression order
    stage_order = ['New', 'Qualified', 'Interested', 'Proposal']

    try:
        current_stage_index = stage_order.index(current_status) if current_status in stage_order else 0
    except ValueError:
        current_stage_index = 0

    if total_days <= 7:
        return "Fast"
    elif total_days <= 30:
        return "Average"
    else:
        return "Slow"


def get_conditions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += f" AND DATE(creation) >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        conditions += f" AND DATE(creation) <= '{filters.get('to_date')}'"
    if filters.get("lead_owner"):
        conditions += f" AND lead_owner = '{filters.get('lead_owner')}'"
    if filters.get("territory"):
        conditions += f" AND territory = '{filters.get('territory')}'"
    return conditions


def get_chart_data(data):
    if not data:
        return None

    # Average days per stage
    stages = ['New', 'Qualified', 'Interested', 'Proposal']
    avg_durations = []

    for stage in stages:
        field_name = f'days_in_{stage.lower()}'
        values = [row[field_name] for row in data if row[field_name] > 0]
        avg_duration = sum(values) / len(values) if values else 0
        avg_durations.append(round(avg_duration, 1))

    return {
        "data": {
            "labels": stages,
            "datasets": [{
                "name": "Average Days in Stage",
                "values": avg_durations
            }]
        },
        "type": "bar",
        "height": 300,
        "colors": ["#007bff"]
    }


def get_summary_data(data):
    if not data:
        return []

    total_leads = len(data)
    avg_total_days = sum([row['total_days'] for row in data]) / total_leads if total_leads > 0 else 0

    # Velocity distribution
    velocity_counts = {}
    for row in data:
        velocity = row['stage_velocity']
        velocity_counts[velocity] = velocity_counts.get(velocity, 0) + 1

    # Longest stage analysis
    longest_stage_data = {}
    for row in data:
        for stage in ['New', 'Qualified', 'Interested', 'Proposal']:
            field_name = f'days_in_{stage.lower()}'
            days = row[field_name]
            if days > longest_stage_data.get(stage, 0):
                longest_stage_data[stage] = days

    longest_stage = max(longest_stage_data, key=longest_stage_data.get) if longest_stage_data else "New"
    longest_duration = longest_stage_data.get(longest_stage, 0)

    # Fast movers (less than 7 days total)
    fast_movers = len([row for row in data if row['total_days'] <= 7])
    fast_mover_percentage = (fast_movers / total_leads * 100) if total_leads > 0 else 0

    return [
        {
            "value": total_leads,
            "label": "Total Leads Analyzed",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": f"{avg_total_days:.1f}",
            "label": "Average Days in Pipeline",
            "indicator": "Gray",
            "datatype": "Data"
        },
        {
            "value": f"{longest_stage} ({longest_duration} days)",
            "label": "Longest Stage",
            "indicator": "Red" if longest_duration > 30 else "Orange",
            "datatype": "Data"
        },
        {
            "value": f"{fast_mover_percentage:.1f}%",
            "label": "Fast Movers (≤7 days)",
            "indicator": "Green",
            "datatype": "Data"
        },
        {
            "value": velocity_counts.get('Fast', 0),
            "label": "Fast Velocity Leads",
            "indicator": "Green",
            "datatype": "Int"
        },
        {
            "value": velocity_counts.get('Slow', 0),
            "label": "Slow Velocity Leads",
            "indicator": "Red",
            "datatype": "Int"
        }
    ]