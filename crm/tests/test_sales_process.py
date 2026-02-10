
import frappe
from frappe.tests.utils import FrappeTestCase

class TestSalesProcess(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("CRM Deal")
		frappe.db.delete("CRM Site Visit")
		frappe.db.delete("CRM Lead")

		# Create prerequisites
		self.create_prerequisites()

	def create_prerequisites(self):
		if not frappe.db.exists("CRM Product", "Test Alloy"):
			p = frappe.new_doc("CRM Product")
			p.product_name = "Test Alloy"
			p.insert(ignore_permissions=True)

		if not frappe.db.exists("CRM Industry", "Test Industry"):
			i = frappe.new_doc("CRM Industry")
			i.industry = "Test Industry"
			i.insert(ignore_permissions=True)

		if not frappe.db.exists("CRM Lead Source", "Test Source"):
			s = frappe.new_doc("CRM Lead Source")
			s.source_name = "Test Source"
			s.insert(ignore_permissions=True)

	def test_lead_to_meeting_gate(self):
		# Create Lead with missing fields
		lead = frappe.new_doc("CRM Lead")
		lead.first_name = "Test Lead"
		lead.email_id = "test@example.com"
		lead.status = "New"
		lead.source = "Test Source"
		lead.industry = "Test Industry"
		lead.designation = "Manager"
		lead.product_interest = "Test Alloy"
		# Missing mandatory application__use_case for gate
		lead.application__use_case = "" 
		lead.save(ignore_permissions=True)

		# Try creating meeting - should fail due to missing Lead field
		visit = frappe.new_doc("CRM Site Visit")
		visit.reference_type = "CRM Lead"
		visit.reference_name = lead.name
		visit.next_action_date = "2026-03-01" # Valid meeting field
		
		# Validation error expected
		try:
			visit.save(ignore_permissions=True)
		except frappe.ValidationError:
			pass
		else:
			self.fail("CRM Site Visit should have failed due to missing Lead fields")

		# Fix Lead
		lead.application__use_case = "Valid Case"
		lead.save(ignore_permissions=True)

		# Try creating meeting again - should now require meeting fields
		visit = frappe.new_doc("CRM Site Visit")
		visit.reference_type = "CRM Lead"
		visit.reference_name = lead.name
		# Missing mandatory meeting fields (pain, role, etc)
		
		try:
			visit.save(ignore_permissions=True)
		except frappe.ValidationError:
			pass
		else:
			self.fail("CRM Site Visit should have failed due to missing mandatory meeting fields")

		# Fill meeting fields
		visit.next_action_date = "2026-03-01"
		visit.primary_pain_category = "Quality Consistency"
		visit.pain_description = "Issues with current alloy"
		visit.customer_role_type = "Decision Maker"
		visit.decision_process = "Board approval"
		visit.current_supplier = "Competitor X"
		visit.meeting_type = "Call" # from seed
		visit.visit_date = "2026-02-10"
		
		visit.save(ignore_permissions=True)
		self.assertTrue(visit.name)

	def test_deal_gates(self):
		# 1. Setup Valid Lead & Meeting
		lead = frappe.new_doc("CRM Lead")
		lead.first_name = "Deal Lead"
		lead.status = "New"
		lead.source = "Test Source"
		lead.industry = "Test Industry"
		lead.designation = "Director"
		lead.product_interest = "Test Alloy"
		lead.application__use_case = "Testing Deal"
		lead.save(ignore_permissions=True)

		visit = frappe.new_doc("CRM Site Visit")
		visit.reference_type = "CRM Lead"
		visit.reference_name = lead.name
		visit.next_action_date = "2026-03-01"
		visit.primary_pain_category = "Quality Consistency"
		visit.pain_description = "Pain desc"
		visit.customer_role_type = "Decision Maker" 
		visit.decision_process = "Process"
		visit.current_supplier = "Supplier"
		visit.meeting_type = "Call"
		visit.visit_date = "2026-02-10"
		visit.volume_rangekg = "100-500" # needed for deal gate
		visit.save(ignore_permissions=True)

		# 2. Test Meeting -> Opportunity Gate
		deal = frappe.new_doc("CRM Deal")
		deal.lead = lead.name
		deal.deal_owner = frappe.session.user
		deal.status = "Qualification"
		
		deal.save(ignore_permissions=True) # Should pass
		
		# 3. Test Opportunity -> Trial Gate
		deal.status = "Demo/Making"
		
		# Should fail
		try:
			deal.save(ignore_permissions=True)
		except frappe.ValidationError:
			pass
		else:
			self.fail("Should fail moving to Demo/Making without trial fields")

		# Add trial fields
		deal.product_alloy_type = "Test Alloy"
		deal.trial_volume = 100
		deal.trial_success_criteria = "Success"
		deal.trial_start_date = "2026-03-01"
		deal.trial_end_date = "2026-03-15"
		
		deal.save(ignore_permissions=True) # Should pass

		# 4. Test Trial -> Proposal Gate
		deal.status = "Proposal/Quotation"
		
		# Should fail
		try:
			deal.save(ignore_permissions=True)
		except frappe.ValidationError:
			pass
		else:
			self.fail("Should fail moving to Proposal/Quotation without trial outcome")

		# Add trial outcome
		deal.trial_outcome = "Fail"
		deal.trial_outcome_notes = "Failed test"
		
		# Should fail because outcome must be Pass
		try:
			deal.save(ignore_permissions=True)
		except frappe.ValidationError:
			pass
		else:
			self.fail("Should fail if outcome is not Pass")

		deal.trial_outcome = "Pass"
		deal.save(ignore_permissions=True) # Should pass
