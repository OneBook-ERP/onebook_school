import frappe
from frappe.tests.utils import FrappeTestCase

from onebook_school.school_day import timetable
from onebook_school.tests import fixtures as fx


class TestTimetable(FrappeTestCase):
	def setUp(self):
		fx.periods(4)  # 4 teaching periods x 6 days = 24 slots per section
		tag = frappe.generate_hash(length=4)
		self.a = fx.section(f"OBS TT {tag} A", "OBS Std VI", [])
		self.b = fx.section(f"OBS TT {tag} B", "OBS Std VI", [])
		self.shared = fx.instructor(f"Shared Teacher {tag}")
		self.other = fx.instructor(f"Other Teacher {tag}")
		fx.assignment(self.a, "OBS Maths", self.shared, 6)
		fx.assignment(self.b, "OBS Maths", self.shared, 6)
		fx.assignment(self.a, "OBS Tamil", self.other, 5)
		self.groups = [self.a, self.b]

	def test_teaching_periods_skip_breaks(self):
		self.assertEqual([p["period_no"] for p in timetable.teaching_periods()], [1, 2, 4, 5])

	def test_generate_places_every_period_without_clash(self):
		result = timetable.generate(self.groups)
		self.assertEqual(result["unplaced"], [])
		slots = timetable.slots_for(instructor=self.shared)
		self.assertEqual(len(slots), 12)
		self.assertEqual(len({(s["weekday"], s["period_no"]) for s in slots}), 12)
		self.assertEqual(len(timetable.slots_for(student_group=self.a)), 11)

	def test_overfull_assignment_reports_unplaced(self):
		fx.assignment(self.b, "OBS Science", self.other, 30)
		result = timetable.generate(self.groups)
		self.assertTrue(result["unplaced"])
		for teacher in (self.shared, self.other):
			slots = timetable.slots_for(instructor=teacher)
			self.assertEqual(len(slots), len({(s["weekday"], s["period_no"]) for s in slots}))

	def test_regenerate_replaces_slots(self):
		timetable.generate(self.groups)
		timetable.generate(self.groups)
		self.assertEqual(len(timetable.slots_for(student_group=self.b)), 6)
