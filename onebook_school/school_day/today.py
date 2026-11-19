"""Today: what each person who logs in needs to see first, and the next thing to do, built from live records.

`get_today()` returns sections in the order they should be read: decisions before numbers. Each item is one line
(`text`, optional `sub`) with an optional action the Today block renders as a button:
`{"label", "kind": "route", "route"}` or `{"label", "kind": "cover", "args": {date, period_no, student_group}}`.
"""

import frappe
from frappe.utils import flt, fmt_money, formatdate, get_time, getdate, now_datetime, nowdate

from onebook_school.school_day import cover, exams
from onebook_school.school_day.timetable import slots_for, teaching_periods

LEADERS = {"School Principal", "School Correspondent", "System Manager"}


def build(user):
	roles = set(frappe.get_roles(user))
	instructor = instructor_of(user)
	today = nowdate()
	payload = {
		"date": today, "weekday": getdate(today).strftime("%A"),
		"greeting": greeting(user), "sections": [],
	}  # fmt: skip
	sections = payload["sections"]
	if instructor:
		sections += teacher_sections(instructor, today)
	if roles & LEADERS:
		sections += leader_sections(user, today, money_first="School Correspondent" in roles)
	if "School Accountant" in roles and not roles & LEADERS:
		sections += accountant_sections(today)
	if "School Office" in roles and not roles & LEADERS:
		sections += office_sections()
	payload["sections"] = [s for s in sections if s["items"]]
	return payload


@frappe.whitelist()
def get_today():
	return build(frappe.session.user)


def greeting(user):
	hour = now_datetime().hour
	part = "Good morning" if hour < 12 else "Good afternoon" if hour < 16 else "Good evening"
	name = frappe.db.get_value("User", user, "full_name") or ""
	return f"{part}, {name}".strip(", ")


def instructor_of(user):
	employee = frappe.db.get_value("Employee", {"user_id": user, "status": "Active"})
	return employee and frappe.db.get_value("Instructor", {"employee": employee, "status": "Active"})


def periods_by_no():
	return {p["period_no"]: p for p in teaching_periods()}


def when(period, now):
	start, end = get_time(period["start_time"]), get_time(period["end_time"])
	return "done" if now > end else "now" if start <= now <= end else "later"


def hhmm(value):
	return get_time(value).strftime("%H:%M") if value else ""


def item(text, sub=None, action=None, tone=None):
	return {k: v for k, v in {"text": text, "sub": sub, "action": action, "tone": tone}.items() if v}


def section(key, title, tone, items):
	return {"key": key, "title": title, "tone": tone, "items": items}


def route(label, path):
	return {"label": label, "kind": "route", "route": path}


# ---- teacher ----------------------------------------------------------------------------------------------------


def teacher_sections(instructor, today):
	weekday = getdate(today).strftime("%A")
	if instructor in cover.away_instructors(today):
		return [section("now_next", "Your day", "info", [item("You are marked away today. Your periods are being covered.")])]
	periods = periods_by_no()
	rows = [dict(s, cover_for=None) for s in slots_for(instructor=instructor, weekday=weekday)]
	for c in frappe.get_all("Cover Assignment", filters={"date": today, "cover_instructor": instructor}, fields=["period_no", "student_group", "course", "absent_instructor"]):
		rows.append({"period_no": c.period_no, "student_group": c.student_group, "course": c.course,
					 "cover_for": frappe.db.get_value("Instructor", c.absent_instructor, "instructor_name")})  # fmt: skip
	now = now_datetime().time()
	day, next_marked = [], False
	for r in sorted(rows, key=lambda r: r["period_no"]):
		p = periods.get(r["period_no"])
		if not p:
			continue
		state = when(p, now)
		label = "NOW" if state == "now" else ("NEXT" if state == "later" and not next_marked else "")
		next_marked = next_marked or label == "NEXT"
		cover_note = f" · cover for {r['cover_for']}" if r["cover_for"] else ""
		day.append(item(
			f"{p['label']} {hhmm(p['start_time'])} · {r['student_group']} · {r['course']}{cover_note}",
			sub=label or ("done" if state == "done" else None),
			action=route("Take attendance", f"/desk/student-attendance-tool?student_group={r['student_group']}") if state != "done" else None,
			tone="alert" if r["cover_for"] else ("now" if label == "NOW" else None),
		))  # fmt: skip
	todo = attendance_todo(instructor, today) + marks_todo(instructor)
	pairs = my_papers(instructor)
	mine = [e for e in exams.upcoming(30, sorted({p for p, _c in pairs})) if (e["program"], e["course"]) in pairs]
	exam_items = [item(f"{formatdate(e['exam_date'], 'EEE d MMM')} · {e['program']} · {e['course']}", sub=f"{e['exam']} · you teach this paper") for e in mine[:6]]
	return [
		section("now_next", f"Your periods today ({len(day)})" if day else "Your periods today", "info", day or [item("No periods on the timetable today.")]),
		section("todo", "To do", "alert", todo),
		section("my_exams", "Exams coming up for your classes", "info", exam_items),
	]


def my_papers(instructor):
	"""(class, subject) pairs the teacher teaches, so only their own exam papers are shown."""
	rows = frappe.get_all("Teaching Assignment", filters={"instructor": instructor}, fields=["student_group", "course"])
	return {(frappe.db.get_value("Student Group", r.student_group, "program"), r.course) for r in rows}


def attendance_todo(instructor, today):
	rows = []
	for group in frappe.get_all("Student Group", filters={"obs_class_teacher": instructor, "disabled": 0}, pluck="name"):
		if not frappe.db.exists("Student Attendance", {"student_group": group, "date": today, "docstatus": 1}):
			rows.append(item(f"Take today's attendance for {group}", action=route("Take attendance", f"/desk/student-attendance-tool?student_group={group}")))
	return rows


def latest_exam():
	return frappe.db.get_value("Mark Entry", {"docstatus": 1}, "exam", order_by="creation desc")


def missing_marks(filters=None):
	"""(section, subject, teacher) whose marks are not in for the latest exam while the section's other subjects are."""
	exam = latest_exam()
	if not exam:
		return [], None
	entered = {(m.student_group, m.course) for m in frappe.get_all("Mark Entry", filters={"exam": exam, "docstatus": 1}, fields=["student_group", "course"])}
	started = {g for g, _c in entered}
	rows = []
	for a in frappe.get_all("Teaching Assignment", filters=filters or {}, fields=["student_group", "course", "instructor", "instructor_name"]):
		if a.student_group in started and (a.student_group, a.course) not in entered:
			rows.append(a)
	return rows, exam


def marks_todo(instructor):
	rows, exam = missing_marks({"instructor": instructor})
	return [item(f"Enter {exam} marks: {r.student_group} · {r.course}", action=route("Enter marks", "/desk/mark-entry/new")) for r in rows]


# ---- principal / correspondent ----------------------------------------------------------------------------------


def leader_sections(user, today, money_first=False):
	attention = []
	periods = periods_by_no()
	now = now_datetime().time()
	open_rows = [r for r in cover.uncovered(today) if periods.get(r["period_no"]) and when(periods[r["period_no"]], now) != "done"]
	for r in open_rows[:6]:
		p = periods.get(r["period_no"], {})
		attention.append(item(
			f"No teacher: {p.get('label', 'P' + str(r['period_no']))} {hhmm(p.get('start_time'))} · {r['student_group']} · {r['course']}",
			sub=f"{r['instructor_name']} is away",
			action={"label": "Assign cover", "kind": "cover", "period_label": p.get("label"), "args": {"date": today, "period_no": r["period_no"], "student_group": r["student_group"]}},
			tone="alert",
		))  # fmt: skip
	if len(open_rows) > 6:
		attention.append(item(f"+{len(open_rows) - 6} more periods need cover today", action=route("Timetable", "/desk/timetable-slot")))
	missing, exam = missing_marks()
	by_teacher = {}
	for m in missing:
		by_teacher.setdefault(m.instructor_name or m.instructor, []).append(f"{m.student_group} {m.course}")
	for teacher, subjects in sorted(by_teacher.items(), key=lambda kv: -len(kv[1]))[:5]:
		attention.append(item(f"{exam} marks pending from {teacher}", sub=", ".join(subjects[:4]) + (" …" if len(subjects) > 4 else ""), action=route("Open", "/desk/mark-entry")))
	not_taken = sections_without_attendance(today)
	if not_taken:
		attention.append(item(f"Attendance not taken yet in {len(not_taken)} sections", sub=", ".join(not_taken[:8]), action=route("Open", "/desk/student-attendance")))
	attention += approvals(user)

	day = day_items(today)
	exam_items = exam_lines()
	fees = fee_items()
	out = [section("attention", "Needs your attention", "alert", attention)]
	out += [section("fees", "Fees", "info", fees)] if money_first else []
	out += [section("day", "The school today", "ok", day), section("exams", "Exams", "info", exam_items)]
	out += [] if money_first else [section("fees", "Fees", "info", fees)]
	return out


def sections_without_attendance(today):
	groups = frappe.get_all("Student Group", filters={"group_based_on": "Batch", "disabled": 0}, pluck="name")
	taken = set(frappe.get_all("Student Attendance", filters={"date": today, "docstatus": 1}, pluck="student_group", distinct=True))
	return sorted(g for g in groups if g not in taken)


def approvals(user):
	try:
		from campus.campus_platform.api import pending_approvals

		rows = pending_approvals(user)
	except Exception:
		return []
	return [item(f"Approve {r.get('reference_doctype')} {r.get('reference_name')}", action=route("Review", f"/desk/approval-request/{r.get('name')}")) for r in rows[:5]]


def day_items(today):
	marks = frappe.get_all("Student Attendance", filters={"date": today, "docstatus": 1}, fields=["status"])
	present = sum(1 for m in marks if m.status == "Present")
	rows = []
	if marks:
		rows.append(item(f"{round(present * 100 / len(marks), 1)}% of students present · {len(marks) - present} absent", action=route("Absentees", "/desk/student-attendance?status=Absent&date=" + today)))
	away = cover.away_instructors(today)
	if away:
		names = [frappe.db.get_value("Instructor", i, "instructor_name") for i in sorted(away)]
		rows.append(item(f"{len(away)} teachers away: {', '.join(names)}"))
	return rows


def exam_lines():
	papers = exams.upcoming(45)
	if not papers:
		return []
	first = papers[0]
	days = (getdate(first["exam_date"]) - getdate(nowdate())).days
	rows = [item(f"{first['exam']} exams start in {days} days ({formatdate(first['exam_date'], 'EEE d MMM')})", sub=f"{len(papers)} papers in the next 45 days",
				 action=route("Schedule", "/desk/exam-schedule"))]  # fmt: skip
	return rows


def fee_items():
	rows = frappe.db.sql(
		"""select obs_program, count(distinct student) n, sum(outstanding_amount) due from `tabSales Invoice`
		where docstatus=1 and outstanding_amount>0 and status='Overdue' and student is not null
		group by obs_program order by due desc limit 3""",
		as_dict=True,
	)
	return [item(f"{r.obs_program}: {fmt_money(r.due, currency='INR')} overdue", sub=f"{r.n} students", action=route("Call list", "/desk/sales-invoice?status=Overdue&obs_program=" + (r.obs_program or ""))) for r in rows]


# ---- fees office and front office ------------------------------------------------------------------------------


def accountant_sections(today):
	collected = frappe.db.sql("select sum(paid_amount) from `tabPayment Entry` where docstatus=1 and payment_type='Receive' and posting_date=%s", today)[0][0]
	rows = [item(f"Collected today: {fmt_money(flt(collected), currency='INR')}", action=route("New receipt", "/desk/family-receipt/new"))]
	families = frappe.db.sql(
		"""select g.guardian, g.guardian_name, sum(si.outstanding_amount) due, count(distinct si.student) kids
		from `tabSales Invoice` si join `tabStudent Guardian` g on g.parent=si.student and g.parenttype='Student' and g.relation='Father'
		where si.docstatus=1 and si.status='Overdue' group by g.guardian order by due desc limit 10""",
		as_dict=True,
	)
	calls = [
		item(f"{f.guardian_name} · {fmt_money(f.due, currency='INR')}", sub=f"{f.kids} child(ren) · {frappe.db.get_value('Guardian', f.guardian, 'mobile_number') or ''}",
			 action=route("Take payment", f"/desk/family-receipt/new?guardian={f.guardian}"))
		for f in families
	]  # fmt: skip
	return [section("fees_today", "Fees today", "ok", rows), section("call_list", "Call today: largest overdue families", "alert", calls)]


def office_sections():
	leads = frappe.get_all("Lead", filters={"status": ["in", ["Open", "Replied", "Interested"]]}, fields=["name", "lead_name"], limit=8)
	drafts = frappe.get_all("Certificate Request", filters={"docstatus": 0}, fields=["name", "student_name", "certificate_type"], limit=8)
	return [
		section("enquiries", "Enquiries to follow up", "alert", [item(l.lead_name, action=route("Open", f"/desk/lead/{l.name}")) for l in leads]),
		section("certificates", "Certificates waiting", "info", [item(f"{d.certificate_type} for {d.student_name}", action=route("Open", f"/desk/certificate-request/{d.name}")) for d in drafts]),
	]
