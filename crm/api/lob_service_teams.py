import frappe
from frappe import _
from typing import Dict, List, Optional


@frappe.whitelist()
def get_all_service_teams() -> List[Dict]:
	"""
	Get all configured service teams with their details.

	Returns:
		list: All service teams with team information
	"""
	try:
		lobs = frappe.get_all(
			"CRM Line of Business",
			filters={"is_active": 1},
			fields=["name", "lob_code", "lob_name", "default_service_manager", "display_order"],
			order_by="display_order asc, lob_name asc"
		)

		service_teams = []
		for lob in lobs:
			team_info = {
				"lob": lob.name,
				"lob_code": lob.lob_code,
				"lob_name": lob.lob_name,
				"service_manager": lob.default_service_manager,
				"service_manager_name": "",
				"engineers": [],
				"engineer_count": 0,
				"team_type": "Primary" if lob.lob_name in ["Alloys", "Plating", "Machines"] else "General"
			}

			# Get service manager name
			if lob.default_service_manager:
				team_info["service_manager_name"] = frappe.db.get_value(
					"User", lob.default_service_manager, "full_name"
				) or lob.default_service_manager

			# Get engineers for this LoB
			engineers = get_lob_engineers_detailed(lob.name)
			team_info["engineers"] = engineers
			team_info["engineer_count"] = len(engineers)

			service_teams.append(team_info)

		return service_teams

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error getting all service teams")
		return []


@frappe.whitelist()
def get_lob_engineers_detailed(lob_name: str) -> List[Dict]:
	"""
	Get detailed information about engineers for a specific LoB.

	Args:
		lob_name: Name of the Line of Business

	Returns:
		list: Detailed engineer information
	"""
	if not lob_name:
		return []

	try:
		lob = frappe.get_doc("CRM Line of Business", lob_name)
		engineers = []

		for engineer_row in lob.service_engineers or []:
			if not engineer_row.service_engineer:
				continue

			# Get user details
			user_doc = frappe.get_doc("User", engineer_row.service_engineer)

			engineer_info = {
				"user": engineer_row.service_engineer,
				"full_name": user_doc.full_name or engineer_row.service_engineer,
				"first_name": user_doc.first_name,
				"last_name": user_doc.last_name,
				"email": user_doc.email,
				"is_primary": engineer_row.is_primary,
				"expertise_level": engineer_row.expertise_level or "Intermediate",
				"enabled": user_doc.enabled,
				"last_login": user_doc.last_login,
				"user_image": user_doc.user_image,
				"roles": [d.role for d in user_doc.roles]
			}
			engineers.append(engineer_info)

		# Sort by primary status and expertise
		engineers.sort(key=lambda x: (
			not x["is_primary"],
			{"Expert": 0, "Advanced": 1, "Intermediate": 2, "Beginner": 3}.get(x["expertise_level"], 2),
			x["full_name"]
		))

		return engineers

	except frappe.DoesNotExistError:
		return []
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting engineers for LoB {lob_name}")
		return []


@frappe.whitelist()
def add_engineer_to_lob(lob_name: str, engineer_user: str, is_primary: bool = False, expertise_level: str = "Intermediate") -> Dict:
	"""
	Add an engineer to a LoB service team.

	Args:
		lob_name: Name of the Line of Business
		engineer_user: User ID of the engineer
		is_primary: Whether this is a primary engineer
		expertise_level: Engineer's expertise level

	Returns:
		dict: Operation result
	"""
	try:
		frappe.only_for(["System Manager", "Sales Manager"])

		# Validate LoB exists
		if not frappe.db.exists("CRM Line of Business", lob_name):
			return {
				"success": False,
				"message": f"Line of Business '{lob_name}' not found"
			}

		# Validate user exists and is active
		if not frappe.db.exists("User", engineer_user):
			return {
				"success": False,
				"message": f"User '{engineer_user}' not found"
			}

		user_enabled = frappe.db.get_value("User", engineer_user, "enabled")
		if not user_enabled:
			return {
				"success": False,
				"message": f"User '{engineer_user}' is not active"
			}

		# Get LoB document
		lob = frappe.get_doc("CRM Line of Business", lob_name)

		# Check if engineer is already in the team
		for engineer_row in lob.service_engineers or []:
			if engineer_row.service_engineer == engineer_user:
				return {
					"success": False,
					"message": f"Engineer {engineer_user} is already in {lob_name} service team"
				}

		# Add engineer to team
		lob.append("service_engineers", {
			"service_engineer": engineer_user,
			"is_primary": is_primary,
			"expertise_level": expertise_level
		})

		lob.save()

		engineer_name = frappe.db.get_value("User", engineer_user, "full_name") or engineer_user

		return {
			"success": True,
			"message": f"Engineer {engineer_name} added to {lob.lob_name} service team"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error adding engineer {engineer_user} to LoB {lob_name}")
		return {
			"success": False,
			"message": f"Error: {str(e)}"
		}


@frappe.whitelist()
def remove_engineer_from_lob(lob_name: str, engineer_user: str) -> Dict:
	"""
	Remove an engineer from a LoB service team.

	Args:
		lob_name: Name of the Line of Business
		engineer_user: User ID of the engineer to remove

	Returns:
		dict: Operation result
	"""
	try:
		frappe.only_for(["System Manager", "Sales Manager"])

		# Get LoB document
		lob = frappe.get_doc("CRM Line of Business", lob_name)

		# Find and remove engineer
		engineer_removed = False
		for i, engineer_row in enumerate(lob.service_engineers or []):
			if engineer_row.service_engineer == engineer_user:
				lob.service_engineers.pop(i)
				engineer_removed = True
				break

		if not engineer_removed:
			return {
				"success": False,
				"message": f"Engineer {engineer_user} not found in {lob_name} service team"
			}

		lob.save()

		engineer_name = frappe.db.get_value("User", engineer_user, "full_name") or engineer_user

		return {
			"success": True,
			"message": f"Engineer {engineer_name} removed from {lob.lob_name} service team"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error removing engineer {engineer_user} from LoB {lob_name}")
		return {
			"success": False,
			"message": f"Error: {str(e)}"
		}


@frappe.whitelist()
def update_engineer_in_lob(lob_name: str, engineer_user: str, is_primary: bool = None, expertise_level: str = None) -> Dict:
	"""
	Update an engineer's details in a LoB service team.

	Args:
		lob_name: Name of the Line of Business
		engineer_user: User ID of the engineer
		is_primary: Whether this is a primary engineer (optional)
		expertise_level: Engineer's expertise level (optional)

	Returns:
		dict: Operation result
	"""
	try:
		frappe.only_for(["System Manager", "Sales Manager"])

		# Get LoB document
		lob = frappe.get_doc("CRM Line of Business", lob_name)

		# Find and update engineer
		engineer_found = False
		for engineer_row in lob.service_engineers or []:
			if engineer_row.service_engineer == engineer_user:
				if is_primary is not None:
					engineer_row.is_primary = is_primary
				if expertise_level is not None:
					engineer_row.expertise_level = expertise_level
				engineer_found = True
				break

		if not engineer_found:
			return {
				"success": False,
				"message": f"Engineer {engineer_user} not found in {lob_name} service team"
			}

		lob.save()

		engineer_name = frappe.db.get_value("User", engineer_user, "full_name") or engineer_user

		return {
			"success": True,
			"message": f"Engineer {engineer_name} updated in {lob.lob_name} service team"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error updating engineer {engineer_user} in LoB {lob_name}")
		return {
			"success": False,
			"message": f"Error: {str(e)}"
		}


@frappe.whitelist()
def get_available_engineers_for_lob(lob_name: str) -> List[Dict]:
	"""
	Get list of available users who can be assigned as engineers for a LoB.

	Args:
		lob_name: Name of the Line of Business

	Returns:
		list: Available users who are not yet in the service team
	"""
	try:
		# Get all active users with appropriate roles
		users = frappe.get_all(
			"User",
			filters={
				"enabled": 1,
				"user_type": "System User",
				"name": ["not in", ["Administrator", "Guest"]]
			},
			fields=["name", "email", "first_name", "last_name", "full_name"]
		)

		# Get current engineers in this LoB
		current_engineers = []
		if frappe.db.exists("CRM Line of Business", lob_name):
			lob = frappe.get_doc("CRM Line of Business", lob_name)
			current_engineers = [row.service_engineer for row in lob.service_engineers or []]

		# Filter out current engineers
		available_users = []
		for user in users:
			if user.name not in current_engineers:
				# Check if user has relevant roles
				user_roles = frappe.get_roles(user.name)
				if any(role in user_roles for role in ["Sales User", "Sales Manager", "Service User"]):
					available_users.append({
						"user": user.name,
						"full_name": user.full_name or user.name,
						"email": user.email,
						"first_name": user.first_name,
						"last_name": user.last_name
					})

		return available_users

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting available engineers for LoB {lob_name}")
		return []


@frappe.whitelist()
def get_service_workload_summary() -> List[Dict]:
	"""
	Get service workload summary for all teams.

	Returns:
		list: Workload summary by service team
	"""
	try:
		teams = get_all_service_teams()
		workload_summary = []

		for team in teams:
			lob_name = team["lob"]

			# Count active site visits for this LoB
			active_visits = frappe.db.count("CRM Site Visit", {
				"line_of_business": lob_name,
				"status": ["in", ["Planned", "In Progress"]]
			})

			# Count pending leads/deals for this LoB
			pending_leads = frappe.db.count("CRM Lead", {
				"line_of_business": lob_name,
				"status": ["!=", "Converted"]
			})

			pending_deals = frappe.db.count("CRM Deal", {
				"line_of_business": lob_name,
				"status": ["not in", ["Won", "Lost"]]
			})

			workload_info = {
				"lob": lob_name,
				"lob_name": team["lob_name"],
				"team_type": team["team_type"],
				"engineer_count": team["engineer_count"],
				"service_manager": team["service_manager_name"],
				"active_visits": active_visits,
				"pending_leads": pending_leads,
				"pending_deals": pending_deals,
				"total_workload": active_visits + pending_leads + pending_deals,
				"workload_per_engineer": round((active_visits + pending_leads + pending_deals) / max(team["engineer_count"], 1), 1)
			}

			workload_summary.append(workload_info)

		# Sort by workload
		workload_summary.sort(key=lambda x: x["total_workload"], reverse=True)

		return workload_summary

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error getting service workload summary")
		return []


@frappe.whitelist()
def set_service_manager(lob_name: str, manager_user: str) -> Dict:
	"""
	Set or update the service manager for a LoB.

	Args:
		lob_name: Name of the Line of Business
		manager_user: User ID of the service manager

	Returns:
		dict: Operation result
	"""
	try:
		frappe.only_for(["System Manager", "Sales Manager"])

		# Validate user exists and is active
		if not frappe.db.exists("User", manager_user):
			return {
				"success": False,
				"message": f"User '{manager_user}' not found"
			}

		user_enabled = frappe.db.get_value("User", manager_user, "enabled")
		if not user_enabled:
			return {
				"success": False,
				"message": f"User '{manager_user}' is not active"
			}

		# Update LoB with new service manager
		lob = frappe.get_doc("CRM Line of Business", lob_name)
		old_manager = lob.default_service_manager
		lob.default_service_manager = manager_user
		lob.save()

		manager_name = frappe.db.get_value("User", manager_user, "full_name") or manager_user
		old_manager_name = frappe.db.get_value("User", old_manager, "full_name") if old_manager else "None"

		return {
			"success": True,
			"message": f"Service manager for {lob.lob_name} changed from {old_manager_name} to {manager_name}"
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error setting service manager for LoB {lob_name}")
		return {
			"success": False,
			"message": f"Error: {str(e)}"
		}