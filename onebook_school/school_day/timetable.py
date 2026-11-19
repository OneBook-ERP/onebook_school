"""The school timetable: section x weekday x period -> subject and teacher, generated from Teaching Assignments.

Greedy and clash-free: the biggest assignments are placed first, each spread across the week (one period a day before
a second), and a slot is used only when both its section and its teacher are free. What does not fit is reported, never
forced in.
"""

import frappe

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def teaching_periods():
	rows = frappe.get_all(
		"School Period", filters={"parent": "School Settings", "is_break": 0}, fields=["period_no", "label", "start_time", "end_time"], order_by="period_no"
	)
	return [dict(r) for r in rows]


def generate(student_groups=None):
	filters = {"student_group": ["in", student_groups]} if student_groups else {}
	assignments = frappe.get_all(
		"Teaching Assignment", filters=filters, fields=["student_group", "course", "instructor", "periods_per_week"],
		order_by="periods_per_week desc, student_group, course",
	)  # fmt: skip
	groups = student_groups or sorted({a.student_group for a in assignments})
	frappe.db.delete("Timetable Slot", {"student_group": ["in", groups]} if groups else {"name": ""})
	periods = [p["period_no"] for p in teaching_periods()]
	section_busy, teacher_busy = set(), busy_elsewhere(groups)
	placed, unplaced = 0, []
	for a in assignments:
		left = a.periods_per_week
		for weekday, period in spread(periods, a):
			if left == 0:
				break
			if (a.student_group, weekday, period) in section_busy or (a.instructor, weekday, period) in teacher_busy:
				continue
			if not frappe.db.exists("Timetable Slot", {"student_group": a.student_group, "weekday": weekday, "period_no": period}):
				frappe.get_doc(
					{"doctype": "Timetable Slot", "student_group": a.student_group, "weekday": weekday, "period_no": period,
					 "course": a.course, "instructor": a.instructor}
				).insert(ignore_permissions=True)  # fmt: skip
			section_busy.add((a.student_group, weekday, period))
			teacher_busy.add((a.instructor, weekday, period))
			placed += 1
			left -= 1
		if left:
			unplaced.append({"student_group": a.student_group, "course": a.course, "instructor": a.instructor, "periods": left})
	return {"placed": placed, "unplaced": unplaced}


def spread(periods, assignment):
	"""Candidate slots, one round of the week at a time, each round starting on a different period."""
	offset = sum(map(ord, f"{assignment.student_group}{assignment.course}")) % max(len(periods), 1)
	for round_no in range(len(periods)):
		for d, weekday in enumerate(WEEKDAYS):
			yield weekday, periods[(offset + round_no + d) % len(periods)]


def busy_elsewhere(groups):
	"""Teacher slots already taken by sections this run does not regenerate."""
	rows = frappe.get_all("Timetable Slot", filters={"student_group": ["not in", groups or [""]]}, fields=["instructor", "weekday", "period_no"])
	return {(r.instructor, r.weekday, r.period_no) for r in rows}


def slots_for(instructor=None, student_group=None, weekday=None):
	filters = {}
	if instructor:
		filters["instructor"] = instructor
	if student_group:
		filters["student_group"] = student_group
	if weekday:
		filters["weekday"] = weekday
	rows = frappe.get_all(
		"Timetable Slot", filters=filters, fields=["name", "student_group", "weekday", "period_no", "course", "instructor", "instructor_name"],
		order_by="weekday, period_no",
	)  # fmt: skip
	return [dict(r) for r in rows]
