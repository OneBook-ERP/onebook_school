"""The rest of the story: admission enquiries for next year, parent message templates in English and Tamil, and a
verified transfer certificate for a Std X leaver whose fees are clear."""

import frappe
from frappe.utils import flt, nowdate

ENQUIRIES = [
	("Harini Selvam", "LKG", "Walk-in"), ("Mithran Gopal", "LKG", "Reference"), ("Yazhini Kumar", "UKG", "Website"),
	("Sanjay Raman", "Std I", "Walk-in"), ("Nivetha Prakash", "Std VI", "Campaign"), ("Akash Murugan", "Std XI - Bio-Maths", "Reference"),
]  # fmt: skip

TEMPLATES = {
	"school_fee_due": (
		"Fee reminder",
		"Dear parent, {student_name}'s {term} fee of Rs {amount} is due on {due_date}. Pay by UPI or at the school office. - Aanoor Vidyalaya",
		"அன்புள்ள பெற்றோரே, {student_name} அவர்களின் {term} கட்டணம் ரூ {amount} {due_date} அன்று செலுத்த வேண்டும். UPI அல்லது பள்ளி அலுவலகத்தில் செலுத்தலாம். - ஆனூர் வித்யாலயா",
	),
	"school_absent_today": (
		"Absent today",
		"Dear parent, {student_name} of {section} is absent today ({date}). Please inform the class teacher. - Aanoor Vidyalaya",
		"அன்புள்ள பெற்றோரே, {section} வகுப்பு {student_name} இன்று ({date}) பள்ளிக்கு வரவில்லை. வகுப்பு ஆசிரியருக்குத் தெரிவிக்கவும். - ஆனூர் வித்யாலயா",
	),
	"school_results_out": (
		"Results published",
		"Dear parent, {student_name}'s {exam} report card is ready: {percentage}% ({grade}). - Aanoor Vidyalaya",
		"அன்புள்ள பெற்றோரே, {student_name} அவர்களின் {exam} தேர்வு முன்னேற்ற அறிக்கை தயார்: {percentage}% ({grade}). - ஆனூர் வித்யாலயா",
	),
}


def load(ctx):
	enquiries(ctx)
	templates(ctx)
	transfer_certificate(ctx)


def enquiries(ctx):
	for name, cls, source in ENQUIRIES:
		if frappe.db.exists("Lead", {"lead_name": name}):
			continue
		first, _, last = name.partition(" ")
		doc = frappe.get_doc(
			{"doctype": "Lead", "first_name": first, "last_name": last, "company": ctx.company, "status": "Open",
			 "mobile_no": f"0{abs(hash(name)) % 900000000 + 100000000}", "notes": [{"note": f"Enquiry for {cls}, 2027-28"}]}
		)  # fmt: skip
		if frappe.get_meta("Lead").has_field("source") and frappe.db.exists("Lead Source", source):
			doc.source = source
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert()
		ctx.made()


def templates(ctx):
	for key, (subject, en, ta) in TEMPLATES.items():
		if frappe.db.exists("Message Template", key):
			continue
		doc = frappe.get_doc(
			{"doctype": "Message Template", "event_key": key, "enabled": 1, "purpose": "transactional",
			 "variables": ", ".join(sorted({v.split("}")[0] for v in en.split("{")[1:]})),
			 "channels": [{"channel": "whatsapp"}, {"channel": "sms"}],
			 "bodies": [{"language": "en", "subject": subject, "body": en}, {"language": "ta", "subject": subject, "body": ta}]}
		)  # fmt: skip
		doc.flags.ignore_permissions = True
		doc.flags.ignore_mandatory = True
		doc.insert()
		ctx.made()


def transfer_certificate(ctx):
	if not frappe.db.exists("Certificate Type", "Transfer Certificate"):
		frappe.get_doc(
			{"doctype": "Certificate Type", "type_name": "Transfer Certificate", "enabled": 1, "number_prefix": "TC/{abbr}/{yyyy}/",
			 "verifiable": 1, "is_transfer_certificate": 1, "needs_approval": 0}
		).insert(ignore_permissions=True)  # fmt: skip
	if frappe.db.exists("Certificate Request", {"certificate_type": "Transfer Certificate", "docstatus": 1}):
		return
	leaver = None
	for row in frappe.get_all("Student Group Student", filters={"parent": "X - B", "active": 1}, fields=["student"], order_by="group_roll_number desc"):
		owed = frappe.db.sql("select sum(outstanding_amount) from `tabSales Invoice` where student=%s and docstatus=1", row.student)[0][0]
		if not flt(owed):
			leaver = row.student
			break
	if not leaver:
		return
	doc = frappe.get_doc(
		{"doctype": "Certificate Request", "student": leaver, "company": ctx.company, "certificate_type": "Transfer Certificate",
		 "purpose": "Family moving to Coimbatore", "leaving_date": nowdate(), "reason_for_leaving": "Parent's transfer"}
	)  # fmt: skip
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()
	ctx.made()
