"""Attendance for the last school days (and today), Quarterly marks for Std VI to X, attendance on the report cards."""

import random

import frappe
from frappe.utils import add_days, getdate, nowdate

from onebook_school.demo.classes import CLASSES, SUBJECTS, group_name, sections_of
from onebook_school.demo.school import YEAR

MARKS_CLASSES = ("Std VI", "Std VII", "Std VIII", "Std IX", "Std X")
DAYS = 6


def school_days():
	days, day = [], getdate(nowdate())
	while len(days) < DAYS:
		if day.weekday() < 6:  # Monday to Saturday
			days.append(day)
		day = add_days(day, -1)
	return days


def load(ctx):
	rng = random.Random(ctx.seed + 11)
	groups = [group_name(cls, sec) for cls in CLASSES for sec in sections_of(cls, ctx.scale)]
	attendance(ctx, rng, groups)
	marks(ctx, rng)
	attendance_on_cards()


def attendance(ctx, rng, groups):
	ability = {}
	for day in school_days():
		for group in groups:
			for s in frappe.get_all("Student Group Student", filters={"parent": group, "active": 1}, fields=["student", "student_name"]):
				if frappe.db.exists("Student Attendance", {"student": s.student, "date": day, "docstatus": 1}):
					continue
				regular = ability.setdefault(s.student, rng.random())
				absent = rng.random() < (0.2 if regular < 0.08 else 0.04)
				doc = frappe.get_doc(
					{"doctype": "Student Attendance", "student": s.student, "student_name": s.student_name, "date": day,
					 "student_group": group, "status": "Absent" if absent else "Present"}
				)  # fmt: skip
				doc.flags.ignore_permissions = True
				doc.flags.attendance_correction = True  # historical back-fill, as when a school's old registers are migrated
				doc.insert()
				doc.submit()
				ctx.made()


def marks(ctx, rng):
	skill = {}
	for cls in MARKS_CLASSES:
		for sec in sections_of(cls, ctx.scale):
			group = group_name(cls, sec)
			for subject in SUBJECTS[cls]:
				if frappe.db.exists("Mark Entry", {"student_group": group, "course": subject, "exam": "Quarterly", "docstatus": 1}):
					continue
				entry = frappe.get_doc(
					{"doctype": "Mark Entry", "academic_year": YEAR, "exam": "Quarterly", "student_group": group, "course": subject, "max_marks": 100}
				)
				entry.get_students()
				for row in entry.rows:
					base = skill.setdefault(row.student, rng.gauss(72, 13))
					row.absent = 1 if rng.random() < 0.01 else 0
					row.marks = 0 if row.absent else max(18, min(100, round(rng.gauss(base, 7))))
				entry.flags.ignore_permissions = True
				entry.insert()
				entry.submit()
				ctx.made()


def attendance_on_cards():
	for card in frappe.get_all("Report Card", filters={"academic_year": YEAR}, fields=["name", "student"]):
		total = frappe.db.count("Student Attendance", {"student": card.student, "docstatus": 1})
		present = frappe.db.count("Student Attendance", {"student": card.student, "docstatus": 1, "status": "Present"})
		if total:
			frappe.db.set_value("Report Card", card.name, "attendance_percent", round(present * 100 / total, 1))
