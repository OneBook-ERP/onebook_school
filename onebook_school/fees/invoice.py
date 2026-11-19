"""Fee invoices carry the student's class, so dues can be read class by class."""

import frappe


def set_class(doc, method=None):
	if doc.get("student") and not doc.get("obs_program"):
		doc.obs_program = frappe.db.get_value(
			"Program Enrollment", {"student": doc.student, "docstatus": 1}, "program", order_by="enrollment_date desc, creation desc"
		)
