"""
API endpoints for testing territory synchronization
"""

import frappe
from frappe import _
import json


@frappe.whitelist()
def test_territory_sync():
    """
    API endpoint to test territory synchronization
    Returns comprehensive test results
    """
    
    try:
        # Run the comprehensive test
        results = run_comprehensive_sync_test()
        
        return {
            "success": True,
            "data": results,
            "message": _("Territory synchronization test completed successfully")
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Territory Sync Test API Error")
        return {
            "success": False,
            "error": str(e),
            "message": _("Territory synchronization test failed")
        }


@frappe.whitelist()
def quick_sync_test():
    """
    Quick test of territory synchronization
    """
    
    try:
        print("🚀 Starting Quick Territory Sync Test")
        
        # Check if integration is enabled
        erpnext_settings = frappe.get_single("ERPNext CRM Settings")
        if not erpnext_settings.enabled:
            return {
                "success": False,
                "message": "ERPNext CRM integration is not enabled"
            }
        
        if not erpnext_settings.enable_territory_sync:
            return {
                "success": False, 
                "message": "Territory synchronization is not enabled"
            }
        
        # Test 1: Create Territory and check if CRM Territory is created
        territory_name = f"Quick Test Territory {frappe.utils.now()}"
        
        # Clean up first
        cleanup_test_territory(territory_name)
        
        # Create Territory
        territory = frappe.get_doc({
            "doctype": "Territory",
            "territory_name": territory_name,
            "is_group": 0
        })
        territory.insert()
        frappe.db.commit()
        
        # Check if CRM Territory was created
        crm_territory_exists = frappe.db.exists("CRM Territory", territory_name)
        
        test_results = {
            "territory_created": True,
            "crm_territory_auto_created": bool(crm_territory_exists),
            "territory_name": territory_name
        }
        
        # Test 2: Create CRM Territory and check if Territory is created
        crm_territory_name = f"Quick Test CRM Territory {frappe.utils.now()}"
        
        # Clean up first
        cleanup_test_territory(crm_territory_name)
        
        # Create CRM Territory
        crm_territory = frappe.get_doc({
            "doctype": "CRM Territory", 
            "territory_name": crm_territory_name,
            "is_group": 1
        })
        crm_territory.insert()
        frappe.db.commit()
        
        # Check if Territory was created
        territory_exists = frappe.db.exists("Territory", crm_territory_name)
        
        test_results.update({
            "crm_territory_created": True,
            "territory_auto_created": bool(territory_exists),
            "crm_territory_name": crm_territory_name
        })
        
        # Clean up test data
        cleanup_test_territory(territory_name)
        cleanup_test_territory(crm_territory_name)
        
        # Determine overall success
        success = (test_results["crm_territory_auto_created"] and 
                  test_results["territory_auto_created"])
        
        return {
            "success": success,
            "data": test_results,
            "message": "Quick sync test completed" if success else "Sync test failed - check results"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Quick Territory Sync Test Error")
        return {
            "success": False,
            "error": str(e),
            "message": "Quick sync test failed with error"
        }


@frappe.whitelist()
def test_field_mapping():
    """
    Test field mapping functionality
    """
    
    try:
        from crm.fcrm.doctype.crm_territory.field_mapping import (
            get_territory_field_mapping,
            get_doctype_fields
        )
        
        # Get field information
        territory_fields = get_doctype_fields("Territory")
        crm_territory_fields = get_doctype_fields("CRM Territory")
        mapping = get_territory_field_mapping()
        
        return {
            "success": True,
            "data": {
                "territory_fields_count": len(territory_fields),
                "crm_territory_fields_count": len(crm_territory_fields),
                "territory_fields": territory_fields[:10],  # First 10 for brevity
                "crm_territory_fields": crm_territory_fields[:10],
                "crm_to_territory_mappings": mapping["crm_to_territory"],
                "territory_to_crm_mappings": mapping["territory_to_crm"]
            },
            "message": "Field mapping test completed successfully"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Field Mapping Test Error")
        return {
            "success": False,
            "error": str(e),
            "message": "Field mapping test failed"
        }


@frappe.whitelist()
def test_bulk_sync():
    """
    Test bulk synchronization
    """
    
    try:
        from crm.fcrm.doctype.crm_territory.sync_territories import sync_all_territories
        
        # Count existing records before sync
        territory_count_before = frappe.db.count("Territory")
        crm_territory_count_before = frappe.db.count("CRM Territory")
        
        # Run bulk sync
        sync_all_territories()
        
        # Count records after sync
        territory_count_after = frappe.db.count("Territory")
        crm_territory_count_after = frappe.db.count("CRM Territory")
        
        return {
            "success": True,
            "data": {
                "territory_count_before": territory_count_before,
                "territory_count_after": territory_count_after,
                "crm_territory_count_before": crm_territory_count_before,
                "crm_territory_count_after": crm_territory_count_after,
                "territories_synced": abs(territory_count_after - crm_territory_count_after) == 0
            },
            "message": "Bulk synchronization completed successfully"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Bulk Sync Test Error")
        return {
            "success": False,
            "error": str(e),
            "message": "Bulk synchronization test failed"
        }


def cleanup_test_territory(territory_name):
    """Helper function to clean up test territories"""
    try:
        if frappe.db.exists("Territory", territory_name):
            frappe.delete_doc("Territory", territory_name, force=True)
        if frappe.db.exists("CRM Territory", territory_name):
            frappe.delete_doc("CRM Territory", territory_name, force=True)
        frappe.db.commit()
    except:
        pass


def run_comprehensive_sync_test():
    """
    Run comprehensive territory synchronization test
    """
    
    print("🚀 Running Comprehensive Territory Sync Test")
    
    results = {}
    
    # Test 1: Field Mapping
    print("📋 Testing field mapping...")
    field_mapping_result = test_field_mapping()
    results["field_mapping"] = field_mapping_result["success"]
    
    # Test 2: Quick Sync
    print("⚡ Testing quick sync...")
    quick_sync_result = test_quick_sync()
    results["quick_sync"] = quick_sync_result["success"]
    
    # Test 3: Bulk Sync
    print("📦 Testing bulk sync...")
    bulk_sync_result = test_bulk_sync()
    results["bulk_sync"] = bulk_sync_result["success"]
    
    # Calculate overall success
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "success_rate": f"{passed_tests}/{total_tests}",
        "overall_success": passed_tests == total_tests
    }
    
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed")
    
    return results


def test_quick_sync():
    """Internal quick sync test"""
    return quick_sync_test()








