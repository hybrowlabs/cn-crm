import frappe


@frappe.whitelist()
def add_existing_users(users, role="Sales User"):
	"""
	Add existing users to the CRM by assigning them a role (Sales User, Sales Manager, or Service User).
	:param users: List of user names to be added
	"""
	frappe.only_for(["System Manager", "Sales Manager"])
	users = frappe.parse_json(users)

	for user in users:
		add_user(user, role)


@frappe.whitelist()
def update_user_role(user, new_role):
	"""
	Update the role of the user to Sales Manager, Sales User, Service User, or System Manager.
	:param user: The name of the user
	:param new_role: The new role to assign (Sales Manager, Sales User, or Service User)
	"""

	frappe.only_for(["System Manager", "Sales Manager"])

	if new_role not in ["System Manager", "Sales Manager", "Sales User", "Service User"]:
		frappe.throw("Cannot assign this role")

	user_doc = frappe.get_doc("User", user)

	if new_role == "System Manager":
		user_doc.append_roles("System Manager", "Sales Manager", "Sales User")
		user_doc.set("block_modules", [])
	if new_role == "Sales Manager":
		user_doc.append_roles("Sales Manager", "Sales User")
		user_doc.remove_roles("System Manager")
	if new_role == "Sales User":
		user_doc.append_roles("Sales User")
		user_doc.remove_roles("Sales Manager", "System Manager", "Service User")
		update_module_in_user(user_doc, "FCRM")
	if new_role == "Service User":
		user_doc.append_roles("Service User")
		user_doc.remove_roles("Sales Manager", "System Manager", "Sales User")
		update_module_in_user(user_doc, "FCRM")

	user_doc.save(ignore_permissions=True)


@frappe.whitelist()
def add_user(user, role):
	"""
	Add a user means adding role (Sales User, Sales Manager, or Service User) to the user.
	:param user: The name of the user to be added
	:param role: The role to be assigned (Sales User, Sales Manager, or Service User)
	"""
	update_user_role(user, role)


@frappe.whitelist()
def remove_user(user):
	"""
	Remove a user means removing Sales User & Sales Manager roles from the user.
	:param user: The name of the user to be removed
	"""
	frappe.only_for(["System Manager", "Sales Manager"])

	user_doc = frappe.get_doc("User", user)
	roles = [d.role for d in user_doc.roles]

	if "Sales User" in roles:
		user_doc.remove_roles("Sales User")
	if "Sales Manager" in roles:
		user_doc.remove_roles("Sales Manager")
	if "Service User" in roles:
		user_doc.remove_roles("Service User")

	user_doc.save(ignore_permissions=True)
	frappe.msgprint(f"User {user} has been removed from CRM roles.")


def update_module_in_user(user, module):
	block_modules = frappe.get_all(
		"Module Def",
		fields=["name as module"],
		filters={"name": ["!=", module]},
	)

	if block_modules:
		user.set("block_modules", block_modules)
