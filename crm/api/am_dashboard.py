import frappe
from frappe.utils import get_first_day, get_last_day, today

@frappe.whitelist()
def get_am_dashboard_data():
	user = frappe.session.user
	
	current_date = today()
	first_day = get_first_day(current_date)
	last_day = get_last_day(current_date)
	
	# 1. My Booked Volume (Sales Order)
	# Formula: Sum of base_grand_total where custom_sales_by = user and transaction_date is in current month
	try:
		booked_volume = frappe.db.sql("""
			SELECT IFNULL(SUM(base_grand_total), 0) as total
			FROM `tabSales Order`
			WHERE custom_sales_by = %(user)s
			AND transaction_date BETWEEN %(first_day)s AND %(last_day)s
			AND docstatus = 1
		""", {
			"user": user,
			"first_day": first_day,
			"last_day": last_day
		}, as_dict=True)[0].total
	except Exception:
		booked_volume = 0
		
	# 2. My Pipeline Volume (CRM Deal)
	# Formula: Sum of annual_revenue where deal_owner = user and status in ('Opportunity', 'Trial', 'Proposal')
	pipeline_volume = frappe.db.sql("""
		SELECT IFNULL(SUM(annual_revenue), 0) as total
		FROM `tabCRM Deal`
		WHERE deal_owner = %(user)s
		AND status IN ('Opportunity', 'Trial', 'Proposal')
	""", {
		"user": user
	}, as_dict=True)[0].total
	
	# 3. My Pain Mix (CRM Deal)
	# Formula: Group by primary_pain_category where deal_owner = user
	pain_mix = frappe.db.sql("""
		SELECT IFNULL(primary_pain_category, 'Uncategorized') as category, COUNT(name) as value
		FROM `tabCRM Deal`
		WHERE deal_owner = %(user)s
		GROUP BY primary_pain_category
	""", {
		"user": user
	}, as_dict=True)
	
	return {
		"booked_volume": booked_volume,
		"pipeline_volume": pipeline_volume,
		"pain_mix": pain_mix
	}
