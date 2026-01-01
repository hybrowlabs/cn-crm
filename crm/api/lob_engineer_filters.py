import frappe
from frappe import _
from typing import Dict, List, Optional


@frappe.whitelist()
def get_engineers_for_lob_selection(lob_name: str = None, include_general: bool = True) -> List[Dict]:
	"""
	Get filtered list of service engineers for LoB-based selection fields.

	Args:
		lob_name: Specific LoB to filter engineers for
		include_general: Whether to include General Services engineers as fallback

	Returns:
		list: Filtered engineers suitable for selection dropdowns
	"""
	if not lob_name:
		# If no LoB specified, return all service engineers
		return get_all_service_engineers()

	try:
		engineers = []

		# Get engineers for the specific LoB
		if frappe.db.exists("CRM Line of Business", lob_name):
			lob_engineers = get_engineers_for_specific_lob(lob_name)
			engineers.extend(lob_engineers)

		# Include General Services engineers if requested and LoB is not General Services
		if include_general and lob_name != "General Services":
			general_engineers = get_engineers_for_specific_lob("General Services")
			for eng in general_engineers:
				# Avoid duplicates
				if not any(e["user"] == eng["user"] for e in engineers):
					eng["from_general"] = True  # Mark as fallback option
					engineers.append(eng)

		# Sort by relevance: LoB-specific engineers first, then General Services
		engineers.sort(key=lambda x: (
			x.get("from_general", False),  # LoB-specific first
			not x.get("is_primary", False),  # Primary engineers first
			{"Expert": 0, "Advanced": 1, "Intermediate": 2, "Beginner": 3}.get(x.get("expertise_level", "Intermediate"), 2)
		))

		return engineers

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error filtering engineers for LoB {lob_name}")
		return []


def get_engineers_for_specific_lob(lob_name: str) -> List[Dict]:
	"""
	Get engineers assigned to a specific LoB.

	Args:
		lob_name: Name of the Line of Business

	Returns:
		list: Engineers for the specific LoB
	"""
	if not frappe.db.exists("CRM Line of Business", lob_name):
		return []

	try:
		lob = frappe.get_doc("CRM Line of Business", lob_name)
		engineers = []

		for engineer_row in lob.service_engineers or []:
			if not engineer_row.service_engineer:
				continue

			# Check if user is active
			user_doc = frappe.db.get_value(
				"User",
				engineer_row.service_engineer,
				["enabled", "full_name", "first_name", "last_name"],
				as_dict=True
			)

			if not user_doc or not user_doc.enabled:
				continue

			engineer_info = {
				"user": engineer_row.service_engineer,
				"full_name": user_doc.full_name or engineer_row.service_engineer,
				"first_name": user_doc.first_name,
				"last_name": user_doc.last_name,
				"is_primary": engineer_row.is_primary,
				"expertise_level": engineer_row.expertise_level or "Intermediate",
				"lob": lob_name,
				"lob_name": lob.lob_name,
				"from_general": False
			}
			engineers.append(engineer_info)

		return engineers

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting engineers for LoB {lob_name}")
		return []


def get_all_service_engineers() -> List[Dict]:
	"""
	Get all service engineers across all LoB teams.

	Returns:
		list: All service engineers with their LoB assignments
	"""
	try:
		all_engineers = []

		# Get all active LoB records
		lobs = frappe.get_all(
			"CRM Line of Business",
			filters={"is_active": 1},
			fields=["name", "lob_name"]
		)

		engineer_users = set()  # Track users to avoid duplicates

		for lob in lobs:
			lob_engineers = get_engineers_for_specific_lob(lob.name)
			for engineer in lob_engineers:
				if engineer["user"] not in engineer_users:
					all_engineers.append(engineer)
					engineer_users.add(engineer["user"])

		# Sort by name
		all_engineers.sort(key=lambda x: x["full_name"])

		return all_engineers

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error getting all service engineers")
		return []


@frappe.whitelist()
def get_lob_engineer_options(doctype: str = None, docname: str = None) -> List[Dict]:
	"""
	Get engineer options based on document context (for dynamic filtering).

	Args:
		doctype: Document type requesting the options
		docname: Document name to get LoB context from

	Returns:
		list: Context-aware engineer options
	"""
	lob_name = None

	# Get LoB context from the document
	if doctype and docname:
		try:
			if doctype in ["CRM Site Visit", "CRM Deal", "CRM Lead"]:
				lob_name = frappe.db.get_value(doctype, docname, "line_of_business")
		except Exception:
			pass

	# Return filtered engineers based on LoB context
	return get_engineers_for_lob_selection(lob_name, include_general=True)


@frappe.whitelist()
def validate_engineer_lob_assignment(engineer_user: str, lob_name: str) -> Dict:
	"""
	Validate if an engineer can be assigned to a specific LoB.

	Args:
		engineer_user: User ID of the engineer
		lob_name: Line of Business to check assignment for

	Returns:
		dict: Validation result
	"""
	try:
		if not engineer_user or not lob_name:
			return {
				"valid": False,
				"message": "Engineer and LoB are required for validation"
			}

		# Check if user exists and is active
		user_exists = frappe.db.exists("User", engineer_user)
		if not user_exists:
			return {
				"valid": False,
				"message": f"User {engineer_user} not found"
			}

		user_enabled = frappe.db.get_value("User", engineer_user, "enabled")
		if not user_enabled:
			return {
				"valid": False,
				"message": f"User {engineer_user} is not active"
			}

		# Get available engineers for the LoB
		available_engineers = get_engineers_for_lob_selection(lob_name, include_general=True)
		engineer_users = [eng["user"] for eng in available_engineers]

		if engineer_user in engineer_users:
			# Find the engineer info
			engineer_info = next((eng for eng in available_engineers if eng["user"] == engineer_user), None)
			return {
				"valid": True,
				"message": "Engineer is eligible for this LoB",
				"engineer_info": engineer_info
			}
		else:
			return {
				"valid": False,
				"message": f"Engineer {engineer_user} is not assigned to {lob_name} service team",
				"suggestion": "Consider using General Services team or assign engineer to this LoB first"
			}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error validating engineer LoB assignment")
		return {
			"valid": False,
			"message": f"Validation error: {str(e)}"
		}


@frappe.whitelist()
def get_primary_engineers_by_lob() -> Dict:
	"""
	Get primary engineers grouped by Line of Business.
	Useful for quick assignment and overview dashboards.

	Returns:
		dict: Primary engineers grouped by LoB
	"""
	try:
		lob_engineers = {}

		# Get all active LoB records
		lobs = frappe.get_all(
			"CRM Line of Business",
			filters={"is_active": 1},
			fields=["name", "lob_name", "lob_code"],
			order_by="display_order asc, lob_name asc"
		)

		for lob in lobs:
			engineers = get_engineers_for_specific_lob(lob.name)
			primary_engineers = [eng for eng in engineers if eng.get("is_primary")]

			lob_engineers[lob.name] = {
				"lob_name": lob.lob_name,
				"lob_code": lob.lob_code,
				"primary_engineers": primary_engineers,
				"total_engineers": len(engineers),
				"primary_count": len(primary_engineers)
			}

		return lob_engineers

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error getting primary engineers by LoB")
		return {}


@frappe.whitelist()
def get_engineer_workload_by_lob(lob_name: str = None) -> List[Dict]:
	"""
	Get engineer workload information for a specific LoB or all LoBs.

	Args:
		lob_name: Specific LoB to get workload for (optional)

	Returns:
		list: Engineer workload information
	"""
	try:
		workload_data = []

		if lob_name:
			lobs_to_check = [lob_name] if frappe.db.exists("CRM Line of Business", lob_name) else []
		else:
			lobs_to_check = [
				lob.name for lob in frappe.get_all(
					"CRM Line of Business",
					filters={"is_active": 1},
					fields=["name"]
				)
			]

		for lob in lobs_to_check:
			engineers = get_engineers_for_specific_lob(lob)

			for engineer in engineers:
				user = engineer["user"]

				# Count active assignments
				active_site_visits = frappe.db.count("CRM Site Visit", {
					"service_engineer": user,
					"status": ["in", ["Planned", "In Progress"]]
				})

				# Count assignments in this LoB
				lob_site_visits = frappe.db.count("CRM Site Visit", {
					"service_engineer": user,
					"line_of_business": lob,
					"status": ["in", ["Planned", "In Progress"]]
				})

				workload_info = {
					"engineer": user,
					"engineer_name": engineer["full_name"],
					"lob": lob,
					"lob_name": engineer["lob_name"],
					"is_primary": engineer["is_primary"],
					"expertise_level": engineer["expertise_level"],
					"total_active_visits": active_site_visits,
					"lob_active_visits": lob_site_visits,
					"availability_score": calculate_availability_score(active_site_visits)
				}
				workload_data.append(workload_info)

		# Sort by availability (lower active visits = more available)
		workload_data.sort(key=lambda x: (x["total_active_visits"], not x["is_primary"]))

		return workload_data

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting engineer workload for LoB {lob_name}")
		return []


def calculate_availability_score(active_visits: int) -> str:
	"""
	Calculate engineer availability based on active site visits.

	Args:
		active_visits: Number of active site visits

	Returns:
		str: Availability score
	"""
	if active_visits == 0:
		return "Available"
	elif active_visits <= 2:
		return "Moderate"
	elif active_visits <= 5:
		return "Busy"
	else:
		return "Overloaded"