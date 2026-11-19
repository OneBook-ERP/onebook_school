import frappe
from frappe.tests.utils import FrappeTestCase

from onebook_school.fees.fee_cap import approved_amounts
from onebook_school.tests import fixtures as fx

PROGRAM = "OBS Std VI"


def committee_order(lines, program=PROGRAM, valid_from=fx.YEAR, valid_to=fx.NEXT_YEAR, submit=True):
	order = frappe.get_doc(
		{
			"doctype": "Fee Committee Order",
			"company": fx.company(),
			"order_number": frappe.generate_hash(length=8),
			"order_date": "2031-05-01",
			"valid_from_year": fx.academic_year(valid_from),
			"valid_to_year": fx.academic_year(fx.NEXT_YEAR, "2032-06-01", "2033-04-30") if valid_to == fx.NEXT_YEAR else valid_to,
			"lines": [
				{"program": fx.program(program), "fee_category": fx.fee_category(c), "approved_amount": a}
				for c, a in lines.items()
			],
		}
	).insert()
	if submit:
		order.submit()
	return order


class TestFeeCap(FrappeTestCase):
	def test_structure_within_cap_saves(self):
		committee_order({"Tuition": 20000, "Development": 3000})
		structure = fx.fee_structure(PROGRAM, {"Tuition": 20000, "Development": 2500}).insert()
		self.assertTrue(structure.name)

	def test_structure_over_cap_refused(self):
		committee_order({"Tuition": 20000})
		structure = fx.fee_structure(PROGRAM, {"Tuition": 21000})
		with self.assertRaises(frappe.ValidationError) as caught:
			structure.insert()
		message = str(caught.exception)
		self.assertIn("Tuition", message)
		self.assertIn("20,000", message)
		self.assertIn("21,000", message)

	def test_no_order_means_no_cap(self):
		structure = fx.fee_structure("OBS Std VII", {"Tuition": 99000}).insert()
		self.assertTrue(structure.name)
		self.assertEqual(approved_amounts(fx.company(), "OBS Std VII", fx.YEAR), {})

	def test_cancelled_order_ignored(self):
		order = committee_order({"Tuition": 15000}, program="OBS Std VIII")
		order.cancel()
		self.assertNotIn("Tuition", approved_amounts(fx.company(), "OBS Std VIII", fx.YEAR))
		self.assertEqual(approved_amounts(fx.company(), PROGRAM, "Unknown Year"), {})

	def test_term_structures_sum_against_year_cap(self):
		committee_order({"Tuition": 30000}, program="OBS Std XI")
		first = fx.fee_structure("OBS Std XI", {"Tuition": 15000})
		first.insert()
		first.submit()
		second = fx.fee_structure("OBS Std XI", {"Tuition": 16000})
		with self.assertRaises(frappe.ValidationError):
			second.insert()

	def test_draft_structure_does_not_count(self):
		committee_order({"Tuition": 30000}, program="OBS Std XII")
		fx.fee_structure("OBS Std XII", {"Tuition": 20000}).insert()
		self.assertTrue(fx.fee_structure("OBS Std XII", {"Tuition": 20000}).insert().name)

	def test_student_categories_counted_separately(self):
		committee_order({"Tuition": 30000}, program="OBS Std V")
		for category in ("OBS General", "OBS RTE"):
			if not frappe.db.exists("Student Category", category):
				frappe.get_doc({"doctype": "Student Category", "category": category}).insert(ignore_permissions=True)
			doc = fx.fee_structure("OBS Std V", {"Tuition": 20000})
			doc.student_category = category
			doc.insert()
			doc.submit()
