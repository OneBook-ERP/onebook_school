"""Shared test records: one school company with its own academic year, classes and fee categories.
Every helper finds its record first, so the records persist across runs on the test site."""

import frappe

COMPANY = "OBS Test School"
ABBR = "OBST"
YEAR = "OBS 2031-32"
NEXT_YEAR = "OBS 2032-33"


def company():
	if not frappe.db.exists("Company", COMPANY):
		frappe.get_doc(
			{"doctype": "Company", "company_name": COMPANY, "abbr": ABBR, "default_currency": "INR", "country": "India"}
		).insert(ignore_permissions=True)
	return COMPANY


def academic_year(name=YEAR, start="2031-06-01", end="2032-04-30"):
	if not frappe.db.exists("Academic Year", name):
		frappe.get_doc(
			{"doctype": "Academic Year", "academic_year_name": name, "year_start_date": start, "year_end_date": end}
		).insert(ignore_permissions=True)
	return name


def program(name):
	if not frappe.db.exists("Program", name):
		frappe.get_doc({"doctype": "Program", "program_name": name, "oc_company": company()}).insert(
			ignore_permissions=True
		)
	return name


def fee_category(name):
	if not frappe.db.exists("Fee Category", name):
		frappe.get_doc({"doctype": "Fee Category", "category_name": name}).insert(ignore_permissions=True)
	return name


def receivable():
	return frappe.db.get_value("Account", {"company": company(), "account_type": "Receivable", "is_group": 0})


def fee_structure(program_name, components, year=YEAR):
	"""An unsaved Fee Structure; `components` maps fee category to amount."""
	return frappe.get_doc(
		{
			"doctype": "Fee Structure",
			"program": program(program_name),
			"academic_year": academic_year(year),
			"company": company(),
			"receivable_account": receivable(),
			"components": [{"fees_category": fee_category(c), "amount": a} for c, a in components.items()],
		}
	)
