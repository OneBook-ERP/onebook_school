import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate, nowdate

from onebook_school.school_day import cover, timetable
from onebook_school.school_day.today import build
from onebook_school.tests import fixtures as fx


def section(payload, key):
	return next((s for s in payload["sections"] if s["key"] == key), None)


class TestToday(FrappeTestCase):
	def setUp(self):
		fx.periods(4)
		tag = frappe.generate_hash(length=4)
		self.today = nowdate()
		self.weekday = getdate(self.today).strftime("%A")
		self.group = fx.section(f"OBS TD {tag} A", "OBS Std VIII", [])
		self.mine = fx.instructor(f"Mine T {tag}")
		self.absent = fx.instructor(f"Gone T {tag}")
		fx.assignment(self.group, "OBS English", self.mine, 6)
		other = fx.section(f"OBS TD {tag} B", "OBS Std VIII", [])
		fx.assignment(other, "OBS History", self.absent, 6)
		timetable.generate([self.group, other])
		self.other = other
		self.teacher_user = fx.user(f"t{tag}@obs-test.example.com", ["Instructor"])
		frappe.db.set_value("Employee", fx.employee_for(self.mine), "user_id", self.teacher_user)
		self.principal_user = fx.user(f"p{tag}@obs-test.example.com", ["School Principal"])
		fx.mark_staff(self.absent, "Absent")

	def test_teacher_sees_own_periods_and_cover(self):
		if not timetable.slots_for(instructor=self.absent, weekday=self.weekday):
			self.skipTest("no school today")
		slot = timetable.slots_for(instructor=self.absent, weekday=self.weekday)[0]
		if self.mine in [s["instructor"] for s in cover.suggest(self.today, slot["period_no"], self.other)]:
			cover.assign(self.today, slot["period_no"], self.other, self.mine)
		payload = build(self.teacher_user)
		periods = section(payload, "now_next")
		self.assertIsNotNone(periods)
		texts = " ".join(i["text"] for i in periods["items"])
		self.assertIn(self.group, texts)
		if frappe.db.exists("Cover Assignment", {"date": self.today, "cover_instructor": self.mine}):
			self.assertIn("cover", texts.lower())

	def test_principal_sees_uncovered_periods(self):
		if not timetable.slots_for(instructor=self.absent, weekday=self.weekday):
			self.skipTest("no school today")
		attention = section(build(self.principal_user), "attention")
		self.assertIsNotNone(attention)
		covers = [i for i in attention["items"] if (i.get("action") or {}).get("kind") == "cover"]
		self.assertTrue(any(i["action"]["args"]["student_group"] == self.other for i in covers))

	def test_user_without_instructor_gets_no_teacher_section(self):
		payload = build(self.principal_user)
		self.assertIsNone(section(payload, "now_next"))
		self.assertTrue(payload["greeting"])
