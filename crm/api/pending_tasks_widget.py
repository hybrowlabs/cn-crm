"""
pending_tasks_widget.py
-----------------------
API methods for the Pending Tasks dashboard widget.
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_pending_tasks():
	"""
	Return all CRM Tasks whose status is NOT 'Done',
	enriched with the linked Lead / Deal / Customer name and organization.
	Results are ordered: overdue first (red), due today (orange), upcoming (green).
	"""
	user = frappe.session.user
	is_admin = user == "Administrator" or "System Manager" in frappe.get_roles(user)

	where_clause = """
		t.status NOT IN ('Done', 'Canceled')
	"""

	if not is_admin:
		where_clause += """
			AND (
				t.assigned_to = %(user)s
				OR EXISTS (
					SELECT 1 FROM `tabToDo` td
					WHERE td.reference_type = 'CRM Task'
					AND td.reference_name = t.name
					AND td.allocated_to = %(user)s
					AND td.status = 'Open'
				)
			)
		"""

	tasks = frappe.db.sql(f"""
		SELECT
			t.name,
			t.title,
			t.status,
			t.priority,
			t.due_date,
			t.assigned_to,
			t.reference_doctype,
			t.reference_docname,
			t.description
		FROM `tabCRM Task` t
		WHERE
			{where_clause}
		ORDER BY
			CASE
				WHEN t.due_date IS NULL THEN 2
				WHEN DATE(t.due_date) < CURDATE() THEN 0
				WHEN DATE(t.due_date) = CURDATE() THEN 1
				ELSE 2
			END ASC,
			t.due_date ASC
		LIMIT 200
	""", {"user": user}, as_dict=True)

	# Enrich each task with lead/deal/customer info
	today = frappe.utils.today()

	for task in tasks:
		ref_dt = task.get("reference_doctype")
		ref_dn = task.get("reference_docname")

		task["ref_name"] = ""
		task["organization"] = ""
		task["ref_url"] = ""

		if ref_dt and ref_dn:
			try:
				if ref_dt == "CRM Lead":
					row = frappe.db.get_value(
						"CRM Lead", ref_dn,
						["lead_name", "organization", "name"],
						as_dict=True
					)
					if row:
						task["ref_name"] = row.lead_name or ref_dn
						task["organization"] = row.organization or ""
						task["ref_url"] = f"/crm/leads/{ref_dn}"

				elif ref_dt == "CRM Deal":
					row = frappe.db.get_value(
						"CRM Deal", ref_dn,
						["organization", "name"],
						as_dict=True
					)
					if row:
						task["ref_name"] = row.organization or ref_dn
						task["organization"] = row.organization or ""
						task["ref_url"] = f"/crm/deals/{ref_dn}"

				elif ref_dt == "Customer":
					row = frappe.db.get_value(
						"Customer", ref_dn,
						["customer_name", "name"],
						as_dict=True
					)
					if row:
						task["ref_name"] = row.customer_name or ref_dn
						task["organization"] = row.customer_name or ""
						task["ref_url"] = f"/app/customer/{ref_dn}"

			except Exception:
				pass

		# Due-date bucket for colour coding
		if task.due_date:
			due_str = str(task.due_date)[:10]
			if due_str < today:
				task["due_bucket"] = "overdue"
			elif due_str == today:
				task["due_bucket"] = "today"
			else:
				task["due_bucket"] = "upcoming"
		else:
			task["due_bucket"] = "none"

	return {"tasks": tasks, "total": len(tasks)}


@frappe.whitelist()
def mark_task_done(task_name):
	"""Mark a single CRM Task as Done."""
	task = frappe.get_doc("CRM Task", task_name)
	task.status = "Done"
	task.save(ignore_permissions=True)
	frappe.db.commit()
	return {"success": True, "name": task_name}


@frappe.whitelist()
def cancel_task(task_name):
	"""Mark a single CRM Task as Canceled."""
	task = frappe.get_doc("CRM Task", task_name)
	task.status = "Canceled"
	task.save(ignore_permissions=True)
	frappe.db.commit()
	return {"success": True, "name": task_name}
