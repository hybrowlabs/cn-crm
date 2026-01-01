# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, add_days, add_months, formatdate, flt, cint, date_diff
from datetime import datetime, timedelta
import json


def execute(filters=None):
    # For individual reports, default to current user unless specified
    if not filters.get("user") and not frappe.has_permission("User", "read"):
        filters["user"] = frappe.session.user

    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    summary = get_summary_data(data, filters)

    return columns, data, None, chart, summary


def get_columns():
    return [
        {
            "label": _("Metric Category"),
            "fieldname": "metric_category",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Metric"),
            "fieldname": "metric_name",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Current Value"),
            "fieldname": "current_value",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Previous Period"),
            "fieldname": "previous_value",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Change"),
            "fieldname": "change",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Trend"),
            "fieldname": "trend",
            "fieldtype": "Data",
            "width": 80
        },
        {
            "label": _("Target"),
            "fieldname": "target",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Achievement %"),
            "fieldname": "achievement_pct",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Rating"),
            "fieldname": "rating",
            "fieldtype": "Data",
            "width": 80
        }
    ]


def get_data(filters):
    user_id = filters.get("user") or frappe.session.user

    # Get date ranges for current and previous periods
    date_ranges = get_date_ranges(filters)

    # Get user's performance data for both periods
    current_metrics = get_user_metrics(user_id, date_ranges["current_start"], date_ranges["current_end"])
    previous_metrics = get_user_metrics(user_id, date_ranges["previous_start"], date_ranges["previous_end"])

    # Build comprehensive metrics report
    report_data = []

    # Lead Management Metrics
    report_data.extend(get_lead_metrics(current_metrics, previous_metrics))

    # Deal Management Metrics
    report_data.extend(get_deal_metrics(current_metrics, previous_metrics))

    # Activity Metrics
    report_data.extend(get_activity_metrics(current_metrics, previous_metrics))

    # Revenue Metrics
    report_data.extend(get_revenue_metrics(current_metrics, previous_metrics))

    # Efficiency Metrics
    report_data.extend(get_efficiency_metrics(current_metrics, previous_metrics))

    return report_data


def get_date_ranges(filters):
    """Calculate current and previous period date ranges"""
    if filters.get("from_date") and filters.get("to_date"):
        current_start = getdate(filters.get("from_date"))
        current_end = getdate(filters.get("to_date"))
    else:
        # Default to current month
        current_end = getdate()
        current_start = current_end.replace(day=1)

    # Calculate previous period (same duration)
    period_days = (current_end - current_start).days
    previous_end = add_days(current_start, -1)
    previous_start = add_days(previous_end, -period_days)

    return {
        "current_start": current_start,
        "current_end": current_end,
        "previous_start": previous_start,
        "previous_end": previous_end
    }


def get_user_metrics(user_id, start_date, end_date):
    """Get all metrics for a user in a date range"""
    metrics = {}

    # Leads metrics
    leads_data = frappe.db.sql("""
        SELECT name, converted, status, creation, annual_revenue, territory
        FROM `tabCRM Lead`
        WHERE lead_owner = %s AND DATE(creation) BETWEEN %s AND %s
        AND docstatus < 2
    """, (user_id, start_date, end_date), as_dict=1)

    # Apply territory filtering
    from crm.api.territory_permissions import has_permission as territory_has_permission
    filtered_leads = []

    for lead in leads_data:
        mock_doc = frappe._dict({
            'territory': lead.get('territory'),
            'doctype': 'CRM Lead'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_leads.append(lead)

    metrics['leads'] = filtered_leads

    # Deals metrics
    deals_data = frappe.db.sql("""
        SELECT d.name, d.deal_value, d.status, d.creation, d.close_date, d.probability, l.territory
        FROM `tabCRM Deal` d
        LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
        WHERE d.deal_owner = %s AND DATE(d.creation) BETWEEN %s AND %s
        AND d.docstatus < 2
    """, (user_id, start_date, end_date), as_dict=1)

    # Apply territory filtering to deals
    filtered_deals = []
    for deal in deals_data:
        mock_doc = frappe._dict({
            'territory': deal.get('territory'),
            'doctype': 'CRM Deal'
        })

        if territory_has_permission(mock_doc, frappe.session.user):
            filtered_deals.append(deal)

    metrics['deals'] = filtered_deals

    # Site visits
    metrics['site_visits'] = frappe.db.count("CRM Site Visit", {
        "sales_person": user_id,
        "visit_date": ["between", [start_date, end_date]],
        "docstatus": ["<", 2]
    })

    # Activities
    metrics['notes'] = frappe.db.count("FCRM Note", {
        "owner": user_id,
        "creation": ["between", [start_date, end_date]]
    })

    metrics['tasks_completed'] = frappe.db.count("CRM Task", {
        "assigned_to": user_id,
        "status": "Completed",
        "completion_date": ["between", [start_date, end_date]]
    }) if frappe.db.exists("DocType", "CRM Task") else 0

    return metrics


def get_lead_metrics(current, previous):
    """Generate lead management metrics"""
    current_leads = len(current['leads'])
    previous_leads = len(previous['leads'])

    current_converted = len([l for l in current['leads'] if l.converted])
    previous_converted = len([l for l in previous['leads'] if l.converted])

    current_conversion_rate = (current_converted / current_leads * 100) if current_leads > 0 else 0
    previous_conversion_rate = (previous_converted / previous_leads * 100) if previous_leads > 0 else 0

    return [
        {
            'metric_category': 'Lead Management',
            'metric_name': 'Total Leads Assigned',
            'current_value': current_leads,
            'previous_value': previous_leads,
            'change': current_leads - previous_leads,
            'trend': get_trend(current_leads, previous_leads),
            'target': '20',  # Example target
            'achievement_pct': (current_leads / 20 * 100) if current_leads > 0 else 0,
            'rating': get_rating(current_leads, 20)
        },
        {
            'metric_category': 'Lead Management',
            'metric_name': 'Leads Converted',
            'current_value': current_converted,
            'previous_value': previous_converted,
            'change': current_converted - previous_converted,
            'trend': get_trend(current_converted, previous_converted),
            'target': '5',
            'achievement_pct': (current_converted / 5 * 100) if current_converted > 0 else 0,
            'rating': get_rating(current_converted, 5)
        },
        {
            'metric_category': 'Lead Management',
            'metric_name': 'Conversion Rate (%)',
            'current_value': f"{current_conversion_rate:.1f}%",
            'previous_value': f"{previous_conversion_rate:.1f}%",
            'change': f"{current_conversion_rate - previous_conversion_rate:.1f}%",
            'trend': get_trend(current_conversion_rate, previous_conversion_rate),
            'target': '25%',
            'achievement_pct': (current_conversion_rate / 25 * 100) if current_conversion_rate > 0 else 0,
            'rating': get_rating(current_conversion_rate, 25)
        }
    ]


def get_deal_metrics(current, previous):
    """Generate deal management metrics"""
    current_deals = len(current['deals'])
    previous_deals = len(previous['deals'])

    current_won = len([d for d in current['deals'] if d.status == "Won"])
    previous_won = len([d for d in previous['deals'] if d.status == "Won"])

    current_win_rate = (current_won / current_deals * 100) if current_deals > 0 else 0
    previous_win_rate = (previous_won / previous_deals * 100) if previous_deals > 0 else 0

    return [
        {
            'metric_category': 'Deal Management',
            'metric_name': 'Total Deals Assigned',
            'current_value': current_deals,
            'previous_value': previous_deals,
            'change': current_deals - previous_deals,
            'trend': get_trend(current_deals, previous_deals),
            'target': '10',
            'achievement_pct': (current_deals / 10 * 100) if current_deals > 0 else 0,
            'rating': get_rating(current_deals, 10)
        },
        {
            'metric_category': 'Deal Management',
            'metric_name': 'Deals Won',
            'current_value': current_won,
            'previous_value': previous_won,
            'change': current_won - previous_won,
            'trend': get_trend(current_won, previous_won),
            'target': '3',
            'achievement_pct': (current_won / 3 * 100) if current_won > 0 else 0,
            'rating': get_rating(current_won, 3)
        },
        {
            'metric_category': 'Deal Management',
            'metric_name': 'Deal Win Rate (%)',
            'current_value': f"{current_win_rate:.1f}%",
            'previous_value': f"{previous_win_rate:.1f}%",
            'change': f"{current_win_rate - previous_win_rate:.1f}%",
            'trend': get_trend(current_win_rate, previous_win_rate),
            'target': '30%',
            'achievement_pct': (current_win_rate / 30 * 100) if current_win_rate > 0 else 0,
            'rating': get_rating(current_win_rate, 30)
        }
    ]


def get_activity_metrics(current, previous):
    """Generate activity metrics"""
    current_visits = current['site_visits']
    previous_visits = previous['site_visits']

    current_notes = current['notes']
    previous_notes = previous['notes']

    return [
        {
            'metric_category': 'Activities',
            'metric_name': 'Site Visits Conducted',
            'current_value': current_visits,
            'previous_value': previous_visits,
            'change': current_visits - previous_visits,
            'trend': get_trend(current_visits, previous_visits),
            'target': '15',
            'achievement_pct': (current_visits / 15 * 100) if current_visits > 0 else 0,
            'rating': get_rating(current_visits, 15)
        },
        {
            'metric_category': 'Activities',
            'metric_name': 'Notes Created',
            'current_value': current_notes,
            'previous_value': previous_notes,
            'change': current_notes - previous_notes,
            'trend': get_trend(current_notes, previous_notes),
            'target': '50',
            'achievement_pct': (current_notes / 50 * 100) if current_notes > 0 else 0,
            'rating': get_rating(current_notes, 50)
        }
    ]


def get_revenue_metrics(current, previous):
    """Generate revenue metrics"""
    current_revenue = sum([d.deal_value or 0 for d in current['deals'] if d.status == "Won"])
    previous_revenue = sum([d.deal_value or 0 for d in previous['deals'] if d.status == "Won"])

    return [
        {
            'metric_category': 'Revenue',
            'metric_name': 'Revenue Generated',
            'current_value': f"₹{current_revenue:,.0f}" if current_revenue > 0 else "₹0",
            'previous_value': f"₹{previous_revenue:,.0f}" if previous_revenue > 0 else "₹0",
            'change': f"₹{current_revenue - previous_revenue:,.0f}",
            'trend': get_trend(current_revenue, previous_revenue),
            'target': '₹500,000',
            'achievement_pct': (current_revenue / 500000 * 100) if current_revenue > 0 else 0,
            'rating': get_rating(current_revenue, 500000)
        }
    ]


def get_efficiency_metrics(current, previous):
    """Generate efficiency metrics"""
    # Calculate deals per lead ratio
    current_leads_count = len(current['leads'])
    current_deals_count = len(current['deals'])

    current_efficiency = (current_deals_count / current_leads_count) if current_leads_count > 0 else 0
    previous_efficiency = (len(previous['deals']) / len(previous['leads'])) if len(previous['leads']) > 0 else 0

    return [
        {
            'metric_category': 'Efficiency',
            'metric_name': 'Deal Creation Rate (Deals/Leads)',
            'current_value': f"{current_efficiency:.2f}",
            'previous_value': f"{previous_efficiency:.2f}",
            'change': f"{current_efficiency - previous_efficiency:.2f}",
            'trend': get_trend(current_efficiency, previous_efficiency),
            'target': '0.50',
            'achievement_pct': (current_efficiency / 0.50 * 100) if current_efficiency > 0 else 0,
            'rating': get_rating(current_efficiency, 0.50)
        }
    ]


def get_trend(current, previous):
    """Calculate trend direction"""
    if current > previous:
        return "↗️"
    elif current < previous:
        return "↘️"
    else:
        return "→"


def get_rating(current, target):
    """Calculate performance rating"""
    if isinstance(current, str):
        return "N/A"

    achievement = (current / target * 100) if target > 0 else 0

    if achievement >= 100:
        return "⭐⭐⭐⭐⭐"
    elif achievement >= 80:
        return "⭐⭐⭐⭐"
    elif achievement >= 60:
        return "⭐⭐⭐"
    elif achievement >= 40:
        return "⭐⭐"
    elif achievement >= 20:
        return "⭐"
    else:
        return "💔"


def get_chart_data(data, filters):
    if not data:
        return None

    # Create achievement percentage chart
    categories = list(set([row['metric_category'] for row in data]))

    category_achievements = {}
    for category in categories:
        category_data = [row for row in data if row['metric_category'] == category]
        avg_achievement = sum([row['achievement_pct'] for row in category_data]) / len(category_data)
        category_achievements[category] = avg_achievement

    return {
        "data": {
            "labels": list(category_achievements.keys()),
            "datasets": [{
                "name": "Achievement %",
                "values": list(category_achievements.values())
            }]
        },
        "type": "bar",
        "height": 300,
        "colors": ["#28a745"]
    }


def get_summary_data(data, filters):
    if not data:
        return []

    user_id = filters.get("user") or frappe.session.user
    user_name = frappe.db.get_value("User", user_id, "full_name") or user_id

    total_metrics = len(data)
    avg_achievement = sum([row['achievement_pct'] for row in data]) / total_metrics if total_metrics > 0 else 0

    # Count metrics by rating
    five_star = len([row for row in data if "⭐⭐⭐⭐⭐" in str(row['rating'])])
    four_star = len([row for row in data if "⭐⭐⭐⭐" in str(row['rating']) and "⭐⭐⭐⭐⭐" not in str(row['rating'])])

    # Categories performance
    categories = list(set([row['metric_category'] for row in data]))
    best_category = None
    best_achievement = 0

    for category in categories:
        category_data = [row for row in data if row['metric_category'] == category]
        avg_cat_achievement = sum([row['achievement_pct'] for row in category_data]) / len(category_data)
        if avg_cat_achievement > best_achievement:
            best_achievement = avg_cat_achievement
            best_category = category

    return [
        {
            "value": user_name,
            "label": "Performance Report for",
            "indicator": "Blue",
            "datatype": "Data"
        },
        {
            "value": f"{avg_achievement:.1f}%",
            "label": "Overall Achievement",
            "indicator": "Green" if avg_achievement >= 80 else "Orange" if avg_achievement >= 60 else "Red",
            "datatype": "Data"
        },
        {
            "value": five_star,
            "label": "5-Star Metrics",
            "indicator": "Green",
            "datatype": "Int"
        },
        {
            "value": four_star,
            "label": "4-Star Metrics",
            "indicator": "Blue",
            "datatype": "Int"
        },
        {
            "value": best_category if best_category else "None",
            "label": "Best Performing Category",
            "indicator": "Purple",
            "datatype": "Data"
        },
        {
            "value": len(categories),
            "label": "Categories Tracked",
            "indicator": "Gray",
            "datatype": "Int"
        }
    ]