# OneBook School Parent App: Product and Technical Spec

Date: 19 Nov 2026. Status: draft for review after the Aanoor demo.
App: `onebook_school` (Frappe v16), on `campus`. First school: Sri Aanoor Vidyalaya Matric HSS, Muthur.

Labels used below:
- **[Verified]**: checked in this bench's code.
- **[Assumption]**: not checked in code. Needs confirmation.

## 1. Goal, users, and targets

**Goal.** Parents of Aanoor replace the ClassPep app before the June 2027 term starts. Two things must be quicker than today: paying fees and knowing your child is safe.

**Users.**

| User | Profile | Main need |
|---|---|---|
| Parent | 1–3 children in the school. Low-end Android phone. Uses WhatsApp daily. Reads Tamil or English. | Is my child in school? What do I owe? What did the school send? |
| Grandparent or guardian | Often the one who picks up the child. May share the parent's phone. | Alerts and circulars in Tamil, with large text. |
| Class teacher (sender) | Uses desk or a phone. | Post homework. Reply to parents without giving out a personal number. |
| Office and accountant | Use desk. | Fewer phone calls and fewer cash payments at the counter. |

**Jobs to be done.**
1. "Tell me within 30 minutes if my child is marked absent."
2. "Let me pay all my children's fees in one UPI payment and keep the receipt."
3. "Show me today's homework and circulars, and let me confirm I read them."
4. "Give me the report card and certificates without a trip to the office."

**"Better than ClassPep" as numbers.** These are targets for the first pilot term. The ClassPep baselines are [Assumption], apart from the 500+ installs.

| Measure | Target |
|---|---|
| Activated families (logged in at least once) by end of week 4 | 70% of families (ClassPep has 500+ installs for about 550 students [Assumption: student count from the demo seed plan]) |
| Weekly active families | 50% |
| Time from opening the app to a confirmed UPI payment, for a family with 2 children | Under 60 seconds, 4 taps or fewer |
| Absence alert delivered (push or WhatsApp) after attendance is marked | 95% within 15 minutes |
| Share of fees paid online | 40% in term 1 |
| First-load size on 3G | Under 200 KB gzipped JS+CSS. Interactive in under 5 s on a ₹7,000 Android phone [Assumption: device class] |
| Play Store rating | 4.3★ or above |
| Circulars needing acknowledgement that are acknowledged within 48 h | 80% |

## 2. Scope by release

| Feature | MVP (pilot, live by 1 June 2027) | Later |
|---|---|---|
| Login with mobile OTP | Yes | — |
| Child switcher and family view | Yes | — |
| Today's attendance and absence alert | Yes | Monthly attendance calendar |
| Fee dues, UPI/gateway pay, receipts, one Family Receipt across children | Yes | Autopay or e-mandate |
| Circulars with acknowledgement and attachments | Yes | — |
| Homework and class diary | Yes (text plus one attachment) | Submit work back |
| Exam marks and report card PDF | Yes | Holistic Progress Card (HPC) |
| Certificate requests (bonafide, TC) and QR verification | Yes | — |
| School calendar and holidays | Yes | — |
| Contact class teacher (in-app message, office hours, no personal number) | Yes (one-way request plus teacher reply) | Two-way chat |
| Bus tracking | No | Through a GPS partner |
| Leave application | No (the campus portal already has `apply_leave` [Verified]) | Phase 2. Cheap to add. |
| PTM slot booking, photo gallery | No | Phase 2 |
| Tamil and English UI | Yes | — |

## 3. Screens

All screens come in English and Tamil. The default language comes from the guardian's `language` field. The parent can switch it on the profile screen. [Assumption: Guardian has a language field. If not, a custom field `obs_language` is needed.]

| # | Screen | Shows | Actions |
|---|---|---|---|
| S1 | Login | Mobile field and OTP field | Request OTP, verify, change language |
| S2 | Consent (first login) | Plain-language notice in Tamil/English. Purposes listed. | Accept each purpose, decline optional purposes, read full notice |
| S3 | Home | Child switcher. For each child: today's attendance, fee due, unread circulars, today's homework. | Pay, open item, switch child |
| S4 | Attendance | Today plus the last 30 days, and term % | None (read only) |
| S5 | Fees | Dues across all children, receipts | Pay all or select, download receipt |
| S6 | Payment result | Success or failure, amount, receipt number | Download, share to WhatsApp |
| S7 | Circulars | List, newest first. Unread marked. | Open, acknowledge, open attachment |
| S8 | Homework/diary | By date, by subject | Open attachment |
| S9 | Results | Exams, marks per subject, grade | Download report card PDF |
| S10 | Certificates | Requests and their status | Request bonafide or TC, download PDF with QR |
| S11 | Calendar | Holidays, exams, events | None |
| S12 | Contact teacher | Class teacher name, office hours, earlier messages | Send a message (500 characters), see the reply |
| S13 | Profile | Guardian details, children, language, notification settings, consents | Change language, withdraw consent, log out |

**Home wireframe**

```
+----------------------------------+
| [logo] Aanoor Vidyalaya   EN|தமி |
| ( Kavin VI-A ) ( Nila II-B )     |  <- child chips, "All" when >1
+----------------------------------+
| TODAY  Wed 3 Jun                 |
| Kavin  ● Present  08:52          |
| Nila   ● Absent   (alert sent)   |
+----------------------------------+
| FEES DUE            ₹ 18,400     |
| Term 1, due 15 Jun               |
| [ Pay with UPI ]                 |
+----------------------------------+
| CIRCULARS (2 new)                |
| • PTM on Saturday   [Acknowledge]|
| • Uniform change                 |
+----------------------------------+
| HOMEWORK today                   |
| Kavin: Maths Ex 3.2, Tamil p.41  |
+----------------------------------+
| Home | Fees | Circulars | More   |
+----------------------------------+
```

**Fees wireframe**

```
+----------------------------------+
| < Fees                           |
+----------------------------------+
| Total due (2 children) ₹ 18,400  |
+----------------------------------+
| [x] Kavin  VI-A                  |
|     Term 1 Tuition   ₹ 9,000     |
|     Books            ₹ 1,800     |
|     Due 15 Jun                   |
| [x] Nila   II-B                  |
|     Term 1 Tuition   ₹ 7,600     |
|     Due 15 Jun                   |
+----------------------------------+
| Sibling concession applied  ✓    |
+----------------------------------+
| [ Pay ₹ 18,400 with UPI ]        |
| Fee approved by Fee Committee:   |
| [view order]                     |
+----------------------------------+
| RECEIPTS                         |
| FR-0012  12 Apr  ₹ 6,000  [PDF]  |
+----------------------------------+
```

**Low-end phone rules.**
- No animations. System fonts plus one Tamil font subset. Images lazy-loaded.
- Cache the last screen data in IndexedDB. Show it with a "last updated 10:42" label when offline.
- Attachments open the browser's own viewer on the first tap. Load PDFs by URL, not inline. This fixes the CampusCare complaint.
- Minimum tap size 48 px. Base text 16 px. One action per card.

## 4. Architecture

### Options

| Criterion | (a) PWA with frappe-ui on the site | (b) Extend the server-rendered `/campus-portal` | (c) Native/Flutter app |
|---|---|---|---|
| Fits blueprint | D15 defers the Vue SPA until after the pilot [Verified] | Matches D15 now | New stack |
| Reuse of `portal.py` APIs | Full: the methods return plain dicts [Verified] | Full | Full, over REST |
| Installable, home-screen icon | Yes (manifest + service worker) | Possible but awkward | Yes |
| Play Store | Yes, as a TWA | TWA possible, poor UX | Yes |
| Push | Web push / FCM through the service worker | Same, but harder without app shell | FCM native |
| Offline | Good (service worker cache) | Weak | Good |
| Per-school branding | Manifest generated per site | Same | One build per school |
| Bundle on 3G | ~150–200 KB if lean [Assumption] | Smallest | 10–25 MB APK [Assumption] |
| Team skill | Vue + Frappe (already in the bench: HRMS frontend uses `vite-plugin-pwa` [Verified]; Education frontend uses `frappe-ui` [Verified]) | Jinja | New skill |
| Effort | Medium | Low | High |

### Recommendation: (a) PWA, wrapped as a TWA for the Play Store

Reasons:
1. The school already has a branded store app. Parents expect "the school app" in the Play Store. A TWA gives that from one codebase.
2. HRMS in this bench already ships a frappe-ui PWA with `vite-plugin-pwa`, `sw.js` and `frappe-push-notification.js` [Verified]. We copy a working pattern.
3. Offline cache and push need a service worker and an app shell. The server-rendered portal is a poor fit for both.
4. All data methods already exist in `campus.student_services.portal` and `campus_messaging.circulars`, and they are already scoped to guardians [Verified]. The PWA is a new front end, not a new back end.

**D15 conflict.** D15 says the server-rendered portal is the one portal until after the pilot. This app is a parent-only front end on the same APIs, at `/parent`. The plan is to amend D15, not to break it: the portal stays for students and staff, and parents get redirected to `/parent`. This needs a decision (see Open questions).

### Components

| Concern | Design |
|---|---|
| Location | `onebook_school/frontend/` (Vite + Vue 3 + frappe-ui), built into `onebook_school/public/parent/`, served at `/parent` through a `www/parent.html` shell |
| Bundle | Only the frappe-ui components we use. No chart library. Tamil font subset of about 40 KB [Assumption]. Route-level code splitting. |
| Branding per school | `/parent/manifest.webmanifest` is generated by a whitelisted method from School Settings: `short_name`, `name`, icons, `theme_color`. The install name reads "Aanoor Vidyalaya". Needs School Settings fields for app name, icon and colour [Assumption: not present yet]. |
| Play Store | One TWA per school, built with Bubblewrap [Assumption: tool choice]. Package e.g. `in.onebook.aanoor`. `/.well-known/assetlinks.json` served per site. The listing is published under the school's or OneBook's developer account (open question). The ClassPep package id cannot be reused. |
| Push | Frappe v16 has `frappe/push_notification.py` and the `Push Notification Settings` single. They send through Frappe's central relay (`notification_relay`) using FCM tokens [Verified]. Campus messaging already has a `push` channel. Its adapter `send_push` is a stub that raises "Push is not configured" [Verified]. MVP work: implement `send_push` on the Frappe relay or on our own FCM project. Recommendation: our own FCM project per deployment. Reason: the school's data then does not pass through a third-party relay (DPDP processor chain). |
| OTP login | Frappe has no passwordless SMS-OTP login. It has SMS OTP only as a second factor (`twofactor.py`) and "login with mobile number" plus password [Verified]. New endpoints: `onebook_school.parent.auth.send_otp(mobile)` and `verify_otp(mobile, otp)`. Rate-limited (`frappe.rate_limiter`). 6 digits, 5-minute expiry, stored hashed in cache. Sent by SMS through the campus SMS channel with a DLT template. On WhatsApp as well if the number has opted in. On success: `frappe.local.login_manager.login_as(user)` and a session cookie with a 30-day expiry. |
| User provisioning | One Website User per Guardian, keyed by mobile. Created in bulk from the import (section 8). `Guardian.user` is set. Role `Guardian`. |
| Multi-school | One Frappe site per school (current campus model [Assumption: one site per institution]). Branding, gateway, SMS sender and FCM keys are per site. For trusts with several schools on one site: scope by `company`, as the campus APIs already do with `by_company` [Verified]. |

## 5. Data and APIs

### Permission model
- Every method resolves the student through `campus.student_services.portal.resolve_student`. That function only accepts students linked to the session user through `Student Guardian` rows. A student id from the request is never trusted on its own [Verified].
- Guardians can read Sales Invoices only for their wards (`owns_invoice`) [Verified].
- Circular visibility goes through `circulars_for(user)` plus the hook's `has_permission` [Verified].
- New methods follow the same rule: `resolve_student` first, then return plain dicts. No `frappe.client.get_list` from the PWA.

### Screen to data map

| Screen | Reads | Writes | Method |
|---|---|---|---|
| S3/Child switcher | Student, Student Guardian | — | `portal.my_students` [Verified] |
| S3 Home summary | All below | — | **New** `onebook_school.parent.api.home()`: one call that returns per child: attendance today, dues, unread circulars, homework |
| S4 Attendance | Student Attendance (Education) | — | `portal.get_attendance` [Verified] |
| S5 Fees | Sales Invoice, Fee Committee Order | — | `portal.get_fees` [Verified]. **New** `family_dues()`, which wraps `fees.family.get_outstanding(guardian, company)` [Verified] for the session user's own guardian only. Today that method takes a `guardian` argument and relies on Guardian read permission. |
| S5 Pay | Payment Request | Payment Request | Single invoice: `portal.pay_invoice` [Verified]. **New** `pay_family(invoices)`: one gateway request for several invoices. When the webhook settles it, a Family Receipt is created with allocations [Assumption: the gateway settle path (`gateways.settle`) handles one invoice today, so it needs a family variant]. |
| S6 Receipt | Family Receipt, Payment Entry | — | **New** `receipt_pdf(name)` (owner check) |
| S7 Circulars | Circular, Circular Acknowledgement, File | Circular Acknowledgement | `circulars.get_my_circulars`, `circulars.acknowledge` [Verified] |
| S8 Homework | **New DocType** `Class Diary Entry` (student_group, course, date, text, attachment, posted_by) | — | **New** `homework(student, from_date)` |
| S9 Results | Report Card (onebook_school, planned for the demo [Verified in plan; not built]) | — | **New** `report_cards(student)`, `report_card_pdf(name)`. `portal.get_results` covers campus Student Result, not school Report Card. |
| S10 Certificates | Certificate Request, Certificate Type | Certificate Request | `portal.certificate_types`, `request_certificate`, `my_certificates` [Verified]. QR verification at `/verify/<code>` [Verified]. |
| S11 Calendar | Holiday List, Academic Term, school events | — | **New** `calendar(from, to)` [Assumption: events stored as a new `School Event` or ERPNext Event] |
| S12 Contact teacher | Student Group `obs_class_teacher` [Verified], Parent Interaction (campus) [Verified exists] or new `Parent Message` | Parent Message | **New** `send_teacher_message(student, text)`, `my_messages(student)` |
| S13 Profile/consent | Guardian, Communication Consent | Communication Consent | **New** `my_consents()`, `set_consent(purpose, channel, status)` |
| Push token | — | FCM token per user | **New** `register_push_token(token)`, `unregister_push_token(token)` |

All new methods go in `onebook_school/parent/api.py`. Each one has a test that a guardian cannot read a non-ward.

## 6. Notifications

Delivery uses campus messaging: Message Template with `en` and `ta` bodies [Verified], Message Log with idempotency keys and retries [Verified], channel order from `Messaging Settings.channel_order` [Verified], quiet hours [Verified], and consent check per party/channel/purpose [Verified].

| Event | Trigger | Purpose | Respect quiet hours | Template |
|---|---|---|---|---|
| Absent today | Student Attendance submitted as Absent | transactional | No (safety) | `absent_today` (in the demo plan) |
| Late arrival | Attendance marked late [Assumption: field exists] | transactional | No | `late_today` |
| Fee due | 7 days and 1 day before the due date | transactional | Yes | `fee_due` (in the demo plan) |
| Fee overdue | Due date + 3 days, then weekly, at most 3 | transactional | Yes | `fee_overdue` |
| Receipt | Payment settled or Family Receipt submitted | transactional | No | `fee_receipt` |
| Circular | Circular published | transactional | Yes | `circular_new` |
| Marks published | Report Card released | transactional | Yes | `results_out` (in the demo plan) |
| Certificate ready | Certificate Request issued | transactional | Yes | `certificate_ready` |
| Teacher reply | Reply saved | transactional | Yes | `teacher_reply` |

**Channel rules.** Push first. If no push token exists, or the push fails, send on WhatsApp through `frappe_whatsapp`, then SMS. Email is never used for parents unless they choose it. If push is not opened within 30 minutes, WhatsApp follows only for absent and fee receipt [Assumption: needs FCM delivery receipts or an "opened" ping from the service worker]. Set `channel_order = push, whatsapp, sms` per site.

**Quiet hours.** 21:00–07:00 by default. Held messages are released at the end of the window [Verified: `quiet_hours.release_time`]. The absence alert ignores quiet hours, because attendance happens in school hours anyway.

**Tamil.** Every parent template has a `ta` body. WhatsApp templates must be approved by Meta in both languages before go-live. SMS templates must be DLT-registered [Verified: Messaging Settings has `sms_dlt_param_name`].

**In-app.** Every notification also creates an in-app item, so the bell shows the same list as push. The badge clears on open. MyClassboard's "notifications stay unread" problem is fixed by marking an item read when its target screen is viewed.

## 7. Privacy and compliance

| Rule | Design |
|---|---|
| DPDP: verifiable parental consent | At first login, the OTP-verified mobile must match the guardian mobile the school recorded at admission. That match is the verification. Screen S2 records each purpose in `Communication Consent` with `source = parent_app` and a timestamp [Verified fields]. A new `Data Consent` DocType records the notice version accepted. |
| School is fiduciary, OneBook is processor | The notice names the school as fiduciary. A DPA between the school and OneBook is signed before launch. |
| No tracking or targeted ads to children | No third-party analytics, ads, crash or session-replay SDKs in the PWA or TWA. Usage metrics come from server logs only, aggregated per day, with no child identifiers. CSP blocks third-party scripts. |
| Data minimisation | The app never shows Aadhaar, social category, religion, CWSN, or RTE status to the parent screens. These `obs_` fields stay desk-only. APIs return named fields, never full docs. |
| APAAR consent | Profile shows APAAR status per child (`obs_apaar_consent`: Pending, Given, Refused [Verified]). Parents can give or refuse consent in the app, and can withdraw it later. Refusal has no effect on anything else. |
| Fee display mandate | The fee screen links to the approved Fee Committee Order. Fee Committee Order already has notice-board display [Verified per brief; not opened]. |
| TC and unpaid fees (Madras HC, July 2024) | **Conflict found.** `campus.student_services.certificates.check_transfer_allowed` blocks a TC while any dues are outstanding [Verified]. For schools, the app must let parents request a TC regardless of dues. `onebook_school` needs a setting or override so that dues are shown as information only and do not block issue. |
| Retention | OTP codes are deleted on use or after 5 minutes. Push tokens are removed on logout or after 90 days unused. Message Logs are kept 1 year. When a student leaves, guardian access ends 1 year after the TC, unless a sibling is still enrolled [Assumption: periods need the school's sign-off]. |
| Audit | Log logins, OTP requests, consent changes, and certificate and receipt downloads, with user, time and IP. Frappe Access Log and Activity Log can cover part of this [Assumption: not checked]. |
| Data rights | The profile screen has "Download my data" (JSON plus PDFs) and "Request correction", which links to campus `Student Record Correction` [Verified exists]. |

## 8. Migration from ClassPep

**Import (CSV from ClassPep export or school records [Assumption: ClassPep allows export]):**
- Guardians: name, mobile (primary key), relation, language, and the student links.
- Students: should already be in OneBook from the Aanoor setup. Match on admission number (`obs_admission_no`).
- Opening fee balances for the current year: these come from the school's accounts, not from ClassPep.
- Do not import: ClassPep chat history, old circulars, old homework. Archive them as a PDF that the office keeps.

**How parents switch.**
1. Before cutover, the office checks each family's mobile number. That number becomes the login.
2. Two weeks before term, a WhatsApp broadcast in Tamil and English goes out from the school's number. It has a link to the Play Store listing and to `/parent`, plus a 30-second video.
3. The first login uses OTP on the same number. No password, no school code.
4. At admission desk and fee counter days, staff help parents install on the spot.
5. Families who do not activate still get WhatsApp and SMS alerts. Nobody is cut off.

**Cutover plan.**

| When | Step |
|---|---|
| March 2027 | Pilot with 30 families (staff children first) |
| April 2027 | Open to 2 classes. Fix issues. Get the Play Store listing approved. |
| May 2027 | Bulk import. WhatsApp onboarding. Install drives on fee-collection days. |
| 1 June 2027 | Term starts. All alerts come from OneBook. ClassPep stays read-only for 30 days. |
| 1 July 2027 | ClassPep switched off. The school asks ClassPep to delist its app. |

## 9. Risks, open questions, effort

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Play Store review or developer account delays | No store presence at launch | Submit the TWA in April. The PWA install link works without it. |
| WhatsApp/SMS template approval (Meta, DLT) is slow | No fallback alerts | Submit templates in March |
| FCM push is unreliable on Chinese-OEM phones (battery savers) [Assumption] | Missed alerts | WhatsApp fallback for absent and receipt |
| Parents share one phone across two guardians | Login conflicts | Several guardians per student allowed. One user per mobile. |
| Gateway fees on UPI | School resists online pay | Show the UPI zero-MDR option, depending on gateway [Assumption] |
| D15 says no Vue SPA before the pilot | Blueprint conflict | Amend D15 for a parent-only PWA |
| TC dues gate in campus | Legal exposure in TN | Override for schools before MVP |

### Open questions
1. Do we amend D15 to allow a parent-only frappe-ui PWA before the pilot?
2. Whose Play Store developer account publishes the app: the school's, or OneBook's?
3. Do we use Frappe's push relay or our own FCM project per deployment?
4. Which SMS provider and DLT entity sends OTPs: the school's sender ID or OneBook's?
5. Which payment gateway does Aanoor use? Does it support one payment split across several invoices?
6. Can ClassPep export guardian, mobile and student-link data, and in what format?
7. Is "contact teacher" an extension of campus `Parent Interaction`, or a new `Parent Message` DocType?
8. Where do school events live: ERPNext Event, Holiday List only, or a new DocType?
9. What retention periods will the school sign off for guardian accounts and message logs?
10. Should the TC dues gate be a School Settings toggle, or always off for K-12?

### Effort (estimates, person-weeks, one full-stack Frappe developer)

| Work | MVP |
|---|---|
| PWA shell, frappe-ui setup, i18n (en/ta), offline cache, manifest per site | 2.0 |
| OTP login, user provisioning, consent screens and DocType | 1.5 |
| Home, attendance, circulars (reusing APIs) | 1.0 |
| Fees, family pay, Family Receipt on webhook, receipts | 2.0 |
| Homework DocType + teacher entry + parent screen | 1.0 |
| Results and report card PDF (after Report Card is built) | 0.5 |
| Certificates screen + TC dues override | 0.5 |
| Calendar, contact teacher | 1.0 |
| Push (FCM adapter in campus messaging, service worker, tokens) | 1.5 |
| TWA build, Play listing, assetlinks | 0.5 |
| Notification events and en/ta templates | 1.0 |
| ClassPep import and onboarding kit | 1.0 |
| Testing on low-end devices, security review, pilot fixes | 2.0 |
| **MVP total** | **about 16 person-weeks** |

| Later release | Estimate |
|---|---|
| Leave application (reuse `portal.apply_leave`) | 0.5 |
| PTM booking | 1.5 |
| Gallery | 1.0 |
| Two-way chat with moderation | 3.0 |
| HPC view | 2.0 |
| Bus tracking through a GPS partner | 3.0–4.0, depending on the partner API |
