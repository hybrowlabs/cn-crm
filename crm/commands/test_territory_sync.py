"""
Frappe command to test territory synchronization
Usage: bench execute crm.commands.test_territory_sync.run_tests
"""

import frappe
from frappe.commands import pass_context, click


@click.command('test-territory-sync')
@pass_context
def test_territory_sync(context):
    """Test territory synchronization functionality"""
    
    # Import the test script
    import sys
    import os
    
    # Add the project root to Python path
    project_root = frappe.get_app_path("crm", "..", "..", "..")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Import and run tests
    from test_territory_sync import run_territory_sync_tests
    
    # Set site context
    frappe.init(site=context.sites[0] if context.sites else None)
    frappe.connect()
    
    try:
        results = run_territory_sync_tests()
        return results
    finally:
        frappe.destroy()


def run_tests():
    """Function that can be called via bench execute"""
    
    # Import the test script
    import sys
    import os
    
    # Add the project root to Python path  
    project_root = os.path.join(frappe.get_app_path("crm"), "..", "..", "..")
    project_root = os.path.abspath(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Import and run tests
    from test_territory_sync import run_territory_sync_tests
    
    return run_territory_sync_tests()


@frappe.whitelist()
def run_sync_tests_api():
    """API method to run territory sync tests"""
    
    try:
        # Import the test script
        import sys
        import os
        
        # Add the project root to Python path
        project_root = os.path.join(frappe.get_app_path("crm"), "..", "..", "..")
        project_root = os.path.abspath(project_root)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Import and run tests
        from test_territory_sync import run_territory_sync_tests
        
        results = run_territory_sync_tests()
        
        return {
            "success": True,
            "results": results,
            "message": "Territory sync tests completed"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Territory Sync Test Error")
        return {
            "success": False,
            "error": str(e),
            "message": "Territory sync tests failed"
        }


if __name__ == "__main__":
    test_territory_sync()








