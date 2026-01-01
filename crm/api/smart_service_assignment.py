import frappe
from frappe import _
from typing import Dict, List, Optional


# Primary LoB categories that have dedicated service teams
PRIMARY_LOBS = ["Alloys", "Plating", "Machines"]
FALLBACK_LOB = "GENERAL"


@frappe.whitelist()
def assign_service_team(lob_name: str, priority: str = "Normal") -> Dict:
	"""
	Smart service team assignment based on Line of Business.

	Routes to specific service teams for Alloys, Plating, and Machines.
	Falls back to General Services team for other LoB values.

	Args:
		lob_name (str): Line of Business name
		priority (str): Priority level for assignment preference

	Returns:
		dict: Service team assignment details
	"""
	if not lob_name:
		return get_fallback_service_team("No LoB specified")

	try:
		# Check if LoB exists in the system
		lob_doc = frappe.get_doc("CRM Line of Business", lob_name)

		if not lob_doc.is_active:
			frappe.log_error(f"Inactive LoB {lob_name} used for service assignment")
			return get_fallback_service_team(f"LoB {lob_name} is inactive")

		# Check if this is a primary LoB with dedicated team
		if lob_doc.lob_name in PRIMARY_LOBS or lob_doc.lob_code in PRIMARY_LOBS:
			return get_primary_service_team(lob_doc, priority)
		else:
			# Route to General Services for other business lines
			return get_fallback_service_team(f"Non-primary LoB: {lob_name}")

	except frappe.DoesNotExistError:
		frappe.log_error(f"LoB {lob_name} not found in system")
		return get_fallback_service_team(f"LoB {lob_name} not found")
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Service Assignment Error")
		return get_fallback_service_team(f"Error processing LoB {lob_name}: {str(e)}")


def get_primary_service_team(lob_doc, priority: str = "Normal") -> Dict:
	"""
	Get service team for primary LoB (Alloys, Plating, Machines).

	Args:
		lob_doc: CRM Line of Business document
		priority: Assignment priority

	Returns:
		dict: Service team details with manager and engineers
	"""
	try:
		service_team = {
			"success": True,
			"lob": lob_doc.name,
			"lob_name": lob_doc.lob_name,
			"team_type": "Primary",
			"service_manager": lob_doc.default_service_manager,
			"service_engineers": [],
			"assignment_notes": f"Assigned to {lob_doc.lob_name} specialized team"
		}

		# Get service engineers for this LoB
		engineers = get_available_engineers(lob_doc, priority)
		service_team["service_engineers"] = engineers

		# Select primary engineer if available
		primary_engineer = get_primary_engineer(engineers)
		service_team["assigned_engineer"] = primary_engineer

		if not primary_engineer:
			service_team["assignment_notes"] += " (No engineers available - may need manual assignment)"

		return service_team

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting primary service team for {lob_doc.name}")
		return get_fallback_service_team(f"Error with {lob_doc.lob_name} team: {str(e)}")


def get_fallback_service_team(reason: str = "") -> Dict:
	"""
	Get General Services team as fallback for non-primary LoB or errors.

	Args:
		reason: Reason for fallback assignment

	Returns:
		dict: General Services team details
	"""
	try:
		# Try to get General Services LoB
		general_lob = frappe.get_doc("CRM Line of Business", FALLBACK_LOB)

		if not general_lob.is_active:
			# If General Services is inactive, return minimal team info
			return {
				"success": False,
				"lob": FALLBACK_LOB,
				"lob_name": "General Services",
				"team_type": "Fallback",
				"service_manager": None,
				"assigned_engineer": None,
				"service_engineers": [],
				"assignment_notes": f"Fallback assignment failed: General Services LoB inactive. Reason: {reason}",
				"error": "General Services team unavailable"
			}

		service_team = {
			"success": True,
			"lob": general_lob.name,
			"lob_name": general_lob.lob_name,
			"team_type": "Fallback",
			"service_manager": general_lob.default_service_manager,
			"service_engineers": [],
			"assignment_notes": f"Assigned to General Services team. Reason: {reason}"
		}

		# Get available general service engineers
		engineers = get_available_engineers(general_lob, "Normal")
		service_team["service_engineers"] = engineers

		# Assign primary engineer
		primary_engineer = get_primary_engineer(engineers)
		service_team["assigned_engineer"] = primary_engineer

		return service_team

	except frappe.DoesNotExistError:
		# General Services LoB doesn't exist - return minimal info
		return {
			"success": False,
			"lob": None,
			"lob_name": "General Services",
			"team_type": "Fallback",
			"service_manager": None,
			"assigned_engineer": None,
			"service_engineers": [],
			"assignment_notes": f"No General Services team configured. Reason: {reason}",
			"error": "Fallback team not configured"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Error getting fallback service team")
		return {
			"success": False,
			"lob": None,
			"lob_name": "General Services",
			"team_type": "Fallback",
			"service_manager": None,
			"assigned_engineer": None,
			"service_engineers": [],
			"assignment_notes": f"Error getting fallback team: {str(e)}. Reason: {reason}",
			"error": str(e)
		}


def get_available_engineers(lob_doc, priority: str = "Normal") -> List[Dict]:
	"""
	Get list of available service engineers for a LoB.

	Args:
		lob_doc: CRM Line of Business document
		priority: Priority for engineer selection

	Returns:
		list: Available engineers with details
	"""
	if not lob_doc.service_engineers:
		return []

	engineers = []
	for engineer_row in lob_doc.service_engineers:
		if not engineer_row.service_engineer:
			continue

		# Check if user is active
		user_enabled = frappe.db.get_value("User", engineer_row.service_engineer, "enabled")
		if not user_enabled:
			continue

		engineer_info = {
			"user": engineer_row.service_engineer,
			"is_primary": engineer_row.is_primary,
			"expertise_level": engineer_row.expertise_level or "Intermediate",
			"name": frappe.db.get_value("User", engineer_row.service_engineer, "full_name") or engineer_row.service_engineer
		}
		engineers.append(engineer_info)

	# Sort by priority: Primary engineers first, then by expertise level
	engineers.sort(key=lambda x: (
		not x["is_primary"],  # Primary engineers first
		{"Expert": 0, "Advanced": 1, "Intermediate": 2, "Beginner": 3}.get(x["expertise_level"], 2)
	))

	return engineers


def get_primary_engineer(engineers: List[Dict]) -> Optional[str]:
	"""
	Select the best available engineer from the list.

	Args:
		engineers: List of available engineers

	Returns:
		str: Selected engineer's user ID, or None if none available
	"""
	if not engineers:
		return None

	# Return the first engineer (already sorted by priority)
	return engineers[0]["user"]


@frappe.whitelist()
def get_service_team_for_lead(lead_name: str) -> Dict:
	"""
	Get appropriate service team for a lead based on its LoB.

	Args:
		lead_name: Name of the CRM Lead

	Returns:
		dict: Service team assignment details
	"""
	try:
		lead = frappe.get_doc("CRM Lead", lead_name)
		return assign_service_team(lead.line_of_business, "Normal")
	except frappe.DoesNotExistError:
		return {
			"success": False,
			"error": f"Lead {lead_name} not found"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting service team for lead {lead_name}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def get_service_team_for_deal(deal_name: str) -> Dict:
	"""
	Get appropriate service team for a deal based on its LoB.

	Args:
		deal_name: Name of the CRM Deal

	Returns:
		dict: Service team assignment details
	"""
	try:
		deal = frappe.get_doc("CRM Deal", deal_name)
		return assign_service_team(deal.line_of_business, "High")  # Deals get higher priority
	except frappe.DoesNotExistError:
		return {
			"success": False,
			"error": f"Deal {deal_name} not found"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting service team for deal {deal_name}")
		return {
			"success": False,
			"error": str(e)
		}


@frappe.whitelist()
def auto_assign_service_engineer(site_visit_name: str) -> Dict:
	"""
	Automatically assign service engineer to a site visit based on LoB.

	Args:
		site_visit_name: Name of the CRM Site Visit

	Returns:
		dict: Assignment result
	"""
	try:
		site_visit = frappe.get_doc("CRM Site Visit", site_visit_name)

		if not site_visit.line_of_business:
			return {
				"success": False,
				"message": "No Line of Business specified for this site visit"
			}

		# Get service team assignment
		team_assignment = assign_service_team(site_visit.line_of_business, "High")

		if not team_assignment.get("success"):
			return {
				"success": False,
				"message": f"Could not assign service team: {team_assignment.get('error', 'Unknown error')}"
			}

		# Update site visit with assigned engineer
		assigned_engineer = team_assignment.get("assigned_engineer")
		if assigned_engineer:
			site_visit.service_engineer = assigned_engineer
			site_visit.save()

			return {
				"success": True,
				"assigned_engineer": assigned_engineer,
				"engineer_name": frappe.db.get_value("User", assigned_engineer, "full_name"),
				"team_type": team_assignment.get("team_type"),
				"lob": team_assignment.get("lob_name"),
				"message": f"Service engineer assigned successfully"
			}
		else:
			return {
				"success": False,
				"message": f"No engineers available for {team_assignment.get('lob_name')} service team"
			}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error auto-assigning engineer to site visit {site_visit_name}")
		return {
			"success": False,
			"message": f"Error: {str(e)}"
		}


@frappe.whitelist()
def get_lob_engineers(lob_name: str) -> List[Dict]:
	"""
	Get list of engineers for a specific LoB (for dropdowns/selection).

	Args:
		lob_name: Name of the Line of Business

	Returns:
		list: Engineers available for the LoB
	"""
	if not lob_name:
		return []

	try:
		team_assignment = assign_service_team(lob_name)
		if team_assignment.get("success"):
			return team_assignment.get("service_engineers", [])
		else:
			# Return empty list for invalid LoB
			return []
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), f"Error getting engineers for LoB {lob_name}")
		return []