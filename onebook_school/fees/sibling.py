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
	for sibling in siblings:
		row = frappe.db.get_value("Student", sibling, ["enabled", "date_of_birth"], as_dict=True)
		if not (row and row.enabled and row.date_of_birth and getdate(row.date_of_birth) < getdate(dob)):
			continue
		if frappe.db.exists("Program Enrollment", {"student": sibling, "docstatus": 1}):
			return True
	return False


def apply_sibling_discount(doc, method=None):
	"""Sales Invoice before_validate: set the concession on a draft fee invoice of a younger sibling."""
	if doc.docstatus != 0 or not doc.get("student") or flt(doc.get("additional_discount_percentage")):
		return
	percent = flt(frappe.db.get_single_value("School Settings", "sibling_discount_percent"))
	if percent and has_elder_sibling(doc.student):
		doc.additional_discount_percentage = percent
		doc.apply_discount_on = doc.get("apply_discount_on") or "Grand Total"
