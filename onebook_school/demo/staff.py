"""Teaching staff as HR sees them: an Employee behind every Instructor, and today's staff attendance
(two teachers absent, one on leave), so the principal's desk can show teachers, ratio and who is away."""

import random

import frappe
from frappe.utils import nowdate

AWAY_TODAY = {"S. Ramesh": "Absent", "T. Sumathi": "Absent", "V. Jayanthi": "On Leave"}
FEMALE_NAMES = ("Anitha", "Kalaiselvi", "Jayanthi", "Sumathi", "Selvi", "Mahalakshmi", "Vasanthi", "Kavitha", "Malathi",
				"Deepa", "Geetha", "Uma", "Shanthi", "Priya", "Nirmala")  # fmt: skip


def load(ctx):
	rng = random.Random(ctx.seed + 3)
	department = ensure_department(ctx)
	for inst in frappe.get_all("Instructor", filters={"status": "Active"}, fields=["name", "instructor_name", "employee"]):
		employee = inst.employee or make_employee(ctx, rng, inst, department)
		mark_today(ctx, employee, AWAY_TODAY.get(inst.instructor_name, "Present"))


def ensure_department(ctx):
	name = frappe.db.get_value("Department", {"department_name": "Teaching", "company": ctx.company})
	if name:
		return name
	parent = frappe.db.get_value("Department", {"is_group": 1, "company": ["in", ["", None]]}) or "All Departments"
	return frappe.get_doc({"doctype": "Department", "department_name": "Teaching", "company": ctx.company, "parent_department": parent}).insert(ignore_permissions=True).name


def make_employee(ctx, rng, inst, department):
	initial, _, first = inst.instructor_name.partition(" ")
	doc = frappe.get_doc(
		{"doctype": "Employee", "first_name": first or inst.instructor_name, "last_name": initial.rstrip("."), "company": ctx.company,
		 "status": "Active", "gender": "Female" if first in FEMALE_NAMES else "Male", "department": department,
		 "designation": ensure_designation("Teacher"), "date_of_birth": f"{rng.randint(1970, 1996)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
		 "date_of_joining": f"{rng.randint(2005, 2024)}-06-01", "holiday_list": frappe.db.get_value("Company", ctx.company, "default_holiday_list")}
	)  # fmt: skip
	doc.flags.ignore_permissions = True
	doc.insert()
	frappe.db.set_value("Instructor", inst.name, {"employee": doc.name, "department": department})
	ctx.made()
	return doc.name


def ensure_designation(name):
	if not frappe.db.exists("Designation", name):
		frappe.get_doc({"doctype": "Designation", "designation_name": name}).insert(ignore_permissions=True)
	return name


def mark_today(ctx, employee, status):
	today = nowdate()
	if frappe.db.exists("Attendance", {"employee": employee, "attendance_date": today, "docstatus": 1}):
		return
	doc = frappe.get_doc({"doctype": "Attendance", "employee": employee, "attendance_date": today, "status": status, "company": ctx.company})
	if status == "On Leave":
		doc.leave_type = None
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()
	ctx.made()
