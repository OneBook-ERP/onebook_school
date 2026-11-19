import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from onebook_school.fees.family import get_outstanding


class FamilyReceipt(Document):
	def allocate(self):
		"""Fill allocations from amount_paid, oldest due invoice first."""
		self.set("allocations", [])
		left = flt(self.amount_paid)
		for row in get_outstanding(self.guardian, self.company):
			if left <= 0:
				break
			paying = min(left, flt(row["outstanding_amount"]))
			self.append("allocations", dict(row, allocated_amount=paying))
			left -= paying
		self.set_total()

	def set_total(self):
		self.total_allocated = sum(flt(r.allocated_amount) for r in self.allocations)

	def validate(self):
		for row in self.allocations:
			invoice = frappe.db.get_value(
				"Sales Invoice", row.sales_invoice, ["outstanding_amount", "student", "docstatus"], as_dict=True
			)
			if not invoice or invoice.docstatus != 1:
				frappe.throw(_("Row {0}: {1} is not a submitted invoice.").format(row.idx, row.sales_invoice))
			row.outstanding_amount = flt(invoice.outstanding_amount)
			if flt(row.allocated_amount) <= 0 or flt(row.allocated_amount) > row.outstanding_amount:
				frappe.throw(
					_("Row {0}: paying {1} on {2}, which has {3} outstanding.").format(
						row.idx, row.allocated_amount, row.sales_invoice, row.outstanding_amount
					)
				)
		self.set_total()
		if self.total_allocated > flt(self.amount_paid):
			frappe.throw(_("Allocated {0} is more than the amount received {1}.").format(self.total_allocated, self.amount_paid))

	def on_submit(self):
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		for row in self.allocations:
			entry = get_payment_entry("Sales Invoice", row.sales_invoice, party_amount=flt(row.allocated_amount))
			entry.mode_of_payment = self.mode_of_payment
			entry.posting_date = self.posting_date
			entry.reference_no = self.reference_no or self.name
			entry.reference_date = self.posting_date
			entry.remarks = _("Family Receipt {0}").format(self.name)
			entry.flags.ignore_permissions = True
			entry.insert()
			entry.submit()
			row.db_set("payment_entry", entry.name)

	def on_cancel(self):
		self.ignore_linked_doctypes = ("Payment Entry",)
		for row in self.allocations:
			if row.payment_entry and frappe.db.get_value("Payment Entry", row.payment_entry, "docstatus") == 1:
				entry = frappe.get_doc("Payment Entry", row.payment_entry)
				entry.flags.ignore_permissions = True
				entry.cancel()

	@frappe.whitelist()
	def allocate_from_client(self):
		if not flt(self.amount_paid):
			self.amount_paid = sum(flt(r["outstanding_amount"]) for r in get_outstanding(self.guardian, self.company))
		self.allocate()
