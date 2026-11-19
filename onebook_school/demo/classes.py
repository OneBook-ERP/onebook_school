"""Classes LKG to XII as Programs, subjects as Courses, sections as batch-based Student Groups, and the teachers."""

import random

import frappe

from onebook_school.demo.school import YEAR

PRIMARY = ["Tamil", "English", "Mathematics", "Environmental Science", "Computer Science"]
MIDDLE = ["Tamil", "English", "Mathematics", "Science", "Social Science"]
SUBJECTS = {
	"LKG": ["English", "Tamil", "Numbers", "Rhymes and Stories"],
	"UKG": ["English", "Tamil", "Numbers", "Rhymes and Stories"],
	**{f"Std {r}": PRIMARY for r in ("I", "II", "III", "IV", "V")},
	**{f"Std {r}": MIDDLE for r in ("VI", "VII", "VIII", "IX", "X")},
	"Std XI - Bio-Maths": ["Tamil", "English", "Physics", "Chemistry", "Biology", "Mathematics"],
	"Std XI - Computer Science": ["Tamil", "English", "Physics", "Chemistry", "Computer Science", "Mathematics"],
	"Std XII - Bio-Maths": ["Tamil", "English", "Physics", "Chemistry", "Biology", "Mathematics"],
	"Std XII - Computer Science": ["Tamil", "English", "Physics", "Chemistry", "Computer Science", "Mathematics"],
}
CLASSES = list(SUBJECTS)
TEACHERS = [
	"P. Anitha", "N. Karthikeyan", "S. Kalaiselvi", "R. Murugesan", "V. Jayanthi", "K. Senthilkumar", "T. Sumathi",
	"M. Gopinath", "A. Selvi", "D. Prabhu", "G. Mahalakshmi", "S. Ramesh", "L. Vasanthi", "B. Arunkumar", "J. Kavitha",
	"C. Thangaraj", "E. Malathi", "H. Sathish", "I. Deepa", "U. Venkatesh", "R. Geetha", "S. Balamurugan", "K. Uma",
	"P. Manikandan", "N. Shanthi", "V. Suresh", "M. Priya", "A. Rajendran", "T. Nirmala", "S. Kannan",
]  # fmt: skip


def sections_of(cls, scale):
	if scale == "small":
		return ["A"]
	return ["A"] if cls.startswith(("Std XI", "Std XII")) else ["A", "B"]


def group_name(cls, sec):
	short = cls.replace("Std ", "").replace(" - Computer Science", " CS").replace(" - Bio-Maths", " BM")
	return f"{short} - {sec}"


def load(ctx):
	for cls in CLASSES:
		if not frappe.db.exists("Program", cls):
			frappe.get_doc({"doctype": "Program", "program_name": cls, "program_abbreviation": cls[:10], "oc_company": ctx.company,
							"courses": [{"course": course(ctx, c), "course_name": c} for c in SUBJECTS[cls]]}).insert(ignore_permissions=True)  # fmt: skip
			ctx.made()
	for sec in ("A", "B"):
		if not frappe.db.exists("Student Batch Name", sec):
			frappe.get_doc({"doctype": "Student Batch Name", "batch_name": sec}).insert(ignore_permissions=True)
	teachers = [instructor(ctx, name) for name in TEACHERS]
	rng = random.Random(ctx.seed)
	pool = teachers[:]
	rng.shuffle(pool)
	fixed = {("Std VI", "A"): instructor(ctx, "P. Anitha"), ("Std X", "A"): instructor(ctx, "N. Karthikeyan")}
	for cls in CLASSES:
		for sec in sections_of(cls, ctx.scale):
			name = group_name(cls, sec)
			if frappe.db.exists("Student Group", name):
				continue
			teacher = fixed.get((cls, sec)) or pool.pop() if pool else teachers[0]
			frappe.get_doc(
				{"doctype": "Student Group", "student_group_name": name, "group_based_on": "Batch", "academic_year": YEAR,
				 "program": cls, "batch": sec, "oc_company": ctx.company, "obs_class_teacher": teacher, "max_strength": 40,
				 "instructors": [{"instructor": teacher}]}
			).insert(ignore_permissions=True)  # fmt: skip
			ctx.made()


def course(ctx, name):
	if not frappe.db.exists("Course", name):
		frappe.get_doc({"doctype": "Course", "course_name": name, "oc_company": ctx.company}).insert(ignore_permissions=True)
		ctx.made()
	return name


def instructor(ctx, name):
	existing = frappe.db.get_value("Instructor", {"instructor_name": name})
	if existing:
		return existing
	ctx.made()
	return frappe.get_doc({"doctype": "Instructor", "instructor_name": name, "status": "Active", "oc_company": ctx.company}).insert(ignore_permissions=True).name
