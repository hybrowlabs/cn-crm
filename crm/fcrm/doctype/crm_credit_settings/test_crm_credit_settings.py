# Copyright (c) 2026, Frappe and contributors
# For license information, please see license.txt

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCRMCreditSettings(FrappeTestCase):
	def test_credit_limit_validation(self):
		"""Test credit limit validation"""
		settings = frappe.get_doc({
			"doctype": "CRM Credit Settings",
			"enabled": 1,
			"default_credit_limit": 200000,
			"max_credit_limit": 100000  # Invalid: default > max
		})

		with self.assertRaises(frappe.ValidationError):
			settings.save()

	def test_approval_limit_validation(self):
		"""Test approval limit validation"""
		settings = frappe.get_doc({
			"doctype": "CRM Credit Settings",
			"enabled": 1,
			"auto_approval_limit": 600000,
			"require_approval_above": 500000  # Invalid: auto >= required
		})

		with self.assertRaises(frappe.ValidationError):
			settings.save()

	def test_credit_settings_creation(self):
		"""Test successful credit settings creation"""
		settings = frappe.get_doc({
			"doctype": "CRM Credit Settings",
			"enabled": 1,
			"default_credit_limit": 100000,
			"max_credit_limit": 1000000,
			"auto_approval_limit": 500000,
			"require_approval_above": 500001
		})

		settings.save()
		self.assertEqual(settings.enabled, 1)
		self.assertEqual(settings.default_credit_limit, 100000)