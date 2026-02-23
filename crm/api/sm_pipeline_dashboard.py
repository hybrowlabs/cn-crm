import frappe


@frappe.whitelist()
def get_sm_pipeline_data():
	"""
	Returns pipeline data for the Sales Manager dashboard.
	- Sales Manager: shows their direct-report sales users with pipeline counts.
	- Administrator: shows data grouped by Sales Manager, each with their subordinates.
	"""
	user = frappe.session.user

	# Check if user has Sales Manager role
	is_admin = (user == "Administrator")
	is_sales_manager = "Sales Manager" in frappe.get_roles(user)

	if not is_admin and not is_sales_manager:
		return {"is_sales_manager": False}

	# Lead stages (CRM Lead statuses)
	lead_stages = ["New", "Contacted", "Nurture", "Qualified", "Unqualified", "Junk"]
	# Deal stages (CRM Deal statuses)
	deal_stages = ["Qualification", "Demo/Making", "Proposal/Quotation", "Negotiation", "Won", "Lost"]

	stage_columns = [
		{"stage": s, "doctype": "CRM Lead"} for s in lead_stages
	] + [
		{"stage": s, "doctype": "CRM Deal"} for s in deal_stages
	]

	if is_admin:
		# Administrator view: grouped by Sales Manager
		return _get_admin_grouped_data(lead_stages, deal_stages, stage_columns)
	else:
		# Sales Manager view: flat list of direct reports
		return _get_manager_data(user, lead_stages, deal_stages, stage_columns)


def _get_manager_data(user, lead_stages, deal_stages, stage_columns):
	"""Get pipeline data for a specific Sales Manager's team."""
	employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
	if not employee:
		return {"is_sales_manager": True, "view_mode": "manager", "sales_users": [],
				"stage_columns": stage_columns, "error": "No Employee record linked to your user."}

	my_sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
	if not my_sales_person:
		return {"is_sales_manager": True, "view_mode": "manager", "sales_users": [],
				"stage_columns": stage_columns, "error": "No Sales Person record linked to your employee."}

	subordinates = _get_subordinates(my_sales_person)
	sales_users = _build_pipeline_for_users(subordinates, lead_stages, deal_stages)

	return {
		"is_sales_manager": True,
		"view_mode": "manager",
		"sales_users": sales_users,
		"stage_columns": stage_columns
	}


def _get_admin_grouped_data(lead_stages, deal_stages, stage_columns):
	"""Get pipeline data grouped by each Sales Manager for the Administrator view."""
	# Find all Sales Persons that are groups (i.e. Sales Managers with subordinates)
	manager_sales_persons = frappe.db.get_all(
		"Sales Person",
		filters={"is_group": 1, "enabled": 1},
		fields=["name", "sales_person_name", "employee"]
	)

	groups = []
	for mgr in manager_sales_persons:
		# Get manager's full name
		mgr_user = None
		if mgr.employee:
			mgr_user = frappe.db.get_value("Employee", mgr.employee, "user_id")

		mgr_full_name = mgr.sales_person_name
		if mgr_user:
			mgr_full_name = frappe.db.get_value("User", mgr_user, "full_name") or mgr_full_name

		subordinates = _get_subordinates(mgr.name)
		if not subordinates:
			continue

		sales_users = _build_pipeline_for_users(subordinates, lead_stages, deal_stages)
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
		"groups": groups,
		"stage_columns": stage_columns
	}


def _get_subordinates(parent_sales_person):
	"""Get all Sales Person records that report to the given parent."""
	return frappe.db.get_all(
		"Sales Person",
		filters={"parent_sales_person": parent_sales_person, "enabled": 1},
		fields=["name", "sales_person_name", "employee"]
	)


def _build_pipeline_for_users(subordinates, lead_stages, deal_stages):
	"""Build pipeline counts for a list of subordinate Sales Persons."""
	sales_users = []

	for sp in subordinates:
		sp_user = None
		if sp.employee:
			sp_user = frappe.db.get_value("Employee", sp.employee, "user_id")

		if not sp_user:
			continue

		full_name = frappe.db.get_value("User", sp_user, "full_name") or sp.sales_person_name

		# Count leads by status
		lead_counts = {}
		lead_data = frappe.db.sql("""
			SELECT status, COUNT(name) as count
			FROM `tabCRM Lead`
			WHERE lead_owner = %(user)s
			GROUP BY status
		""", {"user": sp_user}, as_dict=True)

		for row in lead_data:
			lead_counts[row.status] = row["count"]

		# Count deals by status
		deal_counts = {}
		deal_data = frappe.db.sql("""
			SELECT status, COUNT(name) as count
			FROM `tabCRM Deal`
			WHERE deal_owner = %(user)s
			GROUP BY status
		""", {"user": sp_user}, as_dict=True)

		for row in deal_data:
			deal_counts[row.status] = row["count"]

		# Build stage data in pipeline order
		stages = []
		for s in lead_stages:
			stages.append({"stage": s, "doctype": "CRM Lead", "count": lead_counts.get(s, 0)})
		for s in deal_stages:
			stages.append({"stage": s, "doctype": "CRM Deal", "count": deal_counts.get(s, 0)})

		sales_users.append({
			"sales_person": sp.name,
			"full_name": full_name,
			"user": sp_user,
			"stages": stages
		})

	return sales_users


@frappe.whitelist()
def get_stage_details(user, doctype, status):
	"""
	Returns the list of records for a specific user, doctype and status.
	Used for drill-down when clicking on a count in the dashboard.
	"""
	current_user = frappe.session.user
	if "Sales Manager" not in frappe.get_roles(current_user) and current_user != "Administrator":
		frappe.throw("You do not have permission to view this data.")

	if doctype == "CRM Lead":
		records = frappe.db.sql("""
			SELECT name as id, organization, first_name, last_name, status, mobile_no
			FROM `tabCRM Lead`
			WHERE lead_owner = %(user)s AND status = %(status)s
			ORDER BY modified DESC
		""", {"user": user, "status": status}, as_dict=True)

		for r in records:
			r["doc_route"] = f"/app/crm-lead/{r['id']}"

	elif doctype == "CRM Deal":
		records = frappe.db.sql("""
			SELECT name as id, organization, organization_name, status, deal_value
			FROM `tabCRM Deal`
			WHERE deal_owner = %(user)s AND status = %(status)s
			ORDER BY modified DESC
		""", {"user": user, "status": status}, as_dict=True)

		for r in records:
			r["doc_route"] = f"/app/crm-deal/{r['id']}"

	else:
		frappe.throw("Invalid doctype")

	return records
