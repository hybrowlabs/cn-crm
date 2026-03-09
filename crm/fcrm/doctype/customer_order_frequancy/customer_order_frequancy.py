# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, today
from datetime import datetime


class CustomerOrderFrequancy(Document):
	pass


@frappe.whitelist()
def calculate_frequency_for_customer(customer_id):
	"""
	Whitelist method to calculate frequency for a specific customer.
	Called from the front-end button — always force-recalculates regardless of recent orders.
	"""
	if not customer_id:
		frappe.throw("Customer ID is required")
	
	process_customer_frequency(customer_id)
	frappe.db.commit()
	frappe.msgprint(f"Frequency calculation completed for {customer_id}")


def calculate_customer_order_frequency(customer=None):
	"""
	Scheduled nightly job (runs at midnight via cron 0 0 * * *).

	Behaviour:
	  - If `customer` is given (e.g. triggered manually): always recalculate that customer.
	  - If running automatically (customer=None):
	      1. CREATE a new Customer Order Frequancy for customers who have Sales Orders
	         but do NOT yet have a frequency record.
	      2. UPDATE the existing Customer Order Frequancy ONLY for customers who placed
	         a Sales Order on the previous calendar day (yesterday).

	This keeps the nightly job lightweight and data fresh for active customers.
	"""
	try:
		if customer:
			# Manual / specific customer — always process
			frappe.logger().info(f"[COF] Force-processing customer: {customer}")
			process_customer_frequency(customer)
			frappe.db.commit()
			frappe.logger().info("[COF] Done (manual).")
			return

		yesterday = add_days(today(), -1)

		# ── 1. CREATE: customers with Sales Orders but NO frequency record ──────────
		all_so_customers = frappe.db.sql_list("""
			SELECT DISTINCT customer
			FROM `tabSales Order`
			WHERE docstatus = 1
			  AND customer IS NOT NULL
			  AND customer != ''
		""")

		existing_records = frappe.db.sql_list("""
			SELECT DISTINCT customer_id
			FROM `tabCustomer Order Frequancy`
			WHERE customer_id IS NOT NULL
		""")

		existing_set = set(existing_records)
		new_customers = [c for c in all_so_customers if c not in existing_set]

		frappe.logger().info(
			f"[COF] Nightly run — {len(new_customers)} new customer(s) to CREATE, "
			f"checking yesterday's reorders for UPDATE..."
		)

		created = 0
		for customer_id in new_customers:
			try:
				process_customer_frequency(customer_id)
				created += 1
			except Exception as e:
				frappe.logger().error(f"[COF] Error creating for {customer_id}: {str(e)}")

		# ── 2. UPDATE: customers who placed a Sales Order yesterday ──────────────────
		yesterday_customers = frappe.db.sql_list("""
			SELECT DISTINCT customer
			FROM `tabSales Order`
			WHERE docstatus = 1
			  AND transaction_date = %(yesterday)s
			  AND customer IS NOT NULL
			  AND customer != ''
		""", {"yesterday": yesterday})

		# Only update customers who already HAVE a frequency record
		to_update = [c for c in yesterday_customers if c in existing_set]

		frappe.logger().info(
			f"[COF] {len(to_update)} existing customer(s) to UPDATE (reordered yesterday: {yesterday})."
		)

		updated = 0
		for customer_id in to_update:
			try:
				process_customer_frequency(customer_id)
				updated += 1
			except Exception as e:
				frappe.logger().error(f"[COF] Error updating for {customer_id}: {str(e)}")

		frappe.db.commit()
		frappe.logger().info(
			f"[COF] Nightly run complete — created: {created}, updated: {updated}."
		)

	except Exception as e:
		frappe.logger().error(f"[COF] Fatal error in calculate_customer_order_frequency: {str(e)}")
		frappe.db.rollback()


def process_customer_frequency(customer_id):
	"""
	Process frequency calculation for a single customer.
	Fetches their last 10 submitted Sales Orders, computes item-wise average
	order frequency (days between orders), then saves/updates the
	Customer Order Frequancy document.

	Args:
		customer_id (str): Customer ID to process
	"""
	# Fetch last 10 submitted Sales Orders for this customer, sorted by date descending
	sales_orders = frappe.db.sql("""
		SELECT name, transaction_date
		FROM `tabSales Order`
		WHERE customer = %(customer)s
			AND docstatus = 1
		ORDER BY transaction_date DESC
		LIMIT 10
	""", {'customer': customer_id}, as_dict=True)
	
	if not sales_orders:
		# No orders for this customer — skip (nothing to calculate)
		return
	
	sales_order_names = [so.name for so in sales_orders]
	
	allowed_item_groups = [
		'Bronze', 'Casting Machine', 'Consumable', 'Furnace',
		'Investment Mixer', 'Master-Ag', 'Ni Based', 'Ni Free',
		'Ni Safe', 'Pink', 'Plating Ag', 'Plating Au',
		'Plating Other', 'Plating Pd', 'Plating Pt', 'Plating Rh',
		'RTU-Ag', 'RTU-Pd', 'RTU-Pt', 'Semi Finished',
		'Solder-Pink', 'Solder-Silver', 'Solder-White', 'Solder-Yellow',
		'Spares', 'Yellow'
	]

	items_data = frappe.db.sql("""
		SELECT 
			soi.item_code,
			soi.qty,
			so.transaction_date,
			so.name as sales_order
		FROM `tabSales Order Item` soi
		INNER JOIN `tabSales Order` so ON soi.parent = so.name
		INNER JOIN `tabItem` item ON soi.item_code = item.name
		WHERE so.name IN %(orders)s
			AND item.item_group IN %(item_groups)s
		ORDER BY so.transaction_date DESC
	""", {'orders': sales_order_names, 'item_groups': allowed_item_groups}, as_dict=True)
	
	if not items_data:
		return
	
	# Group items by item_code
	items_by_code = {}
	for item in items_data:
		if item.item_code not in items_by_code:
			items_by_code[item.item_code] = []
		items_by_code[item.item_code].append(item)
	
	# Calculate frequency for each item
	frequency_data = []
	
	for item_code, item_orders in items_by_code.items():
		# Sort by date descending (most recent first)
		item_orders.sort(key=lambda x: x.transaction_date, reverse=True)
		
		# Quantity from the most recent order
		last_order_qty = item_orders[0].qty
		
		# Calculate frequency_day (average days between consecutive orders)
		if len(item_orders) == 1:
			frequency_day = 0
		else:
			# Deduplicate by Sales Order (an item may appear multiple times in one order)
			order_dates = []
			seen_orders = set()
			for item_order in item_orders:
				if item_order.sales_order not in seen_orders:
					order_dates.append(item_order.transaction_date)
					seen_orders.add(item_order.sales_order)
			
			order_dates.sort()  # ascending (oldest first)
			
			if len(order_dates) > 1:
				oldest_date = getdate(order_dates[0])
				newest_date = getdate(order_dates[-1])
				days_diff = (newest_date - oldest_date).days
				frequency_day = days_diff / (len(order_dates) - 1)
			else:
				frequency_day = 0
		
		frequency_data.append({
			'item': item_code,
			'quantity': last_order_qty,
			'frequency_day': int(round(frequency_day))
		})
	
	# Save / update the Customer Order Frequancy document
	update_customer_frequency_doc(customer_id, frequency_data)


def update_customer_frequency_doc(customer_id, frequency_data):
	"""
	Update or create Customer Order Frequancy document for a customer.

	Args:
		customer_id (str): Customer ID
		frequency_data (list): List of dicts with item, quantity, frequency_day
	"""
	existing_doc = frappe.db.exists("Customer Order Frequancy", {"customer_id": customer_id})
	
	if existing_doc:
		doc = frappe.get_doc("Customer Order Frequancy", existing_doc)
		doc.item_wise_frequency = []  # Clear existing data before repopulating
	else:
		doc = frappe.new_doc("Customer Order Frequancy")
		doc.customer_id = customer_id
	
	for item_freq in frequency_data:
		doc.append("item_wise_frequency", item_freq)
	
	doc.save(ignore_permissions=True)
	frappe.logger().info(f"[COF] Saved Customer Order Frequancy for {customer_id}")
