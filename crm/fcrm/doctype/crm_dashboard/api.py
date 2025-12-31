# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import json
from frappe import _
from frappe.utils import getdate, add_days, today, get_datetime


@frappe.whitelist()
def get_dashboard(name=None):
	"""Get dashboard by name or default dashboard for user"""
	try:
		if name:
			try:
				dashboard = frappe.get_doc("CRM Dashboard", name)
			except frappe.DoesNotExistError:
				frappe.throw(_("Dashboard {0} not found").format(name))
		else:
			# Get default dashboard for user
			try:
				dashboard_name = frappe.db.get_value(
					"CRM Dashboard",
					{"owner": frappe.session.user, "is_default": 1},
					"name",
					order_by="modified desc"
				)
			except Exception as e:
				frappe.log_error(f"Error getting default dashboard: {str(e)}", "Dashboard Error")
				dashboard_name = None
			
			if not dashboard_name:
				# Get any dashboard for user
				try:
					dashboard_name = frappe.db.get_value(
						"CRM Dashboard",
						{"owner": frappe.session.user},
						"name",
						order_by="modified desc"
					)
				except Exception as e:
					frappe.log_error(f"Error getting user dashboard: {str(e)}", "Dashboard Error")
					dashboard_name = None
			
			if not dashboard_name:
				# Get any public dashboard as fallback
				try:
					dashboard_name = frappe.db.get_value(
						"CRM Dashboard",
						{"is_public": 1},
						"name",
						order_by="modified desc"
					)
				except Exception as e:
					frappe.log_error(f"Error getting public dashboard: {str(e)}", "Dashboard Error")
					dashboard_name = None
			
			if dashboard_name:
				try:
					dashboard = frappe.get_doc("CRM Dashboard", dashboard_name)
				except frappe.DoesNotExistError:
					frappe.throw(_("Dashboard not found"))
			else:
				frappe.throw(_("No dashboard found"))
		
		dashboard.check_permission("read")
		
		# Convert widgets to list format
		dashboard_dict = dashboard.as_dict()
		if dashboard_dict.get("widgets"):
			dashboard_dict["widgets"] = [w.as_dict() for w in dashboard.widgets]
		
		return dashboard_dict
	except frappe.ValidationError:
		# Re-raise validation errors as-is
		raise
	except Exception as e:
		import traceback
		error_trace = traceback.format_exc()
		frappe.log_error(
			message=f"Error in get_dashboard:\n{error_trace}\n\nName: {name}",
			title="Dashboard Error"
		)
		frappe.throw(_("Failed to load dashboard: {0}").format(str(e)))


@frappe.whitelist()
def get_dashboards():
	"""Get all dashboards accessible to user"""
	try:
		user = frappe.session.user
		roles = frappe.get_roles()
		
		# Get user's own dashboards and public dashboards
		try:
			dashboards = frappe.get_all(
				"CRM Dashboard",
				filters={
					"owner": ["in", [user, "Administrator"]],
					"is_public": 0
				},
				fields=["name", "dashboard_name", "description", "is_default", "modified"],
				order_by="modified desc"
			)
		except Exception as e:
			frappe.log_error(f"Error getting user dashboards: {str(e)}", "Dashboard Error")
			dashboards = []
		
		# Add public dashboards
		try:
			public_dashboards = frappe.get_all(
				"CRM Dashboard",
				filters={"is_public": 1},
				fields=["name", "dashboard_name", "description", "is_default", "modified"],
				order_by="modified desc"
			)
		except Exception as e:
			frappe.log_error(f"Error getting public dashboards: {str(e)}", "Dashboard Error")
			public_dashboards = []
		
		# Merge and deduplicate
		all_dashboards = {d.name: d for d in dashboards}
		for d in public_dashboards:
			if d.name not in all_dashboards:
				all_dashboards[d.name] = d
		
		return list(all_dashboards.values())
	except Exception as e:
		import traceback
		error_trace = traceback.format_exc()
		frappe.log_error(
			message=f"Error in get_dashboards:\n{error_trace}",
			title="Dashboard Error"
		)
		frappe.throw(_("Failed to load dashboards: {0}").format(str(e)))


@frappe.whitelist()
def save_dashboard(dashboard_data):
	"""Save or update dashboard"""
	try:
		dashboard_data = json.loads(dashboard_data) if isinstance(dashboard_data, str) else dashboard_data
		
		is_new = not dashboard_data.get("name")
		
		# Validate dashboard_name for new dashboards
		if is_new:
			dashboard_name = dashboard_data.get("dashboard_name")
			if not dashboard_name:
				frappe.throw(_("Dashboard name is required"))
			
			dashboard = frappe.new_doc("CRM Dashboard")
			dashboard.name = dashboard_name
			dashboard.check_permission("create")
		else:
			dashboard = frappe.get_doc("CRM Dashboard", dashboard_data["name"])
			dashboard.check_permission("write")
			# Delete existing child widgets to avoid duplicate key errors
			frappe.db.delete("CRM Dashboard Widget", {"parent": dashboard.name})
			# Reload dashboard to get clean state after deletion
			dashboard.reload()
		
		# Update dashboard fields
		dashboard.update({
			"dashboard_name": dashboard_data.get("dashboard_name"),
			"description": dashboard_data.get("description"),
			"is_default": dashboard_data.get("is_default", 0),
			"is_public": dashboard_data.get("is_public", 0),
			"date_range_type": dashboard_data.get("date_range_type"),
			"from_date": dashboard_data.get("from_date"),
			"to_date": dashboard_data.get("to_date"),
			"user_filter": dashboard_data.get("user_filter"),
			"team_filter": dashboard_data.get("team_filter"),
		})
		
		# Clear widgets list and rebuild
		dashboard.widgets = []
		for widget_data in dashboard_data.get("widgets", []):
			widget = dashboard.append("widgets", {})
			# Clean widget data - remove None values and handle JSON fields
			clean_widget = {}
			widget_type = widget_data.get("widget_type")
			
			for key, value in widget_data.items():
				if value is not None:
					if key in ["table_columns", "table_filters", "drilldown_filters"]:
						if isinstance(value, str):
							clean_widget[key] = value
						elif isinstance(value, (dict, list)):
							clean_widget[key] = json.dumps(value)
						else:
							clean_widget[key] = value
					else:
						clean_widget[key] = value
			
			# LMOTPO widgets don't need data_source fields - clear them if set
			if widget_type == "LMOTPO":
				clean_widget["data_source_type"] = ""
				clean_widget["data_source"] = ""
				clean_widget.pop("metric_field", None)
				clean_widget.pop("aggregation_type", None)
				clean_widget.pop("chart_type", None)
				clean_widget.pop("x_axis_field", None)
				clean_widget.pop("y_axis_field", None)
				clean_widget.pop("group_by_field", None)
				clean_widget.pop("table_columns", None)
				clean_widget.pop("table_filters", None)
			
			widget.update(clean_widget)
		
		dashboard.save(ignore_permissions=True)
		
		# Return with widgets as list
		dashboard_dict = dashboard.as_dict()
		if dashboard_dict.get("widgets"):
			dashboard_dict["widgets"] = [w.as_dict() for w in dashboard.widgets]
		
		return dashboard_dict
	except frappe.ValidationError:
		# Re-raise validation errors as-is
		raise
	except Exception as e:
		import traceback
		error_trace = traceback.format_exc()
		frappe.log_error(
			message=f"Error in save_dashboard:\n{error_trace}\n\nDashboard Data: {dashboard_data}",
			title="Dashboard Save Error"
		)
		frappe.throw(_("Failed to save dashboard: {0}").format(str(e)))


@frappe.whitelist()
def delete_dashboard(name):
	"""Delete dashboard"""
	dashboard = frappe.get_doc("CRM Dashboard", name)
	dashboard.check_permission("delete")
	dashboard.delete()
	return {"success": True}


@frappe.whitelist()
def get_widget_data(widget_config, filters=None):
	"""Get data for a widget based on its configuration"""
	try:
		# Parse inputs safely
		try:
			widget_config = json.loads(widget_config) if isinstance(widget_config, str) else widget_config
		except (json.JSONDecodeError, TypeError) as e:
			frappe.throw(_("Invalid widget_config format: {0}").format(str(e)))
		
		try:
			filters = json.loads(filters) if isinstance(filters, str) else (filters or {})
		except (json.JSONDecodeError, TypeError):
			filters = {}
		
		# Extract only the fields we need, filtering out None/null values
		widget_type = widget_config.get("widget_type")
		data_source_type = widget_config.get("data_source_type")
		data_source = widget_config.get("data_source")
		
		if not widget_type:
			frappe.throw(_("widget_type is required"))

		# LMOTPO widgets are non–data-source and should bypass fetch/validation
		if widget_type == "LMOTPO":
			return {}

		if not data_source_type:
			frappe.throw(_("data_source_type is required"))
		if not data_source:
			frappe.throw(_("data_source is required"))
		
		# Create a clean config with only non-null values
		clean_config = {
			"widget_type": widget_type,
			"data_source_type": data_source_type,
			"data_source": data_source
		}
		
		# Add optional fields only if they exist and are not None/null
		for key in ["metric_field", "aggregation_type", "chart_type", "x_axis_field", 
		            "y_axis_field", "group_by_field", "table_columns", "table_filters"]:
			value = widget_config.get(key)
			if value is not None and value != "" and value != "null":
				clean_config[key] = value
		
		# Apply global filters
		applied_filters = apply_global_filters(filters, data_source_type, data_source)
		
		if widget_type == "KPI":
			return get_kpi_data(clean_config, applied_filters)
		elif widget_type == "Chart":
			return get_chart_data(clean_config, applied_filters)
		elif widget_type == "Table":
			return get_table_data(clean_config, applied_filters)
		else:
			frappe.throw(_("Unknown widget type: {0}").format(widget_type))
	except frappe.ValidationError:
		# Re-raise validation errors as-is (these are already properly formatted)
		raise
	except BrokenPipeError:
		# Handle broken pipe errors gracefully
		frappe.log_error(
			message="BrokenPipeError in get_widget_data - client disconnected",
			title="Dashboard Widget Error"
		)
		frappe.throw(_("Request was interrupted. Please try again."))
	except (OSError, IOError) as e:
		# Handle connection errors
		if "Broken pipe" in str(e) or "BrokenPipeError" in str(type(e).__name__):
			frappe.log_error(
				message=f"Connection error in get_widget_data: {str(e)}",
				title="Dashboard Widget Error"
			)
			frappe.throw(_("Connection error. Please try again."))
		raise
	except Exception as e:
		# Log the full error for debugging
		import traceback
		error_trace = traceback.format_exc()
		frappe.log_error(
			message=f"Error in get_widget_data:\n{error_trace}\n\nWidget Config: {widget_config}\nFilters: {filters}",
			title="Dashboard Widget Error"
		)
		# Return a user-friendly error message
		frappe.throw(_("Failed to load widget data: {0}").format(str(e)))


def apply_global_filters(filters, data_source_type, data_source):
	"""Apply global filters (date, user, team) to filters"""
	filters = filters or {}
	applied = {}
	# keep any user-provided filters that are not global keys
	for key, val in filters.items():
		if key not in {"from_date", "to_date", "date_range_type", "user_filter", "team_filter"}:
			applied[key] = val
	
	# Date range filter
	if filters.get("from_date") and filters.get("to_date"):
		if data_source_type == "DocType":
			# Apply to common date fields
			date_field = get_date_field_for_doctype(data_source)
			if date_field:
				applied[date_field] = ["between", [filters["from_date"], filters["to_date"]]]
	
	# User filter
	if filters.get("user_filter"):
		if data_source_type == "DocType":
			user_field = get_user_field_for_doctype(data_source)
			if user_field:
				applied[user_field] = filters["user_filter"]
	
	# Team filter (if applicable)
	if filters.get("team_filter"):
		# Team filtering would depend on specific doctype structure
		pass
	
	return applied


def get_date_field_for_doctype(doctype):
	"""Get the primary date field for a doctype"""
	meta = frappe.get_meta(doctype)
	
	# Common date field names
	date_fields = ["creation", "modified", "date", "transaction_date", "visit_date", "due_date"]
	
	for field_name in date_fields:
		if meta.get_field(field_name):
			return field_name
	
	# Find first date field
	for field in meta.fields:
		if field.fieldtype == "Date" or field.fieldtype == "Datetime":
			return field.fieldname
	
	return None


def get_user_field_for_doctype(doctype):
	"""Get the user field for a doctype"""
	meta = frappe.get_meta(doctype)
	
	# Common user field names
	user_fields = ["owner", "assigned_to", "sales_person", "deal_owner", "lead_owner"]
	
	for field_name in user_fields:
		if meta.get_field(field_name):
			return field_name
	
	return None


def get_kpi_data(widget_config, filters):
	"""Get KPI metric data"""
	try:
		data_source_type = widget_config.get("data_source_type")
		data_source = widget_config.get("data_source")
		metric_field = widget_config.get("metric_field")
		aggregation_type = widget_config.get("aggregation_type", "Count")
		
		if data_source_type != "DocType":
			frappe.throw(_("KPI widgets currently only support DocType data sources"))
		
		# Build query
		if aggregation_type == "Count":
			try:
				result = frappe.db.count(data_source, filters=filters)
			except Exception as e:
				frappe.log_error(f"Error counting {data_source}: {str(e)}", "Dashboard Widget Error")
				# Return 0 instead of failing
				result = 0
			return {"value": result, "label": f"Total {data_source}"}
		
		elif aggregation_type in ["Sum", "Average", "Min", "Max"]:
			if not metric_field:
				frappe.throw(_("Metric Field is required for {0} aggregation").format(aggregation_type))
			
			field_type = frappe.get_meta(data_source).get_field(metric_field)
			if not field_type:
				frappe.throw(_("Field {0} not found in {1}").format(metric_field, data_source))
			
			if field_type.fieldtype not in ["Currency", "Float", "Int", "Percent"]:
				frappe.throw(_("Field {0} must be numeric for aggregation").format(metric_field))
			
			# Get aggregation
			try:
				if aggregation_type == "Sum":
					result = frappe.db.get_all(
						data_source,
						filters=filters,
						fields=[f"sum(`{metric_field}`) as total"],
						as_list=True
					)
					value = result[0][0] if result and result[0][0] else 0
				elif aggregation_type == "Average":
					result = frappe.db.get_all(
						data_source,
						filters=filters,
						fields=[f"avg(`{metric_field}`) as avg_val"],
						as_list=True
					)
					value = result[0][0] if result and result[0][0] else 0
				elif aggregation_type == "Min":
					result = frappe.db.get_all(
						data_source,
						filters=filters,
						fields=[f"min(`{metric_field}`) as min_val"],
						as_list=True
					)
					value = result[0][0] if result and result[0][0] else 0
				elif aggregation_type == "Max":
					result = frappe.db.get_all(
						data_source,
						filters=filters,
						fields=[f"max(`{metric_field}`) as max_val"],
						as_list=True
					)
					value = result[0][0] if result and result[0][0] else 0
			except Exception as e:
				frappe.log_error(f"Error aggregating {metric_field} for {data_source}: {str(e)}", "Dashboard Widget Error")
				value = 0
			
			return {"value": value, "label": f"{aggregation_type} of {metric_field}"}
		else:
			return {"value": 0, "label": "No data"}
	except Exception as e:
		frappe.log_error(f"Error in get_kpi_data: {str(e)}", "Dashboard Widget Error")
		raise


def get_chart_data(widget_config, filters):
	"""Get chart data"""
	data_source_type = widget_config.get("data_source_type")
	data_source = widget_config.get("data_source")
	chart_type = widget_config.get("chart_type")
	x_axis_field = widget_config.get("x_axis_field")
	y_axis_field = widget_config.get("y_axis_field")
	group_by_field = widget_config.get("group_by_field")
	
	if data_source_type != "DocType":
		frappe.throw(_("Chart widgets currently only support DocType data sources"))
	
	meta = frappe.get_meta(data_source)
	
	# Validate fields - only validate if not using group_by
	if group_by_field:
		# When using group_by, we need group_by_field and y_axis_field
		if not meta.get_field(group_by_field):
			frappe.throw(_("Group By Field {0} not found").format(group_by_field))
		if not y_axis_field:
			frappe.throw(_("Y Axis Field is required for group_by charts"))
		if y_axis_field and not meta.get_field(y_axis_field):
			frappe.throw(_("Y Axis Field {0} not found").format(y_axis_field))
	else:
		# Simple x-y chart needs both fields
		if not x_axis_field:
			frappe.throw(_("X Axis Field is required for chart widgets"))
		if x_axis_field and not meta.get_field(x_axis_field):
			frappe.throw(_("X Axis Field {0} not found").format(x_axis_field))
		if not y_axis_field:
			frappe.throw(_("Y Axis Field is required for chart widgets"))
		if y_axis_field and not meta.get_field(y_axis_field):
			frappe.throw(_("Y Axis Field {0} not found").format(y_axis_field))
	
	# Get data
	if group_by_field:
		# Group by aggregation
		group_by_meta = meta.get_field(group_by_field)
		if not group_by_meta:
			frappe.throw(_("Group By Field {0} not found").format(group_by_field))
		
		# Check if y_axis_field is numeric for sum, otherwise use count
		y_axis_meta = meta.get_field(y_axis_field)
		if y_axis_meta and y_axis_meta.fieldtype in ["Currency", "Float", "Int", "Percent"]:
			# Use sum for numeric fields
			aggregation = f"sum(`{y_axis_field}`)"
		else:
			# Use count for non-numeric fields (like name field for counting records)
			aggregation = f"count(`{y_axis_field}`)"
		
		# Get grouped data
		try:
			data = frappe.db.get_all(
				data_source,
				filters=filters,
				fields=[group_by_field, f"{aggregation} as total"],
				group_by=group_by_field,
				order_by="total desc",
				limit=50  # Limit results to prevent timeouts
			)
		except Exception as e:
			frappe.log_error(f"Error getting chart data for {data_source}: {str(e)}", "Dashboard Widget Error")
			data = []
		
		labels = [str(d[group_by_field]) for d in data] if data else []
		values = [d.total for d in data] if data else []
		
		return {
			"labels": labels,
			"datasets": [{
				"label": y_axis_field,
				"data": values
			}]
		}
	else:
		# Simple x-y chart
		try:
			data = frappe.db.get_all(
				data_source,
				filters=filters,
				fields=[x_axis_field, y_axis_field],
				limit=100,
				order_by=x_axis_field
			)
		except Exception as e:
			frappe.log_error(f"Error getting chart data for {data_source}: {str(e)}", "Dashboard Widget Error")
			data = []
		
		labels = [str(d[x_axis_field]) for d in data] if data else []
		values = [d[y_axis_field] for d in data] if data else []
		
		return {
			"labels": labels,
			"datasets": [{
				"label": y_axis_field,
				"data": values
			}]
		}


def get_table_data(widget_config, filters):
	"""Get table data"""
	data_source_type = widget_config.get("data_source_type")
	data_source = widget_config.get("data_source")
	table_columns = widget_config.get("table_columns")
	table_filters = widget_config.get("table_filters")
	
	if data_source_type != "DocType":
		frappe.throw(_("Table widgets currently only support DocType data sources"))
	
	# Parse columns
	if isinstance(table_columns, str):
		table_columns = json.loads(table_columns)
	
	if not table_columns or not isinstance(table_columns, list):
		frappe.throw(_("Table Columns must be a list of field names"))
	
	# Merge filters
	merged_filters = filters.copy() if filters else {}
	if table_filters:
		if isinstance(table_filters, str):
			table_filters = json.loads(table_filters)
		merged_filters.update(table_filters)
	
	# Get data
	try:
		data = frappe.db.get_all(
			data_source,
			filters=merged_filters,
			fields=table_columns,
			limit=100,
			order_by="modified desc"
		)
	except Exception as e:
		frappe.log_error(f"Error getting table data for {data_source}: {str(e)}", "Dashboard Widget Error")
		data = []
	
	return {
		"columns": table_columns,
		"rows": data
	}


@frappe.whitelist()
def get_available_data_sources():
	"""Get list of available data sources for widgets"""
	try:
		doctypes = [
			"CRM Lead",
			"CRM Deal",
			"CRM Site Visit",
			"CRM Task",
			"FCRM Note",
			"CRM Call Log",
			"Contact",
			"Quotation"
		]
		
		# Filter out doctypes that don't exist
		valid_doctypes = []
		for doctype in doctypes:
			try:
				if frappe.db.exists("DocType", doctype):
					valid_doctypes.append(doctype)
			except Exception:
				# Skip if we can't check
				pass
		
		return {
			"DocType": valid_doctypes,
			"Report": [],  # Can be extended later
			"Query": []  # Can be extended later
		}
	except Exception as e:
		import traceback
		error_trace = traceback.format_exc()
		frappe.log_error(
			message=f"Error in get_available_data_sources:\n{error_trace}",
			title="Dashboard Error"
		)
		# Return default list instead of throwing
		return {
			"DocType": ["CRM Lead", "CRM Deal"],
			"Report": [],
			"Query": []
		}

