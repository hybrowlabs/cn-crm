# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _


def make_dashboard_doc(dashboard_name, description, date_range="This Month", is_default=0, is_public=1):
    """Initialize a CRM Dashboard doc with explicit name (autoname='prompt' requires this)."""
    dashboard = frappe.new_doc("CRM Dashboard")
    dashboard.name = dashboard_name
    dashboard.dashboard_name = dashboard_name
    dashboard.description = description
    dashboard.is_default = is_default
    dashboard.is_public = is_public
    dashboard.date_range_type = date_range
    return dashboard


def add_lmotpo_widget(dashboard):
	"""Append LMOTPO pipeline widget if not already present."""
	if any(w.widget_type in ("LMOTPO", "Spanco") for w in dashboard.widgets):
		return

	max_y = 0
	for w in dashboard.widgets:
		try:
			max_y = max(max_y, int(w.y_position or 0) + int(w.height or 0))
		except Exception:
			continue

	dashboard.append(
		"widgets",
		{
			"widget_type": "LMOTPO",
			"widget_title": "LMOTPO Pipeline",
			"widget_description": "Lead → Meetings → Opportunities → Trial → Pricing → Order Booking",
			"width": 12,
			"height": 6,
			"x_position": 0,
			"y_position": max_y,
			"show_refresh": 0,
		},
	)


def execute():
    """Create default dashboards and reports for CRM"""
    create_default_dashboards()


def create_default_dashboards():
	"""Create default dashboards with widgets"""
	
	# 8.1.1: Leads Created Dashboard
	create_leads_created_dashboard()
	
	# 8.1.2: Stage-wise Leads Dashboard
	create_stage_wise_leads_dashboard()
	
	# 8.1.3: Conversion Rates Dashboard
	create_conversion_rates_dashboard()
	
	# 8.1.4: Stage Duration Dashboard
	create_stage_duration_dashboard()
	
	# 8.1.5: Revenue Dashboard
	create_revenue_dashboard()
	
	# 8.1.6: Negotiation Dashboard
	create_negotiation_dashboard()
	
	# 8.2.1: Team Performance Reports
	create_team_performance_reports()
	
	# 8.2.2: Individual Metrics Report
	create_individual_metrics_report()
	
	# 8.2.3: Team Metrics Report
	create_team_metrics_report()
	
	frappe.db.commit()


def create_leads_created_dashboard():
	"""8.1.1: Create Leads Created Dashboard - Display number of leads created"""
	dashboard_name = "Leads Created Dashboard"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Display number of leads created")
	
	# Widget 1: Total Leads Created (KPI)
	widget1 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Total Leads Created",
		"widget_description": "Total number of leads created in selected period",
		"width": 4,
		"height": 3,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: Leads Created This Week (KPI)
	widget2 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Leads Created This Week",
		"widget_description": "Leads created in the last 7 days",
		"width": 4,
		"height": 3,
		"x_position": 4,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: Leads Created by Day (Chart)
	widget3 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Leads Created by Day",
		"widget_description": "Daily lead creation trend",
		"width": 8,
		"height": 4,
		"x_position": 0,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"chart_type": "Bar",
		"x_axis_field": "creation",
		"y_axis_field": "name",
		"group_by_field": "creation",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_stage_wise_leads_dashboard():
	"""8.1.2: Create Stage-wise Leads Dashboard - Display leads at each stage"""
	dashboard_name = "Stage-wise Leads Dashboard"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Display leads at each stage")
	
	# Widget 1: Leads by Status (Pie Chart)
	widget1 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Leads by Status",
		"widget_description": "Distribution of leads across different stages",
		"width": 6,
		"height": 4,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"chart_type": "Pie",
		"x_axis_field": "status",
		"y_axis_field": "name",
		"group_by_field": "status",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: Leads by Status (Bar Chart)
	widget2 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Leads Count by Status",
		"widget_description": "Number of leads in each stage",
		"width": 6,
		"height": 4,
		"x_position": 6,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"chart_type": "Bar",
		"x_axis_field": "status",
		"y_axis_field": "name",
		"group_by_field": "status",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: Stage-wise Leads Table
	widget3 = dashboard.append("widgets", {
		"widget_type": "Table",
		"widget_title": "Leads by Stage",
		"widget_description": "Detailed view of leads at each stage",
		"width": 12,
		"height": 5,
		"x_position": 0,
		"y_position": 4,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"table_columns": json.dumps(["lead_name", "status", "lead_owner", "organization", "email", "mobile_no", "creation"]),
		"table_filters": json.dumps({}),
		"color_scheme": "Gray",
		"show_refresh": 1,
		"refresh_interval": 0,
		"drilldown_doctype": "CRM Lead"
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_conversion_rates_dashboard():
	"""8.1.3: Create Conversion Rates Dashboard - Display conversion rates at each stage"""
	dashboard_name = "Conversion Rates Dashboard"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Display conversion rates at each stage")
	
	# Widget 1: Lead Conversion Rate (KPI)
	widget1 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Lead Conversion Rate",
		"widget_description": "Percentage of leads converted to deals",
		"width": 4,
		"height": 3,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: Total Leads (KPI)
	widget2 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Total Leads",
		"widget_description": "Total number of leads",
		"width": 4,
		"height": 3,
		"x_position": 4,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: Converted Leads (KPI)
	widget3 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Converted Leads",
		"widget_description": "Number of leads converted to deals",
		"width": 4,
		"height": 3,
		"x_position": 8,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 4: Conversion Rate by Status (Chart)
	widget4 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Conversion Rate by Lead Status",
		"widget_description": "Conversion rates at each lead stage",
		"width": 12,
		"height": 4,
		"x_position": 0,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"chart_type": "Bar",
		"x_axis_field": "status",
		"y_axis_field": "converted",
		"group_by_field": "status",
		"color_scheme": "Orange",
		"show_refresh": 1,
		"refresh_interval": 0
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_stage_duration_dashboard():
	"""8.1.4: Create Stage Duration Dashboard - Display stage durations and cycle times"""
	dashboard_name = "Stage Duration Dashboard"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Display stage durations and cycle times")
	
	# Widget 1: Average Deal Cycle Time (KPI)
	widget1 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Deals in Pipeline",
		"widget_description": "Total deals in selected period",
		"width": 4,
		"height": 3,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Purple",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: Average Lead Cycle Time (KPI)
	widget2 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Leads in Pipeline",
		"widget_description": "Total leads in selected period",
		"width": 4,
		"height": 3,
		"x_position": 4,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: Deal Duration by Status (Chart)
	widget3 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Deal Duration by Status",
		"widget_description": "Average time spent in each deal stage",
		"width": 6,
		"height": 4,
		"x_position": 0,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"chart_type": "Bar",
		"x_axis_field": "status",
		"y_axis_field": "modified",
		"group_by_field": "status",
		"color_scheme": "Orange",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 4: Lead Duration by Status (Chart)
	widget4 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Lead Duration by Status",
		"widget_description": "Average time spent in each lead stage",
		"width": 6,
		"height": 4,
		"x_position": 6,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"chart_type": "Bar",
		"x_axis_field": "status",
		"y_axis_field": "modified",
		"group_by_field": "status",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_revenue_dashboard():
	"""8.1.5: Create Revenue Dashboard - Display revenue and potential deal sizes"""
	dashboard_name = "Revenue Dashboard"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Display revenue and potential deal sizes")
	
	# Widget 1: Total Revenue (KPI)
	widget1 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Total Revenue",
		"widget_description": "Sum of all won deal values",
		"width": 4,
		"height": 3,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "deal_value",
		"aggregation_type": "Sum",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: Average Deal Value (KPI)
	widget2 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Average Deal Value",
		"widget_description": "Average value of all deals",
		"width": 4,
		"height": 3,
		"x_position": 4,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "deal_value",
		"aggregation_type": "Average",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: Potential Revenue (KPI)
	widget3 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Potential Revenue",
		"widget_description": "Sum of all open deal values",
		"width": 4,
		"height": 3,
		"x_position": 8,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "deal_value",
		"aggregation_type": "Sum",
		"color_scheme": "Orange",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 4: Revenue by Status (Chart)
	widget4 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Revenue by Deal Status",
		"widget_description": "Total deal value grouped by status",
		"width": 8,
		"height": 4,
		"x_position": 0,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"chart_type": "Bar",
		"x_axis_field": "status",
		"y_axis_field": "deal_value",
		"group_by_field": "status",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 5: Revenue Trend (Chart)
	widget5 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Revenue Trend",
		"widget_description": "Revenue trend over time",
		"width": 4,
		"height": 4,
		"x_position": 8,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"chart_type": "Line",
		"x_axis_field": "close_date",
		"y_axis_field": "deal_value",
		"group_by_field": "close_date",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_negotiation_dashboard():
	"""8.1.6: Create Negotiation Dashboard - Display negotiation volumes"""
	dashboard_name = "Negotiation Dashboard"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Display negotiation volumes")
	
	# Widget 1: Deals in Negotiation (KPI)
	widget1 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Deals in Negotiation",
		"widget_description": "Number of deals currently in negotiation stage",
		"width": 4,
		"height": 3,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Orange",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: Negotiation Value (KPI)
	widget2 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Total Negotiation Value",
		"widget_description": "Sum of deal values in negotiation",
		"width": 4,
		"height": 3,
		"x_position": 4,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "deal_value",
		"aggregation_type": "Sum",
		"color_scheme": "Purple",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: Average Negotiation Time (KPI)
	widget3 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Avg Deal Probability",
		"widget_description": "Average probability across deals",
		"width": 4,
		"height": 3,
		"x_position": 8,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "probability",
		"aggregation_type": "Average",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 4: Negotiation Volume Trend (Chart)
	widget4 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Negotiation Volume Trend",
		"widget_description": "Number of deals entering negotiation over time",
		"width": 12,
		"height": 4,
		"x_position": 0,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"chart_type": "Area",
		"x_axis_field": "modified",
		"y_axis_field": "name",
		"group_by_field": "modified",
		"color_scheme": "Orange",
		"show_refresh": 1,
		"refresh_interval": 0
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_team_performance_reports():
	"""8.2.1: Create Team Performance Reports - Capture dynamics of sales and service activities"""
	dashboard_name = "Team Performance Reports"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Capture dynamics of sales and service activities")
	
	# Widget 1: Team Performance Table - Deals
	widget1 = dashboard.append("widgets", {
		"widget_type": "Table",
		"widget_title": "Team Deal Performance",
		"widget_description": "Deal metrics by team member",
		"width": 12,
		"height": 5,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"table_columns": json.dumps(["name", "deal_owner", "status", "deal_value", "probability", "close_date", "creation"]),
		"table_filters": json.dumps({}),
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0,
		"drilldown_doctype": "CRM Deal"
	})
	
	# Widget 2: Team Performance Table - Leads
	widget2 = dashboard.append("widgets", {
		"widget_type": "Table",
		"widget_title": "Team Lead Performance",
		"widget_description": "Lead metrics by team member",
		"width": 12,
		"height": 5,
		"x_position": 0,
		"y_position": 5,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"table_columns": json.dumps(["name", "lead_owner", "status", "organization", "converted", "creation", "modified"]),
		"table_filters": json.dumps({}),
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0,
		"drilldown_doctype": "CRM Lead"
	})
	
	# Widget 3: Revenue by Owner (Chart)
	widget3 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Revenue by Team Member",
		"widget_description": "Total revenue generated by each team member",
		"width": 12,
		"height": 4,
		"x_position": 0,
		"y_position": 10,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"chart_type": "Bar",
		"x_axis_field": "deal_owner",
		"y_axis_field": "deal_value",
		"group_by_field": "deal_owner",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_individual_metrics_report():
	"""8.2.2: Create Individual Metrics Report - Provide visibility into individual performance metrics"""
	dashboard_name = "Individual Metrics Report"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Provide visibility into individual performance metrics")
	
	# Widget 1: My Deals (KPI)
	widget1 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "My Total Deals",
		"widget_description": "Total number of deals assigned to me",
		"width": 3,
		"height": 3,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: My Revenue (KPI)
	widget2 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "My Total Revenue",
		"widget_description": "Total revenue from my deals",
		"width": 3,
		"height": 3,
		"x_position": 3,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "deal_value",
		"aggregation_type": "Sum",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: My Leads (KPI)
	widget3 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "My Total Leads",
		"widget_description": "Total number of leads assigned to me",
		"width": 3,
		"height": 3,
		"x_position": 6,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Orange",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 4: My Conversion Rate (KPI)
	widget4 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "My Conversion Rate",
		"widget_description": "Percentage of my leads converted",
		"width": 3,
		"height": 3,
		"x_position": 9,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Purple",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 5: My Deals Table
	widget5 = dashboard.append("widgets", {
		"widget_type": "Table",
		"widget_title": "My Deals",
		"widget_description": "All deals assigned to me",
		"width": 6,
		"height": 5,
		"x_position": 0,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"table_columns": json.dumps(["name", "status", "deal_value", "probability", "close_date", "creation"]),
		"table_filters": json.dumps({}),
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0,
		"drilldown_doctype": "CRM Deal"
	})
	
	# Widget 6: My Leads Table
	widget6 = dashboard.append("widgets", {
		"widget_type": "Table",
		"widget_title": "My Leads",
		"widget_description": "All leads assigned to me",
		"width": 6,
		"height": 5,
		"x_position": 6,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"table_columns": json.dumps(["name", "status", "organization", "email", "mobile_no", "converted", "creation"]),
		"table_filters": json.dumps({}),
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0,
		"drilldown_doctype": "CRM Lead"
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)


def create_team_metrics_report():
	"""8.2.3: Create Team Metrics Report - Provide visibility into team performance metrics"""
	dashboard_name = "Team Metrics Report"
	
	if frappe.db.exists("CRM Dashboard", {"dashboard_name": dashboard_name}):
		return
	
	dashboard = make_dashboard_doc(dashboard_name, "Provide visibility into team performance metrics")
	
	# Widget 1: Team Total Deals (KPI)
	widget1 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Team Total Deals",
		"widget_description": "Total number of deals for the team",
		"width": 4,
		"height": 3,
		"x_position": 0,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Blue",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 2: Team Total Revenue (KPI)
	widget2 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Team Total Revenue",
		"widget_description": "Total revenue generated by the team",
		"width": 4,
		"height": 3,
		"x_position": 4,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"metric_field": "deal_value",
		"aggregation_type": "Sum",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 3: Team Total Leads (KPI)
	widget3 = dashboard.append("widgets", {
		"widget_type": "KPI",
		"widget_title": "Team Total Leads",
		"widget_description": "Total number of leads for the team",
		"width": 4,
		"height": 3,
		"x_position": 8,
		"y_position": 0,
		"data_source_type": "DocType",
		"data_source": "CRM Lead",
		"metric_field": "name",
		"aggregation_type": "Count",
		"color_scheme": "Orange",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 4: Team Performance by Member (Chart)
	widget4 = dashboard.append("widgets", {
		"widget_type": "Chart",
		"widget_title": "Team Performance by Member",
		"widget_description": "Deal count and revenue by team member",
		"width": 12,
		"height": 4,
		"x_position": 0,
		"y_position": 3,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"chart_type": "Bar",
		"x_axis_field": "deal_owner",
		"y_axis_field": "deal_value",
		"group_by_field": "deal_owner",
		"color_scheme": "Green",
		"show_refresh": 1,
		"refresh_interval": 0
	})
	
	# Widget 5: Team Metrics Table
	widget5 = dashboard.append("widgets", {
		"widget_type": "Table",
		"widget_title": "Team Performance Metrics",
		"widget_description": "Detailed team performance metrics",
		"width": 12,
		"height": 5,
		"x_position": 0,
		"y_position": 7,
		"data_source_type": "DocType",
		"data_source": "CRM Deal",
		"table_columns": json.dumps(["name", "deal_owner", "status", "deal_value", "probability", "close_date", "creation", "modified"]),
		"table_filters": json.dumps({}),
		"color_scheme": "Gray",
		"show_refresh": 1,
		"refresh_interval": 0,
		"drilldown_doctype": "CRM Deal"
	})

	add_lmotpo_widget(dashboard)
	dashboard.insert(ignore_permissions=True)

