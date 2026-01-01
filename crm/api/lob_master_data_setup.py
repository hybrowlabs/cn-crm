import frappe
from frappe import _


@frappe.whitelist()
def setup_lob_master_data():
	"""
	Set up master data for Line of Business service teams.
	Creates the primary LoB categories and General Services fallback.
	"""
	try:
		frappe.only_for(["System Manager", "Administrator"])

		results = {
			"created": [],
			"updated": [],
			"errors": []
		}

		# Define LoB master data
		lob_data = [
			{
				"lob_code": "ALLOY",
				"lob_name": "Alloys",
				"description": "Specialized alloy manufacturing and processing services",
				"display_order": 10,
				"is_active": 1
			},
			{
				"lob_code": "PLATING",
				"lob_name": "Plating",
				"description": "Metal plating and surface treatment services",
				"display_order": 20,
				"is_active": 1
			},
			{
				"lob_code": "MACHINE",
				"lob_name": "Machines",
				"description": "Manufacturing machinery and equipment services",
				"display_order": 30,
				"is_active": 1
			},
			{
				"lob_code": "GENERAL",
				"lob_name": "General Services",
				"description": "General business services for all other lines of business",
				"display_order": 100,
				"is_active": 1
			}
		]

		print("Setting up Line of Business Master Data...")

		for lob_info in lob_data:
			try:
				# Check if LoB already exists
				existing_lob = frappe.db.exists("CRM Line of Business", lob_info["lob_code"])

				if existing_lob:
					# Update existing LoB
					lob = frappe.get_doc("CRM Line of Business", existing_lob)

					# Update fields if they've changed
					updated_fields = []
					for field, value in lob_info.items():
						if hasattr(lob, field) and getattr(lob, field) != value:
							setattr(lob, field, value)
							updated_fields.append(field)

					if updated_fields:
						lob.save()
						results["updated"].append({
							"lob": lob_info["lob_name"],
							"code": lob_info["lob_code"],
							"updated_fields": updated_fields
						})
						print(f"✅ Updated LoB: {lob_info['lob_name']} ({lob_info['lob_code']})")
					else:
						print(f"ℹ️  LoB already exists: {lob_info['lob_name']} ({lob_info['lob_code']})")

				else:
					# Create new LoB
					lob = frappe.get_doc({
						"doctype": "CRM Line of Business",
						**lob_info
					})
					lob.insert()

					results["created"].append({
						"lob": lob_info["lob_name"],
						"code": lob_info["lob_code"]
					})
					print(f"✅ Created LoB: {lob_info['lob_name']} ({lob_info['lob_code']})")

			except Exception as e:
				error_msg = f"Error processing LoB {lob_info['lob_name']}: {str(e)}"
				results["errors"].append(error_msg)
				print(f"❌ {error_msg}")
				frappe.log_error(frappe.get_traceback(), f"LoB Setup Error: {lob_info['lob_name']}")
				continue

		frappe.db.commit()

		# Summary
		print(f"\n📊 Setup Summary:")
		print(f"   Created: {len(results['created'])} LoB records")
		print(f"   Updated: {len(results['updated'])} LoB records")
		print(f"   Errors: {len(results['errors'])} errors")

		if results["errors"]:
			print(f"\n❌ Errors encountered:")
			for error in results["errors"]:
				print(f"   - {error}")

		return {
			"success": len(results["errors"]) == 0,
			"message": f"LoB setup completed. Created: {len(results['created'])}, Updated: {len(results['updated'])}, Errors: {len(results['errors'])}",
			"details": results
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "LoB Master Data Setup Error")
		return {
			"success": False,
			"message": f"LoB master data setup failed: {str(e)}",
			"error": str(e)
		}


@frappe.whitelist()
def setup_sample_service_teams():
	"""
	Set up sample service teams for demonstration.
	Creates sample engineers for each LoB category.
	"""
	try:
		frappe.only_for(["System Manager", "Administrator"])

		results = {
			"engineers_created": [],
			"teams_configured": [],
			"errors": []
		}

		# Sample service team structure
		sample_teams = {
			"ALLOY": {
				"manager_email": "alloy.manager@company.com",
				"manager_name": "Alloy Service Manager",
				"engineers": [
					{"email": "alloy.engineer1@company.com", "name": "John Alloy", "expertise": "Expert", "primary": True},
					{"email": "alloy.engineer2@company.com", "name": "Sarah Metals", "expertise": "Advanced", "primary": False}
				]
			},
			"PLATING": {
				"manager_email": "plating.manager@company.com",
				"manager_name": "Plating Service Manager",
				"engineers": [
					{"email": "plating.engineer1@company.com", "name": "Mike Coating", "expertise": "Expert", "primary": True},
					{"email": "plating.engineer2@company.com", "name": "Lisa Surface", "expertise": "Advanced", "primary": False}
				]
			},
			"MACHINE": {
				"manager_email": "machine.manager@company.com",
				"manager_name": "Machine Service Manager",
				"engineers": [
					{"email": "machine.engineer1@company.com", "name": "David Mechanical", "expertise": "Expert", "primary": True},
					{"email": "machine.engineer2@company.com", "name": "Anna Technical", "expertise": "Intermediate", "primary": False}
				]
			},
			"GENERAL": {
				"manager_email": "general.manager@company.com",
				"manager_name": "General Service Manager",
				"engineers": [
					{"email": "general.engineer1@company.com", "name": "Robert General", "expertise": "Advanced", "primary": True},
					{"email": "general.engineer2@company.com", "name": "Jennifer Support", "expertise": "Intermediate", "primary": False}
				]
			}
		}

		print("Setting up Sample Service Teams...")

		for lob_code, team_info in sample_teams.items():
			try:
				# Check if LoB exists
				if not frappe.db.exists("CRM Line of Business", lob_code):
					results["errors"].append(f"LoB {lob_code} not found. Run setup_lob_master_data first.")
					continue

				lob = frappe.get_doc("CRM Line of Business", lob_code)
				team_configured = False

				# Create and assign service manager
				manager_created = create_sample_user(
					team_info["manager_email"],
					team_info["manager_name"],
					"Sales Manager"
				)

				if manager_created:
					lob.default_service_manager = team_info["manager_email"]
					team_configured = True
					print(f"✅ Set manager for {lob.lob_name}: {team_info['manager_name']}")

				# Create and assign engineers
				for engineer_info in team_info["engineers"]:
					engineer_created = create_sample_user(
						engineer_info["email"],
						engineer_info["name"],
						"Sales User"
					)

					if engineer_created:
						# Add to service team
						engineer_exists = any(
							row.service_engineer == engineer_info["email"]
							for row in lob.service_engineers or []
						)

						if not engineer_exists:
							lob.append("service_engineers", {
								"service_engineer": engineer_info["email"],
								"is_primary": engineer_info["primary"],
								"expertise_level": engineer_info["expertise"]
							})
							team_configured = True
							print(f"✅ Added engineer to {lob.lob_name}: {engineer_info['name']}")

				# Save LoB changes
				if team_configured:
					lob.save()
					results["teams_configured"].append({
						"lob": lob.lob_name,
						"lob_code": lob_code
					})

			except Exception as e:
				error_msg = f"Error setting up team for {lob_code}: {str(e)}"
				results["errors"].append(error_msg)
				print(f"❌ {error_msg}")
				frappe.log_error(frappe.get_traceback(), f"Sample Team Setup Error: {lob_code}")
				continue

		frappe.db.commit()

		print(f"\n📊 Sample Teams Setup Summary:")
		print(f"   Teams configured: {len(results['teams_configured'])}")
		print(f"   Engineers created: {len(results['engineers_created'])}")
		print(f"   Errors: {len(results['errors'])}")

		return {
			"success": len(results["errors"]) == 0,
			"message": f"Sample teams setup completed. Teams: {len(results['teams_configured'])}, Engineers: {len(results['engineers_created'])}, Errors: {len(results['errors'])}",
			"details": results
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Sample Service Teams Setup Error")
		return {
			"success": False,
			"message": f"Sample teams setup failed: {str(e)}",
			"error": str(e)
		}


def create_sample_user(email: str, full_name: str, role: str) -> bool:
	"""
	Create a sample user if it doesn't exist.

	Args:
		email: User email
		full_name: User's full name
		role: Role to assign

	Returns:
		bool: True if user was created or already exists, False on error
	"""
	try:
		# Check if user already exists
		if frappe.db.exists("User", email):
			print(f"ℹ️  User already exists: {email}")
			return True

		# Create user
		names = full_name.split(' ', 1)
		first_name = names[0]
		last_name = names[1] if len(names) > 1 else ""

		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"full_name": full_name,
			"send_welcome_email": 0,
			"enabled": 1,
			"user_type": "System User"
		})

		# Add role
		user.append("roles", {"role": role})

		# Block non-CRM modules
		all_modules = frappe.get_all("Module Def", fields=["name"])
		for module in all_modules:
			if module.name != "FCRM":
				user.append("block_modules", {"module": module.name})

		user.insert(ignore_permissions=True)
		print(f"✅ Created user: {full_name} ({email})")
		return True

	except Exception as e:
		print(f"❌ Error creating user {email}: {str(e)}")
		frappe.log_error(frappe.get_traceback(), f"User Creation Error: {email}")
		return False


@frappe.whitelist()
def cleanup_sample_data():
	"""
	Clean up sample service teams and users (for testing purposes).
	"""
	try:
		frappe.only_for(["System Manager", "Administrator"])

		# Sample user emails to clean up
		sample_emails = [
			"alloy.manager@company.com", "alloy.engineer1@company.com", "alloy.engineer2@company.com",
			"plating.manager@company.com", "plating.engineer1@company.com", "plating.engineer2@company.com",
			"machine.manager@company.com", "machine.engineer1@company.com", "machine.engineer2@company.com",
			"general.manager@company.com", "general.engineer1@company.com", "general.engineer2@company.com"
		]

		deleted_count = 0

		# Delete sample users
		for email in sample_emails:
			if frappe.db.exists("User", email):
				try:
					frappe.delete_doc("User", email, ignore_permissions=True)
					deleted_count += 1
					print(f"✅ Deleted user: {email}")
				except Exception as e:
					print(f"❌ Error deleting user {email}: {str(e)}")

		# Clear service teams from LoB records
		lob_codes = ["ALLOY", "PLATING", "MACHINE", "GENERAL"]
		cleared_count = 0

		for lob_code in lob_codes:
			if frappe.db.exists("CRM Line of Business", lob_code):
				try:
					lob = frappe.get_doc("CRM Line of Business", lob_code)
					lob.default_service_manager = ""
					lob.service_engineers = []
					lob.save()
					cleared_count += 1
					print(f"✅ Cleared service team for: {lob.lob_name}")
				except Exception as e:
					print(f"❌ Error clearing team for {lob_code}: {str(e)}")

		frappe.db.commit()

		return {
			"success": True,
			"message": f"Cleanup completed. Deleted {deleted_count} users, cleared {cleared_count} service teams",
			"deleted_users": deleted_count,
			"cleared_teams": cleared_count
		}

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Sample Data Cleanup Error")
		return {
			"success": False,
			"message": f"Cleanup failed: {str(e)}",
			"error": str(e)
		}


@frappe.whitelist()
def verify_lob_setup():
	"""
	Verify that LoB master data and service teams are properly configured.
	"""
	try:
		verification_results = {
			"lob_records": [],
			"service_teams": [],
			"issues": [],
			"summary": {}
		}

		# Check LoB records
		expected_lobs = ["ALLOY", "PLATING", "MACHINE", "GENERAL"]

		for lob_code in expected_lobs:
			if frappe.db.exists("CRM Line of Business", lob_code):
				lob = frappe.get_doc("CRM Line of Business", lob_code)

				lob_info = {
					"code": lob_code,
					"name": lob.lob_name,
					"is_active": lob.is_active,
					"has_manager": bool(lob.default_service_manager),
					"engineer_count": len(lob.service_engineers or []),
					"status": "✅ OK"
				}

				# Check for issues
				issues = []
				if not lob.is_active:
					issues.append("LoB is inactive")
				if not lob.default_service_manager:
					issues.append("No service manager assigned")
				if len(lob.service_engineers or []) == 0:
					issues.append("No engineers assigned")

				if issues:
					lob_info["status"] = "⚠️ Issues found"
					lob_info["issues"] = issues
					verification_results["issues"].extend([f"{lob_code}: {issue}" for issue in issues])

				verification_results["lob_records"].append(lob_info)
			else:
				verification_results["issues"].append(f"Missing LoB: {lob_code}")
				verification_results["lob_records"].append({
					"code": lob_code,
					"status": "❌ Missing"
				})

		# Generate summary
		verification_results["summary"] = {
			"total_lobs": len(expected_lobs),
			"configured_lobs": len([r for r in verification_results["lob_records"] if "name" in r]),
			"total_issues": len(verification_results["issues"]),
			"setup_complete": len(verification_results["issues"]) == 0
		}

		return {
			"success": True,
			"verification": verification_results
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "LoB Setup Verification Error")
		return {
			"success": False,
			"error": str(e)
		}