import frappe
from frappe import _
from frappe.auth import LoginManager
import random
from datetime import datetime, timedelta


@frappe.whitelist(allow_guest=True)
def login():
	if not frappe.conf.demo_username or not frappe.conf.demo_password:
		return
	frappe.local.response["redirect_to"] = "/crm"
	login_manager = LoginManager()
	login_manager.authenticate(frappe.conf.demo_username, frappe.conf.demo_password)
	login_manager.post_login()
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = frappe.local.response["redirect_to"]


def validate_reset_password(doc, event):
	if frappe.conf.demo_username and frappe.session.user == frappe.conf.demo_username:
		frappe.throw(
			_("Password cannot be reset by Demo User {}").format(frappe.bold(frappe.conf.demo_username)),
			frappe.PermissionError,
		)


def validate_user(doc, event):
	if frappe.conf.demo_username and frappe.session.user == frappe.conf.demo_username and doc.new_password:
		frappe.throw(
			_("Password cannot be reset by Demo User {}").format(frappe.bold(frappe.conf.demo_username)),
			frappe.PermissionError,
		)


@frappe.whitelist()
def create_sample_leads(count=15):
	"""
	Create sample lead data for CRM demonstration
	
	Args:
		count: Number of sample leads to create (default: 15)
	
	Returns:
		dict: Response with created leads information
	"""
	try:
		if not frappe.has_permission("CRM Lead", "create"):
			frappe.throw(_("Insufficient permissions to create leads"), frappe.PermissionError)
		
		count = int(count) if count else 15
		if count > 50:
			frappe.throw(_("Cannot create more than 50 sample leads at once"))
		
		# Sample data for lead generation
		sample_data = get_sample_lead_data()
		
		created_leads = []
		failed_leads = []
		
		for i in range(count):
			try:
				lead_data = generate_random_lead_data(sample_data, i)
				
				# Check if lead with same email already exists
				if lead_data.get("email") and frappe.db.exists("CRM Lead", {"email": lead_data["email"]}):
					lead_data["email"] = f"demo{i}_{lead_data['email']}"
				
				# Create the lead document
				lead_doc = frappe.get_doc({
					"doctype": "CRM Lead",
					**lead_data
				})
				
				lead_doc.insert(ignore_permissions=True)
				created_leads.append({
					"name": lead_doc.name,
					"lead_name": lead_doc.lead_name,
					"email": lead_doc.email,
					"organization": lead_doc.organization
				})
				
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), f"Sample Lead Creation Error {i}")
				failed_leads.append({
					"index": i,
					"error": str(e)
				})
				continue
		
		frappe.db.commit()
		
		return {
			"success": True,
			"message": _("Successfully created {0} sample leads").format(len(created_leads)),
			"data": {
				"created": len(created_leads),
				"failed": len(failed_leads),
				"leads": created_leads,
				"errors": failed_leads if failed_leads else None
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Sample Lead Creation Error")
		return {
			"success": False,
			"error": str(e),
			"message": _("Failed to create sample leads")
		}


def get_sample_lead_data():
	"""Get sample data for lead generation"""
	
	# Get available statuses, sources, industries, territories from database
	lead_statuses = frappe.get_all("CRM Lead Status", pluck="lead_status") or ["New", "Contacted", "Nurture"]
	lead_sources = frappe.get_all("CRM Lead Source", pluck="source_name") or ["Website", "Referral", "Cold Call"]
	industries = frappe.get_all("CRM Industry", pluck="industry") or ["Technology", "Healthcare", "Finance"]
	territories = frappe.get_all("Territory", pluck="territory_name") or []
	users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name") or ["Administrator"]
	
	return {
		"first_names": [
			"John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Lisa", 
			"James", "Maria", "William", "Jennifer", "Richard", "Patricia", "Charles",
			"Linda", "Thomas", "Elizabeth", "Christopher", "Barbara", "Daniel", "Susan",
			"Matthew", "Jessica", "Anthony", "Karen", "Mark", "Nancy", "Donald", "Helen"
		],
		"last_names": [
			"Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
			"Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
			"Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
			"White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"
		],
		"organizations": [
			"Tech Solutions Inc", "Global Healthcare Systems", "Financial Advisors Ltd", 
			"Manufacturing Corp", "Retail Dynamics", "Education Partners", "Construction Group",
			"Marketing Agency Pro", "Software Development Co", "Consulting Experts",
			"Real Estate Holdings", "Food & Beverage Inc", "Transportation Solutions",
			"Energy Systems Ltd", "Media Productions", "Legal Services Group",
			"Insurance Partners", "Automotive Solutions", "Pharmaceutical Research",
			"Telecommunications Corp", "Banking Solutions", "Entertainment Group"
		],
		"job_titles": [
			"CEO", "CTO", "CFO", "VP Sales", "VP Marketing", "Director of Operations",
			"Sales Manager", "Marketing Manager", "Product Manager", "Project Manager",
			"Business Development Manager", "Account Manager", "Operations Manager",
			"IT Director", "HR Director", "Finance Manager", "Regional Manager",
			"Senior Consultant", "Business Analyst", "Team Lead"
		],
		"domains": [
			"techsolutions.com", "globalhealthcare.org", "financialadvisors.net",
			"manufacturingcorp.com", "retaildynamics.com", "educationpartners.edu",
			"constructiongroup.com", "marketingpro.com", "softwaredev.com",
			"consultingexperts.com", "realestate.com", "foodbeverage.com"
		],
		"phone_prefixes": ["+1", "+44", "+49", "+33", "+61", "+91"],
		"salutations": ["Mr", "Ms", "Mrs", "Dr"],
		"genders": ["Male", "Female"],
		"employee_ranges": ["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"],
		"statuses": lead_statuses,
		"sources": lead_sources,
		"industries": industries,
		"territories": territories,
		"users": users
	}


def generate_random_lead_data(sample_data, index):
	"""Generate random lead data using sample data"""
	
	first_name = random.choice(sample_data["first_names"])
	last_name = random.choice(sample_data["last_names"])
	organization = random.choice(sample_data["organizations"])
	domain = random.choice(sample_data["domains"])
	
	# Generate realistic email
	email_variants = [
		f"{first_name.lower()}.{last_name.lower()}@{domain}",
		f"{first_name.lower()}{last_name.lower()}@{domain}",
		f"{first_name[0].lower()}{last_name.lower()}@{domain}",
		f"{first_name.lower()}@{domain}"
	]
	email = random.choice(email_variants)
	
	# Generate phone numbers
	phone_prefix = random.choice(sample_data["phone_prefixes"])
	mobile_no = f"{phone_prefix} {random.randint(100, 999)} {random.randint(100, 999)} {random.randint(1000, 9999)}"
	phone = f"{phone_prefix} {random.randint(100, 999)} {random.randint(100, 999)} {random.randint(1000, 9999)}"
	
	# Generate website
	website = f"https://www.{domain}"
	
	# Generate annual revenue (random between 100K and 50M)
	revenue_ranges = [100000, 500000, 1000000, 5000000, 10000000, 50000000]
	annual_revenue = random.choice(revenue_ranges) + random.randint(0, 500000)
	
	lead_data = {
		"first_name": first_name,
		"last_name": last_name,
		"email": email,
		"mobile_no": mobile_no,
		"phone": phone,
		"organization": organization,
		"website": website,
		"job_title": random.choice(sample_data["job_titles"]),
		"salutation": random.choice(sample_data["salutations"]),
		"gender": random.choice(sample_data["genders"]),
		"status": random.choice(sample_data["statuses"]),
		"source": random.choice(sample_data["sources"]) if sample_data["sources"] else None,
		"industry": random.choice(sample_data["industries"]) if sample_data["industries"] else None,
		"territory": random.choice(sample_data["territories"]) if sample_data["territories"] else None,
		"lead_owner": random.choice(sample_data["users"]),
		"annual_revenue": annual_revenue,
		"no_of_employees": random.choice(sample_data["employee_ranges"]),
	}
	
	# Randomly assign some fields as None to simulate realistic incomplete data
	optional_fields = ["territory", "source", "industry", "phone", "annual_revenue", "job_title"]
	for field in optional_fields:
		if random.random() < 0.3:  # 30% chance to be None
			lead_data[field] = None
	
	return lead_data


@frappe.whitelist()
def get_sample_leads_count():
	"""
	Get count of existing sample leads in the system
	
	Returns:
		dict: Response with count information
	"""
	try:
		total_leads = frappe.db.count("CRM Lead")
		recent_leads = frappe.db.count("CRM Lead", {"creation": [">=", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")]})
		
		return {
			"success": True,
			"data": {
				"total_leads": total_leads,
				"recent_leads": recent_leads,
				"message": _("Found {0} total leads, {1} created in the last 24 hours").format(total_leads, recent_leads)
			}
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Sample Leads Count Error")
		return {
			"success": False,
			"error": str(e),
			"message": _("Failed to get leads count")
		}


@frappe.whitelist()
def delete_sample_leads():
	"""
	Delete all sample leads created for demonstration
	WARNING: This will delete ALL leads in the system!
	
	Returns:
		dict: Response with deletion information
	"""
	try:
		if not frappe.has_permission("CRM Lead", "delete"):
			frappe.throw(_("Insufficient permissions to delete leads"), frappe.PermissionError)
		
		# Get all leads
		leads = frappe.get_all("CRM Lead", pluck="name")
		
		if not leads:
			return {
				"success": True,
				"message": _("No leads found to delete"),
				"data": {"deleted": 0}
			}
		
		# Delete all leads
		deleted_count = 0
		for lead_name in leads:
			try:
				frappe.delete_doc("CRM Lead", lead_name, ignore_permissions=True)
				deleted_count += 1
			except Exception as e:
				frappe.log_error(f"Error deleting lead {lead_name}: {str(e)}")
				continue
		
		frappe.db.commit()
		
		return {
			"success": True,
			"message": _("Successfully deleted {0} leads").format(deleted_count),
			"data": {
				"deleted": deleted_count,
				"total_found": len(leads)
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Delete Sample Leads Error")
		return {
			"success": False,
			"error": str(e),
			"message": _("Failed to delete sample leads")
		}
