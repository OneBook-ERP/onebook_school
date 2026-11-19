"""The school day for the demo: eight periods and two breaks, who teaches what in every section, a generated
timetable, the Half Yearly exam schedule, and the demo teacher logins linked to their HR records. One subject's
Quarterly marks are taken back out so the principal and the teacher see a real pending item."""

import frappe
from frappe.utils import add_days, getdate

from onebook_school.demo.classes import CLASSES, SUBJECTS, group_name, sections_of
from onebook_school.demo.school import YEAR, email
from onebook_school.school_day import timetable

PERIODS = [
	(1, "P1", "09:00", "09:40", 0), (2, "P2", "09:40", "10:20", 0), (3, "Break", "10:20", "10:35", 1), (4, "P3", "10:35", "11:15", 0),
	(5, "P4", "11:15", "11:55", 0), (6, "Lunch", "11:55", "12:40", 1), (7, "P5", "12:40", "13:20", 0), (8, "P6", "13:20", "14:00", 0),
	(9, "P7", "14:00", "14:40", 0), (10, "P8", "14:40", "15:20", 0),
]  # fmt: skip
PER_WEEK = {"Tamil": 7, "English": 7, "Mathematics": 8, "Science": 7, "Social Science": 6, "Environmental Science": 6, "Computer Science": 4,
			"Physics": 6, "Chemistry": 6, "Biology": 6, "Numbers": 6, "Rhymes and Stories": 5}  # fmt: skip
TEAMS = {
	"Tamil": ["S. Kalaiselvi", "R. Murugesan", "A. Selvi", "G. Mahalakshmi"],
	"English": ["V. Jayanthi", "J. Kavitha", "E. Malathi", "R. Geetha"],
	"Mathematics": ["P. Anitha", "S. Ramesh", "B. Arunkumar", "H. Sathish", "S. Kannan"],
	"Science": ["N. Karthikeyan", "T. Sumathi", "L. Vasanthi", "I. Deepa"],
	"Environmental Science": ["K. Uma", "N. Shanthi"],
	"Social Science": ["K. Senthilkumar", "M. Gopinath", "D. Prabhu"],
	"Computer Science": ["U. Venkatesh", "P. Manikandan"],
	"Physics": ["S. Balamurugan", "V. Suresh"], "Chemistry": ["M. Priya", "A. Rajendran"], "Biology": ["T. Nirmala", "C. Thangaraj"],
	"Numbers": ["K. Uma", "N. Shanthi"], "Rhymes and Stories": ["J. Kavitha", "R. Geetha"],
}  # fmt: skip
FIXED = {("VI - A", "Mathematics"): "P. Anitha", ("VI - B", "Mathematics"): "P. Anitha", ("VIII - B", "Mathematics"): "P. Anitha",
		 ("X - A", "Science"): "N. Karthikeyan", ("X - B", "Science"): "N. Karthikeyan"}  # fmt: skip
PENDING_MARKS = ("VIII - B", "Mathematics")
DEMO_TEACHERS = {"teacher.vi": "P. Anitha", "teacher.x": "N. Karthikeyan"}


def load(ctx):
	periods()
	groups = assignments(ctx)
	if not frappe.db.exists("Timetable Slot", {"student_group": groups[0]}):
		result = timetable.generate(groups)
		ctx.made(result["placed"])
	link_teacher_logins()
	exam_schedule(ctx)
	take_back_marks()


def periods():
	settings = frappe.get_single("School Settings")
	if settings.periods:
		return
	for no, label, start, end, brk in PERIODS:
		settings.append("periods", {"period_no": no, "label": label, "start_time": f"{start}:00", "end_time": f"{end}:00", "is_break": brk})
	settings.save(ignore_permissions=True)


def instructor(name):
	return frappe.db.get_value("Instructor", {"instructor_name": name})


def assignments(ctx):
	groups, turn = [], {}
	for cls in CLASSES:
		for sec in sections_of(cls, ctx.scale):
			group = group_name(cls, sec)
			groups.append(group)
			for subject in SUBJECTS[cls]:
				if frappe.db.exists("Teaching Assignment", {"student_group": group, "course": subject}):
					continue
				team = TEAMS[subject]
				name = FIXED.get((group, subject)) or team[turn.setdefault(subject, 0) % len(team)]
				turn[subject] += 1
				frappe.get_doc(
					{"doctype": "Teaching Assignment", "student_group": group, "course": subject, "instructor": instructor(name), "periods_per_week": PER_WEEK[subject]}
				).insert(ignore_permissions=True)  # fmt: skip
				ctx.made()
	return groups


def link_teacher_logins():
	for login, name in DEMO_TEACHERS.items():
		employee = frappe.db.get_value("Instructor", instructor(name), "employee")
		if employee:
			frappe.db.set_value("Employee", employee, "user_id", email(login))


def exam_schedule(ctx):
	if frappe.db.exists("Exam Schedule", {"exam": "Half Yearly", "academic_year": YEAR}):
		return
	papers = []
	for cls in CLASSES:
		if cls in ("LKG", "UKG"):
			continue
		day = getdate("2026-12-08")
		for subject in SUBJECTS[cls]:
			while day.weekday() == 6:
				day = add_days(day, 1)
			papers.append({"program": cls, "course": subject, "exam_date": day, "start_time": "10:00:00", "end_time": "12:30:00" if cls.startswith("Std X") or cls.startswith("Std IX") else "12:00:00"})
			day = add_days(day, 1)
	frappe.get_doc({"doctype": "Exam Schedule", "academic_year": YEAR, "exam": "Half Yearly", "papers": papers}).insert(ignore_permissions=True)
	ctx.made()


def take_back_marks():
	group, subject = PENDING_MARKS
	name = frappe.db.get_value("Mark Entry", {"student_group": group, "course": subject, "exam": "Quarterly", "docstatus": 1})
	if name:
		doc = frappe.get_doc("Mark Entry", name)
		doc.flags.ignore_permissions = True
		doc.cancel()
		frappe.delete_doc("Mark Entry", name, ignore_permissions=True, force=True)
