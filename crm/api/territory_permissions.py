import frappe
from frappe import _


def get_lead_permission_query_conditions(user=None):
	return get_permission_query_conditions("CRM Lead", user)


def get_deal_permission_query_conditions(user=None):
	return get_permission_query_conditions("CRM Deal", user)


def get_permission_query_conditions(doctype, user=None):
	"""
	Returns permission query conditions for CRM Lead and CRM Deal based on territory access.

	Users can access records where:
	1. They are owner or assigned owner (lead_owner for Lead, deal_owner for Deal)
	2. They are territory manager of the record's territory
	3. They have User Permission for the record's territory
	4. They have Sales Manager or System Manager role (broader access)
	"""
	if not user:
		user = frappe.session.user

	# System Managers and Administrators get full access
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""

	# Get user territories (where user is territory manager)
	user_territories = get_user_territories(user)

	# Base conditions: owner
	conditions = [f"owner = '{user}'"]

	# Check for assignment field based on doctype
	if doctype == "CRM Lead":
		conditions.append(f"lead_owner = '{user}'")
	elif doctype == "CRM Deal":
		conditions.append(f"deal_owner = '{user}'")

	# Check for explicitly assigned users via _assign
	conditions.append(f"_assign LIKE '%\"{user}\"%'")

	if user_territories:
		territory_list = "', '".join(user_territories)
		conditions.append(f"territory in ('{territory_list}')")

	return "(" + " OR ".join(conditions) + ")"


def has_permission(doc, ptype=None, user=None):
	"""
	Check if user has permission for a specific document based on territory.

	Args:
		doc: The document to check permission for
		ptype: Permission type (read, write, etc.) - required by Frappe hook signature
		user: The user to check permission for (defaults to current user)
	"""
	if not user:
		user = frappe.session.user

	# System Managers and Administrators get full access
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True

	# Ownership check (owner, lead_owner or deal_owner)
	if (doc.owner == user or
		getattr(doc, 'lead_owner', None) == user or
		getattr(doc, 'deal_owner', None) == user):
		return True

	# Explicitly Assigned check
	_assign = getattr(doc, '_assign', None)
	if _assign:
		try:
			import json
			assign_list = json.loads(_assign)
			if user in assign_list:
				return True
		except Exception:
			# Handle any JSON parsing errors gracefully
			pass

	# Check if document has territory field
	if not hasattr(doc, 'territory') or not doc.territory:
		# If no territory is set, check if user has general access
		return has_general_crm_access(user)

	# Check if user has access to this territory
	user_territories = get_user_territories(user)

	return doc.territory in user_territories


def get_user_territories(user=None):
	"""
	Get list of territories that a user has access to.
	This includes:
	1. Territories where user is territory_manager
	2. Territories granted via User Permission
	"""
	if not user:
		user = frappe.session.user

	territories = []

	# Get territories where user is territory manager
	territory_manager_territories = frappe.get_all(
		"Territory",
		filters={"territory_manager": user},
		fields=["name"]
	)

	for territory in territory_manager_territories:
		territories.append(territory.name)

	# Get territories from User Permissions
	user_permission_territories = frappe.get_all(
		"User Permission",
		filters={
			"user": user,
			"allow": "Territory",
			"for_value": ["is", "set"]
		},
		fields=["for_value"]
	)

	for perm in user_permission_territories:
		if perm.for_value not in territories:
			territories.append(perm.for_value)

	# Sales Managers get broader access - include child territories
	if "Sales Manager" in frappe.get_roles(user):
		extended_territories = []
		for territory in territories:
			# Get child territories using nested set
			child_territories = frappe.get_all(
				"Territory",
				filters={
					"lft": [">=", frappe.db.get_value("Territory", territory, "lft")],
					"rgt": ["<=", frappe.db.get_value("Territory", territory, "rgt")]
				},
				fields=["name"]
			)

			for child in child_territories:
				if child.name not in extended_territories:
					extended_territories.append(child.name)

		territories.extend(extended_territories)
		territories = list(set(territories))  # Remove duplicates

	return territories


def has_general_crm_access(user=None):
	"""
	Check if user has general CRM access (Sales User, Sales Manager roles).
	"""
	if not user:
		user = frappe.session.user

	user_roles = frappe.get_roles(user)
	crm_roles = ["Sales User", "Sales Manager", "System Manager"]

	return any(role in user_roles for role in crm_roles)


def assign_user_to_territory(user, territory):
	"""
	Assign a user to a territory by creating User Permission.
	"""
	# Check if permission already exists
	existing = frappe.db.exists("User Permission", {
		"user": user,
		"allow": "Territory",
		"for_value": territory
	})

	if existing:
		return existing

	# Create new User Permission
	user_permission = frappe.get_doc({
		"doctype": "User Permission",
		"user": user,
		"allow": "Territory",
		"for_value": territory,
		"applicable_for": "CRM Lead,CRM Deal"
	})

	user_permission.insert(ignore_permissions=True)
	return user_permission.name


def remove_user_from_territory(user, territory):
	"""
	Remove user from territory by deleting User Permission.
	"""
	existing = frappe.db.exists("User Permission", {
		"user": user,
		"allow": "Territory",
		"for_value": territory
	})

	if existing:
		frappe.delete_doc("User Permission", existing, ignore_permissions=True)
		return True

	return False


@frappe.whitelist()
def get_user_territory_access(user=None):
	"""
	API endpoint to get territory access for a user.
	"""
	if not user:
		user = frappe.session.user

	territories = get_user_territories(user)

	# Get territory details
	territory_details = []
	for territory in territories:
		territory_doc = frappe.get_doc("Territory", territory)
		territory_details.append({
			"name": territory_doc.name,
			"territory_name": territory_doc.territory_name,
			"is_manager": territory_doc.territory_manager == user,
			"parent_crm_territory": territory_doc.parent_crm_territory
		})

	return {
		"territories": territory_details,
		"total_count": len(territories)
	}


def get_task_permission_conditions(user=None):
	"""
	Returns permission query conditions for CRM Task.
	Users can see tasks if:
	1. Assigned to them
	2. Created by them (owner)
	3. Related to a Lead/Deal in their territory (for Managers)
	"""
	if not user:
		user = frappe.session.user

	# System Managers and Administrators get full access
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return ""

	user_territories = get_user_territories(user)

	# Base condition: Assigned to or Owned by user
	conditions = [f"(assigned_to = '{user}' OR owner = '{user}')"]

	if user_territories:
		territory_list = "', '".join(user_territories)

		# Add conditions for Leads/Deals in accessible territories
		conditions.append(f"""(
			reference_doctype = 'CRM Lead'
			AND reference_docname IN (SELECT name FROM `tabCRM Lead` WHERE territory IN ('{territory_list}'))
		)""")

		conditions.append(f"""(
			reference_doctype = 'CRM Deal'
			AND reference_docname IN (SELECT name FROM `tabCRM Deal` WHERE territory IN ('{territory_list}'))
		)""")

	return "(" + " OR ".join(conditions) + ")"


def has_task_permission(doc, ptype=None, user=None):
	"""
	Checks if user has permission to access a specific CRM Task.
	"""
	if not user:
		user = frappe.session.user

	# System Managers and Administrators get full access
	if user == "Administrator" or "System Manager" in frappe.get_roles(user):
		return True

	# Base access: Assigned to or Owned by user
	if doc.assigned_to == user or doc.owner == user:
		return True

	# Territory-based access via reference Lead/Deal
	if doc.reference_doctype in ["CRM Lead", "CRM Deal"] and doc.reference_docname:
		try:
			ref_doc = frappe.get_cached_doc(doc.reference_doctype, doc.reference_docname)
			return has_permission(ref_doc, ptype, user)
		except frappe.DoesNotExistError:
			return False

	return False


@frappe.whitelist()
def validate_territory_access(doctype, name, user=None):
	"""
	API endpoint to validate if user has access to a specific record.
	"""
	if not user:
		user = frappe.session.user

	try:
		doc = frappe.get_doc(doctype, name)
		has_access = has_permission(doc, user)

		return {
			"has_access": has_access,
			"territory": getattr(doc, 'territory', None),
			"user_territories": get_user_territories(user)
		}

	except frappe.DoesNotExistError:
		return {
			"has_access": False,
			"error": "Document not found"
		}