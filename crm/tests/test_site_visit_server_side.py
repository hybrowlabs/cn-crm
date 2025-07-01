"""
Test cases for CRM Site Visit Server-Side Workflow API
Tests all workflow transitions, validations, and business logic
"""

import frappe
import unittest
from frappe.utils import getdate, now_datetime, add_days
from crm.api.site_visit_workflow import (
    get_form_metadata, perform_workflow_action, 
    get_workflow_metadata, get_available_actions
)


class TestSiteVisitWorkflow(unittest.TestCase):
    
    def setUp(self):
        """Setup test data"""
        self.test_lead = frappe.get_doc({
            'doctype': 'CRM Lead',
            'lead_name': 'Test Customer',
            'organization': 'Test Company',
            'email': 'test@example.com',
            'mobile_no': '1234567890',
            'city': 'Test City',
            'state': 'Test State'
        }).insert()
        
        self.test_visit = frappe.get_doc({
            'doctype': 'CRM Site Visit',
            'visit_date': getdate(),
            'visit_type': 'Initial Meeting',
            'reference_type': 'CRM Lead',
            'reference_name': self.test_lead.name,
            'sales_person': frappe.session.user,
            'status': 'Planned'
        }).insert()
    
    def tearDown(self):
        """Cleanup test data"""
        frappe.delete_doc('CRM Site Visit', self.test_visit.name, force=True)
        frappe.delete_doc('CRM Lead', self.test_lead.name, force=True)
    
    def test_get_form_metadata(self):
        """Test form metadata retrieval"""
        result = get_form_metadata(docname=self.test_visit.name)
        
        self.assertTrue(result['success'])
        self.assertIn('workflow_state', result['metadata'])
        self.assertIn('available_actions', result['metadata'])
        self.assertIn('form_guidance', result['metadata'])
        
        # Check workflow state
        workflow_state = result['metadata']['workflow_state']
        self.assertEqual(workflow_state['current_status'], 'Planned')
        self.assertTrue(workflow_state['can_checkin'])
        self.assertFalse(workflow_state['can_checkout'])
        self.assertFalse(workflow_state['can_submit'])
    
    def test_get_available_actions_planned_status(self):
        """Test available actions for planned visit"""
        visit = frappe.get_doc('CRM Site Visit', self.test_visit.name)
        actions = get_available_actions(visit)
        
        # Should have check-in actions
        action_types = [action['action'] for action in actions]
        self.assertIn('checkin', action_types)
        self.assertIn('manual_checkin', action_types)
        self.assertNotIn('checkout', action_types)
        self.assertNotIn('submit', action_types)
    
    def test_workflow_checkin(self):
        """Test check-in workflow"""
        # Perform check-in
        result = perform_workflow_action(
            docname=self.test_visit.name,
            action='checkin',
            latitude=19.0760,
            longitude=72.8777,
            accuracy=10
        )
        
        self.assertTrue(result['success'])
        self.assertIn('Check-in successful', result['message'])
        self.assertIn('location', result)
        
        # Verify document state
        visit = frappe.get_doc('CRM Site Visit', self.test_visit.name)
        self.assertEqual(visit.status, 'In Progress')
        self.assertIsNotNone(visit.check_in_time)
        self.assertEqual(visit.check_in_latitude, 19.0760)
        self.assertEqual(visit.check_in_longitude, 72.8777)
    
    def test_workflow_manual_checkin(self):
        """Test manual check-in workflow"""
        result = perform_workflow_action(
            docname=self.test_visit.name,
            action='manual_checkin',
            location_name='Test Office',
            latitude=19.0760,
            longitude=72.8777,
            reason='GPS not available'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('Manual check-in successful', result['message'])
        
        # Verify document state
        visit = frappe.get_doc('CRM Site Visit', self.test_visit.name)
        self.assertEqual(visit.status, 'In Progress')
        self.assertEqual(visit.check_in_location, 'Test Office')
        self.assertIn('Manual Entry', visit.location_accuracy)
    
    def test_workflow_checkout(self):
        """Test check-out workflow"""
        # First check-in
        perform_workflow_action(
            docname=self.test_visit.name,
            action='checkin',
            latitude=19.0760,
            longitude=72.8777,
            accuracy=10
        )
        
        # Then check-out
        result = perform_workflow_action(
            docname=self.test_visit.name,
            action='checkout',
            latitude=19.0761,
            longitude=72.8778,
            visit_summary='Good meeting with customer',
            lead_quality='Hot'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('Check-out successful', result['message'])
        self.assertIn('duration', result)
        
        # Verify document state
        visit = frappe.get_doc('CRM Site Visit', self.test_visit.name)
        self.assertEqual(visit.status, 'Completed')
        self.assertIsNotNone(visit.check_out_time)
        self.assertEqual(visit.visit_summary, 'Good meeting with customer')
        self.assertEqual(visit.lead_quality, 'Hot')
        self.assertIsNotNone(visit.total_duration)
    
    def test_workflow_submission(self):
        """Test visit submission workflow"""
        # Complete the visit workflow first
        perform_workflow_action(
            docname=self.test_visit.name,
            action='checkin',
            latitude=19.0760,
            longitude=72.8777,
            accuracy=10
        )
        
        perform_workflow_action(
            docname=self.test_visit.name,
            action='checkout',
            latitude=19.0761,
            longitude=72.8778,
            visit_summary='Meeting completed'
        )
        
        # Submit the visit
        result = perform_workflow_action(
            docname=self.test_visit.name,
            action='submit'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('submitted successfully', result['message'])
        
        # Verify document state
        visit = frappe.get_doc('CRM Site Visit', self.test_visit.name)
        self.assertEqual(visit.docstatus, 1)
    
    def test_workflow_error_handling(self):
        """Test workflow error handling"""
        # Try to check-out without check-in
        result = perform_workflow_action(
            docname=self.test_visit.name,
            action='checkout',
            latitude=19.0760,
            longitude=72.8777
        )
        
        self.assertFalse(result['success'])
        self.assertIn('failed', result['message'].lower())
    
    def test_workflow_progress_percentage(self):
        """Test workflow progress calculation"""
        visit = frappe.get_doc('CRM Site Visit', self.test_visit.name)
        
        # Planned status
        metadata = get_workflow_metadata(visit)
        self.assertEqual(metadata['progress_percentage'], 20)
        
        # Check-in (In Progress)
        visit.check_in_time = now_datetime()
        visit.status = 'In Progress'
        visit.save()
        metadata = get_workflow_metadata(visit)
        self.assertEqual(metadata['progress_percentage'], 50)
        
        # Check-out (Completed)
        visit.check_out_time = now_datetime()
        visit.status = 'Completed'
        visit.save()
        metadata = get_workflow_metadata(visit)
        self.assertEqual(metadata['progress_percentage'], 80)
        
        # Submitted
        visit.docstatus = 1
        metadata = get_workflow_metadata(visit)
        self.assertEqual(metadata['progress_percentage'], 100)
    
    def test_reference_metadata(self):
        """Test reference metadata retrieval"""
        result = get_form_metadata(
            reference_type='CRM Lead',
            reference_name=self.test_lead.name
        )
        
        self.assertTrue(result['success'])
        self.assertIn('reference_data', result['metadata'])
        
        ref_data = result['metadata']['reference_data']
        self.assertIn('auto_populate_data', ref_data)
        
        auto_data = ref_data['auto_populate_data']
        self.assertEqual(auto_data['reference_title'], 'Test Customer')
        self.assertEqual(auto_data['contact_email'], 'test@example.com')
        self.assertEqual(auto_data['contact_phone'], '1234567890')
    
    def test_validation_rules(self):
        """Test form validation rules"""
        result = get_form_metadata()
        
        self.assertTrue(result['success'])
        self.assertIn('validation_rules', result['metadata'])
        
        rules = result['metadata']['validation_rules']
        self.assertIn('required_fields', rules)
        self.assertIn('workflow_rules', rules)
        self.assertIn('visit_date', rules['required_fields'])
        self.assertTrue(rules['workflow_rules']['checkin_requires_planned_status'])


class TestFormController(unittest.TestCase):
    
    def setUp(self):
        """Setup test data"""
        self.test_address = frappe.get_doc({
            'doctype': 'Address',
            'address_title': 'Test Office',
            'address_line1': '123 Test Street',
            'address_line2': 'Test Area',
            'city': 'Test City',
            'state': 'Test State',
            'country': 'India',
            'pincode': '123456'
        }).insert()
    
    def tearDown(self):
        """Cleanup test data"""
        frappe.delete_doc('Address', self.test_address.name, force=True)
    
    def test_field_change_handling(self):
        """Test server-side field change handling"""
        from crm.api.form_controller import handle_field_change
        
        # Test follow-up required change
        result = handle_field_change(
            docname=None,
            fieldname='follow_up_required',
            value=1,
            form_data={'visit_date': getdate()}
        )
        
        self.assertTrue(result['success'])
        self.assertIn('follow_up_date', result['field_updates'])
        self.assertEqual(
            result['field_updates']['follow_up_date'],
            add_days(getdate(), 7)
        )
    
    def test_auto_populate_form_data(self):
        """Test auto-population of form data"""
        from crm.api.form_controller import auto_populate_form_data
        
        result = auto_populate_form_data(
            reference_type=None,
            reference_name=None,
            customer_address=self.test_address.name
        )
        
        self.assertTrue(result['success'])
        self.assertIn('visit_address', result['data'])
        self.assertIn('city', result['data'])
        self.assertEqual(result['data']['city'], 'Test City')
        self.assertEqual(result['data']['pincode'], '123456')
    
    def test_field_validation(self):
        """Test field validation"""
        from crm.api.form_controller import validate_field_change
        
        # Test past follow-up date
        result = validate_field_change(
            'follow_up_date',
            add_days(getdate(), -1),
            {}
        )
        
        self.assertTrue(len(result['errors']) > 0)
        self.assertIn('cannot be in the past', result['errors'][0])
        
        # Test negative potential value
        result = validate_field_change(
            'potential_value',
            -1000,
            {}
        )
        
        self.assertTrue(len(result['errors']) > 0)
        self.assertIn('greater than zero', result['errors'][0])


class TestMobileInterface(unittest.TestCase):
    
    def test_mobile_dashboard_data(self):
        """Test mobile dashboard data retrieval"""
        from crm.api.mobile_interface import get_mobile_dashboard_data
        
        result = get_mobile_dashboard_data()
        
        self.assertTrue(result['success'])
        self.assertIn('data', result)
        
        data = result['data']
        self.assertIn('visits', data)
        self.assertIn('stats', data)
        self.assertIn('quick_actions', data)
    
    def test_create_quick_visit_mobile(self):
        """Test quick visit creation from mobile"""
        from crm.api.mobile_interface import create_quick_visit_mobile
        
        result = create_quick_visit_mobile(
            customer_name='Quick Test Customer',
            visit_type='Initial Meeting',
            purpose='Quick visit test'
        )
        
        self.assertTrue(result['success'])
        self.assertIn('visit_id', result)
        
        # Cleanup
        frappe.delete_doc('CRM Site Visit', result['visit_id'], force=True)
    
    def test_mobile_workflow_state(self):
        """Test mobile workflow state calculation"""
        from crm.api.mobile_interface import get_mobile_workflow_state
        
        # Create test visit
        visit = frappe.get_doc({
            'doctype': 'CRM Site Visit',
            'visit_date': getdate(),
            'status': 'Planned'
        })
        
        workflow = get_mobile_workflow_state(visit)
        
        self.assertEqual(workflow['current_status'], 'Planned')
        self.assertEqual(workflow['current_step'], 'Planned')
        self.assertTrue(workflow['can_checkin'])
        self.assertFalse(workflow['can_checkout'])
        self.assertIn('next_action', workflow)


if __name__ == '__main__':
    unittest.main()
