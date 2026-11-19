"""Cover for absent teachers: their periods today are uncovered until the principal gives each one to a free teacher.

A teacher is away when HR attendance for their Employee today says Absent or On Leave. A suggested cover teacher is
not away and has no class (timetable or another cover) in that period; same-subject teachers come first, then the
lightest day.
"""

import frappe
from frappe import _
from frappe.utils import cint, getdate

from onebook_school.school_day.timetable import slots_for

AWAY = ("Absent", "On Leave")


def weekday_of(date):
	return getdate(date).strftime("%A")


def away_instructors(date):
	employees = frappe.get_all("Attendance", filters={"attendance_date": date, "docstatus": 1, "status": ["in", AWAY]}, pluck="employee")
	if not employees:
		return set()
	return set(frappe.get_all("Instructor", filters={"employee": ["in", employees]}, pluck="name"))


def covers_on(date):
	rows = frappe.get_all("Cover Assignment", filters={"date": date}, fields=["period_no", "student_group", "cover_instructor", "course"])
	return {(r.student_group, r.period_no): r for r in rows}


def uncovered(date):
	away = away_instructors(date)
	if not away:
		return []
	covered = covers_on(date)
	rows = []
	for slot in slots_for(weekday=weekday_of(date)):
		if slot["instructor"] in away and (slot["student_group"], slot["period_no"]) not in covered:
			rows.append(dict(slot, absent_instructor=slot["instructor"]))
	return sorted(rows, key=lambda r: (r["period_no"], r["student_group"]))


@frappe.whitelist()
def suggest_cover(date, period_no, student_group):
	frappe.has_permission("Cover Assignment", "create", throw=True)
	return suggest(date, period_no, student_group)[:8]


def suggest(date, period_no, student_group):
	period_no = cint(period_no)
	weekday = weekday_of(date)
	day = slots_for(weekday=weekday)
	slot = next((s for s in day if s["student_group"] == student_group and s["period_no"] == period_no), None)
	subject = slot["course"] if slot else None
	covers = covers_on(date)
	busy = {s["instructor"] for s in day if s["period_no"] == period_no}
	busy |= {c.cover_instructor for (g, p), c in covers.items() if p == period_no}
	away = away_instructors(date)
	load = {}
	for s in day:
		load[s["instructor"]] = load.get(s["instructor"], 0) + 1
	for c in covers.values():
		load[c.cover_instructor] = load.get(c.cover_instructor, 0) + 1
	teaches = {}
	for a in frappe.get_all("Teaching Assignment", fields=["instructor", "course"]):
		teaches.setdefault(a.instructor, set()).add(a.course)
	rows = []
	for inst in frappe.get_all("Instructor", filters={"status": "Active"}, fields=["name", "instructor_name"]):
		if inst.name in busy or inst.name in away:
			continue
		rows.append({"instructor": inst.name, "instructor_name": inst.instructor_name,
					 "same_subject": bool(subject and subject in teaches.get(inst.name, ())), "load_today": load.get(inst.name, 0)})  # fmt: skip
	return sorted(rows, key=lambda r: (not r["same_subject"], r["load_today"], r["instructor_name"] or ""))


@frappe.whitelist()
def assign(date, period_no, student_group, cover_instructor):
	frappe.has_permission("Cover Assignment", "create", throw=True)
	period_no = cint(period_no)
	if cover_instructor not in {s["instructor"] for s in suggest(date, period_no, student_group)}:
		frappe.throw(_("{0} is away or already teaching in period {1}.").format(cover_instructor, period_no))
	slot = next((s for s in slots_for(student_group=student_group, weekday=weekday_of(date)) if s["period_no"] == period_no), {})
	doc = frappe.get_doc(
		{"doctype": "Cover Assignment", "date": date, "period_no": period_no, "student_group": student_group,
		 "course": slot.get("course"), "absent_instructor": slot.get("instructor"), "cover_instructor": cover_instructor}
	)  # fmt: skip
	doc.insert(ignore_permissions=True)
	return doc.name
