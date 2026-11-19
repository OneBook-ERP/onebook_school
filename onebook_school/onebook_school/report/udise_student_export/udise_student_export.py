"""UDISE Student Export: one row per student of a year (optionally a class or section), in UDISE+ SDMS field order."""

import frappe
from frappe import _

from onebook_school.compliance.udise import student_issues

COLUMNS = [
	("udise_code", "UDISE Code", "Data", 110), ("class", "Class", "Data", 90), ("section", "Section", "Data", 120),
	("roll_no", "Roll No", "Int", 70), ("admission_no", "Admission No", "Data", 110),
	("student", "Student", "Link/Student", 120), ("student_name", "Student Name", "Data", 170),
	("gender", "Gender", "Data", 80), ("date_of_birth", "Date of Birth", "Date", 100),
	("mother_tongue", "Mother Tongue", "Data", 100), ("social_category", "Social Category", "Data", 90),
	("religion", "Religion", "Data", 90), ("father_name", "Father's Name", "Data", 140),
	("mother_name", "Mother's Name", "Data", 140), ("guardian_mobile", "Guardian Mobile", "Data", 110),
	("emis_id", "EMIS ID", "Data", 130), ("pen", "PEN", "Data", 110), ("apaar_id", "APAAR ID", "Data", 120),
	("apaar_consent", "APAAR Consent", "Data", 100), ("rte", "RTE", "Check", 50), ("cwsn", "CWSN", "Check", 55),
	("admission_date", "Admission Date", "Date", 100), ("issues", "Issues", "Data", 300),
]  # fmt: skip


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = [
		{"fieldname": f, "label": _(label), "fieldtype": t.split("/")[0], "options": t.split("/")[1] if "/" in t else None, "width": w}
		for f, label, t, w in COLUMNS
	]
	rows = get_rows(filters)
	ready = sum(1 for r in rows if not r["issues"])
	summary = [
		{"label": _("Students"), "value": len(rows), "indicator": "Blue"},
		{"label": _("Ready for UDISE+"), "value": ready, "indicator": "Green"},
		{"label": _("Need fixing"), "value": len(rows) - ready, "indicator": "Red" if len(rows) - ready else "Green"},
	]
	return columns, rows, None, None, summary


def get_rows(filters):
	udise = frappe.db.get_single_value("School Settings", "udise_code")
	company = filters.company or frappe.db.get_single_value("School Settings", "company")
	group_filters = {"academic_year": filters.academic_year, "group_based_on": "Batch", "disabled": 0}
	if company:
		group_filters["oc_company"] = company
	if filters.student_group:
		group_filters["name"] = filters.student_group
	if filters.program:
		group_filters["program"] = filters.program
	rows = []
	for group in frappe.get_list("Student Group", filters=group_filters, fields=["name", "program"], order_by="program, name"):
		members = frappe.get_all(
			"Student Group Student",
			filters={"parent": group.name, "parenttype": "Student Group", "active": 1},
			fields=["student", "group_roll_number"],
			order_by="group_roll_number asc",
		)
		for m in members:
			rows.append(student_row(m.student, group, m.group_roll_number, udise))
	return rows


def student_row(student, group, roll_no, udise):
	s = frappe.db.get_value(
		"Student", student,
		["student_name", "gender", "date_of_birth", "joining_date", "obs_admission_no", "obs_mother_tongue",
		 "obs_social_category", "obs_religion", "obs_emis_id", "obs_pen", "obs_apaar_id", "obs_apaar_consent",
		 "obs_rte", "obs_cwsn", "student_mobile_number"],
		as_dict=True,
	)  # fmt: skip
	parents = {"Father": None, "Mother": None}
	mobile = None
	for g in frappe.get_all("Student Guardian", filters={"parent": student, "parenttype": "Student"}, fields=["guardian", "guardian_name", "relation"]):
		if g.relation in parents and not parents[g.relation]:
			parents[g.relation] = g.guardian_name
		mobile = mobile or frappe.db.get_value("Guardian", g.guardian, "mobile_number")
	row = {
		"udise_code": udise, "class": group.program, "section": group.name, "roll_no": roll_no,
		"admission_no": s.obs_admission_no, "student": student, "student_name": s.student_name, "gender": s.gender,
		"date_of_birth": s.date_of_birth, "mother_tongue": s.obs_mother_tongue, "social_category": s.obs_social_category,
		"religion": s.obs_religion, "father_name": parents["Father"], "mother_name": parents["Mother"],
		"guardian_mobile": mobile or s.student_mobile_number, "emis_id": s.obs_emis_id, "pen": s.obs_pen,
		"apaar_id": s.obs_apaar_id, "apaar_consent": s.obs_apaar_consent, "rte": s.obs_rte, "cwsn": s.obs_cwsn,
		"admission_date": s.joining_date,
	}  # fmt: skip
	row["issues"] = ", ".join(student_issues(row))
	return row
