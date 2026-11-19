import frappe
from frappe.tests.utils import FrappeTestCase

from onebook_school.assessment.grading import grade_for
from onebook_school.tests import fixtures as fx

EXAM = "Quarterly"


def mark_entry(group, course, marks, absent=(), max_marks=100):
	doc = frappe.get_doc(
		{"doctype": "Mark Entry", "academic_year": fx.academic_year(), "exam": EXAM, "student_group": group,
		 "course": fx.course(course), "max_marks": max_marks}
	)  # fmt: skip
	doc.get_students()
	for row in doc.rows:
		row.marks = marks.get(row.student, 0)
		row.absent = 1 if row.student in absent else 0
	return doc


class TestReportCard(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		tag = frappe.generate_hash(length=4)
		cls.a = fx.student(f"Mathi{tag}", "2015-02-02", "OBS Std IX")
		cls.b = fx.student(f"Ezhil{tag}", "2015-03-03", "OBS Std IX")
		cls.group = fx.section(f"OBS IX {tag} A", "OBS Std IX", [cls.a, cls.b])

	def test_grade_boundaries(self):
		self.assertEqual(grade_for(100), "A1")
		self.assertEqual(grade_for(91), "A1")
		self.assertEqual(grade_for(90), "A2")
		self.assertEqual(grade_for(71), "B1")
		self.assertEqual(grade_for(35), "D")
		self.assertEqual(grade_for(34.9), "E")
		self.assertEqual(grade_for(0), "E")

	def test_get_students_in_roll_order(self):
		doc = mark_entry(self.group, "OBS Tamil", {})
		self.assertEqual([r.student for r in doc.rows], [self.a, self.b])

	def test_marks_above_max_refused(self):
		doc = mark_entry(self.group, "OBS English", {self.a: 101})
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_absent_counts_zero_shows_ab(self):
		mark_entry(self.group, "OBS Maths", {self.a: 88, self.b: 50}, absent=[self.b]).insert().submit()
		card = frappe.get_doc("Report Card", {"student": self.b, "academic_year": fx.YEAR, "exam": EXAM})
		row = next(r for r in card.subjects if r.course == "OBS Maths")
		self.assertEqual(row.marks, 0)
		self.assertTrue(row.absent)
		self.assertEqual(row.grade, "AB")

	def test_submit_builds_report_card_totals(self):
		mark_entry(self.group, "OBS Science", {self.a: 92, self.b: 40}).insert().submit()
		mark_entry(self.group, "OBS Social Science", {self.a: 78, self.b: 61}).insert().submit()
		card = frappe.get_doc("Report Card", {"student": self.a, "academic_year": fx.YEAR, "exam": EXAM})
		science = next(r for r in card.subjects if r.course == "OBS Science")
		self.assertEqual(science.grade, "A1")
		subjects = {r.course for r in card.subjects}
		self.assertTrue({"OBS Science", "OBS Social Science"} <= subjects)
		self.assertEqual(card.max_total, 100 * len(card.subjects))
		self.assertAlmostEqual(card.percentage, card.total * 100 / card.max_total, places=2)
		self.assertEqual(card.overall_grade, grade_for(card.percentage))

	def test_second_subject_updates_same_card(self):
		mark_entry(self.group, "OBS Computer", {self.a: 70}).insert().submit()
		count = frappe.db.count("Report Card", {"student": self.a, "academic_year": fx.YEAR, "exam": EXAM})
		self.assertEqual(count, 1)

	def test_resubmitting_a_subject_replaces_its_marks(self):
		first = mark_entry(self.group, "OBS Hindi", {self.a: 40}).insert().submit()
		first.cancel()
		mark_entry(self.group, "OBS Hindi", {self.a: 60}).insert().submit()
		card = frappe.get_doc("Report Card", {"student": self.a, "academic_year": fx.YEAR, "exam": EXAM})
		rows = [r for r in card.subjects if r.course == "OBS Hindi"]
		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0].marks, 60)

	def test_blank_marks_refused_on_submit(self):
		doc = mark_entry(self.group, "OBS Art", {self.a: 50})
		doc.rows[1].marks = None
		doc.insert()
		with self.assertRaises(frappe.ValidationError):
			doc.submit()

	def test_zero_max_marks_refused(self):
		with self.assertRaises(frappe.ValidationError):
			mark_entry(self.group, "OBS Music", {self.a: 0, self.b: 0}, max_marks=0).insert()

	def test_card_recomputes_when_edited(self):
		mark_entry(self.group, "OBS Physics", {self.a: 50, self.b: 50}).insert().submit()
		card = frappe.get_doc("Report Card", {"student": self.a, "academic_year": fx.YEAR, "exam": EXAM})
		row = next(r for r in card.subjects if r.course == "OBS Physics")
		row.marks = 90
		card.save()
		self.assertEqual(card.total, sum(r.marks for r in card.subjects))
		self.assertEqual(row.grade, "A2")
