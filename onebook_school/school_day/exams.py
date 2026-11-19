"""Exam schedule: the papers coming up, for whoever they affect."""

import frappe
from frappe.utils import add_days, nowdate


def upcoming(days=30, programs=None):
	filters = {"parenttype": "Exam Schedule", "exam_date": ["between", [nowdate(), add_days(nowdate(), days)]]}
	if programs:
		filters["program"] = ["in", programs]
	rows = frappe.get_all(
		"Exam Schedule Paper", filters=filters, fields=["parent", "program", "course", "exam_date", "start_time", "end_time"],
		order_by="exam_date asc, start_time asc, program asc",
	)  # fmt: skip
	exams = {}
	for r in rows:
		r["exam"] = exams.setdefault(r.parent, frappe.db.get_value("Exam Schedule", r.parent, "exam"))
	return [dict(r) for r in rows]
