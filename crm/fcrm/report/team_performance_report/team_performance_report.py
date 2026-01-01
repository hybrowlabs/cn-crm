# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months, formatdate, flt, cint, date_diff
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
            "label": _("Team Member"),
            "fieldname": "team_member",
            "fieldtype": "Link",
            "options": "User",
            "width": 150
        },
        {
            "label": _("Full Name"),
            "fieldname": "full_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Role"),
            "fieldname": "role",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Territory"),
            "fieldname": "territory",
            "fieldtype": "Link",
            "options": "Territory",
            "width": 120
        },
        {
            "label": _("Leads Assigned"),
            "fieldname": "leads_assigned",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Leads Converted"),
            "fieldname": "leads_converted",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Lead Conversion %"),
            "fieldname": "lead_conversion_rate",
            "fieldtype": "Percent",
            "width": 130
        },
        {
            "label": _("Deals Assigned"),
            "fieldname": "deals_assigned",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Deals Won"),
            "fieldname": "deals_won",
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
            "label": _("Site Visits"),
            "fieldname": "site_visits",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Activities Completed"),
            "fieldname": "activities_completed",
            "fieldtype": "Int",
            "width": 150
        },
        {
            "label": _("Performance Score"),
            "fieldname": "performance_score",
            "fieldtype": "Float",
            "width": 130,
            "precision": 1
        }
    ]


def get_data(filters):
    # Get team members based on role filtering
    team_members = get_team_members(filters)

    # Get performance data for each team member
    performance_data = []

    for member in team_members:
        member_performance = get_member_performance(member, filters)
        if member_performance:
            performance_data.append(member_performance)

    # Sort by performance score descending
    performance_data.sort(key=lambda x: x['performance_score'], reverse=True)

    return performance_data


def get_team_members(filters):
    # Build conditions for filtering team members
    conditions = ["enabled = 1", "user_type = 'System User'"]

    # Get users with sales-related roles
    team_members = frappe.db.sql(f"""
        SELECT DISTINCT
            u.name, u.full_name, u.first_name, u.last_name, u.email
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON u.name = hr.parent
        WHERE {' AND '.join(conditions)}
        AND hr.role IN ('Sales User', 'Sales Manager', 'System Manager')
        AND u.name NOT IN ('Administrator', 'Guest')
        ORDER BY u.full_name
    """, as_dict=1)

    # If specific user filter is applied
    if filters.get("user"):
        team_members = [member for member in team_members if member.name == filters.get("user")]

    # Apply territory filtering if needed
    if filters.get("territory"):
        # Get users assigned to this territory through various means
        territory_users = get_territory_users(filters.get("territory"))
        team_members = [member for member in team_members if member.name in territory_users]

    return team_members


def get_territory_users(territory):
    """Get users associated with a territory through leads/deals"""
    territory_users = set()

    # Get users from leads in this territory
    lead_users = frappe.db.sql("""
        SELECT DISTINCT lead_owner
        FROM `tabCRM Lead`
        WHERE territory = %s AND lead_owner IS NOT NULL
    """, (territory,))

    territory_users.update([user[0] for user in lead_users])

    # Get users from deals in this territory (through leads)
    deal_users = frappe.db.sql("""
        SELECT DISTINCT d.deal_owner
        FROM `tabCRM Deal` d
        INNER JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE l.territory = %s AND d.deal_owner IS NOT NULL
    """, (territory,))

    territory_users.update([user[0] for user in deal_users])

    return list(territory_users)


def get_member_performance(member, filters):
    """Calculate comprehensive performance metrics for a team member"""
    user_id = member.name

    # Date range conditions
    date_conditions = ""
    if filters.get("from_date"):
        date_conditions += f" AND DATE(creation) >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        date_conditions += f" AND DATE(creation) <= '{filters.get('to_date')}'"

    # Get leads data
    leads_data = frappe.db.sql(f"""
        SELECT name, converted, territory, creation, annual_revenue
        FROM `tabCRM Lead`
        WHERE lead_owner = %s AND docstatus < 2 {date_conditions}
    """, (user_id,), as_dict=1)

    # Apply territory filtering
    from crm.api.territory_permissions import has_permission as territory_has_permission
    filtered_leads = []
    user_territory = None

    for lead in leads_data:
        mock_doc = frappe._dict({
            'territory': lead.get('territory'),
            'doctype': 'CRM Lead'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_leads.append(lead)
            if not user_territory:
                user_territory = lead.get('territory')

    # Get deals data
    deals_data = frappe.db.sql(f"""
        SELECT d.name, d.deal_value, d.status, d.creation, l.territory
        FROM `tabCRM Deal` d
        LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE d.deal_owner = %s AND d.docstatus < 2 {date_conditions.replace('creation', 'd.creation')}
    """, (user_id,), as_dict=1)

    # Apply territory filtering to deals
    filtered_deals = []
    for deal in deals_data:
        mock_doc = frappe._dict({
            'territory': deal.get('territory'),
            'doctype': 'CRM Deal'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_deals.append(deal)

    # Get site visits data
    site_visits = frappe.db.count("CRM Site Visit", {
        "sales_person": user_id,
        "docstatus": ["<", 2],
        "creation": ["between", [filters.get("from_date"), filters.get("to_date")]] if filters.get("from_date") and filters.get("to_date") else ["is", "set"]
    })

    # Get activities data (notes, tasks, calls)
    activities_count = 0

    # Count notes
    notes_count = frappe.db.count("FCRM Note", {
        "owner": user_id,
        "creation": ["between", [filters.get("from_date"), filters.get("to_date")]] if filters.get("from_date") and filters.get("to_date") else ["is", "set"]
    })

    # Count tasks
    tasks_count = frappe.db.count("CRM Task", {
        "assigned_to": user_id,
        "status": "Completed",
        "creation": ["between", [filters.get("from_date"), filters.get("to_date")]] if filters.get("from_date") and filters.get("to_date") else ["is", "set"]
    })

    activities_count = notes_count + tasks_count

    # Calculate performance metrics
    leads_assigned = len(filtered_leads)
    leads_converted = len([lead for lead in filtered_leads if lead.converted])
    lead_conversion_rate = (leads_converted / leads_assigned * 100) if leads_assigned > 0 else 0

    deals_assigned = len(filtered_deals)
    deals_won = len([deal for deal in filtered_deals if deal.status == "Won"])
    deal_win_rate = (deals_won / deals_assigned * 100) if deals_assigned > 0 else 0

    revenue_generated = sum([deal.deal_value or 0 for deal in filtered_deals if deal.status == "Won"])

    # Get user's primary role
    user_roles = frappe.get_roles(user_id)
    primary_role = "Sales User"
    if "Sales Manager" in user_roles:
        primary_role = "Sales Manager"
    elif "System Manager" in user_roles:
        primary_role = "System Manager"

    # Calculate performance score (weighted average)
    performance_score = calculate_performance_score({
        'lead_conversion_rate': lead_conversion_rate,
        'deal_win_rate': deal_win_rate,
        'leads_assigned': leads_assigned,
        'deals_assigned': deals_assigned,
        'site_visits': site_visits,
        'activities_completed': activities_count,
        'revenue_generated': revenue_generated
    })

    return {
        'team_member': user_id,
        'full_name': member.full_name,
        'role': primary_role,
        'territory': user_territory or "Multiple/None",
        'leads_assigned': leads_assigned,
        'leads_converted': leads_converted,
        'lead_conversion_rate': lead_conversion_rate,
        'deals_assigned': deals_assigned,
        'deals_won': deals_won,
        'deal_win_rate': deal_win_rate,
        'revenue_generated': revenue_generated,
        'site_visits': site_visits,
        'activities_completed': activities_count,
        'performance_score': performance_score
    }


def calculate_performance_score(metrics):
    """Calculate a weighted performance score"""
    score = 0

    # Conversion rates (40% weight)
    score += metrics['lead_conversion_rate'] * 0.2
    score += metrics['deal_win_rate'] * 0.2

    # Volume metrics (30% weight)
    score += min(metrics['leads_assigned'], 50) * 0.1  # Cap at 50 for scoring
    score += min(metrics['deals_assigned'], 20) * 0.2   # Cap at 20 for scoring

    # Activity metrics (20% weight)
    score += min(metrics['site_visits'], 30) * 0.1      # Cap at 30 for scoring
    score += min(metrics['activities_completed'], 100) * 0.1  # Cap at 100 for scoring

    # Revenue impact (10% weight)
    revenue_score = min(metrics['revenue_generated'] / 100000, 10)  # 1 point per 10k, cap at 10
    score += revenue_score * 0.1

    return round(score, 1)


def get_chart_data(data, filters):
    if not data:
        return None

    # Show top 10 performers by performance score
    top_performers = data[:10]

    labels = [row['full_name'] for row in top_performers]
    performance_scores = [row['performance_score'] for row in top_performers]
    revenue_values = [row['revenue_generated'] for row in top_performers]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Performance Score",
                    "values": performance_scores,
                    "chartType": "bar"
                }
            ]
        },
        "type": "bar",
        "height": 300,
        "colors": ["#28a745"]
    }


def get_summary_data(data):
    if not data:
        return []

    total_team_members = len(data)
    total_leads = sum([row['leads_assigned'] for row in data])
    total_converted = sum([row['leads_converted'] for row in data])
    total_deals = sum([row['deals_assigned'] for row in data])
    total_won = sum([row['deals_won'] for row in data])
    total_revenue = sum([row['revenue_generated'] for row in data])
    total_activities = sum([row['activities_completed'] for row in data])

    overall_lead_conversion = (total_converted / total_leads * 100) if total_leads > 0 else 0
    overall_deal_win_rate = (total_won / total_deals * 100) if total_deals > 0 else 0
    avg_revenue_per_member = total_revenue / total_team_members if total_team_members > 0 else 0

    # Find top performers
    top_performer = max(data, key=lambda x: x['performance_score']) if data else None
    top_revenue_generator = max(data, key=lambda x: x['revenue_generated']) if data else None
    most_active = max(data, key=lambda x: x['activities_completed']) if data else None

    # Team territories
    territories = set([row['territory'] for row in data if row['territory'] != "Multiple/None"])

    return [
        {
            "value": total_team_members,
            "label": "Team Members",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": f"{overall_lead_conversion:.1f}%",
            "label": "Team Lead Conversion Rate",
            "indicator": "Green" if overall_lead_conversion >= 20 else "Orange" if overall_lead_conversion >= 10 else "Red",
            "datatype": "Data"
        },
        {
            "value": f"{overall_deal_win_rate:.1f}%",
            "label": "Team Deal Win Rate",
            "indicator": "Green" if overall_deal_win_rate >= 30 else "Orange" if overall_deal_win_rate >= 20 else "Red",
            "datatype": "Data"
        },
        {
            "value": total_revenue,
            "label": "Total Team Revenue",
            "indicator": "Green",
            "datatype": "Currency"
        },
        {
            "value": avg_revenue_per_member,
            "label": "Avg Revenue per Member",
            "indicator": "Purple",
            "datatype": "Currency"
        },
        {
            "value": f"{top_performer['full_name']} ({top_performer['performance_score']})" if top_performer else "None",
            "label": "Top Performer",
            "indicator": "Green",
            "datatype": "Data"
        },
        {
            "value": f"{top_revenue_generator['full_name']}" if top_revenue_generator else "None",
            "label": "Top Revenue Generator",
            "indicator": "Blue",
            "datatype": "Data"
        },
        {
            "value": len(territories),
            "label": "Territories Covered",
            "indicator": "Gray",
            "datatype": "Int"
        }
    ]