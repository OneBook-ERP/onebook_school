"""Fee Determination Committee cap (Tamil Nadu Schools (Regulation of Collection of Fee) Act 22 of 2009).

The committee fixes each class's fee for a block of academic years. A Fee Structure may charge at most the approved
amount per fee category; a category the order does not name is not capped, and a class with no order in force is not
capped at all (schools outside the Act, or before their first order is entered).
"""

import frappe
from frappe import _
from frappe.utils import flt, fmt_money, getdate


def approved_amounts(company, program, academic_year):
	"""Fee category -> approved amount from the latest submitted order in force for `academic_year`, or {}."""
	year_start = frappe.db.get_value("Academic Year", academic_year, "year_start_date")
	if not year_start:
		return {}
	orders = frappe.get_all(
		"Fee Committee Order",
		filters={"company": company, "docstatus": 1},
		fields=["name", "valid_from_year", "valid_to_year"],
		order_by="order_date desc, creation desc",
	)
	for order in orders:
		if covers(order, getdate(year_start)):
			lines = frappe.get_all(
				"Fee Committee Order Line",
				filters={"parent": order.name, "parenttype": "Fee Committee Order", "program": program},
				fields=["fee_category", "approved_amount"],
			)
			if lines:
				return {line.fee_category: flt(line.approved_amount) for line in lines}
	return {}


def covers(order, year_start):
	starts = [frappe.db.get_value("Academic Year", y, "year_start_date") for y in (order.valid_from_year, order.valid_to_year)]
	return all(starts) and getdate(starts[0]) <= year_start <= getdate(starts[1])


def check_fee_structure(doc, method=None):
	"""Fee Structure validate: refuse a category charged above the committee's approved amount."""
	if not (doc.company and doc.program and doc.academic_year):
		return
	approved = approved_amounts(doc.company, doc.program, doc.academic_year)
	if not approved:
		return
	charged = {}
	for row in doc.get("components") or []:
		charged[row.fees_category] = charged.get(row.fees_category, 0) + flt(row.amount)
	over = [
		_("{0}: approved {1}, asked {2}").format(
			frappe.bold(category), fmt_money(approved[category], currency="INR"), fmt_money(amount, currency="INR")
		)
		for category, amount in charged.items()
		if category in approved and amount > approved[category]
	]
	if over:
		frappe.throw(
			_("Fees above the Fee Determination Committee order for {0}:").format(doc.program)
			+ "<br>"
			+ "<br>".join(over),
			title=_("Above Committee-Approved Fee"),
		)
