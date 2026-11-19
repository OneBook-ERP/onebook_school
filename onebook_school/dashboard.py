"""Number-card methods for the school workspaces."""

import frappe
from frappe.utils import flt, nowdate


@frappe.whitelist()
def present_today(filters=None):
	"""Share of today's marked attendance that is Present."""
	rows = frappe.get_all(
		"Student Attendance",
		filters={"date": nowdate(), "docstatus": 1},
		fields=["status", {"COUNT": "*", "as": "n"}],
		group_by="status",
	)
	marked = sum(r.n for r in rows)
	present = sum(r.n for r in rows if r.status == "Present")
	return {"value": flt(present * 100 / marked, 1) if marked else 0, "fieldtype": "Percent"}


PASS_MARK = 35  # Tamil Nadu: 35% in every subject


@frappe.whitelist()
def pass_percentage(filters=None):
	"""Share of report cards with every subject at the pass mark or above; an absent subject is a fail."""
	cards = frappe.get_all("Report Card", pluck="name")
	if not cards:
		return {"value": 0, "fieldtype": "Percent"}
	failed = {
		r.parent
		for r in frappe.get_all(
			"Report Card Subject", filters={"parent": ["in", cards], "parenttype": "Report Card"}, fields=["parent", "marks", "max_marks", "absent"]
		)
		if r.absent or not flt(r.max_marks) or flt(r.marks) * 100 / flt(r.max_marks) < PASS_MARK
	}
	return {"value": flt((len(cards) - len(failed)) * 100 / len(cards), 1), "fieldtype": "Percent"}


@frappe.whitelist()
def students_per_teacher(filters=None):
	students = frappe.db.count("Student", {"enabled": 1})
	teachers = frappe.db.count("Instructor", {"status": "Active"})
	return {"value": f"{flt(students / teachers, 1):g} : 1" if teachers else "-", "fieldtype": "Data"}
