# Today: the school's operating layer

Approved 2026-11-19 ("go"). Demo 2026-11-20.

## Intent

Each person who logs in sees what needs doing next, with the action one click away. Records stay underneath; the
first screen is the school day, not a report. Teacher: where am I now and next, what do I owe (attendance, marks),
what cover was given to me, which exams are coming. Principal: what needs a decision today (periods with no teacher,
pending marks, approvals), then the state of the day, exams and fees. Fee numbers stay but recede.

## Goals

- School timetable: periods of the day; section × day × period → subject and teacher; generated from teaching
  assignments (periods per week) with no teacher or section clash.
- Cover: a teacher absent or on leave today leaves their periods uncovered; free teachers are suggested (same
  subject first, then lightest load); the principal assigns in one click; the cover shows on the cover teacher's Today.
- Exam schedule: exam, class, subject, date and time; shown on Today for everyone it affects.
- A Today block at the top of every role workspace, built from live records.

## Non-goals tonight

Publishing the timetable into Education Course Schedules (attendance stays by section); auto-generation through the
campus CP-SAT solver; room allocation; parent-facing Today.

## Approaches

1. Reuse campus timetable, substitution and exam engines as they are: they need curricula, course offerings and the
   COE pack for every class; too much college wiring for a school. Not chosen.
2. **Chosen:** school-shaped DocTypes and services in onebook_school, borrowing campus's ideas (free-teacher search,
   leave-driven cover), rendered as a Custom HTML Block on each workspace that calls one whitelisted method.
3. Workspace cards only: cannot say "what next". Not chosen.

## Design

- DocTypes: `School Period` (child of School Settings: period no, label, start, end, break flag); `Teaching Assignment`
  (section, subject, teacher, periods per week); `Timetable Slot` (section, weekday, period, subject, teacher; unique
  per section+weekday+period); `Cover Assignment` (date, period, section, subject, absent teacher, cover teacher);
  `Exam Schedule` with child `Exam Schedule Paper` (class, subject, date, start, end).
- Services: `timetable.generate(academic_year)`; `cover.uncovered(date)`, `cover.suggest(date, period, section)`,
  `cover.assign(...)` (whitelisted, principal); `today.get_today()` returning role-shaped sections.
- Teacher identity: User → Employee.user_id → Instructor.employee.
- UI: Custom HTML Block "Today" (script calls `get_today`, renders sections with action buttons) placed first on
  Correspondent, Principal, Fees Office, School Office and Class Teacher workspaces.
- Demo data: periods (8 a day, Mon–Sat), assignments for every section, generated timetable, Half Yearly exam schedule
  from 8 Dec 2026, demo teacher logins linked to their Employees, today's absent teachers' periods left uncovered.
