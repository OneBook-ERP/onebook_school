import frappe
from frappe.tests.utils import FrappeTestCase

from onebook_school.compliance.udise import student_issues
from onebook_school.onebook_school.report.udise_student_export.udise_student_export import execute
from onebook_school.tests import fixtures as fx

COMPLETE = {
	"date_of_birth": "2015-01-01", "gender": "Female", "father_name": "Raman", "mother_name": "Lakshmi",
	"social_category": "BC", "emis_id": "3311223344556677", "pen": "12345678901", "apaar_consent": "Given",
}  # fmt: skip


class TestUdiseExport(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		tag = frappe.generate_hash(length=4)
		cls.ready = fx.student(f"Ready{tag}", "2014-04-04", "OBS Std X")
		frappe.db.set_value("Student", cls.ready, {"gender": "Female", "obs_social_category": "BC", "obs_emis_id": "33" + tag, "obs_pen": "1" + tag, "obs_apaar_consent": "Given"})
		fx.guardian(f"Father {tag}", [cls.ready])
		cls.gaps = fx.student(f"Gaps{tag}", "2014-05-05", "OBS Std X")
		frappe.db.set_value("Student", cls.gaps, "date_of_birth", None)
		cls.group_a = fx.section(f"OBS X {tag} A", "OBS Std X", [cls.ready, cls.gaps])
		cls.other = fx.student(f"Other{tag}", "2014-06-06", "OBS Std X")
		cls.group_b = fx.section(f"OBS X {tag} B", "OBS Std X", [cls.other])

	def test_complete_student_has_no_issues(self):
		self.assertEqual(student_issues(COMPLETE), [])

	def test_missing_fields_named(self):
		issues = student_issues(dict(COMPLETE, date_of_birth=None, father_name=None, mother_name=None, pen=""))
		self.assertIn("Date of Birth", issues)
		self.assertIn("Father's or Mother's Name", issues)
		self.assertIn("PEN", issues)
		self.assertNotIn("Gender", issues)

	def test_filters_by_section(self):
		columns, rows = execute({"academic_year": fx.YEAR, "student_group": self.group_a})[:2]
		names = {r["student"] for r in rows}
		self.assertEqual(names, {self.ready, self.gaps})
		gaps = next(r for r in rows if r["student"] == self.gaps)
		self.assertIn("Date of Birth", gaps["issues"])
		self.assertIn("Father's or Mother's Name", gaps["issues"])
		labels = [c["label"] for c in columns]
		self.assertEqual(labels[0], "UDISE Code")
		self.assertEqual(labels[-1], "Issues")
