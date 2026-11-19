import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate

from onebook_school.dashboard import present_today
from onebook_school.tests import fixtures as fx


def mark(student, status, group):
	doc = frappe.get_doc({"doctype": "Student Attendance", "student": student, "date": nowdate(), "status": status, "student_group": group})
	doc.insert(ignore_permissions=True)
	doc.submit()


class TestDashboard(FrappeTestCase):
	def setUp(self):
		fx.holiday_list()
		frappe.defaults.set_user_default("company", fx.company())

	def tearDown(self):
		frappe.defaults.clear_user_default("company")

	def test_present_today_percent(self):
		frappe.db.delete("Student Attendance", {"date": nowdate()})
		tag = frappe.generate_hash(length=4)
		students = [fx.student(f"Att{tag}{i}", "2016-01-0" + str(i + 1)) for i in range(4)]
		group = fx.section(f"OBS VI {tag} A", "OBS Std VI", students)
		for student, status in zip(students, ["Present", "Present", "Present", "Absent"]):
			mark(student, status, group)
		card = present_today()
		self.assertEqual(card["value"], 75.0)
		self.assertEqual(card["fieldtype"], "Percent")

	def test_present_today_no_attendance(self):
		frappe.db.delete("Student Attendance", {"date": nowdate()})
		self.assertEqual(present_today()["value"], 0)


class TestLearningNumbers(FrappeTestCase):
	def test_pass_percentage_counts_a_card_with_any_subject_below_35_as_fail(self):
		from onebook_school.dashboard import pass_percentage

		frappe.db.delete("Report Card")
		tag = frappe.generate_hash(length=4)
		passed = fx.student(f"Pass{tag}", "2015-01-01")
		failed = fx.student(f"Fail{tag}", "2015-02-02")
		absent = fx.student(f"Away{tag}", "2015-03-03")
		for student, rows in ((passed, [(80, 0), (35, 0)]), (failed, [(90, 0), (34, 0)]), (absent, [(70, 0), (0, 1)])):
			frappe.get_doc(
				{"doctype": "Report Card", "student": student, "academic_year": fx.academic_year(), "exam": "Quarterly",
				 "subjects": [{"course": fx.course(f"OBS Subj{i}"), "max_marks": 100, "marks": m, "absent": a} for i, (m, a) in enumerate(rows)]}
			).insert(ignore_permissions=True)  # fmt: skip
		self.assertEqual(pass_percentage()["value"], 33.3)

	def test_students_per_teacher(self):
		from onebook_school.dashboard import students_per_teacher

		students = frappe.db.count("Student", {"enabled": 1})
		teachers = frappe.db.count("Instructor", {"status": "Active"})
		expected = f"{round(students / teachers, 1):g} : 1" if teachers else "-"
		self.assertEqual(students_per_teacher()["value"], expected)
		self.assertEqual(students_per_teacher()["fieldtype"], "Data")
