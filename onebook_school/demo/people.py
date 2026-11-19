"""Students and their parents. About one family in six has two children in the school; a few records are left
incomplete on purpose so the UDISE+ check has something to find; RTE children sit in LKG and Std I."""

import random

import frappe
from frappe.utils import add_days

from campus.setup.demo_data.names import FEMALE, MALE, SURNAMES
from onebook_school.demo.classes import CLASSES, group_name, sections_of
from onebook_school.demo.school import DOMAIN, YEAR, ensure_user

AGE = {cls: i for i, cls in enumerate(CLASSES)}  # LKG = 0 ... Std XII groups follow
BASE_YEAR = {"LKG": 2022, "UKG": 2021}
MOTHER_TONGUES = ["Tamil"] * 9 + ["Telugu", "Kannada", "Malayalam"]
CATEGORIES = ["BC"] * 5 + ["MBC"] * 3 + ["OC", "SC", "SC", "BCM", "ST"]
RELIGIONS = ["Hindu"] * 8 + ["Christian", "Muslim"]


def birth_year(cls):
	if cls in BASE_YEAR:
		return BASE_YEAR[cls]
	roman = cls.replace("Std ", "").split(" ")[0]
	numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
	return 2020 - numerals.index(roman)


def per_section(scale):
	return 10 if scale == "small" else 22


def load(ctx):
	rng = random.Random(ctx.seed)
	seats = [(cls, sec) for cls in CLASSES for sec in sections_of(cls, ctx.scale)]
	families = []
	serial = 0
	for cls, sec in seats:
		group = frappe.get_doc("Student Group", group_name(cls, sec))
		have = {s.student for s in group.students}
		need = per_section(ctx.scale) - len(have)
		for _i in range(max(need, 0)):
			serial += 1
			key = f"{cls}-{sec}-{len(have) + _i + 1}"
			student = make_student(ctx, rng, key, cls, serial)
			group.append("students", {"student": student, "group_roll_number": len(group.students) + 1, "active": 1})
			families.append(student)
		if need > 0:
			group.flags.ignore_permissions = True
			group.save()
	attach_families(ctx, rng, families)
	parent_login(ctx)


def make_student(ctx, rng, key, cls, serial):
	admission_no = f"SAV{serial:04d}"
	existing = frappe.db.get_value("Student", {"obs_admission_no": admission_no})
	if existing:
		return existing
	gender = rng.choice(["Female", "Male"])
	first = rng.choice(FEMALE if gender == "Female" else MALE)
	father = rng.choice(MALE)
	year = birth_year(cls)
	dob = f"{year}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
	complete = rng.random() > 0.08
	rte = cls in ("LKG", "Std I") and rng.random() < 0.18
	doc = frappe.get_doc(
		{
			"doctype": "Student", "first_name": first, "last_name": father, "gender": gender,
			"date_of_birth": dob if complete or rng.random() > 0.5 else None,
			"joining_date": f"{max(2014, year + 3)}-06-0{rng.randint(1, 9)}", "oc_company": ctx.company,
			"student_mobile_number": f"0{rng.randint(700000000, 999999999)}", "blood_group": rng.choice(["A+", "B+", "O+", "AB+", "O-"]),
			"nationality": "Indian", "obs_admission_no": admission_no, "student_email_id": f"{admission_no.lower()}@students.{DOMAIN}",
			"obs_emis_id": f"33{rng.randint(10**13, 10**14 - 1)}",
			"obs_pen": f"2{rng.randint(10**9, 10**10 - 1)}" if complete else None,
			"obs_apaar_consent": rng.choice(["Given"] * 6 + ["Pending", "Refused"]) if complete else "Pending",
			"obs_mother_tongue": rng.choice(MOTHER_TONGUES), "obs_social_category": rng.choice(CATEGORIES),
			"obs_religion": rng.choice(RELIGIONS), "obs_rte": 1 if rte else 0, "obs_cwsn": 1 if rng.random() < 0.01 else 0,
		}
	)  # fmt: skip
	doc.flags.ignore_permissions = True
	doc.insert()
	enrollment = frappe.get_doc(
		{"doctype": "Program Enrollment", "student": doc.name, "program": cls, "academic_year": YEAR,
		 "enrollment_date": "2026-06-02", "student_category": None}
	)  # fmt: skip
	enrollment.flags.ignore_permissions = True
	enrollment.insert()
	enrollment.submit()
	ctx.made(2)
	return doc.name


def attach_families(ctx, rng, students):
	"""One father (and mother) per child; every sixth child shares the parents of an elder child."""
	pending = [s for s in students if not frappe.db.exists("Student Guardian", {"parent": s, "parenttype": "Student"})]
	elders = []
	for i, student in enumerate(pending):
		row = frappe.db.get_value("Student", student, ["last_name", "date_of_birth"], as_dict=True)
		if i % 6 == 5 and elders:
			elder = rng.choice(elders)
			share_parents(student, elder)
			continue
		father = make_guardian(ctx, rng, f"{row.last_name} {rng.choice(SURNAMES)[0]}.", "Male")
		mother = make_guardian(ctx, rng, f"{rng.choice(FEMALE)} {row.last_name[0]}.", "Female")
		link(student, father, "Father")
		link(student, mother, "Mother")
		if row.date_of_birth:
			elders.append(student)


def make_guardian(ctx, rng, name, gender):
	doc = frappe.get_doc(
		{"doctype": "Guardian", "guardian_name": name, "gender": gender,
		 "mobile_number": f"0{rng.randint(700000000, 999999999)}",
		 "occupation": rng.choice(["Farmer", "Textile business", "Teacher", "Government employee", "Driver", "Homemaker", "Shop owner"])}
	)  # fmt: skip
	doc.insert(ignore_permissions=True)
	ctx.made()
	return doc


def link(student, guardian, relation):
	doc = frappe.get_doc("Student", student)
	doc.append("guardians", {"guardian": guardian.name, "guardian_name": guardian.guardian_name, "relation": relation})
	doc.flags.ignore_permissions = True
	doc.save()


def share_parents(student, elder):
	elder_doc = frappe.get_doc("Student", elder)
	doc = frappe.get_doc("Student", student)
	doc.last_name = elder_doc.last_name
	for g in elder_doc.guardians:
		doc.append("guardians", {"guardian": g.guardian, "guardian_name": g.guardian_name, "relation": g.relation})
	if not doc.date_of_birth or (elder_doc.date_of_birth and doc.date_of_birth <= elder_doc.date_of_birth):
		doc.date_of_birth = add_days(elder_doc.date_of_birth, 700) if elder_doc.date_of_birth else doc.date_of_birth
	doc.flags.ignore_permissions = True
	doc.save()


def parent_login(ctx):
	"""A guardian of a two-child family gets a portal login for the demo."""
	shared = frappe.db.sql(
		"""select guardian from `tabStudent Guardian` where parenttype='Student' and relation='Father'
		group by guardian having count(*) > 1 order by guardian limit 1"""
	)
	if not shared:
		return
	guardian = shared[0][0]
	mail = ensure_user(ctx, f"parent@{DOMAIN}", frappe.db.get_value("Guardian", guardian, "guardian_name"), ["Guardian"], user_type="Website User")
	frappe.db.set_value("Guardian", guardian, {"user": mail, "email_address": mail})
