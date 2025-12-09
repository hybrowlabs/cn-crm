import frappe


def execute():
	"""
	Ensure CRM Dashboard Widget child table has parent link columns and backfill existing rows.
	If no dashboards exist after the fix, seed the default dashboards.
	"""
	table = "CRM Dashboard Widget"
	columns = set(frappe.db.get_table_columns(table))

	# Add missing child link columns (idempotent)
	for col in ("parent", "parentfield", "parenttype"):
		if col not in columns:
			frappe.db.add_column(table, col, "varchar(140)")

	# Backfill parent linkage for existing widgets
	frappe.db.sql(
		"""
		UPDATE `tabCRM Dashboard Widget`
		SET parent = substring_index(name, '-', 1),
		    parentfield = 'widgets',
		    parenttype = 'CRM Dashboard'
		WHERE (parent IS NULL OR parent = '')
		"""
	)

	# Seed defaults only if no dashboards exist
	if not frappe.db.count("CRM Dashboard"):
		from crm.patches.v1_0 import create_default_dashboards

		create_default_dashboards.execute()


