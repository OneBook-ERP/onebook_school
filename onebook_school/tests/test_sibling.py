import frappe
from frappe.tests.utils import FrappeTestCase

from onebook_school.fees.sibling import apply_sibling_discount, has_elder_sibling
from onebook_school.tests import fixtures as fx


def draft_invoice(student):
	return frappe.get_doc({"doctype": "Sales Invoice", "company": fx.company(), "student": student, "items": []})


class TestSiblingConcession(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		fx.school_settings(sibling_discount_percent=10)
		cls.elder = fx.student("Kavin", "2018-03-01")
		cls.younger = fx.student("Kaviya", "2020-07-15")
		fx.guardian("Senthil Kumar", [cls.elder, cls.younger])
		cls.only = fx.student("Nila", "2019-01-10")
		cls.left_elder = fx.student("Arul", "2017-05-05", enabled=0)
		cls.left_younger = fx.student("Arivu", "2019-09-09")
		fx.guardian("Murugesan", [cls.left_elder, cls.left_younger])

	def test_second_child_gets_discount(self):
		invoice = draft_invoice(self.younger)
		apply_sibling_discount(invoice)
		self.assertEqual(invoice.additional_discount_percentage, 10)

	def test_eldest_child_no_discount(self):
		invoice = draft_invoice(self.elder)
		apply_sibling_discount(invoice)
		self.assertFalse(invoice.additional_discount_percentage)
		self.assertFalse(has_elder_sibling(self.only))

	def test_elder_sibling_left_no_discount(self):
		self.assertFalse(has_elder_sibling(self.left_younger))
		invoice = draft_invoice(self.left_younger)
		apply_sibling_discount(invoice)
		self.assertFalse(invoice.additional_discount_percentage)

	def test_non_student_invoice_untouched(self):
		invoice = frappe.get_doc({"doctype": "Sales Invoice", "company": fx.company(), "items": []})
		apply_sibling_discount(invoice)
		self.assertFalse(invoice.additional_discount_percentage)

	def test_submitted_invoice_untouched(self):
		invoice = draft_invoice(self.younger)
		invoice.docstatus = 1
		apply_sibling_discount(invoice)
		self.assertFalse(invoice.additional_discount_percentage)


class TestSiblingLeavers(FrappeTestCase):
	def setUp(self):
		fx.school_settings(sibling_discount_percent=10)
		tag = frappe.generate_hash(length=5)
		self.elder = fx.student(f"Big{tag}", "2015-01-01")
		self.younger = fx.student(f"Small{tag}", "2019-01-01")
		fx.guardian(f"Family {tag}", [self.elder, self.younger])

	def test_elder_with_tc_no_discount(self):
		frappe.db.set_value("Student", self.elder, {"date_of_leaving": "2031-07-01", "leaving_certificate_number": "TC/1"})
		self.assertFalse(has_elder_sibling(self.younger))

	def test_elder_withdrawn_no_discount(self):
		frappe.db.set_value("Student", self.elder, "oc_academic_status", "Withdrawn")
		self.assertFalse(has_elder_sibling(self.younger))

	def test_elder_enrolled_only_in_another_year_no_discount(self):
		frappe.db.set_value("Program Enrollment", {"student": self.elder}, "academic_year", fx.academic_year(fx.NEXT_YEAR, "2032-06-01", "2033-04-30"))
		self.assertFalse(has_elder_sibling(self.younger))

	def test_elder_on_roll_same_year_discount(self):
		self.assertTrue(has_elder_sibling(self.younger))
