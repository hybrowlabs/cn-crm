# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months, formatdate, flt, cint
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
            "label": _("Team/Territory"),
            "fieldname": "team_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Team Type"),
            "fieldname": "team_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Team Members"),
            "fieldname": "team_members_count",
            "fieldtype": "Int",
            "width": 120
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
            "label": _("Lead Conversion %"),
            "fieldname": "lead_conversion_rate",
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
            "label": _("Total Revenue"),
            "fieldname": "total_revenue",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Avg Revenue/Member"),
            "fieldname": "avg_revenue_per_member",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Site Visits"),
            "fieldname": "total_site_visits",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Team Performance Score"),
            "fieldname": "team_performance_score",
            "fieldtype": "Float",
            "width": 170,
            "precision": 1
        }
    ]


def get_data(filters):
    # Get team performance by different groupings
    report_data = []

    # Territory-based teams
    territory_teams = get_territory_teams(filters)
    report_data.extend(territory_teams)

    # Role-based teams
    role_teams = get_role_teams(filters)
    report_data.extend(role_teams)

    # Line of Business teams (if using service teams)
    lob_teams = get_lob_teams(filters)
    report_data.extend(lob_teams)

    # Sort by performance score
    report_data.sort(key=lambda x: x['team_performance_score'], reverse=True)

    return report_data


def get_territory_teams(filters):
    """Get performance data grouped by territory"""
    # Get all territories with leads/deals
    territories = frappe.db.sql("""
        SELECT DISTINCT territory
        FROM `tabCRM Lead`
        WHERE territory IS NOT NULL AND territory != ''
        AND docstatus < 2
    """, as_list=True)

    territory_data = []

    for territory_tuple in territories:
        territory = territory_tuple[0]

        # Apply territory filtering for current user
        from crm.api.territory_permissions import has_permission as territory_has_permission
        mock_doc = frappe._dict({
            'territory': territory,
            'doctype': 'CRM Lead'
        })

        if not territory_has_permission(mock_doc, frappe.session.user):
            continue

        team_metrics = get_team_metrics_by_territory(territory, filters)
        if team_metrics:
            territory_data.append(team_metrics)

    return territory_data


def get_role_teams(filters):
    """Get performance data grouped by role"""
    roles = ['Sales Manager', 'Sales User']
    role_data = []

    for role in roles:
        team_metrics = get_team_metrics_by_role(role, filters)
        if team_metrics:
            role_data.append(team_metrics)

    return role_data


def get_lob_teams(filters):
    """Get performance data grouped by Line of Business"""
    # Get active LoB teams
    lobs = frappe.get_all("CRM Line of Business",
                          filters={"is_active": 1},
                          fields=["name", "lob_name"])

    lob_data = []

    for lob in lobs:
        team_metrics = get_team_metrics_by_lob(lob.name, lob.lob_name, filters)
        if team_metrics and team_metrics['team_members_count'] > 0:
            lob_data.append(team_metrics)

    return lob_data


def get_team_metrics_by_territory(territory, filters):
    """Calculate metrics for a territory-based team"""
    date_conditions = get_date_conditions(filters)

    # Get team members for this territory
    team_members = frappe.db.sql(f"""
        SELECT DISTINCT lead_owner
        FROM `tabCRM Lead`
        WHERE territory = %s AND lead_owner IS NOT NULL {date_conditions}
        AND docstatus < 2
    """, (territory,), as_list=True)

    team_members_list = [member[0] for member in team_members if member[0]]

    if not team_members_list:
        return None

    # Get leads data for this territory
    leads_data = frappe.db.sql(f"""
        SELECT name, lead_owner, converted, annual_revenue
        FROM `tabCRM Lead`
        WHERE territory = %s AND docstatus < 2 {date_conditions}
    """, (territory,), as_dict=1)

    # Get deals data for this territory
    deals_data = frappe.db.sql(f"""
        SELECT d.name, d.deal_owner, d.deal_value, d.status
        FROM `tabCRM Deal` d
        INNER JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE l.territory = %s AND d.docstatus < 2 {date_conditions.replace('creation', 'd.creation')}
    """, (territory,), as_dict=1)

    # Get site visits for this territory
    site_visits = frappe.db.sql(f"""
        SELECT COUNT(*) as count
        FROM `tabCRM Site Visit` sv
        INNER JOIN `tabCRM Lead` l ON sv.reference_name = l.name
        WHERE l.territory = %s AND sv.docstatus < 2 {date_conditions.replace('creation', 'sv.creation')}
    """, (territory,), as_dict=1)

    return calculate_team_metrics(
        team_name=territory,
        team_type="Territory",
        team_members_list=team_members_list,
        leads_data=leads_data,
        deals_data=deals_data,
        site_visits_count=site_visits[0]['count'] if site_visits else 0
    )


def get_team_metrics_by_role(role, filters):
    """Calculate metrics for a role-based team"""
    date_conditions = get_date_conditions(filters)

    # Get team members with this role
    team_members = frappe.db.sql("""
        SELECT DISTINCT u.name
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON u.name = hr.parent
        WHERE hr.role = %s AND u.enabled = 1 AND u.user_type = 'System User'
        AND u.name NOT IN ('Administrator', 'Guest')
    """, (role,), as_list=True)

    team_members_list = [member[0] for member in team_members]

    if not team_members_list:
        return None

    # Get leads data for role members
    leads_data = frappe.db.sql(f"""
        SELECT name, lead_owner, converted, annual_revenue, territory
        FROM `tabCRM Lead`
        WHERE lead_owner IN ({','.join(['%s'] * len(team_members_list))})
        AND docstatus < 2 {date_conditions}
    """, team_members_list, as_dict=1)

    # Apply territory filtering to leads
    filtered_leads = []
    from crm.api.territory_permissions import has_permission as territory_has_permission

    for lead in leads_data:
        mock_doc = frappe._dict({
            'territory': lead.get('territory'),
            'doctype': 'CRM Lead'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_leads.append(lead)

    # Get deals data for role members
    deals_data = frappe.db.sql(f"""
        SELECT d.name, d.deal_owner, d.deal_value, d.status, l.territory
        FROM `tabCRM Deal` d
        LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE d.deal_owner IN ({','.join(['%s'] * len(team_members_list))})
        AND d.docstatus < 2 {date_conditions.replace('creation', 'd.creation')}
    """, team_members_list, as_dict=1)

    # Apply territory filtering to deals
    filtered_deals = []
    for deal in deals_data:
        mock_doc = frappe._dict({
            'territory': deal.get('territory'),
            'doctype': 'CRM Deal'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_deals.append(deal)

    # Get site visits for role members
    site_visits = frappe.db.count("CRM Site Visit", {
        "sales_person": ["in", team_members_list],
        "docstatus": ["<", 2],
        "creation": ["between", [filters.get("from_date"), filters.get("to_date")]] if filters.get("from_date") and filters.get("to_date") else ["is", "set"]
    })

    return calculate_team_metrics(
        team_name=role,
        team_type="Role",
        team_members_list=team_members_list,
        leads_data=filtered_leads,
        deals_data=filtered_deals,
        site_visits_count=site_visits
    )


def get_team_metrics_by_lob(lob_name, lob_display_name, filters):
    """Calculate metrics for LoB service teams"""
    try:
        lob = frappe.get_doc("CRM Line of Business", lob_name)

        # Get service engineers
        team_members_list = [row.service_engineer for row in lob.service_engineers if row.service_engineer]

        if not team_members_list:
            return None

        date_conditions = get_date_conditions(filters)

        # Get LoB-related activities (limited data available for service teams)
        site_visits = frappe.db.count("CRM Site Visit", {
            "line_of_business": lob_name,
            "docstatus": ["<", 2],
            "creation": ["between", [filters.get("from_date"), filters.get("to_date")]] if filters.get("from_date") and filters.get("to_date") else ["is", "set"]
        })

        return {
            'team_name': lob_display_name,
            'team_type': "Line of Business",
            'team_members_count': len(team_members_list),
            'total_leads': 0,  # LoB teams primarily handle service, not lead generation
            'converted_leads': 0,
            'lead_conversion_rate': 0,
            'total_deals': 0,
            'won_deals': 0,
            'total_revenue': 0,
            'avg_revenue_per_member': 0,
            'total_site_visits': site_visits,
            'team_performance_score': min(site_visits * 2, 100)  # Service-focused scoring
        }

    except Exception:
        return None


def calculate_team_metrics(team_name, team_type, team_members_list, leads_data, deals_data, site_visits_count):
    """Calculate comprehensive team metrics"""
    team_members_count = len(team_members_list)

    total_leads = len(leads_data)
    converted_leads = len([lead for lead in leads_data if lead.get('converted')])
    lead_conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

    total_deals = len(deals_data)
    won_deals = len([deal for deal in deals_data if deal.get('status') == 'Won'])

    total_revenue = sum([deal.get('deal_value', 0) for deal in deals_data if deal.get('status') == 'Won'])
    avg_revenue_per_member = total_revenue / team_members_count if team_members_count > 0 else 0

    # Calculate team performance score
    performance_score = calculate_team_performance_score({
        'lead_conversion_rate': lead_conversion_rate,
        'total_deals': total_deals,
        'won_deals': won_deals,
        'total_revenue': total_revenue,
        'site_visits_count': site_visits_count,
        'team_size': team_members_count
    })

    return {
        'team_name': team_name,
        'team_type': team_type,
        'team_members_count': team_members_count,
        'total_leads': total_leads,
        'converted_leads': converted_leads,
        'lead_conversion_rate': lead_conversion_rate,
        'total_deals': total_deals,
        'won_deals': won_deals,
        'total_revenue': total_revenue,
        'avg_revenue_per_member': avg_revenue_per_member,
        'total_site_visits': site_visits_count,
        'team_performance_score': performance_score
    }


def calculate_team_performance_score(metrics):
    """Calculate weighted team performance score"""
    score = 0

    # Conversion efficiency (30%)
    score += min(metrics['lead_conversion_rate'], 50) * 0.6  # Max 30 points

    # Deal performance (25%)
    deal_rate = (metrics['won_deals'] / metrics['total_deals'] * 100) if metrics['total_deals'] > 0 else 0
    score += min(deal_rate, 50) * 0.5  # Max 25 points

    # Revenue impact (25%)
    revenue_per_member = metrics['total_revenue'] / metrics['team_size'] if metrics['team_size'] > 0 else 0
    revenue_score = min(revenue_per_member / 50000, 25)  # 1 point per 2k revenue per member
    score += revenue_score

    # Activity level (20%)
    visits_per_member = metrics['site_visits_count'] / metrics['team_size'] if metrics['team_size'] > 0 else 0
    activity_score = min(visits_per_member * 2, 20)  # 2 points per visit per member
    score += activity_score

    return round(score, 1)


def get_date_conditions(filters):
    """Get date filtering conditions"""
    conditions = ""
    if filters.get("from_date"):
        conditions += f" AND DATE(creation) >= '{filters.get('from_date')}'"
    if filters.get("to_date"):
        conditions += f" AND DATE(creation) <= '{filters.get('to_date')}'"
    return conditions


def get_chart_data(data):
    if not data:
        return None

    # Show performance scores by team
    labels = [row['team_name'] for row in data[:10]]  # Top 10 teams
    scores = [row['team_performance_score'] for row in data[:10]]

    return {
        "data": {
            "labels": labels,
            "datasets": [{
                "name": "Team Performance Score",
                "values": scores
            }]
        },
        "type": "bar",
        "height": 300,
        "colors": ["#28a745"]
    }


def get_summary_data(data):
    if not data:
        return []

    total_teams = len(data)
    total_members = sum([row['team_members_count'] for row in data])
    total_revenue = sum([row['total_revenue'] for row in data])
    avg_team_score = sum([row['team_performance_score'] for row in data]) / total_teams if total_teams > 0 else 0

    # Find top performing team
    top_team = max(data, key=lambda x: x['team_performance_score']) if data else None
    top_revenue_team = max(data, key=lambda x: x['total_revenue']) if data else None

    # Team types breakdown
    team_types = list(set([row['team_type'] for row in data]))

    return [
        {
            "value": total_teams,
            "label": "Total Teams",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": total_members,
            "label": "Total Team Members",
            "indicator": "Gray",
            "datatype": "Int"
        },
        {
            "value": f"{avg_team_score:.1f}",
            "label": "Average Team Score",
            "indicator": "Green" if avg_team_score >= 70 else "Orange" if avg_team_score >= 50 else "Red",
            "datatype": "Data"
        },
        {
            "value": total_revenue,
            "label": "Total Team Revenue",
            "indicator": "Green",
            "datatype": "Currency"
        },
        {
            "value": f"{top_team['team_name']} ({top_team['team_performance_score']})" if top_team else "None",
            "label": "Top Performing Team",
            "indicator": "Green",
            "datatype": "Data"
        },
        {
            "value": f"{top_revenue_team['team_name']}" if top_revenue_team else "None",
            "label": "Highest Revenue Team",
            "indicator": "Blue",
            "datatype": "Data"
        },
        {
            "value": len(team_types),
            "label": "Team Types",
            "indicator": "Purple",
            "datatype": "Int"
        }
    ]