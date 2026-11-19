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
