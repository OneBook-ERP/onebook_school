import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from onebook_school.assessment import report_cards


class MarkEntry(Document):
	@frappe.whitelist()
	def get_students(self):
		"""Fill rows with the section's active students in roll order (marks kept for students already listed)."""
		kept = {r.student: r for r in self.rows}
		group = frappe.get_doc("Student Group", self.student_group)
		group.check_permission("read")
		self.set("rows", [])
		for s in sorted((s for s in group.students if s.active), key=lambda s: (s.group_roll_number or 0, s.student_name or "")):
			old = kept.get(s.student)
			self.append(
				"rows",
				{"student": s.student, "student_name": s.student_name, "roll_no": s.group_roll_number,
				 "marks": old.marks if old else None, "absent": old.absent if old else 0},
			)  # fmt: skip

	def validate(self):
		self.title = f"{self.student_group} · {self.course} · {self.exam}"
		if flt(self.max_marks) <= 0:
			frappe.throw(_("Maximum marks must be more than 0."))
		if not self.rows:
			self.get_students()
		for row in self.rows:
			if row.absent:
				row.marks = 0
			elif flt(row.marks) < 0 or flt(row.marks) > flt(self.max_marks):
				frappe.throw(
					_("Row {0}: {1} has {2} marks; the maximum is {3}.").format(row.idx, row.student_name, row.marks, self.max_marks)
				)

	def before_submit(self):
		blank = [r.student_name or r.student for r in self.rows if not r.absent and r.marks in (None, "")]
		if blank:
			frappe.throw(_("Enter marks or tick Absent for: {0}").format(", ".join(blank)))

	def on_submit(self):
		report_cards.post_marks(self)

	def on_cancel(self):
		report_cards.withdraw_marks(self)
