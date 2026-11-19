import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, nowdate

from onebook_school.school_day import cover, timetable
from onebook_school.tests import fixtures as fx


class TestCover(FrappeTestCase):
	def setUp(self):
		fx.periods(4)
		tag = frappe.generate_hash(length=4)
		self.today = nowdate()
		self.weekday = getdate(self.today).strftime("%A")
		self.a = fx.section(f"OBS CV {tag} A", "OBS Std VII", [])
		self.b = fx.section(f"OBS CV {tag} B", "OBS Std VII", [])
		self.absent = fx.instructor(f"Absent T {tag}")
		self.maths = fx.instructor(f"Maths T {tag}")
		self.free = fx.instructor(f"Free T {tag}")
		self.away = fx.instructor(f"Away T {tag}")
		fx.assignment(self.a, "OBS Maths", self.absent, 6)  # one Maths period every day in A
		fx.assignment(self.b, "OBS Maths", self.maths, 6)
		fx.assignment(self.b, "OBS Art", self.free, 1)
		fx.assignment(self.b, "OBS Music", self.away, 1)
		timetable.generate([self.a, self.b])
		fx.mark_staff(self.absent, "Absent")
		fx.mark_staff(self.away, "On Leave")
		mine = [s for s in timetable.slots_for(instructor=self.absent, weekday=self.weekday)]
		self.slot = mine[0] if mine else None

	def test_absent_teachers_periods_are_uncovered(self):
		if not self.slot:
			self.skipTest("no school today")
		rows = [r for r in cover.uncovered(self.today) if r["student_group"] == self.a]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["absent_instructor"], self.absent)

	def test_suggest_excludes_away_and_busy(self):
		if not self.slot:
			self.skipTest("no school today")
		names = [s["instructor"] for s in cover.suggest(self.today, self.slot["period_no"], self.a)]
		self.assertNotIn(self.absent, names)
		self.assertNotIn(self.away, names)
		busy = {s["instructor"] for s in timetable.slots_for(weekday=self.weekday) if s["period_no"] == self.slot["period_no"]}
		self.assertFalse(busy & set(names))

	def test_suggest_prefers_same_subject(self):
		if not self.slot:
			self.skipTest("no school today")
		suggestions = cover.suggest(self.today, self.slot["period_no"], self.a)
		maths_free = self.maths not in {s["instructor"] for s in timetable.slots_for(weekday=self.weekday) if s["period_no"] == self.slot["period_no"]}
		if maths_free:
			flags = [s["same_subject"] for s in suggestions]
			self.assertTrue(flags[0])
			self.assertEqual(flags, sorted(flags, reverse=True))  # every same-subject teacher before any other
			self.assertIn(self.maths, [s["instructor"] for s in suggestions if s["same_subject"]])

	def test_assign_covers_the_period(self):
		if not self.slot:
			self.skipTest("no school today")
		teacher = cover.suggest(self.today, self.slot["period_no"], self.a)[0]["instructor"]
		cover.assign(self.today, self.slot["period_no"], self.a, teacher)
		self.assertFalse([r for r in cover.uncovered(self.today) if r["student_group"] == self.a])
		self.assertNotIn(teacher, [s["instructor"] for s in cover.suggest(self.today, self.slot["period_no"], self.b)])

	def test_assign_refuses_busy_teacher(self):
		if not self.slot:
			self.skipTest("no school today")
		with self.assertRaises(frappe.ValidationError):
			cover.assign(self.today, self.slot["period_no"], self.a, self.away)
