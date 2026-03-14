import frappe


def execute():
	deal_statuses = frappe.get_all("CRM Deal Status", fields=["name", "probability", "deal_status"])

	for status in deal_statuses:
		if status.probability is None or status.probability == 0:
			if status.deal_status == "Disqualified":
				probability = 10
			elif status.deal_status == "Trial":
				probability = 25
			elif status.deal_status == "Proposal/Quotation":
				probability = 50
			elif status.deal_status == "Won":
				probability = 100
			else:
				probability = 0

			frappe.db.set_value("CRM Deal Status", status.name, "probability", probability)
