# Demo script: Sri Aanoor Vidyalaya (20 Nov 2026)

Site: `http://aanoor.localhost:<port>` (this bench; see "Before you start"). Every login uses the demo password
`Aanoor@Demo2026`. All people and numbers are synthetic.

| Login | Who | Lands on |
| --- | --- | --- |
| `correspondent@aanoor.example.edu` | R. Palanisamy, correspondent | Correspondent |
| `principal@aanoor.example.edu` | Dr. S. Meenakshi, principal | Principal |
| `accounts@aanoor.example.edu` | K. Saravanan, accountant | Fees Office |
| `office@aanoor.example.edu` | M. Revathi, front office | School Office |
| `teacher.vi@aanoor.example.edu` | P. Anitha, class teacher VI - A | Class Teacher |
| `parent@aanoor.example.edu` | Surya A., parent of three | Parent portal |

## Before you start

1. The bench's default site must be `aanoor.localhost` (`bench use aanoor.localhost`, then restart `bench start`), since
   this dev server answers every host name with the default site. Open `http://aanoor.localhost:8003`. After the demo,
   `bench use education.localhost` restores the usual default.
2. **On the demo morning** run `bench --site aanoor.localhost execute onebook_school.demo.refresh_today` so today has
   student and staff attendance, absent teachers with uncovered periods, and a few receipts dated today.
3. Log in once as each user you will show, so the first screen is not a cold start.
4. PDF download needs the site name to resolve inside the container; use **Print** (browser print to PDF) instead of
   **Get PDF** during the demo.

## The click path (about 25 minutes)

0. **Open on Today (3 min).** Principal (`principal@`): the first block is "Needs your attention": periods with no
   teacher because S. Ramesh, T. Sumathi and V. Jayanthi are away; click **Assign cover**, pick the best free teacher,
   the period disappears. Then marks pending from P. Anitha (VIII - B Maths), the day (present %, staff away), Half
   Yearly exams in N days, fees by class. Then log in as `teacher.vi@` (P. Anitha): her periods today with NOW and NEXT,
   the cover she was given, "Enter Quarterly marks: VIII - B Maths", her own exam papers.

1. **Principal's morning (3 min), as correspondent.** Correspondent workspace: Fees Collected Today, Outstanding
   Fees (about Rs 22.8 lakh), Present Today (about 95%), Students Enrolled (616). Charts: Dues by Class (Std IX has the
   most, about Rs 2.6 lakh), Fee Collection by Month, Payment Mode. Click **Defaulters**.
2. **Admission to class (4 min), as office.** School Office: Enquiries (6 for 2027-28). Open a student (for example
   admission no SAV0330, Shalini Rahul, VI - A): EMIS ID, PEN, APAAR consent, guardians.
3. **Fees the accountant trusts (6 min), as accounts.**
   - Fee Committee Order `FCO-FDC/ERD/2025/1147`: print **Fee Display (Notice Board)**. Then open a Fee Structure, raise
     Tuition Fee above the approved amount and save: it is refused, naming the approved and the charged amounts.
   - Fees Office: **New Fee Receipt**, parent **Yogesh V.** (two children with dues), **Get Dues**: both children's
     invoices, oldest first. Submit; print **Family Receipt**. The younger sibling's invoice already carries the 10%
     sibling concession.
   - Show `FR-2026-0001` (Surya A., three children, one UPI payment) as a printed receipt.
4. **Government returns from one record (5 min), as principal.** Report **UDISE Student Export**, Academic Year
   2026-27, Section VI - A: summary Students / Ready / Need fixing; the Issues column names what is missing.
   Say plainly: UDISE+ has no API for schools, so we keep the data clean and ready to enter or upload.
5. **Term report card (3 min), as teacher.vi.** Class Teacher: Enter Marks shows a section's students in roll order;
   open Report Card for Shalini Rahul (VI - A, Quarterly) and print **Report Card (TN)**.
6. **Transfer certificate with QR (2 min), as principal.** Certificate Request `CRQ-2026-00001`, TC `TC/SAV/2026/0001`
   for Jeevan Ganesh, approved by the principal. Open `/verify/44HD9BHPYR` to show the verification page.
7. **Close (2 min).** Pilot: migrate data from the current app, go live for Term 3, price per student per year;
   parent app follows (see `docs/specs/2026-11-19-parent-app-spec.md`).

## Fallbacks

- A screen errors: switch to Administrator (password `admin`) and continue the story there.
- Data looks wrong: restore the backup taken after rehearsal (`bench --site aanoor.localhost restore <file>`).
- Not in this demo: transport, live WhatsApp sending, the parent mobile app. Present them as the roadmap.
