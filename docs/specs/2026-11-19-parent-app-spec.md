# OneBook School Parent App: Spec

Date: 19 Nov 2026. Status: draft for review after the Aanoor demo. App: `onebook_school` on `campus` (Frappe v16).

Labels used below:
- **[V]**: verified in this bench's code.
- **[A]**: assumption, not verified. Needs confirmation.

## 1. Goal, users, targets

**Goal.** Aanoor parents switch from the ClassPep app before the June 2027 term starts. Paying fees and knowing the child is safe must both be quicker than they are today.

| User | Profile | Main need |
|---|---|---|
| Parent | 1–3 children. Low-end Android phone. WhatsApp-first. Reads Tamil or English. | Is my child in school? What do I owe? What did the school send? |
| Grandparent or guardian | Often shares the parent's phone | Alerts and circulars in Tamil, large text |
| Class teacher | Desk or phone | Post homework. Answer parents without giving a personal number. |
| Office and accountant | Desk | Fewer calls and fewer counter payments |

**Jobs to be done.**
1. Tell me fast if my child is absent.
2. Let me pay all my children's fees in one UPI payment and keep the receipt.
3. Show me homework and circulars, and let me confirm I read them.
4. Give me report cards and certificates without a trip to the office.

**Targets for the pilot term.** These define "better than ClassPep". ClassPep baselines are [A], apart from its 500+ installs.

| Measure | Target |
|---|---|
| Families activated (first login) by week 4 | 70% |
| Weekly active families | 50% |
| App open to confirmed UPI payment, 2 children | Under 60 s, 4 taps or fewer |
| Absence alert delivered after attendance is marked | 95% within 15 min |
| Fees paid online, term 1 | 40% |
| First load: JS+CSS gzipped | Under 200 KB. Interactive under 5 s on 3G and an entry-level phone [A] |
| Required circular acknowledged within 48 h | 80% |
| Play Store rating | 4.3★ or above |

## 2. Scope by release

| Feature | MVP (live by 1 June 2027) | Later |
|---|---|---|
| Mobile OTP login, child switcher | Yes | — |
| Today's attendance and absence alert | Yes | Monthly calendar view |
| Fee dues, UPI/gateway pay, receipts, Family Receipt across children | Yes | E-mandate |
| Circulars with acknowledgement | Yes | — |
| Homework/diary | Yes (text plus one file) | Submission |
| Marks and report card PDF | Yes | HPC |
| Bonafide/TC requests with QR verification | Yes | — |
| School calendar and holidays | Yes | — |
| Contact class teacher (in-app, office hours) | Yes (message and reply) | Two-way chat |
| Leave application | — | Phase 2 (`portal.apply_leave` exists [V]) |
| Bus tracking (GPS partner), PTM booking, gallery | — | Phase 2/3 |

## 3. Screens

The UI comes in English and Tamil. Guardian has no language field [V], so add a custom field `obs_language`. The parent can change it on Profile.

| # | Screen | Shows | Actions |
|---|---|---|---|
| S1 | Login | Mobile, OTP | Request and verify OTP, pick language |
| S2 | Consent (first login) | Notice in plain Tamil/English, purposes | Accept, decline optional purposes |
| S3 | Home | Per child: attendance today, dues, new circulars, homework | Pay, open, switch child |
| S4 | Attendance | Today, last 30 days, term % | — |
| S5 | Fees | Dues across children, receipts, Fee Committee Order link | Pay all or selected, download receipt |
| S6 | Payment result | Status, amount, receipt no. | Download, share to WhatsApp |
| S7 | Circulars | Newest first, unread marked | Open, acknowledge, open attachment |
| S8 | Homework | By date and subject | Open attachment |
| S9 | Results | Marks, grades per exam | Download report card |
| S10 | Certificates | Requests and status | Request bonafide/TC, download PDF with QR |
| S11 | Calendar | Holidays, exams, events | — |
| S12 | Contact teacher | Class teacher, office hours, thread | Send message (500 chars) |
| S13 | Profile | Guardian, children, language, consents, notification settings | Change language, withdraw consent, log out |

**Home**

```
+----------------------------------+
| [logo] Aanoor Vidyalaya   EN|தமி |
| (All) (Kavin VI-A) (Nila II-B)   |
+----------------------------------+
| TODAY  Wed 3 Jun                 |
| Kavin  ● Present                 |
| Nila   ● Absent  (alert sent)    |
+----------------------------------+
| FEES DUE   ₹18,400  due 15 Jun   |
| [ Pay with UPI ]                 |
+----------------------------------+
| CIRCULARS (2 new)                |
| • PTM Saturday    [Acknowledge]  |
+----------------------------------+
| HOMEWORK  Kavin: Maths Ex 3.2    |
+----------------------------------+
| Home | Fees | Circulars | More   |
+----------------------------------+
```

**Fees**

```
+----------------------------------+
| < Fees      Total due ₹18,400    |
+----------------------------------+
| [x] Kavin VI-A                   |
|     Term 1 Tuition   ₹9,000      |
|     Books            ₹1,800      |
| [x] Nila II-B                    |
|     Term 1 Tuition   ₹7,600      |
|     Sibling concession applied   |
+----------------------------------+
| [ Pay ₹18,400 with UPI ]         |
| Approved fee order [view]        |
+----------------------------------+
| RECEIPTS                         |
| FR-0012  12 Apr  ₹6,000  [PDF]   |
+----------------------------------+
```

**Low-end phone rules.**
- No animations. System font plus a Tamil font subset.
- Cache the last data in IndexedDB. When offline, show it with a "Last updated 10:42" label.
- Attachments open by URL in the phone's viewer on the first tap.
- Tap targets of 48 px or more. Body text 16 px.

## 4. Architecture

| Criterion | (a) frappe-ui PWA on the site | (b) Extend `/campus-portal` (Jinja) | (c) Native/Flutter |
|---|---|---|---|
| Blueprint | D15 defers the Vue SPA until after the pilot [V] | Matches D15 | New stack |
| Backend reuse | Full: `portal.py` returns plain dicts [V] | Full | Full, over REST |
| Install icon and Play Store | Manifest + TWA | Weak | Native |
| Offline, push | Service worker | Hard without an app shell | Native |
| Branding per school | Manifest per site | Same | One build per school |
| Download size | About 200 KB [A] | Smallest | 10–25 MB [A] |
| Precedent in bench | HRMS frontend uses `vite-plugin-pwa`, `sw.js`, `frappe-push-notification.js` [V]. Education frontend uses `frappe-ui` [V]. | Campus portal | None |
| Effort | Medium | Low | High |

**Recommendation: (a), wrapped as a TWA for the Play Store.**
- Parents expect a school-branded store app, because ClassPep set that habit. A TWA delivers it from one codebase.
- HRMS shows the pattern already works on Frappe v16.
- The backend already exists and is already scoped to guardians.
- (b) cannot give offline use or reliable push.
- (c) costs about twice as much and adds a second stack.

This needs a D15 amendment. The server-rendered portal stays for students and staff. Parents get their own front end at `/parent` on the same APIs.

| Concern | Design |
|---|---|
| Code | `onebook_school/frontend/` (Vite + Vue 3 + frappe-ui), built to `public/parent/`, served at `/parent` |
| Branding | `manifest.webmanifest` generated from School Settings. Existing fields: `school_name`, `school_name_tamil`, `logo` [V]. Add `app_short_name` and `theme_color`. |
| Play Store | One TWA per school (Bubblewrap [A]). `/.well-known/assetlinks.json` per site. ClassPep's package id cannot be reused. |
| Push | Frappe v16 has `push_notification.py` plus `Push Notification Settings`, which send through Frappe's central relay with FCM tokens [V]. Campus `send_push` is a stub that raises "Push is not configured" [V]. Implement it on our own FCM project, so children's data does not go through a third-party relay. |
| OTP login | Frappe has SMS OTP only as a second factor, and mobile-number login with a password [V]. No passwordless OTP. New: `onebook_school.parent.auth.send_otp(mobile)` and `verify_otp(mobile, otp)`. Rate-limited. 6 digits, 5-min expiry, stored hashed in cache. Sent by SMS on a DLT template. On success, `login_as(user)` with a 30-day session. |
| Users | One Website User per Guardian mobile, role `Guardian`, with `Guardian.user` set |
| Multi-school | One site per school [A]. Gateway, SMS sender, FCM keys and branding are per site. A trust with several schools on one site scopes by `company`, as campus fees already do [V]. |

## 5. Data and APIs

**Permission model.** Every method calls `portal.resolve_student`. It accepts only students linked to the session user through `Student Guardian`. It never trusts a student id from the request [V]. Invoices are checked by `gateways.owns_invoice` [V]. Circulars go through `circulars_for(user)` [V]. New methods return named fields only. The PWA never calls `frappe.client`.

| Screen | DocTypes | Method |
|---|---|---|
| Switcher | Student, Student Guardian | `portal.my_students` [V] |
| Home | All below | **New** `parent.api.home()`: one call for all children |
| Attendance | Student Attendance | `portal.get_attendance` [V] |
| Fees | Sales Invoice, Fee Committee Order | `portal.get_fees` [V]. **New** `family_dues()`: wraps `fees.family.get_outstanding` [V] for the session guardian only. Today that method takes any `guardian` argument and depends on Guardian read permission. |
| Pay | Payment Request, Family Receipt | Single invoice: `portal.pay_invoice` [V]. **New** `pay_family(invoices)`: one gateway request. On settle, create a Family Receipt with allocations. `gateways.settle` handles one invoice per request today [A]. |
| Receipts | Family Receipt, Payment Entry | **New** `receipt_pdf(name)` |
| Circulars | Circular, Circular Acknowledgement | `circulars.get_my_circulars`, `circulars.acknowledge` [V] |
| Homework | **New** `Class Diary Entry` (student_group, course, date, text, file, posted_by) | **New** `homework(student, from_date)` |
| Results | Report Card, fed by Mark Entry (`assessment/report_cards.py`) [V]. Needs a "released to parents" flag [A]. | **New** `report_cards(student)`, `report_card_pdf(name)` |
| Certificates | Certificate Request, Certificate Type | `portal.certificate_types`, `request_certificate`, `my_certificates`. Verification at `/verify/<code>` [V]. |
| Calendar | Holiday List, Academic Term, events [A] | **New** `calendar(from_date, to_date)` |
| Teacher | Student Group `obs_class_teacher` [V]. Campus `Parent Interaction` exists [V], or a new `Parent Message`. | **New** `send_teacher_message`, `my_messages` |
| Consent | Communication Consent [V], new `Data Consent` | **New** `my_consents`, `set_consent` |
| Push | Token store | **New** `register_push_token`, `unregister_push_token` |

New code goes in `onebook_school/parent/api.py`. Each method gets a test that a guardian cannot read another family's child.

## 6. Notifications

Notifications reuse campus messaging [V]:
- Message Template with `en` and `ta` bodies, falling back to `en`.
- Message Log with idempotency keys and retries.
- `Messaging Settings.channel_order`.
- Quiet hours.
- Consent check per party, channel and purpose (transactional or promotional).

| Event | Trigger | Quiet hours apply |
|---|---|---|
| Absent | Student Attendance marked Absent | No |
| Fee due | 7 days and 1 day before due date | Yes |
| Fee overdue | Due date + 3 days, then weekly, max 3 | Yes |
| Receipt | Payment settled or Family Receipt submitted | No |
| Circular | Circular published | Yes |
| Marks published | Report Card released | Yes |
| Certificate ready | Certificate Request issued | Yes |
| Teacher reply | Reply saved | Yes |

- **Channels.** Set `channel_order = push, whatsapp, sms` for parents. With no push token, or when push fails, send on WhatsApp through `frappe_whatsapp`, then SMS. Email only if the parent chooses it.
- **Unread push.** For absence and receipt only: if the push is not opened within 30 min, WhatsApp follows. This needs an "opened" ping from the service worker [A].
- **Quiet hours.** 21:00–07:00, released when the window ends [V: `quiet_hours.release_time`].
- **Tamil.** Every template needs a `ta` body. Meta approval of WhatsApp templates and DLT registration of SMS templates must both be done by March.
- **In-app list.** Every alert also appears in an in-app list. An item is marked read when its screen is opened. This fixes MyClassboard's "stays unread".

## 7. Privacy and compliance

| Rule | Design |
|---|---|
| DPDP verifiable parental consent | The OTP proves control of the mobile the school recorded at admission. S2 records each purpose in Communication Consent (`source`, `timestamp` [V]). The new `Data Consent` stores the notice version accepted. |
| Fiduciary vs processor | The notice names the school as fiduciary. A school–OneBook DPA is signed before launch. |
| No tracking or ads | No third-party analytics, ads, crash or replay SDKs. A CSP blocks third-party scripts. Metrics come from server logs, aggregated daily, with no child identifiers. |
| Minimisation | Parent APIs never return Aadhaar, social category, religion, CWSN or RTE status. |
| APAAR | Profile shows `obs_apaar_consent` (Pending/Given/Refused) [V]. The parent can give, refuse or withdraw it. Refusal affects nothing else. |
| Fee display mandate | The fees screen links the approved Fee Committee Order (`order_file` [V]) |
| TC and unpaid fees | **Conflict.** `certificates.check_transfer_allowed` blocks a TC while dues are outstanding [V]. The Madras HC ruling forbids this for schools. `onebook_school` must override it so dues are shown but do not block the TC. |
| Retention | OTPs deleted on use or expiry. Push tokens deleted at logout or after 90 days idle. Message Logs kept 1 year. Guardian access ends 1 year after the last child's TC. Periods need school sign-off [A]. |
| Audit | Log OTP requests, logins, consent changes, and receipt/certificate downloads, with user, time and IP. Some of this may already be covered by Frappe Access Log and Activity Log [A]. |
| Rights | "Download my data" and "Request correction" (campus `Student Record Correction` [V]) |

## 8. Migration from ClassPep

**Import.**
- Guardian name, mobile (the login key), relation, language, student links.
- Students already in OneBook are matched on `obs_admission_no` [V].
- Opening balances come from school accounts, not from ClassPep.
- Not imported: chat, old circulars, old homework. The office keeps a PDF archive.
- Whether ClassPep allows an export is [A].

**How parents switch.**
1. The office confirms each family's mobile number.
2. A WhatsApp broadcast in Tamil/English goes out with the Play Store link, the `/parent` link and a 30-second video.
3. First login is an OTP on the same number. No password, no school code.
4. Install help at the fee counter.
5. Families who never install still get WhatsApp/SMS alerts.

| When | Step |
|---|---|
| Mar 2027 | 30 staff families pilot. Templates submitted. |
| Apr 2027 | 2 classes. Play listing approved. |
| May 2027 | Bulk import, WhatsApp onboarding, install drives |
| 1 Jun 2027 | Term starts. Alerts come from OneBook. ClassPep read-only. |
| 1 Jul 2027 | ClassPep off. The school asks ClassPep to delist the app. |

## 9. Risks, open questions, effort

| Risk | Mitigation |
|---|---|
| Play review or developer account delay | Submit in April. The PWA install link works without the store. |
| Meta/DLT template approval is slow | Submit in March |
| Battery savers drop FCM on some phones [A] | WhatsApp fallback for absence and receipt |
| Two guardians share one phone | One user per mobile. Several guardians per student. |
| D15 conflict | Amend D15 for a parent-only PWA |
| TC dues gate | School override before MVP |

**Open questions**
1. Do we amend D15 to allow a parent-only frappe-ui PWA before the pilot?
2. Whose Play developer account publishes the app: the school's or OneBook's?
3. Frappe push relay, or our own FCM project?
4. Which SMS provider and DLT sender ID send OTPs?
5. Which gateway will Aanoor use, and can one payment settle several invoices?
6. Can ClassPep export guardian/mobile/student data?
7. Contact teacher: extend campus `Parent Interaction`, or a new `Parent Message`?
8. Where do school events live: ERPNext Event, Holiday List, or a new DocType?
9. What retention periods will the school sign off?
10. TC dues gate: a School Settings toggle, or always off for K-12?

**Effort (estimates, person-weeks, one Frappe full-stack developer)**

| MVP work | PW |
|---|---|
| PWA shell, en/ta, offline cache, manifest per site | 2.0 |
| OTP login, provisioning, consent | 1.5 |
| Home, attendance, circulars | 1.0 |
| Fees, family pay, receipts | 2.0 |
| Homework DocType and screens | 1.0 |
| Results (release flag, PDF), certificates, TC override | 1.0 |
| Calendar, contact teacher | 1.0 |
| Push (FCM adapter, service worker, tokens) | 1.5 |
| Notification events, en/ta templates | 1.0 |
| TWA and Play listing | 0.5 |
| ClassPep import, onboarding kit | 1.0 |
| Device testing, security review, pilot fixes | 2.0 |
| **MVP total** | **about 16** |

| Later | PW |
|---|---|
| Leave application | 0.5 |
| PTM booking | 1.5 |
| Gallery | 1.0 |
| HPC view | 2.0 |
| Moderated two-way chat | 3.0 |
| Bus tracking (GPS partner) | 3–4 |
