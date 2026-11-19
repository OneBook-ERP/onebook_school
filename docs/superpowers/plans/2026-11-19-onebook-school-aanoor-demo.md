# OneBook School: Aanoor Vidyalaya Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A demo-ready site `aanoor.localhost` running a new `onebook_school` app on top of `campus`, branded and loaded as Sri Aanoor Vidyalaya Matric Hr Sec School (Muthur, Erode), covering the seven-step click path of the approved plan.

**Architecture:** `onebook_school` is a new Frappe app with `required_apps = ["campus"]`. Classes are Education Programs, sections are batch-based Student Groups, fees run on Education Fee Structure / Fee Schedule (which raise Sales Invoices) and ERPNext Payment Entry. School-only pieces (fee-committee cap, sibling concession, family receipt, marks and report cards, UDISE+ export, dashboard) live in `onebook_school`; campus is called only through `campus.<module>.api`, except `campus.campus_platform.verification.issue` which campus does not yet re-export.

**Tech Stack:** Frappe v16, ERPNext, HRMS, Education, India Compliance, frappe_whatsapp, campus (develop @ 10c1a9c), Python 3.14, MariaDB.

**Spec:** OneBook School — Product Plan (https://claude.ai/artifact/9bLk6k5tvcLoiEpwM6SCjM), sections "Demo tomorrow" and "Product", approved 2026-11-19.

## Global Constraints

- Never edit frappe, erpnext, hrms, education, india_compliance, frappe_whatsapp or campus in this plan.
- Custom fields on upstream DocTypes use the `obs_` prefix, created in code with `create_custom_fields` from `after_install` and `after_migrate`; no fixture JSON for fields.
- DocType names checked for clashes against all installed apps before creation.
- Tests run only on `campus-test.localhost`; the demo runs on `aanoor.localhost`; never touch `education.localhost`.
- Demo data is synthetic: Tamil names from campus's generator, phone numbers starting with 0, e-mails at `aanoor.example.edu`, no Aadhaar numbers.
- School identity: "Sri Aanoor Vidyalaya Matriculation Higher Secondary School", Kodumudi Road, Muthur, Erode 638105, Tamil Nadu; established 1989; board "Tamil Nadu State Board (Matriculation)"; logo from the school's Play Store app (`scratchpad/school-assets/aanoor-logo.png`).
- Academic year `2026-27` with terms `Term 1`, `Term 2`, `Term 3`; demo "today" is the real date.
- Classes: LKG, UKG, Std I to Std X, Std XI and Std XII each in two groups (Bio-Maths, Computer Science); sections A and B up to Std X, one section per XI/XII group. About 600 students.
- TN grade scale: A1 91–100, A2 81–90, B1 71–80, B2 61–70, C1 51–60, C2 41–50, D 35–40, E below 35.
- A transfer certificate must never be withheld for unpaid fees (Madras HC, July 2024). Campus's TC dues gate conflicts; the demo issues a TC only for a paid-up student, and a campus follow-up PR makes the gate a per-company setting.
- No commits carry Claude attribution trailers.

## Review Focus

- Fee Structure amended mid-year: the committee cap is checked on the amended structure, and a cancelled structure no longer counts.
- Sibling concession for a child whose elder sibling has left the school: no concession.
- Family Receipt amount smaller than total outstanding: allocates oldest invoice first, never over-allocates an invoice, and leaves the rest outstanding.
- Mark Entry with an absent student or marks above max: absent counts as 0 and shows "AB"; marks above max are refused.
- UDISE export for a student with no guardian or no DOB: the row still appears, with each missing field named in Issues.

---

### Task 1: Scaffold `onebook_school` and the demo site

**Files:**
- Create: `apps/onebook_school/` via `bench new-app onebook_school` (module "OneBook School", license GPL-3, required_apps `["campus"]`)
- Create: `onebook_school/install.py` with `after_install()` and `after_migrate()` both calling `setup.custom_fields.create_all()`
- Create: `onebook_school/setup/custom_fields.py`
- Move: this plan into `apps/onebook_school/docs/superpowers/plans/`

**Interfaces:**
- Produces: custom fields on Student `obs_admission_no` (Data), `obs_emis_id` (Data), `obs_pen` (Data), `obs_apaar_id` (Data), `obs_apaar_consent` (Select: `\nPending\nGiven\nRefused`), `obs_mother_tongue` (Data), `obs_social_category` (Select: `\nOC\nBC\nBCM\nMBC\nSC\nSCA\nST`), `obs_religion` (Select: `\nHindu\nMuslim\nChristian\nOthers`), `obs_rte` (Check), `obs_cwsn` (Check); on Student Group `obs_class_teacher` (Link Instructor).

- [ ] Step 1: Create the app, git init, first commit.
- [ ] Step 2: Create site `aanoor.localhost` (`bench new-site aanoor.localhost --db-root-password 123 --admin-password admin --install-app erpnext`), then install hrms, education, india_compliance, frappe_whatsapp, campus, onebook_school; set `developer_mode 1` and `campus_demo_site 1` in its site config.
- [ ] Step 3: Complete the setup wizard in code: company "Sri Aanoor Vidyalaya Matric Hr Sec School", abbr `SAV`, country India, currency INR, fiscal year Apr–Mar, then `bench --site aanoor.localhost migrate`.
- [ ] Step 4: Install onebook_school on `campus-test.localhost`; write test `test_custom_fields.py::test_student_fields_exist` asserting each field above is on Student; run it: PASS.
- [ ] Step 5: Verify `http://aanoor.localhost:8003` serves the login page; commit.

### Task 2: Fee Committee Order and the fee cap

**Files:**
- Create: DocType `Fee Committee Order` (submittable; fields `company`, `order_number`, `order_date`, `valid_from_year` Link Academic Year, `valid_to_year` Link Academic Year, `order_file` Attach, `lines` Table) and child `Fee Committee Order Line` (`program` Link Program, `fee_category` Link Fee Category, `approved_amount` Currency)
- Create: `onebook_school/fees/fee_cap.py`
- Create: print format `Fee Display (Notice Board)` on Fee Committee Order
- Modify: `hooks.py` doc_events `Fee Structure.validate`
- Test: `onebook_school/tests/test_fee_cap.py`

**Interfaces:**
- Produces: `fee_cap.check_fee_structure(doc, method=None) -> None` (throws), `fee_cap.approved_amounts(company: str, program: str, academic_year: str) -> dict[str, float]` (fee_category → amount from the submitted order valid for that year; empty dict when none).

- [ ] Step 1: Tests: `test_structure_within_cap_saves`, `test_structure_over_cap_refused` (message names the category, the approved and the asked amount), `test_no_order_means_no_cap`, `test_cancelled_order_ignored`.
- [ ] Step 2: Run, expect FAIL.
- [ ] Step 3: Implement; compare per fee category the sum of the structure's components against the approved amount.
- [ ] Step 4: Run, expect PASS. Print format shows school logo, order number and date, validity, class × category table, total per class. Commit.

### Task 3: Sibling concession

**Files:**
- Create: Single DocType `School Settings` (`company`, `udise_code`, `emis_school_id`, `board`, `sibling_discount_percent` Percent, `logo` Attach Image)
- Create: `onebook_school/fees/sibling.py`
- Modify: `hooks.py` doc_events `Sales Invoice.before_validate`
- Test: `onebook_school/tests/test_sibling.py`

**Interfaces:**
- Produces: `sibling.apply_sibling_discount(doc, method=None) -> None`; `sibling.has_elder_sibling(student: str) -> bool` (another enabled Student sharing a Guardian, older date of birth, with an active Program Enrollment).

- [ ] Step 1: Tests: `test_second_child_gets_discount` (draft invoice for the younger sibling gets `additional_discount_percentage == sibling_discount_percent`), `test_eldest_child_no_discount`, `test_elder_sibling_left_no_discount`, `test_non_student_invoice_untouched`.
- [ ] Step 2: FAIL. Step 3: implement (only on draft invoices with `student` set and no discount already given). Step 4: PASS. Commit.

### Task 4: Family Receipt

**Files:**
- Create: DocType `Family Receipt` (submittable; `guardian` Link Guardian, `company`, `posting_date`, `mode_of_payment`, `reference_no`, `amount_paid` Currency, `allocations` Table, `total_allocated` Currency) and child `Family Receipt Allocation` (`student`, `student_name`, `sales_invoice`, `outstanding_amount`, `allocated_amount`, `payment_entry` Link Payment Entry read-only)
- Create: print format `Family Receipt`
- Test: `onebook_school/tests/test_family_receipt.py`

**Interfaces:**
- Produces: whitelisted `onebook_school.fees.family.get_outstanding(guardian: str, company: str) -> list[dict]` (one row per submitted, unpaid Sales Invoice of the guardian's students, oldest due date first); `FamilyReceipt.allocate()` fills `allocations` from `amount_paid`; `on_submit` creates and submits one Payment Entry per allocation row; `on_cancel` cancels them.

- [ ] Step 1: Tests: `test_full_payment_two_children`, `test_partial_payment_oldest_first`, `test_never_over_allocates_an_invoice`, `test_cancel_cancels_payment_entries`.
- [ ] Step 2: FAIL. Step 3: implement with `erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry("Sales Invoice", name, party_amount=allocated)`. Step 4: PASS. Form button "Get Dues" calls `get_outstanding`. Commit.

### Task 5: Marks and report cards

**Files:**
- Create: DocType `Mark Entry` (submittable; `academic_year`, `exam` Select `Quarterly\nHalf Yearly\nAnnual`, `student_group`, `course`, `max_marks` Int default 100, `rows` Table) with child `Mark Entry Row` (`student`, `student_name`, `marks` Float, `absent` Check); DocType `Report Card` (`student`, `student_name`, `student_group`, `academic_year`, `exam`, `subjects` Table, `total`, `max_total`, `percentage`, `overall_grade`, `attendance_percent`, `remarks`) with child `Report Card Subject` (`course`, `max_marks`, `marks`, `absent`, `grade`)
- Create: `onebook_school/assessment/grading.py`, print format `Report Card (TN)`
- Test: `onebook_school/tests/test_report_card.py`

**Interfaces:**
- Produces: `grading.grade_for(percent: float) -> str` per the TN scale; `MarkEntry.get_students()` (fills rows from the Student Group's active students in roll order); `MarkEntry.on_submit` upserts the subject row on each student's Report Card for (student, academic_year, exam) and recomputes totals; one Report Card per student per exam (unique check).

- [ ] Step 1: Tests: `test_grade_boundaries` (91→A1, 90→A2, 35→D, 34.9→E), `test_marks_above_max_refused`, `test_absent_counts_zero_shows_ab`, `test_submit_builds_report_card_totals`, `test_second_subject_updates_same_card`.
- [ ] Step 2: FAIL. Step 3: implement. Step 4: PASS. Print format: logo, school name in English and Tamil (ஸ்ரீ ஆனூர் வித்யாலயா மெட்ரிகுலேஷன் மேல்நிலைப் பள்ளி), student, class-section, roll no, subject table with grade, total, percentage, attendance, class teacher and principal signature lines. Commit.

### Task 6: UDISE+ student export

**Files:**
- Create: Script Report `UDISE Student Export` (ref DocType Student) with filters `academic_year` (reqd), `program`, `student_group`
- Create: `onebook_school/compliance/udise.py`
- Test: `onebook_school/tests/test_udise.py`

**Interfaces:**
- Produces: `udise.student_issues(row: dict) -> list[str]`; report columns in this order: UDISE Code, Class, Section, Roll No, Admission No, Student Name, Gender, Date of Birth, Mother Tongue, Social Category, Religion, Father's Name, Mother's Name, Guardian Mobile, EMIS ID, PEN, APAAR ID, APAAR Consent, RTE, CWSN, Admission Date, Issues. Issues lists each missing one of: Date of Birth, Gender, Father's or Mother's Name, Social Category, EMIS ID, PEN, APAAR Consent.

- [ ] Step 1: Tests: `test_complete_student_has_no_issues`, `test_missing_fields_named` (student without DOB and guardian lists both), `test_filters_by_section`.
- [ ] Step 2: FAIL. Step 3: implement (guardian names from Student Guardian rows by relation Father/Mother). Step 4: PASS. Report summary shows rows with issues vs ready. Commit.

### Task 7: Demo data loader

**Files:**
- Create: `onebook_school/demo/__init__.py` with `load(seed: int = 2026) -> dict`, and step modules `school.py` (company details, School Settings, logo, branding: Website Settings / Navbar app logo, Institution Profile with every higher-ed pack off), `calendar.py`, `classes.py` (Programs, Courses per stage, Student Groups with class teacher), `people.py` (Guardians with ~15% two-child families, Students with all `obs_` fields filled for ~90% and deliberately missing PEN/DOB for a few, Program Enrollments, RTE flag on 8 LKG/Std I students), `staff.py` (about 30 Instructors and Employees; users: correspondent, principal, accountant, front office, two class teachers, one parent, password `Aanoor@Demo2026`), `fees.py` (Fee Categories Tuition, Term, Books & Notebooks, Computer, Van; Fee Committee Order within cap; Fee Structures per class; Term 1 Fee Schedule per class; ~70% families paid through Family Receipt, ~10 paid today), `attendance.py` (today and the past 20 school days, ~92% present), `marks.py` (Quarterly Mark Entries for Std VI–X all subjects, submitted), `enquiries.py` (6 CRM Leads and 3 Student Applicants for 2027-28 LKG), `messages.py` (campus Message Templates `fee_due`, `absent_today`, `results_out` in English and Tamil), `certificate.py` (Transfer Certificate Certificate Type, verifiable; one issued TC for a paid-up Std X leaver)
- Test: `onebook_school/tests/test_demo_load.py`

**Interfaces:**
- Consumes: Tasks 1–6 DocTypes; `campus.setup.demo_data.names.People` for names; campus `Message Template`, `Certificate Request`, `Certificate Type`.
- Produces: idempotent `load()`; every record found by natural key first; returns `{"created": int, "seconds": float}`. Refuses unless `campus_demo_site` or developer mode.

- [ ] Step 1: Test `test_load_is_idempotent` (second run creates 0) and `test_counts` (≥ 550 students, 26 student groups, Term 1 invoices for every enrolled non-RTE student, ≥ 1 Report Card per Std VI–X student) with `seed=7` and a `scale="small"` option (one section per class, 10 students each) for test speed.
- [ ] Step 2: FAIL. Step 3: implement steps. Step 4: PASS on campus-test. Step 5: run full `load()` on `aanoor.localhost`; commit.

### Task 8: School dashboard and desk

**Files:**
- Create: Workspace `School` (public, module OneBook School) with Number Cards `Collected Today`, `Outstanding Fees`, `Students Enrolled`, `Present Today %` (method card `onebook_school.dashboard.present_today`), Dashboard Chart `Dues by Class` (method chart `onebook_school.dashboard.dues_by_class`), shortcuts to Family Receipt, Mark Entry, Report Card, UDISE Student Export, Fee Committee Order, Student, Certificate Request
- Create: `onebook_school/dashboard.py`
- Test: `onebook_school/tests/test_dashboard.py`

**Interfaces:**
- Produces: `dashboard.present_today() -> dict` (Number Card method result), `dashboard.dues_by_class() -> dict` (chart data labels = class, values = outstanding).

- [ ] Step 1: Tests: `test_present_today_percent` and `test_dues_by_class_sums_outstanding`. Step 2: FAIL. Step 3: implement. Step 4: PASS.
- [ ] Step 5: On `aanoor.localhost`, set the School workspace as home for the correspondent, principal and accountant users and hide higher-ed areas; check each user's desk in the browser. Commit.

### Task 9: Rehearsal

- [ ] Step 1: Walk the seven-step click path in the browser as each demo user; fix any error found (each fix with its test in the owning task's test file).
- [ ] Step 2: Write `apps/onebook_school/docs/demo-script.md`: logins, the click path with exact record names (the two-child family, the defaulter class, the TC student, the section for UDISE), and fallbacks.
- [ ] Step 3: `bench --site aanoor.localhost backup` so the demo can be restored if something goes wrong; commit.
