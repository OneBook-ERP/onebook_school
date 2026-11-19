import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate

from onebook_school.school_day.exams import upcoming
from onebook_school.tests import fixtures as fx


class TestExamSchedule(FrappeTestCase):
	def setUp(self):
		frappe.db.delete("Exam Schedule")
		frappe.db.delete("Exam Schedule Paper")
		frappe.get_doc(
			{"doctype": "Exam Schedule", "academic_year": fx.academic_year(), "exam": "Half Yearly",
			 "papers": [
				 {"program": fx.program("OBS Std VI"), "course": fx.course("OBS Maths"), "exam_date": add_days(nowdate(), 10), "start_time": "10:00:00", "end_time": "12:30:00"},
				 {"program": fx.program("OBS Std VI"), "course": fx.course("OBS Tamil"), "exam_date": add_days(nowdate(), 5), "start_time": "10:00:00", "end_time": "12:30:00"},
				 {"program": fx.program("OBS Std VII"), "course": fx.course("OBS Tamil"), "exam_date": add_days(nowdate(), 6), "start_time": "10:00:00", "end_time": "12:30:00"},
				 {"program": fx.program("OBS Std VI"), "course": fx.course("OBS Science"), "exam_date": add_days(nowdate(), 40), "start_time": "10:00:00", "end_time": "12:30:00"},
			 ]}
		).insert(ignore_permissions=True)  # fmt: skip

	def test_upcoming_in_window_sorted(self):
		rows = upcoming(days=30)
		self.assertEqual([r["course"] for r in rows], ["OBS Tamil", "OBS Tamil", "OBS Maths"])
		self.assertEqual(rows[0]["exam"], "Half Yearly")

	def test_upcoming_filters_programs(self):
		rows = upcoming(days=30, programs=["OBS Std VII"])
		self.assertEqual([(r["program"], r["course"]) for r in rows], [("OBS Std VII", "OBS Tamil")])
