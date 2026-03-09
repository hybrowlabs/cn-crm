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
	Returns a list of dicts with full_name, user, expected_count, actual_count, efficiency_pct,
	and customers detail list.
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

		# --- Step 1: Find all customers for this sales person (via Sales Orders) ---
		customer_rows = frappe.db.sql("""
			SELECT DISTINCT customer
			FROM `tabSales Order`
			WHERE custom_sale_by = %(sp_name)s
			  AND docstatus = 1
		""", {"sp_name": sp.name}, as_dict=True)

		customers = [r.customer for r in customer_rows if r.customer]

		if not customers:
			# No customers linked → efficiency not applicable
			sales_users.append({
				"sales_person": sp.name,
				"full_name": full_name,
				"user": sp_user,
				"expected_count": 0,
				"actual_count": 0,
				"efficiency_pct": None  # N/A
			})
			continue

		# --- Step 2: For each customer, determine if they were expected to reorder this month ---
		expected_customers = []
		actual_reorder_set = set()

		# Get customers who reordered this month (submitted SO with transaction_date in current month)
		if customers:
			reordered_rows = frappe.db.sql("""
				SELECT DISTINCT customer
				FROM `tabSales Order`
				WHERE customer IN %(customers)s
				  AND custom_sale_by = %(sp_name)s
				  AND docstatus = 1
				  AND transaction_date BETWEEN %(first_day)s AND %(last_day)s
			""", {
				"customers": customers,
				"sp_name": sp.name,
				"first_day": first_day,
				"last_day": last_day
			}, as_dict=True)
			actual_reorder_set = {r.customer for r in reordered_rows}

		for customer in customers:
			# Check Customer Order Frequancy for this customer
			cof_name = frappe.db.get_value(
				"Customer Order Frequancy", {"customer_id": customer}, "name"
			)
			if not cof_name:
				continue  # No frequency data → skip

			# Get item-wise frequency records (only items with frequency_day > 0)
			freq_items = frappe.db.get_all(
				"Item Wise Order Frequancy",
				filters={"parent": cof_name, "frequency_day": [">", 0]},
				fields=["item", "frequency_day"]
			)
			if not freq_items:
				continue  # No valid frequency data

			# Get the last Sales Order date for this customer from this sales person
			last_so = frappe.db.sql("""
				SELECT MAX(transaction_date) as last_date
				FROM `tabSales Order`
				WHERE customer = %(customer)s
				  AND custom_sale_by = %(sp_name)s
				  AND docstatus = 1
			""", {"customer": customer, "sp_name": sp.name}, as_dict=True)

			last_order_date = last_so[0].last_date if last_so and last_so[0].last_date else None
			if not last_order_date:
				continue

			last_order_date = getdate(last_order_date)

			# Check if any item's next expected reorder falls within this month
			is_expected = False
			for freq_item in freq_items:
				freq_day = int(freq_item.frequency_day or 0)
				if freq_day <= 0:
					continue
				next_expected_date = last_order_date + timedelta(days=freq_day)
				# Expected if next order date is within current month (or already overdue → still expected)
				if next_expected_date <= last_day:
					is_expected = True
					break

			if is_expected:
				expected_customers.append(customer)

		expected_count = len(expected_customers)
		actual_count = len([c for c in expected_customers if c in actual_reorder_set])

		if expected_count > 0:
			efficiency_pct = round((actual_count / expected_count) * 100, 1)
		else:
			efficiency_pct = None  # N/A — no customers were expected to reorder

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
	Returns a customer-by-customer breakdown for the given Sales Person.
	Used for drill-down in the dashboard widget.
	"""
	current_user = frappe.session.user
	if "Sales Manager" not in frappe.get_roles(current_user) and current_user != "Administrator":
		frappe.throw("You do not have permission to view this data.")

	first_day = get_first_day(today())
	last_day = get_last_day(today())

	# All customers for this sales person
	customer_rows = frappe.db.sql("""
		SELECT DISTINCT customer
		FROM `tabSales Order`
		WHERE custom_sale_by = %(sp_name)s
		  AND docstatus = 1
	""", {"sp_name": sp_name}, as_dict=True)

	customers = [r.customer for r in customer_rows if r.customer]

	if not customers:
		return []

	# Customers who reordered this month
	reordered_rows = frappe.db.sql("""
		SELECT DISTINCT customer
		FROM `tabSales Order`
		WHERE customer IN %(customers)s
		  AND custom_sale_by = %(sp_name)s
		  AND docstatus = 1
		  AND transaction_date BETWEEN %(first_day)s AND %(last_day)s
	""", {
		"customers": customers,
		"sp_name": sp_name,
		"first_day": first_day,
		"last_day": last_day
	}, as_dict=True)
	actual_reorder_set = {r.customer for r in reordered_rows}

	records = []
	for customer in customers:
		customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer

		cof_name = frappe.db.get_value(
			"Customer Order Frequancy", {"customer_id": customer}, "name"
		)

		is_expected = False
		min_freq_day = None

		if cof_name:
			freq_items = frappe.db.get_all(
				"Item Wise Order Frequancy",
				filters={"parent": cof_name, "frequency_day": [">", 0]},
				fields=["item", "frequency_day"]
			)

			if freq_items:
				last_so = frappe.db.sql("""
					SELECT MAX(transaction_date) as last_date
					FROM `tabSales Order`
					WHERE customer = %(customer)s
					  AND custom_sale_by = %(sp_name)s
					  AND docstatus = 1
				""", {"customer": customer, "sp_name": sp_name}, as_dict=True)

				last_order_date = last_so[0].last_date if last_so and last_so[0].last_date else None

				if last_order_date:
					last_order_date = getdate(last_order_date)
					for freq_item in freq_items:
						freq_day = int(freq_item.frequency_day or 0)
						if freq_day <= 0:
							continue
						next_expected = last_order_date + timedelta(days=freq_day)
						if next_expected <= last_day:
							is_expected = True
							if min_freq_day is None or freq_day < min_freq_day:
								min_freq_day = freq_day

		did_reorder = customer in actual_reorder_set

		records.append({
			"customer": customer,
			"customer_name": customer_name,
			"is_expected": is_expected,
			"did_reorder": did_reorder,
			"frequency_day": min_freq_day,
			"doc_route": f"/app/customer/{customer}"
		})

	# Sort: expected first, then by did_reorder desc
	records.sort(key=lambda r: (not r["is_expected"], not r["did_reorder"]))

	return records
