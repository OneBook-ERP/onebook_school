"""Bring a fresh demo site to a set-up school: the setup wizard for the school company, Indian fiscal years
around today and the Gender masters. Idempotent."""

import frappe

COMPANY = "Sri Aanoor Vidyalaya Matric Hr Sec School"
ABBR = "SAV"
GENDERS = ("Male", "Female", "Other")


def complete_setup():
	if not frappe.get_list("Company"):
		from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

		setup_complete(
			{
				"currency": "INR",
				"full_name": "School Office",
				"company_name": COMPANY,
				"timezone": "Asia/Kolkata",
				"company_abbr": ABBR,
				"industry": "Education",
				"country": "India",
				"fy_start_date": "2026-04-01",
				"fy_end_date": "2027-03-31",
				"language": "english",
				"company_tagline": "25 Years of Educational Excellence",
				"email": "office@aanoor.example.edu",
				"password": "Aanoor@Demo2026",
				"chart_of_accounts": "Standard",
			}
		)
	make_fiscal_years()
	make_genders()
	frappe.db.commit()  # nosemgrep


def make_fiscal_years():
	for start in (2025, 2027):
		name = f"{start}-{str(start + 1)[2:]}"
		if not frappe.db.exists("Fiscal Year", {"year_start_date": f"{start}-04-01"}):
			frappe.get_doc(
				{"doctype": "Fiscal Year", "year": name, "year_start_date": f"{start}-04-01", "year_end_date": f"{start + 1}-03-31"}
			).insert(ignore_permissions=True)


def make_genders():
	for gender in GENDERS:
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)
