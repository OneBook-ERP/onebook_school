from frappe.model.document import Document
from frappe.utils import flt

from onebook_school.assessment.grading import ABSENT, grade_for
from onebook_school.assessment.report_cards import recompute


class ReportCard(Document):
	def validate(self):
		for row in self.subjects:
			if row.absent:
				row.marks, row.grade = 0, ABSENT
			elif flt(row.max_marks):
				row.grade = grade_for(flt(row.marks) * 100 / flt(row.max_marks))
		recompute(self)
