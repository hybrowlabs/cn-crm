# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate
from datetime import datetime


class CustomerOrderFrequancy(Document):
	pass


@frappe.whitelist()
def calculate_frequency_for_customer(customer_id):
	"""
	Whitelist method to calculate frequency for a specific customer.
	Called from the front-end button.
	"""
	if not customer_id:
		frappe.throw("Customer ID is required")
	
	calculate_customer_order_frequency(customer=customer_id)
	frappe.msgprint(f"Frequency calculation completed for {customer_id}")


def calculate_customer_order_frequency(customer=None):
	"""
	Calculate item-wise order frequency for customers based on their last 10 Sales Orders.
	
	Args:
		customer (str, optional): Specific customer to process. If None, processes all customers.
	"""
	try:
		# Get list of customers to process
		if customer:
			customers = [customer]
		else:
			# Get all customers who have at least one Sales Order
			customers = frappe.db.sql_list("""
				SELECT DISTINCT customer
				FROM `tabSales Order`
				WHERE docstatus = 1
			""")
		
		frappe.logger().info(f"Processing {len(customers)} customers for order frequency calculation")
		
		for customer_id in customers:
			try:
				process_customer_frequency(customer_id)
			except Exception as e:
				frappe.logger().error(f"Error processing customer {customer_id}: {str(e)}")
				continue
		
		frappe.db.commit()
		frappe.logger().info("Customer order frequency calculation completed")
		
	except Exception as e:
		frappe.logger().error(f"Error in calculate_customer_order_frequency: {str(e)}")
		frappe.db.rollback()


def process_customer_frequency(customer_id):
	"""
	Process frequency calculation for a single customer.
	
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
		# No orders for this customer, skip
		return
	
	# Collect all items from these orders with their details
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
		
		# Get quantity from the most recent order
		last_order_qty = item_orders[0].qty
		
		# Calculate frequency_day
		if len(item_orders) == 1:
			# Only one order containing this item
			frequency_day = 0
		else:
			# Get unique dates for this item (in case same item appears multiple times in one order)
			order_dates = []
			seen_orders = set()
			for item_order in item_orders:
				if item_order.sales_order not in seen_orders:
					order_dates.append(item_order.transaction_date)
					seen_orders.add(item_order.sales_order)
			
			# Sort dates ascending (oldest first)
			order_dates.sort()
			
			if len(order_dates) > 1:
				# Calculate average days between orders
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
	
	# Update or create Customer Order Frequancy document
	update_customer_frequency_doc(customer_id, frequency_data)


def update_customer_frequency_doc(customer_id, frequency_data):
	"""
	Update or create Customer Order Frequancy document for a customer.
	
	Args:
		customer_id (str): Customer ID
		frequency_data (list): List of dicts with item, quantity, frequency_day
	"""
	# Check if document already exists
	existing_doc = frappe.db.exists("Customer Order Frequancy", {"customer_id": customer_id})
	
	if existing_doc:
		# Update existing document
		doc = frappe.get_doc("Customer Order Frequancy", existing_doc)
		doc.item_wise_frequency = []  # Clear existing data
	else:
		# Create new document
		doc = frappe.new_doc("Customer Order Frequancy")
		doc.customer_id = customer_id
	
	# Add frequency data to child table
	for item_freq in frequency_data:
		doc.append("item_wise_frequency", item_freq)
	
	# Save the document
	doc.save(ignore_permissions=True)
	frappe.logger().info(f"Updated Customer Order Frequancy for {customer_id}")
