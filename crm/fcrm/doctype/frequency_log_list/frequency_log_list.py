# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days, today


class FrequencyLogList(Document):
	pass


@frappe.whitelist()
def generate_logs_for_all():
	"""
	Whitelist method to generate logs for all customers.
	Called from the front-end button.
	"""
	generate_frequency_logs()
	frappe.msgprint("Frequency logs generated successfully")


@frappe.whitelist()
def get_followup_logs_for_user():
	"""
	Get frequency logs that need follow-up for the current user.
	Filters based on user permissions:
	- Administrators see all logs
	- Other users see only logs for customers they are assigned to via sales_team
	
	Returns:
		dict: Grouped logs by customer
	"""
	user = frappe.session.user
	
	# Check if user is Administrator
	if "Administrator" in frappe.get_roles(user):
		# Get all logs where done_flow_up = 0
		logs = frappe.get_all(
			"Frequency Log List",
			filters={"done_flow_up": 0},
			fields=["name", "customer_code", "customer_name", "item", "qty", "value", "next_order_date_as_per_frequency"],
			order_by="customer_name asc, item asc"
		)
	else:
		# Get customers where current user is in sales_team
		customer_list = frappe.db.sql("""
			SELECT DISTINCT parent
			FROM `tabSales Team`
			WHERE sales_person = %(user)s
				AND parenttype = 'Customer'
		""", {'user': user}, as_dict=True)
		
		if not customer_list:
			return {"customers": []}
		
		customer_ids = [c.parent for c in customer_list]
		
		# Get logs for these customers where done_flow_up = 0
		logs = frappe.get_all(
			"Frequency Log List",
			filters={
				"customer_code": ["in", customer_ids],
				"done_flow_up": 0
			},
			fields=["name", "customer_code", "customer_name", "item", "qty", "value", "next_order_date_as_per_frequency"],
			order_by="customer_name asc, item asc"
		)
	
	# Group logs by customer
	customers = {}
	for log in logs:
		customer_code = log.customer_code
		if customer_code not in customers:
			try:
				customer_doc = frappe.get_doc("Customer", customer_code)
				custom_branch = ""
				if customer_doc.get("custom_branch_details"):
					custom_branch = customer_doc.get("custom_branch_details")[0].branch
				
				customers[customer_code] = {
					"name": customer_doc.name,
					"customer_code": customer_code,
					"customer_name": log.customer_name,
					"default_currency": customer_doc.default_currency,
					"custom_branch": custom_branch,
					"items": [],
					"total_value": 0.0
				}
			except Exception:
				# Fallback if Customer doesn't exist or is inaccessible
				customers[customer_code] = {
					"name": customer_code,
					"customer_code": customer_code,
					"customer_name": log.customer_name,
					"default_currency": "",
					"custom_branch": "",
					"items": [],
					"total_value": 0.0
				}
		
		# Calculate value for this item (rate * qty)
		item_value = (log.value or 0) * (log.qty or 0)
		customers[customer_code]["total_value"] += item_value

		customers[customer_code]["items"].append({
			"log_id": log.name,
			"item": log.item,
			"qty": log.qty,
			"rate": log.value,
			"value": item_value,
			"next_order_date": log.next_order_date_as_per_frequency
		})
	
	# Convert to list and sort by total_value descending
	customer_list = list(customers.values())
	customer_list.sort(key=lambda x: x["total_value"], reverse=True)
	
	return {"customers": customer_list}


@frappe.whitelist()
def mark_followup_done(log_id):
	"""
	Mark a frequency log as followed up.
	
	Args:
		log_id (str): Name of the Frequency Log List document
	"""
	if not log_id:
		frappe.throw("Log ID is required")
	
	try:
		doc = frappe.get_doc("Frequency Log List", log_id)
		doc.done_flow_up = 1
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"success": True, "message": "Marked as followed up"}
	except Exception as e:
		frappe.logger().error(f"Error marking followup done for {log_id}: {str(e)}")
		frappe.throw(f"Failed to mark as followed up: {str(e)}")


@frappe.whitelist()
def mark_customer_followups_done(customer_code):
	"""
	Mark all frequency logs for a specific customer as followed up.
	
	Args:
		customer_code (str): Customer Code
	"""
	if not customer_code:
		frappe.throw("Customer Code is required")
	
	try:
		logs = frappe.get_all(
			"Frequency Log List",
			filters={
				"customer_code": customer_code,
				"done_flow_up": 0
			}
		)
		
		for log in logs:
			doc = frappe.get_doc("Frequency Log List", log.name)
			doc.done_flow_up = 1
			doc.save(ignore_permissions=True)
			
		frappe.db.commit()
		return {"success": True, "message": f"Marked {len(logs)} items as followed up"}
	except Exception as e:
		frappe.logger().error(f"Error marking customer followups done for {customer_code}: {str(e)}")
		frappe.throw(f"Failed to mark customer followups as done: {str(e)}")


def mark_followups_on_quotation(doc, method=None):
	"""
	Hook triggered after a Quotation is created.
	If it's for a Customer, mark their follow-ups as done.
	"""
	if doc.quotation_to == "Customer" and doc.party_name:
		try:
			mark_customer_followups_done(doc.party_name)
		except Exception as e:
			frappe.logger().error(f"Error in mark_followups_on_quotation for {doc.name}: {str(e)}")


def generate_frequency_logs():
	"""
	Generate logs in Frequency Log List for customers whose items have passed their order frequency.
	This runs nightly at midnight or can be triggered manually.
	"""
	try:
		frappe.logger().info("Starting frequency log generation")
		
		# Clear existing logs before generating new ones
		frappe.db.delete("Frequency Log List")
		frappe.db.commit()
		
		# Get all Customer Order Frequancy records
		frequency_records = frappe.get_all(
			"Customer Order Frequancy",
			fields=["name", "customer_id", "customer_name"]
		)
		
		logs_created = 0
		
		for freq_record in frequency_records:
			try:
				logs_count = process_customer_for_logs(
					freq_record.customer_id,
					freq_record.customer_name
				)
				logs_created += logs_count
			except Exception as e:
				frappe.logger().error(f"Error processing customer {freq_record.customer_id}: {str(e)}")
				continue
		
		frappe.db.commit()
		frappe.logger().info(f"Frequency log generation completed. Created {logs_created} logs.")
		
	except Exception as e:
		frappe.logger().error(f"Error in generate_frequency_logs: {str(e)}")
		frappe.db.rollback()


def process_customer_for_logs(customer_id, customer_name):
	"""
	Process a single customer and create log entries for items past their frequency.
	
	Args:
		customer_id (str): Customer ID
		customer_name (str): Customer Name
		
	Returns:
		int: Number of logs created for this customer
	"""
	logs_created = 0
	
	# Get the Customer Order Frequancy document
	freq_doc = frappe.get_doc("Customer Order Frequancy", {"customer_id": customer_id})
	
	if not freq_doc.item_wise_frequency:
		return 0
	
	current_date = getdate(today())
	
	for item_freq in freq_doc.item_wise_frequency:
		# Skip items with frequency_day = 0 (no follow-up needed)
		if not item_freq.frequency_day or item_freq.frequency_day == 0:
			continue
		
		# Get the last Sales Order date for this customer and item
		last_order_data = get_last_order_date(customer_id, item_freq.item)
		
		if not last_order_data:
			continue
			
		last_order_date = last_order_data.transaction_date
		base_price_list_rate = last_order_data.base_price_list_rate or 0
		
		# Calculate next order date based on frequency
		next_order_date = add_days(last_order_date, item_freq.frequency_day)
		
		# If today >= next_order_date, create a log entry
		if current_date >= getdate(next_order_date):
			try:
				create_log_entry(
					customer_id,
					customer_name,
					item_freq.item,
					item_freq.quantity,
					next_order_date,
					base_price_list_rate
				)
				logs_created += 1
			except Exception as e:
				frappe.logger().error(
					f"Error creating log for {customer_id} - {item_freq.item}: {str(e)}"
				)
				continue
	
	return logs_created


def get_last_order_date(customer_id, item_code):
	"""
	Get the last Sales Order date for a specific customer and item.
	
	Args:
		customer_id (str): Customer ID
		item_code (str): Item Code
		
	Returns:
		dict: Dictionary containing transaction_date and base_price_list_rate or None
	"""
	result = frappe.db.sql("""
		SELECT so.transaction_date, soi.base_price_list_rate
		FROM `tabSales Order` so
		INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE so.customer = %(customer)s
			AND soi.item_code = %(item)s
			AND so.docstatus = 1
		ORDER BY so.transaction_date DESC
		LIMIT 1
	""", {
		'customer': customer_id,
		'item': item_code
	}, as_dict=True)
	
	if result:
		return result[0]
	return None


def create_log_entry(customer_code, customer_name, item, qty, next_order_date, value=0):
	"""
	Create a Frequency Log List entry.
	
	Args:
		customer_code (str): Customer Code
		customer_name (str): Customer Name
		item (str): Item Code
		qty (float): Quantity
		next_order_date (date): Next order date as per frequency
		value (float): Value from base_price_list_rate
	"""
	log_doc = frappe.new_doc("Frequency Log List")
	log_doc.customer_code = customer_code
	log_doc.customer_name = customer_name
	log_doc.item = item
	log_doc.qty = qty
	log_doc.value = value
	log_doc.next_order_date_as_per_frequency = next_order_date
	log_doc.insert(ignore_permissions=True)
