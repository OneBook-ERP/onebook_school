import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, flt, nowdate

from onebook_school.fees.family import get_outstanding
from onebook_school.tests import fixtures as fx


def receipt(guardian, amount):
	doc = frappe.get_doc(
		{"doctype": "Family Receipt", "guardian": guardian, "company": fx.company(), "posting_date": nowdate(),
		 "mode_of_payment": fx.cash_mode(), "amount_paid": amount}
	)  # fmt: skip
	doc.allocate()
	return doc


class TestFamilyReceipt(FrappeTestCase):
	def setUp(self):
		fx.school_settings(sibling_discount_percent=0)
		tag = frappe.generate_hash(length=5)
		self.elder = fx.student(f"Elder{tag}", "2016-01-01")
		self.younger = fx.student(f"Younger{tag}", "2019-01-01")
		self.guardian = fx.guardian(f"Parent {tag}", [self.elder, self.younger])
		self.old = fx.fee_invoice(self.elder, 5000, add_days(nowdate(), -30), add_days(nowdate(), -40))
		self.new = fx.fee_invoice(self.younger, 4000, add_days(nowdate(), 10))

	def test_outstanding_lists_both_children_oldest_first(self):
		rows = get_outstanding(self.guardian, fx.company())
		self.assertEqual([r["sales_invoice"] for r in rows], [self.old.name, self.new.name])

	def test_full_payment_two_children(self):
		doc = receipt(self.guardian, 9000)
		doc.insert()
		doc.submit()
		for invoice in (self.old, self.new):
			self.assertEqual(flt(frappe.db.get_value("Sales Invoice", invoice.name, "outstanding_amount")), 0)
		self.assertTrue(all(row.payment_entry for row in doc.allocations))

	def test_partial_payment_oldest_first(self):
		doc = receipt(self.guardian, 6000)
		self.assertEqual([(r.sales_invoice, flt(r.allocated_amount)) for r in doc.allocations], [(self.old.name, 5000), (self.new.name, 1000)])
		doc.insert()
		doc.submit()
		self.assertEqual(flt(frappe.db.get_value("Sales Invoice", self.new.name, "outstanding_amount")), 3000)

	def test_never_over_allocates_an_invoice(self):
		doc = receipt(self.guardian, 6000)
		doc.allocations[0].allocated_amount = 5500
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_cancel_cancels_payment_entries(self):
		doc = receipt(self.guardian, 9000)
		doc.insert()
		doc.submit()
		doc.cancel()
		for row in doc.allocations:
			self.assertEqual(frappe.db.get_value("Payment Entry", row.payment_entry, "docstatus"), 2)
		self.assertEqual(flt(frappe.db.get_value("Sales Invoice", self.old.name, "outstanding_amount")), 5000)


class TestFamilyReceiptSafety(FrappeTestCase):
	def setUp(self):
		fx.school_settings(sibling_discount_percent=0)
		tag = frappe.generate_hash(length=5)
		self.child = fx.student(f"Kid{tag}", "2016-02-02")
		self.guardian = fx.guardian(f"Dad {tag}", [self.child])
		self.invoice = fx.fee_invoice(self.child, 3000, nowdate())
		stranger = fx.student(f"Other{tag}", "2016-03-03")
		fx.guardian(f"Stranger {tag}", [stranger])
		self.strangers_invoice = fx.fee_invoice(stranger, 2000, nowdate())

	def test_payment_goes_to_the_modes_account(self):
		bank = fx.upi_mode()
		doc = receipt(self.guardian, 3000)
		doc.mode_of_payment = bank["mode"]
		doc.insert()
		doc.submit()
		self.assertEqual(frappe.db.get_value("Payment Entry", doc.allocations[0].payment_entry, "paid_to"), bank["account"])

	def test_amount_received_must_equal_allocated(self):
		doc = receipt(self.guardian, 3000)
		doc.amount_paid = 3500
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_other_familys_invoice_refused(self):
		doc = receipt(self.guardian, 3000)
		doc.append("allocations", {"student": self.child, "sales_invoice": self.strangers_invoice.name, "allocated_amount": 100})
		doc.amount_paid = 3100
		with self.assertRaises(frappe.ValidationError):
			doc.insert()

	def test_invoice_paid_meanwhile_refused_on_submit(self):
		first = receipt(self.guardian, 3000)
		first.insert()
		second = receipt(self.guardian, 3000)
		second.insert()
		first.submit()
		with self.assertRaises(frappe.ValidationError):
			second.submit()
