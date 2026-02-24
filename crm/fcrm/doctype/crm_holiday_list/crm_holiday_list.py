# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

<<<<<<< HEAD
# import frappe
from frappe.model.document import Document
=======

import frappe
from frappe import _, throw
from frappe.model.document import Document
from frappe.utils import cint, formatdate, getdate
>>>>>>> 7b5aa466 (fix: remove unused import statements across multiple files)


class CRMHolidayList(Document):
	pass
