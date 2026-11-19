import frappe
from frappe.tests.utils import FrappeTestCase

from onebook_school.fees.invoice import set_class
from onebook_school.tests import fixtures as fx


class TestInvoiceClass(FrappeTestCase):
	def test_invoice_gets_students_class(self):
		student = fx.student("Thendral", "2015-08-08", "OBS Std IX")
		invoice = frappe.get_doc({"doctype": "Sales Invoice", "company": fx.company(), "student": student, "items": []})
		set_class(invoice)
		self.assertEqual(invoice.obs_program, "OBS Std IX")

	def test_invoice_without_student_untouched(self):
		invoice = frappe.get_doc({"doctype": "Sales Invoice", "company": fx.company(), "items": []})
		set_class(invoice)
		self.assertFalse(invoice.get("obs_program"))
