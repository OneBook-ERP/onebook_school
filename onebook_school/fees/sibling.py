"""Sibling concession: every younger child of a family gets the School Settings percentage off its fee invoice while
an elder sibling (another enabled, enrolled student sharing a guardian, born earlier) studies in the school."""

import frappe
from frappe.utils import flt, getdate


def has_elder_sibling(student):
	dob = frappe.db.get_value("Student", student, "date_of_birth")
	if not dob:
		return False
	guardians = frappe.get_all("Student Guardian", filters={"parent": student, "parenttype": "Student"}, pluck="guardian")
	if not guardians:
		return False
	siblings = set(
		frappe.get_all(
			"Student Guardian",
			filters={"guardian": ["in", guardians], "parenttype": "Student", "parent": ["!=", student]},
			pluck="parent",
		)
	)
	year = current_year(student)
	for sibling in siblings:
		if born_earlier(sibling, dob) and on_roll(sibling, year):
			return True
	return False


def current_year(student):
	return frappe.db.get_value(
		"Program Enrollment", {"student": student, "docstatus": 1}, "academic_year", order_by="enrollment_date desc, creation desc"
	)


def born_earlier(sibling, dob):
	row = frappe.db.get_value("Student", sibling, ["enabled", "date_of_birth"], as_dict=True)
	return bool(row and row.enabled and row.date_of_birth and getdate(row.date_of_birth) < getdate(dob))


def on_roll(student, academic_year):
	"""Still studying here in `academic_year`: no TC or leaving date, campus status on roll (or not yet tracked),
	and a submitted enrollment for that year."""
	from campus.student_services.lifecycle_rules import ON_ROLL

	row = frappe.db.get_value("Student", student, ["date_of_leaving", "leaving_certificate_number", "oc_academic_status"], as_dict=True)
	if not row or row.date_of_leaving or row.leaving_certificate_number:
		return False
	if row.oc_academic_status and row.oc_academic_status not in ON_ROLL:
		return False
	return bool(academic_year and frappe.db.exists("Program Enrollment", {"student": student, "academic_year": academic_year, "docstatus": 1}))


def apply_sibling_discount(doc, method=None):
	"""Sales Invoice before_validate: set the concession on a draft fee invoice of a younger sibling."""
	if doc.docstatus != 0 or not doc.get("student") or flt(doc.get("additional_discount_percentage")):
		return
	percent = flt(frappe.db.get_single_value("School Settings", "sibling_discount_percent"))
	if percent and has_elder_sibling(doc.student):
		doc.additional_discount_percentage = percent
		doc.apply_discount_on = doc.get("apply_discount_on") or "Grand Total"
