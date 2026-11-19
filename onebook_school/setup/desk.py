"""The school desk: one workspace per role, each opening on the numbers that role is judged by.

Built in code on install and migrate (idempotent) because number cards and charts are not synced from files:
roles, number cards, dashboard charts, workspaces, their sidebars, the app's dock and desktop icons.
"""

import json

import frappe

APP = "onebook_school"
MODULE = "OneBook School"
# Frappe keeps one sidebar per module, so each role desk is its own module (its DocTypes stay in OneBook School).
DESK_MODULE = {
	"Correspondent": "School Correspondent", "Principal": "School Principal", "Fees Office": "School Fees Office",
	"School Office": "School Front Office", "Class Teacher": "School Class Teacher",
}  # fmt: skip

ROLES = ["School Correspondent", "School Principal", "School Accountant", "School Office", "Class Teacher"]

R, RW, RWS = ("read", "report", "print"), ("read", "report", "print", "write", "create"), ("read", "report", "print", "write", "create", "submit")
# role -> {doctype: rights}; what each school role needs beyond the standard Education/ERPNext roles it also holds
RIGHTS = {
	"School Correspondent": {"Timetable Slot": R, "Exam Schedule": R, "Cover Assignment": RW, "Teaching Assignment": R, "Instructor": R, "Attendance": R, "Lead": R, "Sales Invoice": R, "Payment Entry": R, "Student Attendance": R, "Report Card": R, "Mark Entry": R,
		"Family Receipt": R, "Certificate Request": R, "Fee Committee Order": RWS, "School Settings": RW},
	"School Principal": {"Timetable Slot": RW, "Exam Schedule": RW, "Cover Assignment": RW, "Teaching Assignment": RW, "Instructor": R, "Attendance": R, "Employee": R, "Lead": R, "Sales Invoice": R, "Payment Entry": R, "Student Attendance": RWS, "Report Card": RW, "Mark Entry": RWS,
		"Certificate Request": RWS, "Family Receipt": R, "Fee Committee Order": R, "Student": RW, "Guardian": RW},
	"School Accountant": {"Family Receipt": RWS, "Sales Invoice": RWS, "Payment Entry": RWS, "Fee Structure": RWS, "Fee Committee Order": R,
		"Student": R, "Guardian": R, "Program Enrollment": R},
	"School Office": {"Lead": RW, "Student": RW, "Guardian": RW, "Program Enrollment": RWS, "Student Applicant": RW, "Certificate Request": RW,
		"Student Attendance": R, "Report Card": R, "Student Group": R},
	"Class Teacher": {"Timetable Slot": R, "Exam Schedule": R, "Cover Assignment": R, "Teaching Assignment": R, "Student Attendance": RWS, "Student Group": R, "Student": R, "Guardian": R, "Mark Entry": RWS, "Report Card": RW, "Course": R, "Program": R},
}  # fmt: skip
for _grants in RIGHTS.values():
	_grants.setdefault("Company", R)  # the School filter on reports and forms

TODAY = ["Timespan", "today"]
MONTH = ["Timespan", "this month"]


def flt_(dt, field, op, value):
	return [dt, field, op, value, False]


CARDS = {
	"Fees Collected Today": dict(document_type="Payment Entry", function="Sum", aggregate_function_based_on="paid_amount", color="#2e7d32",
		filters=[flt_("Payment Entry", "posting_date", *TODAY), flt_("Payment Entry", "docstatus", "=", 1), flt_("Payment Entry", "payment_type", "=", "Receive")]),
	"Fees Collected This Month": dict(document_type="Payment Entry", function="Sum", aggregate_function_based_on="paid_amount", color="#2e7d32",
		filters=[flt_("Payment Entry", "posting_date", *MONTH), flt_("Payment Entry", "docstatus", "=", 1), flt_("Payment Entry", "payment_type", "=", "Receive")]),
	"Outstanding Fees": dict(document_type="Sales Invoice", function="Sum", aggregate_function_based_on="outstanding_amount", color="#c62828",
		filters=[flt_("Sales Invoice", "docstatus", "=", 1), flt_("Sales Invoice", "student", "is", "set"), flt_("Sales Invoice", "outstanding_amount", ">", 0)]),
	"Overdue Fee Invoices": dict(document_type="Sales Invoice", function="Count", color="#ef6c00",
		filters=[flt_("Sales Invoice", "status", "=", "Overdue"), flt_("Sales Invoice", "student", "is", "set")]),
	"Receipts Today": dict(document_type="Family Receipt", function="Count", color="#2e7d32",
		filters=[flt_("Family Receipt", "posting_date", *TODAY), flt_("Family Receipt", "docstatus", "=", 1)]),
	"Students Enrolled": dict(document_type="Student", function="Count", color="#1565c0", filters=[flt_("Student", "enabled", "=", 1)]),
	"Present Today": dict(type="Custom", method="onebook_school.dashboard.present_today", document_type="Student Attendance", color="#2e7d32"),
	"Absent Today": dict(document_type="Student Attendance", function="Count", color="#c62828",
		filters=[flt_("Student Attendance", "date", *TODAY), flt_("Student Attendance", "status", "=", "Absent"), flt_("Student Attendance", "docstatus", "=", 1)]),
	"Open Enquiries": dict(document_type="Lead", function="Count", color="#6a1b9a", filters=[flt_("Lead", "status", "in", ["Open", "Replied", "Interested"])]),
	"Report Cards Ready": dict(document_type="Report Card", function="Count", color="#1565c0", filters=[]),
	"Teachers": dict(document_type="Instructor", function="Count", color="#1565c0", filters=[flt_("Instructor", "status", "=", "Active")]),
	"Students per Teacher": dict(type="Custom", method="onebook_school.dashboard.students_per_teacher", document_type="Student", color="#1565c0"),
	"Staff Away Today": dict(document_type="Attendance", function="Count", color="#c62828",
		filters=[flt_("Attendance", "attendance_date", *TODAY), flt_("Attendance", "status", "in", ["Absent", "On Leave"]), flt_("Attendance", "docstatus", "=", 1)]),
	"Pass Percentage": dict(type="Custom", method="onebook_school.dashboard.pass_percentage", document_type="Report Card", color="#2e7d32"),
	"Top Learners (90%+)": dict(document_type="Report Card", function="Count", color="#2e7d32", filters=[flt_("Report Card", "percentage", ">=", 90)]),
	"Need Support (below 50%)": dict(document_type="Report Card", function="Count", color="#ef6c00", filters=[flt_("Report Card", "percentage", "<", 50)]),
	"Certificates This Month": dict(document_type="Certificate Request", function="Count", color="#6a1b9a",
		filters=[flt_("Certificate Request", "creation", *MONTH), flt_("Certificate Request", "docstatus", "=", 1)]),
}  # fmt: skip

CHARTS = {
	"Fee Collection by Month": dict(chart_type="Sum", document_type="Payment Entry", based_on="posting_date", value_based_on="paid_amount",
		time_interval="Monthly", timespan="Last Year", type="Line", color="#a3197b",
		filters=[flt_("Payment Entry", "docstatus", "=", 1), flt_("Payment Entry", "payment_type", "=", "Receive")]),
	"Fee Collection - Last 30 Days": dict(chart_type="Sum", document_type="Payment Entry", based_on="posting_date", value_based_on="paid_amount",
		time_interval="Daily", timespan="Last Month", type="Bar", color="#2e7d32",
		filters=[flt_("Payment Entry", "docstatus", "=", 1), flt_("Payment Entry", "payment_type", "=", "Receive")]),
	"Dues by Class": dict(chart_type="Group By", document_type="Sales Invoice", group_by_based_on="obs_program", group_by_type="Sum",
		aggregate_function_based_on="outstanding_amount", type="Bar", color="#c62828", number_of_groups=0,
		filters=[flt_("Sales Invoice", "docstatus", "=", 1), flt_("Sales Invoice", "outstanding_amount", ">", 0), flt_("Sales Invoice", "student", "is", "set")]),
	"Payment Mode": dict(chart_type="Group By", document_type="Payment Entry", group_by_based_on="mode_of_payment", group_by_type="Sum",
		aggregate_function_based_on="paid_amount", type="Donut", filters=[flt_("Payment Entry", "docstatus", "=", 1), flt_("Payment Entry", "payment_type", "=", "Receive")]),
	"Students by Class": dict(chart_type="Group By", document_type="Program Enrollment", group_by_based_on="program", group_by_type="Count",
		type="Bar", color="#1565c0", number_of_groups=0, filters=[flt_("Program Enrollment", "docstatus", "=", 1)]),
	"Grade Distribution": dict(chart_type="Group By", document_type="Report Card", group_by_based_on="overall_grade", group_by_type="Count",
		type="Bar", color="#a3197b", number_of_groups=0, filters=[]),
	"Average % by Section": dict(chart_type="Group By", document_type="Report Card", group_by_based_on="student_group", group_by_type="Average",
		aggregate_function_based_on="percentage", type="Bar", color="#1565c0", number_of_groups=0, filters=[]),
	"Staff Attendance Today": dict(chart_type="Group By", document_type="Attendance", group_by_based_on="status", group_by_type="Count",
		type="Donut", filters=[flt_("Attendance", "attendance_date", *TODAY), flt_("Attendance", "docstatus", "=", 1)]),
	"Attendance Today": dict(chart_type="Group By", document_type="Student Attendance", group_by_based_on="status", group_by_type="Count",
		type="Donut", filters=[flt_("Student Attendance", "date", *TODAY), flt_("Student Attendance", "docstatus", "=", 1)]),
}  # fmt: skip


def dt(label, link_to, **kw):
	return dict({"label": label, "link_to": link_to, "type": "DocType", "doc_view": kw.pop("view", "List")}, **kw)


def rpt(label, link_to):
	return {"label": label, "link_to": link_to, "type": "Report", "is_query_report": 1}


OVERDUE = '{"student": ["is", "set"], "status": "Overdue"}'

# name -> (icon, roles, intro, cards, charts, shortcuts, link groups)
WORKSPACES = {
	"Correspondent": (
		"chart-pie", ["School Correspondent", "System Manager"],
		"The school at a glance: money in, money due, children in class.",
		["# Money", "Fees Collected Today", "Fees Collected This Month", "Outstanding Fees", "# School", "Students Enrolled", "Present Today", "Open Enquiries",
		 "# Teaching and learning", "Teachers", "Students per Teacher", "Pass Percentage"],
		["Fee Collection by Month", "Dues by Class", "Payment Mode", "Students by Class", "Grade Distribution", "Average % by Section"],
		[dt("Defaulters", "Sales Invoice", stats_filter=OVERDUE, format="{} Overdue", color="Red"), dt("Fee Receipts", "Family Receipt"),
		 dt("Fee Committee Order", "Fee Committee Order"), rpt("UDISE Student Export", "UDISE Student Export"), dt("Report Cards", "Report Card"),
		 dt("Certificates", "Certificate Request")],
		{"Fees": [("DocType", "Family Receipt"), ("DocType", "Sales Invoice"), ("DocType", "Fee Structure"), ("DocType", "Fee Committee Order"), ("Report", "Accounts Receivable")],
		 "Students": [("DocType", "Student"), ("DocType", "Student Group"), ("DocType", "Report Card"), ("Report", "UDISE Student Export")],
		 "Settings": [("DocType", "School Settings"), ("DocType", "Academic Year"), ("DocType", "Program")]},
	),
	"Principal": (
		"school", ["School Principal", "School Correspondent", "System Manager"],
		"Today's attendance, the teaching staff, how the children are learning, and the returns that are due.",
		["# Today", "Present Today", "Absent Today", "Students Enrolled", "# Teaching staff", "Teachers", "Students per Teacher", "Staff Away Today",
		 "# Learning (latest exam)", "Pass Percentage", "Top Learners (90%+)", "Need Support (below 50%)", "# Office", "Open Enquiries", "Certificates This Month", "Report Cards Ready"],
		["Attendance Today", "Staff Attendance Today", "Grade Distribution", "Average % by Section", "Students by Class", "Dues by Class"],
		[dt("Timetable", "Timetable Slot", view="Report Builder"), dt("Exam Schedule", "Exam Schedule"), dt("Cover Today", "Cover Assignment"),
		 dt("Mark Entry", "Mark Entry"), dt("Report Cards", "Report Card"), rpt("UDISE Student Export", "UDISE Student Export"),
		 dt("Class Sections", "Student Group"), dt("Attendance", "Student Attendance"), dt("Enquiries", "Lead"), dt("Certificates", "Certificate Request"),
		 dt("Students", "Student")],
		{"School Day": [("DocType", "Timetable Slot"), ("DocType", "Teaching Assignment"), ("DocType", "Cover Assignment"), ("DocType", "Exam Schedule"), ("DocType", "School Settings")],
		 "Academics": [("DocType", "Program"), ("DocType", "Course"), ("DocType", "Student Group"), ("DocType", "Mark Entry"), ("DocType", "Report Card")],
		 "Returns": [("Report", "UDISE Student Export"), ("DocType", "Fee Committee Order"), ("DocType", "Student")],
		 "Parents": [("DocType", "Guardian"), ("DocType", "Message Template"), ("DocType", "Circular")]},
	),
	"Fees Office": (
		"wallet", ["School Accountant", "School Correspondent", "System Manager"],
		"Collect, receipt and follow up: every child's fee, one parent payment.",
		["Fees Collected Today", "Receipts Today", "Outstanding Fees", "Overdue Fee Invoices"],
		["Fee Collection - Last 30 Days", "Dues by Class", "Payment Mode"],
		[dt("New Fee Receipt", "Family Receipt", view="New", color="Green"), dt("Fee Receipts", "Family Receipt"),
		 dt("Overdue Invoices", "Sales Invoice", stats_filter=OVERDUE, format="{} Overdue", color="Red"), dt("Fee Structures", "Fee Structure"),
		 dt("Fee Committee Order", "Fee Committee Order"), rpt("Accounts Receivable", "Accounts Receivable")],
		{"Collect": [("DocType", "Family Receipt"), ("DocType", "Payment Entry"), ("DocType", "Mode of Payment")],
		 "Bill": [("DocType", "Sales Invoice"), ("DocType", "Fee Structure"), ("DocType", "Fee Category"), ("DocType", "Fee Committee Order")],
		 "Reports": [("Report", "Accounts Receivable"), ("Report", "General Ledger")]},
	),
	"School Office": (
		"building-2", ["School Office", "School Principal", "System Manager"],
		"Admissions, records and certificates for parents at the counter.",
		["Students Enrolled", "Open Enquiries", "Certificates This Month", "Absent Today"],
		["Students by Class"],
		[dt("Enquiries", "Lead"), dt("Students", "Student"), dt("Parents", "Guardian"), dt("Enrolments", "Program Enrollment"),
		 dt("Certificates", "Certificate Request"), rpt("UDISE Student Export", "UDISE Student Export")],
		{"Admissions": [("DocType", "Lead"), ("DocType", "Student Applicant"), ("DocType", "Program Enrollment")],
		 "Records": [("DocType", "Student"), ("DocType", "Guardian"), ("DocType", "Student Group"), ("DocType", "Certificate Request")],
		 "Parents": [("DocType", "Message Template"), ("DocType", "Circular")]},
	),
	"Class Teacher": (
		"users-round", ["Class Teacher", "School Principal", "System Manager"],
		"Your section: attendance in the morning, marks after each test.",
		["Present Today", "Absent Today", "Report Cards Ready", "Top Learners (90%+)", "Need Support (below 50%)", "Pass Percentage"],
		["Attendance Today", "Average % by Section"],
		[dt("Take Attendance", "Student Attendance Tool", view="New", color="Green"), dt("Enter Marks", "Mark Entry", view="New", color="Blue"),
		 dt("My Timetable", "Timetable Slot", view="Report Builder"), dt("Exam Schedule", "Exam Schedule"),
		 dt("Report Cards", "Report Card"), dt("My Sections", "Student Group"), dt("Students", "Student")],
		{"Class": [("DocType", "Timetable Slot"), ("DocType", "Student Group"), ("DocType", "Student"), ("DocType", "Student Attendance")],
		 "Assessment": [("DocType", "Mark Entry"), ("DocType", "Report Card")]},
	),
}


def build():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)
	rights()
	from onebook_school.setup.today_block import build as today_block

	today_block()
	for name, spec in CARDS.items():
		number_card(name, spec)
	for name, spec in CHARTS.items():
		chart(name, spec)
	for seq, (name, spec) in enumerate(WORKSPACES.items()):
		workspace(name, seq, *spec)
		sidebar(name, spec[0], spec[6])
		desktop_icon(name, spec[0], spec[1], seq)
	dock()
	frappe.clear_cache()


def rights():
	for role, grants in RIGHTS.items():
		for doctype, perms in grants.items():
			if frappe.db.exists("DocType", doctype):
				grant(doctype, role, perms)


def grant(doctype, role, perms):
	"""Give `role` these rights on `doctype` once. A role that already has a row keeps it exactly as the school's admin
	left it, so a migrate never undoes a revocation. Note: the first Custom DocPerm on a doctype freezes its standard
	permissions on this site (Frappe copies them over), so later upstream permission changes need a manual review."""
	from frappe.permissions import add_permission

	if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}):
		return
	add_permission(doctype, role, 0)
	submittable = frappe.get_meta(doctype).is_submittable
	values = {p: 1 for p in perms if p != "submit" or submittable}
	frappe.db.set_value("Custom DocPerm", {"parent": doctype, "role": role, "permlevel": 0}, values)
	frappe.clear_cache(doctype=doctype)


def number_card(name, spec):
	spec = dict(spec)
	filters = spec.pop("filters", [])
	values = {"label": name, "type": spec.pop("type", "Document Type"), "is_public": 1, "is_standard": 0, "module": MODULE,
			  "filters_json": json.dumps(filters), "show_percentage_stats": 0, **spec}  # fmt: skip
	upsert("Number Card", name, values)
	if values.get("function") != "Sum" and frappe.get_meta("Number Card").has_field("currency"):
		frappe.db.set_value("Number Card", name, "currency", None)  # counts and percentages are not money


def chart(name, spec):
	spec = dict(spec)
	filters = spec.pop("filters", [])
	values = {"chart_name": name, "is_public": 1, "is_standard": 0, "module": MODULE, "filters_json": json.dumps(filters), **spec}
	if spec.get("color"):
		values["color"] = spec["color"]
	upsert("Dashboard Chart", name, values)
	if "Count" in (spec.get("group_by_type"), spec.get("chart_type")):
		frappe.db.set_value("Dashboard Chart", name, "currency", None)  # a count is not money


def workspace(name, seq, icon, roles, intro, cards, charts, shortcuts, links):
	blocks = [{"id": "td", "type": "custom_block", "data": {"custom_block_name": "Today", "col": 12}},
			  {"id": "hd", "type": "header", "data": {"text": f'<span class="h5"><b>{name} dashboard</b></span>', "col": 12}},
			  {"id": "pg", "type": "paragraph", "data": {"text": f'<span class="text-muted">{intro}</span>', "col": 12}}]  # fmt: skip
	for i, c in enumerate(cards):
		if c.startswith("# "):
			blocks.append({"id": f"ch{i}h", "type": "header", "data": {"text": f'<span class="h6"><b>{c[2:]}</b></span>', "col": 12}})
		else:
			blocks.append({"id": f"nc{i}", "type": "number_card", "data": {"number_card_name": c, "col": 4}})
	cards = [c for c in cards if not c.startswith("# ")]
	blocks += [{"id": "sp1", "type": "spacer", "data": {"col": 12}}]
	blocks += [{"id": f"ch{i}", "type": "chart", "data": {"chart_name": c, "col": 12 if (len(charts) % 2 and i == 0) else 6}} for i, c in enumerate(charts)]
	blocks += [{"id": "hd2", "type": "header", "data": {"text": '<span class="h5"><b>Quick actions</b></span>', "col": 12}}]
	blocks += [{"id": f"sc{i}", "type": "shortcut", "data": {"shortcut_name": s["label"], "col": 4}} for i, s in enumerate(shortcuts)]
	blocks += [{"id": "hd3", "type": "header", "data": {"text": '<span class="h5"><b>Everything else</b></span>', "col": 12}}]
	blocks += [{"id": f"cd{i}", "type": "card", "data": {"card_name": card, "col": 4}} for i, card in enumerate(links)]
	link_rows = []
	for card, items in links.items():
		link_rows.append({"type": "Card Break", "label": card, "link_count": len(items)})
		link_rows += [{"type": "Link", "label": target, "link_type": kind, "link_to": target, "is_query_report": 1 if kind == "Report" else 0} for kind, target in items]
	values = {
		"label": name, "title": name, "module": DESK_MODULE[name], "app": APP, "public": 1, "icon": icon, "sequence_id": 10 + seq, "is_hidden": 0,
		"content": json.dumps(blocks), "roles": [{"role": r} for r in roles], "custom_blocks": [{"custom_block_name": "Today", "label": "Today"}],
		"number_cards": [{"number_card_name": c, "label": c} for c in cards], "charts": [{"chart_name": c, "label": c} for c in charts],
		"shortcuts": shortcuts, "links": link_rows,
	}  # fmt: skip
	upsert("Workspace", name, values, child_tables=("roles", "number_cards", "charts", "shortcuts", "links", "custom_blocks"))


# which role desk owns each school DocType or report, so opening it keeps that desk's sidebar
OWNER = {
	"Family Receipt": "Fees Office", "Fee Committee Order": "Fees Office", "Mark Entry": "Class Teacher", "Report Card": "Class Teacher",
	"School Settings": "Correspondent", "UDISE Student Export": "Principal", "Timetable Slot": "Principal", "Teaching Assignment": "Principal",
	"Cover Assignment": "Principal", "Exam Schedule": "Principal",
}  # fmt: skip


def sidebar(name, icon, links):
	items = [{"type": "Link", "label": "Home", "link_type": "Workspace", "link_to": name, "icon": "house"}]
	for card, rows in links.items():
		items.append({"type": "Section Break", "label": card, "collapsible": 1, "indent": 1})
		items += [{"type": "Link", "label": target, "link_type": kind, "link_to": target, "child": 1, "is_default_module": 1 if OWNER.get(target) == name else 0} for kind, target in rows]
	doctype = "Sidebar" if frappe.db.exists("DocType", "Sidebar") else "Workspace Sidebar"
	upsert(doctype, name, {"title": name, "header_icon": icon, "app": APP, "module": DESK_MODULE[name], "standard": 1, "items": items}, child_tables=("items",))


def desktop_icon(name, icon, roles, seq):
	upsert("Desktop Icon", "OneBook School", {"label": "OneBook School", "icon_type": "App", "app": APP, "link_type": "External",
		"link": "/desk/correspondent", "logo_url": "/assets/onebook_school/images/onebook-school.svg", "standard": 1, "hidden": 0})  # fmt: skip
	upsert("Desktop Icon", name, {"label": name, "icon_type": "Link", "icon": icon, "app": APP, "link_type": "Workspace Sidebar",
		"link_to": name, "parent_icon": "OneBook School", "standard": 1, "hidden": 0, "idx": seq + 1,
		"roles": [{"role": r} for r in roles]}, child_tables=("roles",))  # fmt: skip


def dock():
	items = [{"link_type": "Workspace", "link_to": name, "title": name, "icon": spec[0]} for name, spec in WORKSPACES.items()]
	name = frappe.db.get_value("Dock", {"app": APP, "user": ["is", "not set"]})
	values = {"app": APP, "standard": 1, "items": items}
	if name:
		doc = frappe.get_doc("Dock", name)
		doc.set("items", [])
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(dict(values, doctype="Dock")).insert(ignore_permissions=True)


def upsert(doctype, name, values, child_tables=()):
	values = {k: v for k, v in values.items() if frappe.get_meta(doctype).has_field(k) or k in child_tables}
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for table in child_tables:
			doc.set(table, [])
		doc.update(values)
		doc.flags.ignore_permissions = True
		doc.flags.ignore_links = True
		doc.save()
		return doc
	doc = frappe.new_doc(doctype)
	doc.update(values)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_links = True
	doc.insert(set_name=name)
	return doc
