"""Fees as the school runs them: the Fee Determination Committee order, a fee structure per class and term inside it,
Term 1 and Term 2 fee invoices for every non-RTE child (younger siblings get the concession), and parents paying
through Family Receipts: almost everyone for Term 1, about two in three for Term 2, a handful today."""

import random

import frappe
from frappe.utils import flt, nowdate

from onebook_school.demo.classes import CLASSES
from onebook_school.demo.school import ABBR, YEAR

# class prefix -> annual approved (Tuition Fee, Special Fee, Computer Fee)
ANNUAL = {
	"LKG": (16000, 2000, 0), "UKG": (16000, 2000, 0),
	"I": (20000, 2500, 1500), "II": (20000, 2500, 1500), "III": (20000, 2500, 1500), "IV": (20000, 2500, 1500), "V": (20000, 2500, 1500),
	"VI": (24000, 3000, 2000), "VII": (24000, 3000, 2000), "VIII": (24000, 3000, 2000),
	"IX": (28000, 3500, 2000), "X": (28000, 3500, 2000), "XI": (34000, 4000, 3000), "XII": (34000, 4000, 3000),
}  # fmt: skip
CAPPED = ("Tuition Fee", "Special Fee", "Computer Fee")
BOOKS = "Books and Notebooks"
TERM_SHARE = {"Term 1": 0.4, "Term 2": 0.3}
TERM_DATES = {"Term 1": ("2026-06-05", "2026-06-30"), "Term 2": ("2026-10-08", "2026-10-31")}
SAC = {"LKG": "999210", "UKG": "999210"}


def key_of(cls):
	return cls if cls in ("LKG", "UKG") else cls.replace("Std ", "").split(" ")[0]


def load(ctx):
	accounts(ctx)
	for category in (*CAPPED, BOOKS):
		fee_category(ctx, category)
	committee_order(ctx)
	structures = {(cls, term): fee_structure(ctx, cls, term) for cls in CLASSES for term in TERM_SHARE}
	rng = random.Random(ctx.seed + 7)
	invoices(ctx, structures)
	payments(ctx, rng)


def accounts(ctx):
	bank_parent = frappe.db.get_value("Account", {"company": ctx.company, "account_type": "Bank", "is_group": 1}) or frappe.db.get_value(
		"Account", {"company": ctx.company, "account_name": "Bank Accounts"}
	)
	bank = f"Indian Bank Muthur - {ABBR}"
	if not frappe.db.exists("Account", bank):
		frappe.get_doc({"doctype": "Account", "account_name": "Indian Bank Muthur", "parent_account": bank_parent, "company": ctx.company,
						"account_type": "Bank", "account_currency": "INR"}).insert(ignore_permissions=True)  # fmt: skip
	cash = frappe.db.get_value("Account", {"company": ctx.company, "account_type": "Cash", "is_group": 0})
	for mode, kind, account in (("Cash", "Cash", cash), ("UPI", "Bank", bank)):
		if not frappe.db.exists("Mode of Payment", mode):
			frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": mode, "type": kind}).insert(ignore_permissions=True)
		doc = frappe.get_doc("Mode of Payment", mode)
		if not any(a.company == ctx.company for a in doc.accounts):
			doc.append("accounts", {"company": ctx.company, "default_account": account})
			doc.save(ignore_permissions=True)


def fee_category(ctx, name):
	if not frappe.db.exists("Item", name):
		frappe.get_doc({"doctype": "Item", "item_code": name, "item_group": "Fee Component", "is_stock_item": 0, "is_sales_item": 1,
						"is_service_item": 1, "stock_uom": "Nos", "gst_hsn_code": "999231"}).insert(ignore_permissions=True)  # fmt: skip
	if not frappe.db.exists("Fee Category", name):
		frappe.get_doc({"doctype": "Fee Category", "category_name": name}).insert(ignore_permissions=True)
		ctx.made()


def committee_order(ctx):
	if frappe.db.exists("Fee Committee Order", {"order_number": "FDC/ERD/2025/1147", "docstatus": 1}):
		return
	lines = []
	for cls in CLASSES:
		for category, amount in zip(CAPPED, ANNUAL[key_of(cls)]):
			if amount:
				lines.append({"program": cls, "fee_category": category, "approved_amount": amount})
	for y, start, end in (("2027-28", "2027-06-01", "2028-04-30"),):
		if not frappe.db.exists("Academic Year", y):
			frappe.get_doc({"doctype": "Academic Year", "academic_year_name": y, "year_start_date": start, "year_end_date": end}).insert(ignore_permissions=True)
	if not frappe.db.exists("Academic Year", "2025-26"):
		frappe.get_doc({"doctype": "Academic Year", "academic_year_name": "2025-26", "year_start_date": "2025-06-01", "year_end_date": "2026-04-30"}).insert(ignore_permissions=True)
	order = frappe.get_doc(
		{"doctype": "Fee Committee Order", "company": ctx.company, "order_number": "FDC/ERD/2025/1147", "order_date": "2025-07-14",
		 "valid_from_year": "2025-26", "valid_to_year": "2027-28", "lines": lines}
	)  # fmt: skip
	order.insert(ignore_permissions=True)
	order.submit()
	ctx.made()


def fee_structure(ctx, cls, term):
	academic_term = f"{YEAR} ({term})"
	existing = frappe.db.get_value("Fee Structure", {"program": cls, "academic_term": academic_term, "docstatus": 1})
	if existing:
		return existing
	share = TERM_SHARE[term]
	components = [{"fees_category": c, "amount": round(a * share)} for c, a in zip(CAPPED, ANNUAL[key_of(cls)]) if a]
	if term == "Term 1":
		components.append({"fees_category": BOOKS, "amount": 2500 if cls in ("LKG", "UKG") else 3800})
	doc = frappe.get_doc(
		{"doctype": "Fee Structure", "program": cls, "academic_year": YEAR, "academic_term": academic_term, "company": ctx.company,
		 "receivable_account": frappe.db.get_value("Company", ctx.company, "default_receivable_account"), "components": components}
	)  # fmt: skip
	doc.insert(ignore_permissions=True)
	doc.submit()
	ctx.made()
	return doc.name


def invoices(ctx, structures):
	enrolled = frappe.get_all("Program Enrollment", filters={"academic_year": YEAR, "docstatus": 1}, fields=["student", "program"])
	rte = set(frappe.get_all("Student", filters={"obs_rte": 1}, pluck="name"))
	for row in enrolled:
		if row.student in rte:
			continue
		customer = frappe.db.get_value("Student", row.student, "customer")
		for term, (posting, due) in TERM_DATES.items():
			remark = f"{YEAR} {term} fees"
			if frappe.db.exists("Sales Invoice", {"student": row.student, "remarks": remark, "docstatus": 1}):
				continue
			structure = frappe.get_doc("Fee Structure", structures[(row.program, term)])
			invoice = frappe.get_doc(
				{"doctype": "Sales Invoice", "company": ctx.company, "customer": customer, "student": row.student,
				 "posting_date": posting, "set_posting_time": 1, "due_date": due, "remarks": remark,
				 "fee_structure": structure.name if frappe.get_meta("Sales Invoice").has_field("fee_structure") else None,
				 "debit_to": structure.receivable_account,
				 "items": [{"item_code": c.fees_category, "qty": 1, "rate": c.amount, "description": f"{c.fees_category} - {term}"} for c in structure.components]}
			)  # fmt: skip
			invoice.flags.ignore_permissions = True
			invoice.insert()
			invoice.submit()
			ctx.made()


def payments(ctx, rng):
	from onebook_school.fees.family import get_outstanding

	fathers = frappe.get_all("Student Guardian", filters={"parenttype": "Student", "relation": "Father"}, pluck="guardian", distinct=True)
	today = nowdate()
	paid_today = 0
	for guardian in sorted(set(fathers)):
		if frappe.db.exists("Family Receipt", {"guardian": guardian, "docstatus": 1}):
			continue
		dues = get_outstanding(guardian, ctx.company)
		if not dues:
			continue
		term1 = sum(flt(d["outstanding_amount"]) for d in dues if str(d["due_date"]) <= "2026-06-30")
		term2 = sum(flt(d["outstanding_amount"]) for d in dues if str(d["due_date"]) > "2026-06-30")
		roll = rng.random()
		if roll < 0.06:
			continue  # defaulter on both terms
		receipt(ctx, guardian, term1, "2026-06-20", rng)
		if roll < 0.40:
			continue  # Term 2 still due
		when = today if paid_today < 12 and roll > 0.9 else "2026-10-25"
		paid_today += when == today
		receipt(ctx, guardian, term2, when, rng)


def receipt(ctx, guardian, amount, date, rng):
	if amount <= 0:
		return
	doc = frappe.get_doc(
		{"doctype": "Family Receipt", "guardian": guardian, "company": ctx.company, "posting_date": date,
		 "mode_of_payment": rng.choice(["UPI", "UPI", "Cash"]), "amount_paid": amount}
	)  # fmt: skip
	doc.reference_no = f"UPI{rng.randint(10**9, 10**10 - 1)}" if doc.mode_of_payment == "UPI" else None
	doc.allocate()
	if not doc.allocations:
		return
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()
	ctx.made()
