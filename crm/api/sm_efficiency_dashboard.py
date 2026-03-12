import frappe
from frappe.utils import getdate, get_first_day, get_last_day, today
from datetime import timedelta


@frappe.whitelist()
def get_sm_efficiency_data():
	"""
	Returns monthly reorder efficiency data for the Sales Manager dashboard.
	- Sales Manager: shows their direct-report sales users with efficiency %.
	- Administrator: shows data grouped by Sales Manager, each with their subordinates.

	Efficiency % = (customers who DID reorder this month) / (customers EXPECTED to reorder this month) × 100

	"Expected to reorder this month" = customer has a Customer Order Frequancy record with at
	  least one item having frequency_day > 0, AND based on their last Sales Order date +
	  frequency_day, the next expected order falls within the current calendar month.

	"Did reorder" = customer placed at least one submitted Sales Order this calendar month.
	"""
	user = frappe.session.user

	is_admin = (user == "Administrator")
	is_sales_manager = "Sales Manager" in frappe.get_roles(user)

	if not is_admin and not is_sales_manager:
		return {"is_sales_manager": False}

	if is_admin:
		return _get_admin_efficiency_grouped()
	else:
		return _get_manager_efficiency(user)


def _get_manager_efficiency(user):
	"""Get efficiency data for a specific Sales Manager's team, including the manager themselves."""
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		return {
			"is_sales_manager": True,
			"view_mode": "manager",
			"sales_users": [],
			"error": "No Employee record linked to your user."
		}

	my_sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
	if not my_sales_person:
		return {
			"is_sales_manager": True,
			"view_mode": "manager",
			"sales_users": [],
			"error": "No Sales Person record linked to your employee."
		}

	# Include the manager's own data first (marked with ⭐)
	manager_sp = frappe.db.get_value(
		"Sales Person", my_sales_person,
		["name", "sales_person_name", "employee"], as_dict=True
	)
	manager_entries = _build_efficiency_for_users([manager_sp])
	for entry in manager_entries:
		entry["full_name"] = entry["full_name"] + " ⭐"

	subordinates = _get_subordinates(my_sales_person)
	subordinate_entries = _build_efficiency_for_users(subordinates)

	sales_users = manager_entries + subordinate_entries

	return {
		"is_sales_manager": True,
		"view_mode": "manager",
		"sales_users": sales_users
	}


def _get_admin_efficiency_grouped():
	"""Get efficiency data grouped by each Sales Manager for the Administrator view."""
	manager_sales_persons = frappe.db.get_all(
		"Sales Person",
		filters={"is_group": 1, "enabled": 1},
		fields=["name", "sales_person_name", "employee"]
	)

	groups = []
	for mgr in manager_sales_persons:
		mgr_user = None
		if mgr.employee:
			mgr_user = frappe.db.get_value("Employee", mgr.employee, "user_id")

		mgr_full_name = mgr.sales_person_name
		if mgr_user:
			mgr_full_name = frappe.db.get_value("User", mgr_user, "full_name") or mgr_full_name

		# Include the manager's own data
		manager_entries = _build_efficiency_for_users([mgr])
		for entry in manager_entries:
			entry["full_name"] = entry["full_name"] + " ⭐"

		subordinates = _get_subordinates(mgr.name)
		subordinate_entries = _build_efficiency_for_users(subordinates)

		sales_users = manager_entries + subordinate_entries
		if not sales_users:
			continue

		groups.append({
			"manager_name": mgr_full_name,
			"manager_sales_person": mgr.name,
			"sales_users": sales_users
		})

	return {
		"is_sales_manager": True,
		"view_mode": "admin",
		"groups": groups
	}


def _get_subordinates(parent_sales_person):
	"""Get all Sales Person records that report to the given parent."""
	return frappe.db.get_all(
		"Sales Person",
		filters={"parent_sales_person": parent_sales_person, "enabled": 1},
		fields=["name", "sales_person_name", "employee"]
	)


def _build_efficiency_for_users(sales_persons):
	"""
	Build monthly reorder efficiency stats for a list of Sales Person records.
	Returns a list of dicts with full_name, user, expected_count, actual_count, efficiency_pct.
	"""
	first_day = get_first_day(today())
	last_day = get_last_day(today())

	sales_users = []

	for sp in sales_persons:
		sp_user = None
		if sp.employee:
			sp_user = frappe.db.get_value("Employee", sp.employee, "user_id")

		if not sp_user:
			continue

		full_name = frappe.db.get_value("User", sp_user, "full_name") or sp.sales_person_name

		# --- Step 1: Query last order dates per customer & item BEFORE this month ---
		last_orders = frappe.db.sql("""
			SELECT 
				so.customer, 
				soi.item_code as item, 
				MAX(so.transaction_date) as last_date
			FROM `tabSales Order` so
			JOIN `tabSales Order Item` soi ON soi.parent = so.name
			WHERE so.docstatus = 1 
			  AND so.custom_sale_by = %(sp_name)s 
			  AND so.transaction_date < %(first_day)s
			GROUP BY so.customer, soi.item_code
		""", {"sp_name": sp.name, "first_day": first_day}, as_dict=True)
		
		last_item_orders = {}
		for row in last_orders:
			if row.customer not in last_item_orders:
				last_item_orders[row.customer] = {}
			last_item_orders[row.customer][row.item] = getdate(row.last_date)

		# --- Step 2: Query ACTUAL orders per customer & item DURING this month ---
		actual_orders = frappe.db.sql("""
			SELECT 
				so.customer, 
				soi.item_code as item, 
				COUNT(DISTINCT so.name) as actual_qty
			FROM `tabSales Order` so
			JOIN `tabSales Order Item` soi ON soi.parent = so.name
			WHERE so.docstatus = 1 
			  AND so.custom_sale_by = %(sp_name)s 
			  AND so.transaction_date BETWEEN %(first_day)s AND %(last_day)s
			GROUP BY so.customer, soi.item_code
		""", {"sp_name": sp.name, "first_day": first_day, "last_day": last_day}, as_dict=True)
		
		actual_month_counts = {}
		for row in actual_orders:
			if row.customer not in actual_month_counts:
				actual_month_counts[row.customer] = {}
			actual_month_counts[row.customer][row.item] = row.actual_qty

		# --- Step 3: Get all unique customers linked to this SP ---
		customers_rows = frappe.db.sql("""
			SELECT DISTINCT customer
			FROM `tabSales Order`
			WHERE custom_sale_by = %(sp_name)s
			  AND docstatus = 1
		""", {"sp_name": sp.name}, as_dict=True)
		customers = [r.customer for r in customers_rows if r.customer]

		if not customers:
			sales_users.append({
				"sales_person": sp.name,
				"full_name": full_name,
				"user": sp_user,
				"expected_count": 0,
				"actual_count": 0,
				"efficiency_pct": None
			})
			continue

		expected_count = 0
		actual_count = 0

		for customer in customers:
			cof_name = frappe.db.get_value("Customer Order Frequancy", {"customer_id": customer}, "name")
			if not cof_name:
				continue
			
			freq_items = frappe.db.get_all(
				"Item Wise Order Frequancy",
				filters={"parent": cof_name, "frequency_day": [">", 0]},
				fields=["item", "frequency_day"]
			)
			
			for freq_item in freq_items:
				item = freq_item.item
				freq_day = int(freq_item.frequency_day or 0)
				
				last_date = last_item_orders.get(customer, {}).get(item)
				if not last_date:
					continue
					
				expected_times_this_month = 0
				cur_date = last_date + timedelta(days=freq_day)
				
				while cur_date <= last_day:
					if cur_date >= first_day:
						expected_times_this_month += 1
					cur_date += timedelta(days=freq_day)
					
				if expected_times_this_month > 0:
					expected_count += expected_times_this_month
					
					actual_times = actual_month_counts.get(customer, {}).get(item, 0)
					actual_count += min(actual_times, expected_times_this_month)

		if expected_count > 0:
			efficiency_pct = round((actual_count / expected_count) * 100, 1)
		else:
			efficiency_pct = None

		sales_users.append({
			"sales_person": sp.name,
			"full_name": full_name,
			"user": sp_user,
			"expected_count": expected_count,
			"actual_count": actual_count,
			"efficiency_pct": efficiency_pct
		})

	return sales_users


@frappe.whitelist()
def get_efficiency_details(sp_name):
	"""
	Returns a customer and item breakdown for the given Sales Person.
	Used for drill-down in the dashboard widget.
	"""
	current_user = frappe.session.user
	if "Sales Manager" not in frappe.get_roles(current_user) and current_user != "Administrator":
		frappe.throw("You do not have permission to view this data.")

	first_day = get_first_day(today())
	last_day = get_last_day(today())

	# Query last orders BEFORE this month per item
	last_orders = frappe.db.sql("""
		SELECT 
			so.customer, 
			soi.item_code as item, 
			MAX(so.transaction_date) as last_date
		FROM `tabSales Order` so
		JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE so.docstatus = 1 
		  AND so.custom_sale_by = %(sp_name)s 
		  AND so.transaction_date < %(first_day)s
		GROUP BY so.customer, soi.item_code
	""", {"sp_name": sp_name, "first_day": first_day}, as_dict=True)
	
	last_item_orders = {}
	for row in last_orders:
		if row.customer not in last_item_orders:
			last_item_orders[row.customer] = {}
		last_item_orders[row.customer][row.item] = getdate(row.last_date)

	# Query ACTUAL orders DURING this month per item
	actual_orders = frappe.db.sql("""
		SELECT 
			so.customer, 
			soi.item_code as item, 
			COUNT(DISTINCT so.name) as actual_qty
		FROM `tabSales Order` so
		JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE so.docstatus = 1 
		  AND so.custom_sale_by = %(sp_name)s 
		  AND so.transaction_date BETWEEN %(first_day)s AND %(last_day)s
		GROUP BY so.customer, soi.item_code
	""", {"sp_name": sp_name, "first_day": first_day, "last_day": last_day}, as_dict=True)
	
	actual_month_counts = {}
	for row in actual_orders:
		if row.customer not in actual_month_counts:
			actual_month_counts[row.customer] = {}
		actual_month_counts[row.customer][row.item] = row.actual_qty

	customers_rows = frappe.db.sql("""
		SELECT DISTINCT customer
		FROM `tabSales Order`
		WHERE custom_sale_by = %(sp_name)s
		  AND docstatus = 1
	""", {"sp_name": sp_name}, as_dict=True)
	customers = [r.customer for r in customers_rows if r.customer]

	records = []
	for customer in customers:
		customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
		cof_name = frappe.db.get_value("Customer Order Frequancy", {"customer_id": customer}, "name")
		
		if not cof_name:
			continue
			
		freq_items = frappe.db.get_all(
			"Item Wise Order Frequancy",
			filters={"parent": cof_name, "frequency_day": [">", 0]},
			fields=["item", "frequency_day"]
		)

		has_expected_or_actual_items = False
		cust_expected = 0
		cust_actual = 0
		cust_items = []

		for freq_item in freq_items:
			item = freq_item.item
			freq_day = int(freq_item.frequency_day or 0)
			
			last_date = last_item_orders.get(customer, {}).get(item)
			if not last_date:
				continue
				
			expected_times_this_month = 0
			cur_date = last_date + timedelta(days=freq_day)
			
			while cur_date <= last_day:
				if cur_date >= first_day:
					expected_times_this_month += 1
				cur_date += timedelta(days=freq_day)
				
			actual_times = actual_month_counts.get(customer, {}).get(item, 0)
			
			if expected_times_this_month > 0:
				has_expected_or_actual_items = True
				actual_capped = min(actual_times, expected_times_this_month)
				cust_expected += expected_times_this_month
				cust_actual += actual_capped
				
				actual_class = "22c55e" if actual_capped >= expected_times_this_month else ("f59e0b" if actual_capped > 0 else "ef4444")
				cust_items.append(f"<span style='color:#{actual_class}; font-weight:600;'>{item} ({actual_times}/{expected_times_this_month})</span>")

		if has_expected_or_actual_items:
			efficiency_pct = round((cust_actual / cust_expected) * 100, 1) if cust_expected > 0 else None
			records.append({
				"customer": customer,
				"customer_name": customer_name,
				"cust_expected": cust_expected,
				"cust_actual": cust_actual,
				"efficiency_pct": efficiency_pct,
				"doc_route": f"/app/customer/{customer}",
				"item_details": ", ".join(cust_items)
			})

	# Sort: Most expected items first
	records.sort(key=lambda r: (-r["cust_expected"], -r["cust_actual"]))

	return records
