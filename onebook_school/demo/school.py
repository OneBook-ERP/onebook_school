"""The school itself: company details, School Settings, logo and desk branding, the academic calendar and the staff
logins the demo uses."""

import os

import frappe
from frappe.utils.password import update_password

COMPANY = "Sri Aanoor Vidyalaya Matric Hr Sec School"
ABBR = "SAV"
YEAR = "2026-27"
TERMS = (("Term 1", "2026-06-02", "2026-09-30"), ("Term 2", "2026-10-06", "2026-12-23"), ("Term 3", "2027-01-04", "2027-04-15"))
PASSWORD = "Aanoor@Demo2026"
DOMAIN = "aanoor.example.edu"

SETTINGS = {
	"school_name": "Sri Aanoor Vidyalaya Matriculation Higher Secondary School",
	"school_name_tamil": "ஸ்ரீ ஆனூர் வித்யாலயா மெட்ரிகுலேஷன் மேல்நிலைப் பள்ளி",
	"address": "Kodumudi Road, Muthur, Erode 638105, Tamil Nadu",
	"board": "Tamil Nadu State Board (Matriculation)",
	"sibling_discount_percent": 10,
}

# login -> (full name, roles, workspace shown first)
USERS = {
	"correspondent": ("R. Palanisamy", ["Education Manager", "Accounts Manager", "Academics User"], "Correspondent"),
	"principal": ("Dr. S. Meenakshi", ["Education Manager", "Academics User", "Instructor"], "Principal"),
	"accounts": ("K. Saravanan", ["Accounts Manager", "Accounts User"], "Fees Office"),
	"office": ("M. Revathi", ["Academics User"], "School Office"),
	"teacher.vi": ("P. Anitha", ["Instructor"], "Class Teacher"),
	"teacher.x": ("N. Karthikeyan", ["Instructor"], "Class Teacher"),
}


def email(login):
	return f"{login}@{DOMAIN}"


def load(ctx):
	company_details(ctx)
	settings(ctx)
	calendar(ctx)
	users(ctx)


def company_details(ctx):
	if not frappe.db.exists("Company", ctx.company):
		frappe.get_doc(
			{"doctype": "Company", "company_name": ctx.company, "abbr": ABBR, "default_currency": "INR", "country": "India"}
		).insert(ignore_permissions=True)
		ctx.made()
	frappe.db.set_value("Company", ctx.company, {"company_description": "25 Years of Educational Excellence", "phone_no": "0424 0000000"})
	frappe.db.set_default("company", ctx.company)
	frappe.db.set_single_value("Global Defaults", "default_company", ctx.company)


def settings(ctx):
	doc = frappe.get_single("School Settings")
	doc.update(dict(SETTINGS, company=ctx.company))
	if ctx.logo_path and os.path.exists(ctx.logo_path):
		doc.logo = logo_url(ctx.logo_path)
		for single, field in (("Navbar Settings", "app_logo"), ("Website Settings", "app_logo"), ("Website Settings", "banner_image")):
			if frappe.get_meta(single).has_field(field):
				frappe.db.set_single_value(single, field, doc.logo)
		frappe.db.set_single_value("Website Settings", "app_name", "Aanoor Vidyalaya")
	doc.save(ignore_permissions=True)
	frappe.db.set_single_value("System Settings", {"app_name": "Aanoor Vidyalaya", "time_zone": "Asia/Kolkata", "date_format": "dd-mm-yyyy", "number_format": "#,##,###.##"})


def logo_url(path):
	existing = frappe.db.get_value("File", {"file_name": "aanoor-logo.png", "is_private": 0}, "file_url")
	if existing:
		return existing
	with open(path, "rb") as f:
		file = frappe.get_doc({"doctype": "File", "file_name": "aanoor-logo.png", "is_private": 0, "content": f.read()})
		file.insert(ignore_permissions=True)
	return file.file_url


def calendar(ctx):
	if not frappe.db.exists("Academic Year", YEAR):
		frappe.get_doc({"doctype": "Academic Year", "academic_year_name": YEAR, "year_start_date": "2026-06-01", "year_end_date": "2027-04-30"}).insert(ignore_permissions=True)
		ctx.made()
	for term, start, end in TERMS:
		name = f"{YEAR} ({term})"
		if not frappe.db.exists("Academic Term", name):
			frappe.get_doc({"doctype": "Academic Term", "academic_year": YEAR, "term_name": term, "term_start_date": start, "term_end_date": end}).insert(ignore_permissions=True)
			ctx.made()
	frappe.db.set_single_value(
		"Education Settings",
		{"current_academic_year": YEAR, "current_academic_term": f"{YEAR} (Term 2)", "user_creation_skip": 1},
	)


def users(ctx):
	for login, (full_name, roles, _workspace) in USERS.items():
		ensure_user(ctx, email(login), full_name, roles)


def ensure_user(ctx, mail, full_name, roles, user_type="System User"):
	if not frappe.db.exists("User", mail):
		first, _, last = full_name.partition(" ")
		user = frappe.get_doc(
			{"doctype": "User", "email": mail, "first_name": first, "last_name": last, "user_type": user_type,
			 "send_welcome_email": 0, "language": "en", "time_zone": "Asia/Kolkata"}
		)  # fmt: skip
		user.insert(ignore_permissions=True)
		ctx.made()
	user = frappe.get_doc("User", mail)
	have = {r.role for r in user.roles}
	missing = [r for r in roles if r not in have]
	if missing:
		user.add_roles(*missing)
	update_password(mail, PASSWORD)
	if not frappe.db.exists("User Permission", {"user": mail, "allow": "Company", "for_value": ctx.company}):
		frappe.get_doc({"doctype": "User Permission", "user": mail, "allow": "Company", "for_value": ctx.company, "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
	return mail
