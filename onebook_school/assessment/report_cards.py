"""Report Card upkeep: a submitted Mark Entry writes its subject row onto each student's card for the exam."""

import frappe
from frappe.utils import flt

from onebook_school.assessment.grading import ABSENT, grade_for


def card_for(student, academic_year, exam, student_group=None, roll_no=None):
	name = frappe.db.get_value("Report Card", {"student": student, "academic_year": academic_year, "exam": exam})
	if name:
		return frappe.get_doc("Report Card", name)
	return frappe.get_doc(
		{"doctype": "Report Card", "student": student, "academic_year": academic_year, "exam": exam,
		 "student_group": student_group, "roll_no": roll_no}
	)  # fmt: skip


def post_marks(entry):
	for row in entry.rows:
		card = card_for(row.student, entry.academic_year, entry.exam, entry.student_group, row.roll_no)
		card.set("subjects", [s for s in card.subjects if s.course != entry.course])
		percent = flt(row.marks) * 100 / flt(entry.max_marks) if not row.absent else 0
		card.append(
			"subjects",
			{"course": entry.course, "max_marks": entry.max_marks, "marks": 0 if row.absent else flt(row.marks),
			 "absent": row.absent, "grade": ABSENT if row.absent else grade_for(percent), "mark_entry": entry.name},
		)  # fmt: skip
		recompute(card)
		card.flags.ignore_permissions = True
		card.save()


def withdraw_marks(entry):
	for row in entry.rows:
		name = frappe.db.get_value("Report Card", {"student": row.student, "academic_year": entry.academic_year, "exam": entry.exam})
		if not name:
			continue
		card = frappe.get_doc("Report Card", name)
		card.set("subjects", [s for s in card.subjects if s.mark_entry != entry.name])
		recompute(card)
		card.flags.ignore_permissions = True
		card.save()


def recompute(card):
	card.total = sum(flt(s.marks) for s in card.subjects)
	card.max_total = sum(flt(s.max_marks) for s in card.subjects)
	card.percentage = flt(card.total * 100 / card.max_total, 2) if card.max_total else 0
	card.overall_grade = grade_for(card.percentage) if card.subjects else ""
