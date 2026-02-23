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
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name") if employee else None

		if not sales_person:
			return {"customers": []}

		# Get customers where current user is in sales_team
		customer_list = frappe.db.sql("""
			SELECT DISTINCT parent
			FROM `tabSales Team`
			WHERE sales_person = %(sales_person)s
				AND parenttype = 'Customer'
		""", {'sales_person': sales_person}, as_dict=True)
		
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
def get_frequency_buckets():
	"""
	Get customer order frequency data grouped into day-range buckets.
	Buckets: 1-10, 11-20, 21-30, 31-40, 41-50, 51+
	Each bucket contains customers with items falling in that frequency range,
	along with the computed next_order_date.
	"""
	user = frappe.session.user

	# Determine which customers the user can see
	if "Administrator" in frappe.get_roles(user):
		freq_records = frappe.get_all(
			"Customer Order Frequancy",
			fields=["name", "customer_id", "customer_name"]
		)
	else:
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name") if employee else None

		if not sales_person:
			return {"buckets": []}

		customer_list = frappe.db.sql("""
			SELECT DISTINCT parent
			FROM `tabSales Team`
			WHERE sales_person = %(sales_person)s
				AND parenttype = 'Customer'
		""", {'sales_person': sales_person}, as_dict=True)

		if not customer_list:
			return {"buckets": []}

		customer_ids = [c.parent for c in customer_list]

		freq_records = frappe.get_all(
			"Customer Order Frequancy",
			filters={"customer_id": ["in", customer_ids]},
			fields=["name", "customer_id", "customer_name"]
		)

	# Define buckets
	bucket_defs = [
		{"label": "1 – 15 Days", "min": 1, "max": 15},
		{"label": "16 – 30 Days", "min": 16, "max": 30},
		{"label": "31 – 60 Days", "min": 31, "max": 60},
		{"label": "60+ Days", "min": 61, "max": 999999},
	]

	# Initialise bucket data structures
	buckets = {b["label"]: {"label": b["label"], "min": b["min"], "max": b["max"], "customers": {}} for b in bucket_defs}

	for rec in freq_records:
		try:
			doc = frappe.get_doc("Customer Order Frequancy", rec.name)
		except Exception:
			continue

		if not doc.item_wise_frequency:
			continue

		for item_row in doc.item_wise_frequency:
			freq_day = item_row.frequency_day or 0
			if freq_day <= 0:
				continue

			# Find the bucket
			target_bucket = None
			for b in bucket_defs:
				if b["min"] <= freq_day <= b["max"]:
					target_bucket = b["label"]
					break
			if not target_bucket:
				continue

			# Calculate next_order_date
			last_order = _get_last_order_date_for_bucket(rec.customer_id, item_row.item)
			next_order_date = None
			if last_order:
				next_order_date = str(add_days(last_order, freq_day))

			bucket_customers = buckets[target_bucket]["customers"]
			if rec.customer_id not in bucket_customers:
				bucket_customers[rec.customer_id] = {
					"customer_code": rec.customer_id,
					"customer_name": rec.customer_name or rec.customer_id,
					"items": []
				}

			bucket_customers[rec.customer_id]["items"].append({
				"item": item_row.item,
				"frequency_day": freq_day,
				"quantity": item_row.quantity,
				"next_order_date": next_order_date
			})

	# Convert to list, drop empty buckets
	result = []
	for b in bucket_defs:
		bucket = buckets[b["label"]]
		customers_list = list(bucket["customers"].values())
		if customers_list:
			customers_list.sort(key=lambda c: c["customer_name"])
			result.append({
				"label": bucket["label"],
				"min": bucket["min"],
				"max": bucket["max"],
				"count": sum(len(c["items"]) for c in customers_list),
				"customers": customers_list
			})

	return {"buckets": result}


def _get_last_order_date_for_bucket(customer_id, item_code):
	"""Helper: get the most recent Sales Order date for a customer + item."""
	result = frappe.db.sql("""
		SELECT so.transaction_date
		FROM `tabSales Order` so
		INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE so.customer = %(customer)s
			AND soi.item_code = %(item)s
			AND so.docstatus = 1
		ORDER BY so.transaction_date DESC
		LIMIT 1
	""", {'customer': customer_id, 'item': item_code}, as_dict=True)

	if result:
		return result[0].transaction_date
	return None


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


@frappe.whitelist()
def get_customers_for_user(**kwargs):
	user = frappe.session.user
	
	limit = frappe.form_dict.get("limit_page_length") or kwargs.get("limit_page_length") or 20
	start = frappe.form_dict.get("limit_start") or kwargs.get("limit_start") or 0
	
	try:
		limit = int(limit)
		start = int(start)
	except ValueError:
		limit = 20
		start = 0

	fields = ["name", "customer_name", "customer_group", "territory", "primary_address", "mobile_no"]
	
	roles = frappe.get_roles(user)
	if "Administrator" in roles or "System Manager" in roles:
		return frappe.get_all("Customer", fields=fields, order_by="creation desc", limit_start=start, limit_page_length=limit)
	else:
		employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
		sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name") if employee else None

		if not sales_person:
			return []

		# Customers where current user is in sales team
		customer_list = frappe.db.sql("""
			SELECT DISTINCT parent
			FROM `tabSales Team`
			WHERE sales_person = %(sales_person)s
				AND parenttype = 'Customer'
		""", {'sales_person': sales_person}, as_dict=True)
		
		if not customer_list:
			return []
			
		customer_ids = [c.parent for c in customer_list]
		
		return frappe.get_all("Customer", filters={"name": ["in", customer_ids]}, fields=fields, order_by="creation desc", limit_start=start, limit_page_length=limit)


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



@frappe.whitelist()
def generate_crm_tasks_for_customer(customer_id):
	"""
	Whitelist method to generate CRM Tasks for a specific customer's frequency items.
	Called from the Customer Order Frequancy form button.
	Creates tasks for all items with frequency data and assigns to the customer's sales team.
	"""
	from frappe.desk.form.assign_to import add as assign_to

	if not customer_id:
		frappe.throw("Customer ID is required")

	freq_doc_name = frappe.db.exists("Customer Order Frequancy", {"customer_id": customer_id})
	if not freq_doc_name:
		frappe.throw(f"No frequency record found for customer {customer_id}")

	freq_doc = frappe.get_doc("Customer Order Frequancy", freq_doc_name)
	if not freq_doc.item_wise_frequency:
		frappe.msgprint("No items with frequency data found")
		return

	# Get sales team user IDs for this customer
	sales_users = _get_sales_users_for_customer(customer_id)

	current_date = getdate(today())
	tasks_created = 0

	for item_freq in freq_doc.item_wise_frequency:
		if not item_freq.frequency_day or item_freq.frequency_day == 0:
			continue

		task_title = f"Frequency Expiry: {item_freq.item}"

		# Check if a CRM Task already exists for this customer + item
		existing_task = frappe.db.exists("CRM Task", {
			"title": task_title,
			"reference_doctype": "Customer",
			"reference_docname": customer_id,
			"status": ["not in", ["Done", "Canceled"]]
		})

		if existing_task:
			continue

		# Create the CRM Task
		task_doc = frappe.new_doc("CRM Task")
		task_doc.title = task_title
		task_doc.reference_doctype = "Customer"
		task_doc.reference_docname = customer_id
		task_doc.status = "Todo"
		task_doc.priority = "Medium"
		task_doc.description = item_freq.item
		task_doc.start_date = current_date
		task_doc.due_date = add_days(current_date, 4)

		# Assign to first sales user if available
		if sales_users:
			task_doc.assigned_to = sales_users[0]

		task_doc.insert(ignore_permissions=True)

		# Assign to additional sales users if multiple
		if len(sales_users) > 1:
			for user in sales_users[1:]:
				try:
					assign_to({
						"assign_to": [user],
						"doctype": "CRM Task",
						"name": task_doc.name,
						"description": task_doc.title,
					})
				except Exception:
					pass

		tasks_created += 1

	frappe.db.commit()
	frappe.msgprint(f"Created {tasks_created} CRM Task(s) for customer items")


def _get_sales_users_for_customer(customer_id):
	"""
	Get the User IDs of all sales persons assigned to a customer via Sales Team.
	Sales Team → Sales Person → Employee → User
	"""
	sales_team = frappe.db.sql("""
		SELECT DISTINCT st.sales_person
		FROM `tabSales Team` st
		WHERE st.parent = %(customer)s
			AND st.parenttype = 'Customer'
	""", {"customer": customer_id}, as_dict=True)

	user_ids = []
	for row in sales_team:
		if not row.sales_person:
			continue
		employee = frappe.db.get_value("Sales Person", row.sales_person, "employee")
		if employee:
			user_id = frappe.db.get_value("Employee", employee, "user_id")
			if user_id:
				user_ids.append(user_id)

	return user_ids


def create_crm_tasks_for_expiring_items():
	"""
	Create CRM Tasks for items whose order frequency is about to expire within 3 days.
	Runs as a scheduled task alongside generate_frequency_logs.
	"""
	from frappe.desk.form.assign_to import add as assign_to

	try:
		frappe.logger().info("Starting CRM Task creation for expiring frequency items")

		frequency_records = frappe.get_all(
			"Customer Order Frequancy",
			fields=["name", "customer_id", "customer_name"]
		)

		tasks_created = 0
		current_date = getdate(today())

		for freq_record in frequency_records:
			try:
				freq_doc = frappe.get_doc("Customer Order Frequancy", freq_record.name)

				if not freq_doc.item_wise_frequency:
					continue

				# Get sales team user IDs for this customer
				sales_users = _get_sales_users_for_customer(freq_record.customer_id)

				for item_freq in freq_doc.item_wise_frequency:
					if not item_freq.frequency_day or item_freq.frequency_day == 0:
						continue

					# Get last order date for this customer + item
					last_order_data = get_last_order_date(freq_record.customer_id, item_freq.item)
					if not last_order_data:
						continue

					last_order_date = last_order_data.transaction_date
					next_order_date = getdate(add_days(last_order_date, item_freq.frequency_day))

					# Check if next_order_date is within 3 days from today
					days_until_expiry = (next_order_date - current_date).days
					if days_until_expiry < 0 or days_until_expiry > 3:
						continue

					task_title = f"Frequency Expiry: {item_freq.item}"

					# Check if a CRM Task already exists for this customer + item
					existing_task = frappe.db.exists("CRM Task", {
						"title": task_title,
						"reference_doctype": "Customer",
						"reference_docname": freq_record.customer_id,
						"status": ["not in", ["Done", "Canceled"]]
					})

					if existing_task:
						continue

					# Create the CRM Task
					task_doc = frappe.new_doc("CRM Task")
					task_doc.title = task_title
					task_doc.reference_doctype = "Customer"
					task_doc.reference_docname = freq_record.customer_id
					task_doc.status = "Todo"
					task_doc.priority = "Medium"
					task_doc.description = item_freq.item
					task_doc.start_date = current_date
					task_doc.due_date = add_days(current_date, 4)

					# Assign to first sales user if available
					if sales_users:
						task_doc.assigned_to = sales_users[0]

					task_doc.insert(ignore_permissions=True)

					# Assign to additional sales users if multiple
					if len(sales_users) > 1:
						for user in sales_users[1:]:
							try:
								assign_to({
									"assign_to": [user],
									"doctype": "CRM Task",
									"name": task_doc.name,
									"description": task_doc.title,
								})
							except Exception:
								pass

					tasks_created += 1

			except Exception as e:
				frappe.logger().error(
					f"Error creating CRM Task for {freq_record.customer_id}: {str(e)}"
				)
				continue

		frappe.db.commit()
		frappe.logger().info(f"CRM Task creation completed. Created {tasks_created} tasks.")

	except Exception as e:
		frappe.logger().error(f"Error in create_crm_tasks_for_expiring_items: {str(e)}")
		frappe.db.rollback()
