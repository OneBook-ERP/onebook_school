"""One payment from a parent for all their children's fee invoices."""

import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_outstanding(guardian, company):
	"""Unpaid submitted fee invoices of `guardian`'s students in `company`, oldest due date first."""
	frappe.has_permission("Guardian", "read", guardian, throw=True)
	students = frappe.get_all(
		"Student Guardian", filters={"guardian": guardian, "parenttype": "Student"}, pluck="parent"
	)
	if not students:
		return []
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"student": ["in", students], "company": company, "docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "student", "due_date", "outstanding_amount", "posting_date"],
		order_by="due_date asc, posting_date asc, name asc",
	)
	return [
		{
			"student": inv.student,
			"student_name": frappe.db.get_value("Student", inv.student, "student_name"),
			"sales_invoice": inv.name,
			"due_date": inv.due_date,
			"outstanding_amount": flt(inv.outstanding_amount),
		}
		for inv in invoices
	]
