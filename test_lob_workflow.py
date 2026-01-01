#!/usr/bin/env python3
"""
Test script for LoB-based service team assignment workflow.
This script tests the complete flow from LoB setup to engineer assignment.
"""

import frappe
import sys
import os

# Add the app path to sys.path for imports
sys.path.append('/home/frappe/bench5/apps/crm')

def run_comprehensive_test():
	"""
	Run comprehensive test of the LoB service team workflow.
	"""
	print("🚀 Starting LoB Service Team Workflow Test")
	print("=" * 60)

	# Initialize Frappe
	try:
		frappe.init(site='site1.local')
		frappe.connect()

		# Run tests in sequence
		test_results = {
			"master_data_setup": test_master_data_setup(),
			"service_assignment": test_service_assignment_logic(),
			"engineer_filtering": test_engineer_filtering(),
			"lob_inheritance": test_lob_inheritance(),
			"site_visit_assignment": test_site_visit_assignment()
		}

		# Print summary
		print("\n" + "=" * 60)
		print("🎯 TEST SUMMARY")
		print("=" * 60)

		all_passed = True
		for test_name, passed in test_results.items():
			status = "✅ PASSED" if passed else "❌ FAILED"
			print(f"{test_name.replace('_', ' ').title():<30} {status}")
			if not passed:
				all_passed = False

		print("\n" + ("🎉 ALL TESTS PASSED!" if all_passed else "⚠️ SOME TESTS FAILED"))
		return all_passed

	except Exception as e:
		print(f"❌ Test execution failed: {str(e)}")
		return False
	finally:
		frappe.destroy()

def test_master_data_setup():
	"""Test LoB master data setup."""
	print("\n📋 Testing Master Data Setup...")

	try:
		from crm.api.lob_master_data_setup import setup_lob_master_data, verify_lob_setup

		# Setup master data
		result = setup_lob_master_data()
		print(f"   Setup result: {result.get('message', 'No message')}")

		# Verify setup
		verification = verify_lob_setup()
		if verification.get("success"):
			verification_data = verification["verification"]
			print(f"   ✅ LoB Records: {verification_data['summary']['configured_lobs']}/{verification_data['summary']['total_lobs']}")
			print(f"   ✅ Issues Found: {verification_data['summary']['total_issues']}")
			return verification_data['summary']['setup_complete']
		else:
			print(f"   ❌ Verification failed: {verification.get('error')}")
			return False

	except Exception as e:
		print(f"   ❌ Master data test failed: {str(e)}")
		return False

def test_service_assignment_logic():
	"""Test smart service assignment logic."""
	print("\n🎯 Testing Service Assignment Logic...")

	try:
		from crm.api.smart_service_assignment import assign_service_team

		# Test primary LoB assignments
		test_cases = [
			("Alloys", "Primary"),
			("Plating", "Primary"),
			("Machines", "Primary"),
			("General Services", "Fallback"),
			("Some Random LoB", "Fallback")
		]

		all_passed = True
		for lob_name, expected_type in test_cases:
			result = assign_service_team(lob_name)
			if result.get("success"):
				actual_type = result.get("team_type")
				if actual_type == expected_type:
					print(f"   ✅ {lob_name:<15} → {actual_type} team")
				else:
					print(f"   ❌ {lob_name:<15} → Expected {expected_type}, got {actual_type}")
					all_passed = False
			else:
				print(f"   ❌ {lob_name:<15} → Assignment failed: {result.get('error')}")
				all_passed = False

		return all_passed

	except Exception as e:
		print(f"   ❌ Service assignment test failed: {str(e)}")
		return False

def test_engineer_filtering():
	"""Test LoB-based engineer filtering."""
	print("\n👥 Testing Engineer Filtering...")

	try:
		from crm.api.lob_engineer_filters import get_engineers_for_lob_selection, get_primary_engineers_by_lob

		# Test engineer filtering for each LoB
		test_lobs = ["Alloys", "Plating", "Machines", "General Services"]

		all_passed = True
		for lob in test_lobs:
			engineers = get_engineers_for_lob_selection(lob)
			print(f"   📊 {lob:<15} → {len(engineers)} engineers available")

			# Check structure
			for engineer in engineers[:1]:  # Check first engineer structure
				required_fields = ["user", "full_name", "is_primary", "expertise_level"]
				missing_fields = [field for field in required_fields if field not in engineer]
				if missing_fields:
					print(f"   ❌ Missing fields in engineer data: {missing_fields}")
					all_passed = False

		# Test primary engineers summary
		primary_summary = get_primary_engineers_by_lob()
		print(f"   📈 Primary engineers summary: {len(primary_summary)} LoB teams configured")

		return all_passed

	except Exception as e:
		print(f"   ❌ Engineer filtering test failed: {str(e)}")
		return False

def test_lob_inheritance():
	"""Test LoB inheritance from Lead to Deal."""
	print("\n🔄 Testing LoB Inheritance...")

	try:
		# Check if there are existing leads with LoB
		leads = frappe.get_all("CRM Lead",
			filters={"line_of_business": ["!=", ""]},
			fields=["name", "line_of_business"],
			limit=1
		)

		if leads:
			lead = leads[0]
			print(f"   📋 Found test lead: {lead.name} with LoB: {lead.line_of_business}")

			# Test deal creation with inheritance
			try:
				# Create a simple test deal
				deal_data = {
					"doctype": "CRM Deal",
					"lead": lead.name,
					"organization": f"Test Org for {lead.name}",
				}

				deal = frappe.get_doc(deal_data)
				deal.insert(ignore_permissions=True)

				print(f"   ✅ Deal created: {deal.name}")
				print(f"   🔄 Inherited LoB: {deal.line_of_business}")

				# Cleanup test data
				frappe.delete_doc("CRM Deal", deal.name, ignore_permissions=True)

				return deal.line_of_business == lead.line_of_business

			except Exception as e:
				print(f"   ❌ Deal creation failed: {str(e)}")
				return False
		else:
			print("   ℹ️ No leads with LoB found for inheritance test")
			return True  # Not a failure, just no test data

	except Exception as e:
		print(f"   ❌ LoB inheritance test failed: {str(e)}")
		return False

def test_site_visit_assignment():
	"""Test automatic service engineer assignment for site visits."""
	print("\n🏠 Testing Site Visit Engineer Assignment...")

	try:
		from crm.api.smart_service_assignment import auto_assign_service_engineer

		# Check if there are existing site visits
		site_visits = frappe.get_all("CRM Site Visit",
			filters={"line_of_business": ["!=", ""]},
			fields=["name", "line_of_business", "service_engineer"],
			limit=1
		)

		if site_visits:
			visit = site_visits[0]
			print(f"   🏠 Found test site visit: {visit.name}")
			print(f"   📋 LoB: {visit.line_of_business}")
			print(f"   👤 Current engineer: {visit.service_engineer or 'None'}")

			# Test auto-assignment
			assignment_result = auto_assign_service_engineer(visit.name)

			if assignment_result.get("success"):
				print(f"   ✅ Engineer assigned: {assignment_result.get('engineer_name')}")
				print(f"   🏢 Team type: {assignment_result.get('team_type')}")
				return True
			else:
				print(f"   ❌ Assignment failed: {assignment_result.get('message')}")
				return False
		else:
			print("   ℹ️ No site visits with LoB found for assignment test")
			return True  # Not a failure, just no test data

	except Exception as e:
		print(f"   ❌ Site visit assignment test failed: {str(e)}")
		return False

if __name__ == "__main__":
	try:
		success = run_comprehensive_test()
		sys.exit(0 if success else 1)
	except KeyboardInterrupt:
		print("\n⚠️ Test interrupted by user")
		sys.exit(1)
	except Exception as e:
		print(f"\n💥 Unexpected error: {str(e)}")
		sys.exit(1)