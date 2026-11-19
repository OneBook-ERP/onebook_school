# Today Operating Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Timetable, cover for absent teachers, exam schedule, and a role-shaped "Today" block on every school workspace.

**Architecture:** New DocTypes and services in onebook_school (`school_day/`), one whitelisted `today.get_today()` that returns
role-shaped sections, rendered by a Custom HTML Block placed first on each role workspace.

**Tech Stack:** Frappe v16, Education, HRMS (Attendance), onebook_school.

**Spec:** `docs/superpowers/specs/2026-11-19-today-operating-layer-design.md`

## Global Constraints

- Weekdays Monday–Saturday; School Settings holds the periods (8 teaching periods a day in the demo).
- A teacher is "away" today when a submitted HRMS Attendance for their Employee is Absent or On Leave.
- Teacher identity: User → Employee.user_id → Instructor.employee.
- Tests on campus-test2.localhost; demo on aanoor.localhost. No upstream edits. No AI attribution in commits.

## Review Focus

- Generator with more periods demanded than slots: places what fits, reports the rest, never double-books a teacher.
- A cover teacher assigned twice in the same period: refused.
- Cover suggestion never offers a teacher who is away or already teaching that period.
- Today for a user with no Employee/Instructor link: no teacher section, no error.
- Exam schedule with no papers in the next 30 days: section omitted.

---

### Task 1: Periods, assignments, timetable generator

**Files:** Create DocTypes `School Period` (child; `period_no` Int, `label` Data, `start_time` Time, `end_time` Time, `is_break` Check), field `periods` (Table) on School Settings; `Teaching Assignment` (`student_group`, `course`, `instructor`, `periods_per_week` Int); `Timetable Slot` (`student_group`, `weekday` Select Monday..Saturday, `period_no` Int, `course`, `instructor`; autoname `TS-{student_group}-{weekday}-{period_no}`). Create `school_day/timetable.py`. Test `tests/test_timetable.py`.

**Interfaces — produces:** `timetable.teaching_periods() -> list[dict]` (non-break periods in order); `timetable.generate(student_groups: list[str] | None = None) -> dict` → `{"placed": int, "unplaced": list[dict]}`, replacing those sections' slots; `timetable.slots_for(instructor=None, student_group=None, weekday=None) -> list[dict]`.

- [ ] Tests: `test_generate_places_every_period_without_clash` (2 sections sharing a teacher: no teacher in two slots of the same weekday+period; each assignment gets `periods_per_week` slots); `test_overfull_assignment_reports_unplaced` (periods_per_week beyond free slots → `unplaced` non-empty, still no clash); `test_regenerate_replaces_slots`. RED → implement (greedy: assignments sorted by periods desc, spread across weekdays round-robin, skip slot if section or teacher busy) → GREEN → commit.

### Task 2: Cover for absent teachers

**Files:** DocType `Cover Assignment` (`date`, `period_no`, `student_group`, `course`, `absent_instructor`, `cover_instructor`; unique date+period+student_group). `school_day/cover.py`. Test `tests/test_cover.py`.

**Interfaces — produces:** `cover.away_instructors(date) -> set[str]`; `cover.uncovered(date) -> list[dict]` (slots of away teachers for that weekday without a Cover Assignment); `cover.suggest(date, period_no, student_group) -> list[dict]` (`instructor`, `instructor_name`, `same_subject`, `load_today`) — excludes away teachers and teachers busy in that period (timetable or cover); same subject first, then lighter load; whitelisted `cover.assign(date, period_no, student_group, cover_instructor) -> str` (checks Cover Assignment create permission; refuses a teacher not in `suggest`).

- [ ] Tests: `test_absent_teachers_periods_are_uncovered`, `test_suggest_excludes_away_and_busy`, `test_suggest_prefers_same_subject`, `test_assign_covers_the_period`, `test_assign_refuses_busy_teacher`. RED → implement → GREEN → commit.

### Task 3: Exam schedule

**Files:** DocType `Exam Schedule` (`academic_year`, `exam` Select Quarterly/Half Yearly/Annual, `papers` Table) and child `Exam Schedule Paper` (`program`, `course`, `exam_date`, `start_time`, `end_time`); `school_day/exams.py`; print format `Exam Schedule` (branded). Test `tests/test_exams.py`.

**Interfaces — produces:** `exams.upcoming(days=30, programs=None) -> list[dict]` (papers from today to today+days, date order).

- [ ] Tests: `test_upcoming_in_window_sorted`, `test_upcoming_filters_programs`. RED → implement → GREEN → commit.

### Task 4: Today payload

**Files:** `school_day/today.py`; Test `tests/test_today.py`.

**Interfaces — consumes:** Tasks 1–3. **Produces:** whitelisted `today.get_today() -> dict` = `{"date", "weekday", "greeting", "sections": [{"key", "title", "tone": "alert|info|ok", "items": [{"text", "sub", "action": {"label", "route"| "method", "args"}}]}]}`. Sections by role:
- Teacher (has Instructor): `now_next` (my slots today incl. covers, current/next by time), `todo` (attendance not taken today for my class-teacher sections; Mark Entries missing for my assignments for the latest exam), `my_exams`.
- Principal/Correspondent: `attention` (uncovered periods with "Assign cover", pending Mark Entries count by section, campus pending approvals), `day` (students present %, staff away names), `exams`, `fees` (top 3 classes by dues).
- Accountant: `fees_today`, `call_list` (top 10 overdue families). Office: enquiries open, certificate requests in draft.

- [ ] Tests: `test_teacher_sees_own_periods_and_cover`, `test_principal_sees_uncovered_periods`, `test_user_without_instructor_gets_no_teacher_section`. RED → implement → GREEN → commit.

### Task 5: Today block on workspaces, demo data, rehearsal

**Files:** `setup/today_block.py` (Custom HTML Block "Today": html container, script calling `get_today` and rendering sections with buttons; style in school colours) wired into `desk.build()` as the first block of every role workspace; `demo/school_day.py` (periods 9:00–15:40 with two breaks, assignments per section from SUBJECTS with real teachers, generate timetable, link demo teacher users to Employees, Half Yearly schedule from 2026-12-08). Add step `school_day` after `academics`.

- [ ] Load on aanoor.localhost; walk Today as principal and teacher.vi in the browser; assign one cover; commit; push.
