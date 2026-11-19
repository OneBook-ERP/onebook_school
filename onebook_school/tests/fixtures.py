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


def student(first_name, date_of_birth, program_name="OBS Std VI", enabled=1):
	"""An enrolled Student of the test school (found by e-mail first)."""
	email = f"{first_name.lower()}@obs-test.example.com"
	name = frappe.db.get_value("Student", {"student_email_id": email})
	if not name:
		doc = frappe.get_doc(
			{
				"doctype": "Student", "first_name": first_name, "student_email_id": email,
				"date_of_birth": date_of_birth, "oc_company": company(), "enabled": 1,
			}
		).insert(ignore_permissions=True)  # fmt: skip
		name = doc.name
		enrollment = frappe.get_doc(
			{"doctype": "Program Enrollment", "student": name, "program": program(program_name), "academic_year": academic_year()}
		).insert(ignore_permissions=True)
		enrollment.submit()
	frappe.db.set_value("Student", name, "enabled", enabled)
	return name


def guardian(guardian_name, students):
	name = frappe.db.get_value("Guardian", {"guardian_name": guardian_name})
	if not name:
		name = frappe.get_doc(
			{"doctype": "Guardian", "guardian_name": guardian_name, "email_address": f"{guardian_name.lower().replace(' ', '')}@obs-test.example.com"}
		).insert(ignore_permissions=True).name
	for s in students:
		doc = frappe.get_doc("Student", s)
		if not any(g.guardian == name for g in doc.guardians):
			doc.append("guardians", {"guardian": name, "guardian_name": guardian_name, "relation": "Father"})
			doc.save(ignore_permissions=True)
	return name


def school_settings(**values):
	settings = frappe.get_single("School Settings")
	settings.update(values)
	settings.save(ignore_permissions=True)
	return settings
