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
