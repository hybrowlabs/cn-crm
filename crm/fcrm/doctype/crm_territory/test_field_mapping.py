# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from crm.fcrm.doctype.crm_territory.field_mapping import (
	get_territory_field_mapping,
	get_doctype_fields,
	map_territory_to_crm_data,
	map_crm_to_territory_data,
	get_safe_field_value,
	update_doc_with_mapped_data
)


class TestFieldMapping(FrappeTestCase):
	def test_get_doctype_fields(self):
		"""Test getting fields for both doctypes"""
		territory_fields = get_doctype_fields("Territory")
		crm_territory_fields = get_doctype_fields("CRM Territory")
		
		# Basic fields that should exist
		self.assertIn("territory_name", territory_fields)
		self.assertIn("territory_name", crm_territory_fields)
		self.assertIn("is_group", territory_fields)
		self.assertIn("is_group", crm_territory_fields)
	
	def test_field_mapping_structure(self):
		"""Test field mapping returns correct structure"""
		mapping = get_territory_field_mapping()
		
		self.assertIn("crm_to_territory", mapping)
		self.assertIn("territory_to_crm", mapping)
		
		# Check basic mappings exist
		crm_to_territory = mapping["crm_to_territory"]
		territory_to_crm = mapping["territory_to_crm"]
		
		self.assertIn("territory_name", crm_to_territory)
		self.assertIn("territory_name", territory_to_crm)
	
	def test_safe_field_value(self):
		"""Test safe field value retrieval"""
		# Create a mock document
		doc = frappe._dict({
			"territory_name": "Test Territory",
			"is_group": 1
		})
		
		# Test existing field
		self.assertEqual(get_safe_field_value(doc, "territory_name"), "Test Territory")
		
		# Test non-existing field with default
		self.assertEqual(get_safe_field_value(doc, "non_existing_field", "default"), "default")
		
		# Test non-existing field without default
		self.assertIsNone(get_safe_field_value(doc, "non_existing_field"))
	
	def test_update_doc_with_mapped_data(self):
		"""Test updating document with mapped data"""
		# Create a mock document
		doc = frappe._dict({
			"territory_name": "Old Name",
			"is_group": 0
		})
		
		# Test data to update
		mapped_data = {
			"territory_name": "New Name",
			"is_group": 1,
			"non_existing_field": "should be ignored"
		}
		
		updated_fields = update_doc_with_mapped_data(doc, mapped_data)
		
		# Check updates
		self.assertEqual(doc.territory_name, "New Name")
		self.assertEqual(doc.is_group, 1)
		
		# Check that only existing fields were updated
		self.assertIn("territory_name", updated_fields)
		self.assertIn("is_group", updated_fields)
		self.assertNotIn("non_existing_field", updated_fields)
		
		# Check non-existing field was not added
		self.assertFalse(hasattr(doc, "non_existing_field"))


def run_field_mapping_tests():
	"""Run field mapping tests manually"""
	frappe.flags.in_test = True
	
	try:
		test_case = TestFieldMapping()
		test_case.setUp()
		
		print("Running field mapping tests...")
		
		test_case.test_get_doctype_fields()
		print("✓ test_get_doctype_fields passed")
		
		test_case.test_field_mapping_structure()
		print("✓ test_field_mapping_structure passed")
		
		test_case.test_safe_field_value()
		print("✓ test_safe_field_value passed")
		
		test_case.test_update_doc_with_mapped_data()
		print("✓ test_update_doc_with_mapped_data passed")
		
		print("All field mapping tests passed!")
		
	except Exception as e:
		print(f"Test failed: {str(e)}")
		frappe.log_error(frappe.get_traceback(), "Field Mapping Test Error")
		raise
	finally:
		frappe.flags.in_test = False








