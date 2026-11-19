"""Data for the school boards: `/desk/school-today/<board>`, one board per school workspace (Correspondent, Principal,
Fees Office, School Office, Class Teacher).

A board is the user's day from `school_day.today` (decisions first), then that workspace's number cards and charts
grouped as the workspace defines them in `setup.desk.WORKSPACES`, plus its quick actions. Cards and charts are the
same Number Card and Dashboard Chart records the workspace uses, computed through Frappe's own APIs as the user, so a
card the user may not read is left out rather than failing the page.
"""

import frappe
from frappe import _
from frappe.utils import flt, now_datetime

from onebook_school.school_day import cover, today as school_today
from onebook_school.setup.desk import WORKSPACES

# the board a role lands on, most senior first
HOME = [("School Correspondent", "Correspondent"), ("School Principal", "Principal"), ("School Accountant", "Fees Office"),
		("School Office", "School Office"), ("Class Teacher", "Class Teacher"), ("System Manager", "Principal")]  # fmt: skip


def slug(name):
	return name.lower().replace(" ", "-")


def boards_for(roles):
	return [name for name, spec in WORKSPACES.items() if roles & set(spec[1])]


def home_board(roles):
	return next((board for role, board in HOME if role in roles), None)


@frappe.whitelist(methods=["GET"])
def get_board(board=None):
	user = frappe.session.user
	roles = set(frappe.get_roles(user))
	allowed = boards_for(roles)
	# a board the user may not open (an old link, the app tile) falls back to their own; the page then moves the URL
	name = next((b for b in allowed if slug(b) == board), None) or home_board(roles)
	if not name or name not in allowed:
		frappe.throw(_("You cannot open this board."), frappe.PermissionError)
	_icon, _roles, intro, cards, charts, shortcuts, _links = WORKSPACES[name]
	day = school_today.build(user)
	return {
		**day,
		"board": slug(name), "title": name, "intro": intro,
		"boards": [{"slug": slug(b), "title": b} for b in allowed],
		"groups": card_groups(name, cards, day, user),
		"charts": [c for c in (chart_data(c) for c in charts) if c],
		"shortcuts": [shortcut_of(s) for s in shortcuts[:6]],  # the rest are under "Quick actions" in the sidebar
	}


# ---- cards -------------------------------------------------------------------------------------------------------


def card_groups(board, cards, day, user):
	groups = []
	now = right_now(board, day, user)
	if now:
		groups.append({"title": "Right now", "cards": now})
	current = None
	for entry in cards:
		if entry.startswith("# "):
			current = {"title": entry[2:], "cards": []}
			groups.append(current)
			continue
		if current is None:
			current = {"title": "", "cards": []}
			groups.append(current)
		card = card_value(entry)
		if card:
			current["cards"].append(card)
	return [g for g in groups if g["cards"]]


def right_now(board, day, user):
	"""The few numbers that ask for action today, above the workspace's own cards."""
	if board in ("Principal", "Correspondent"):
		periods, now = school_today.periods_by_no(), now_datetime().time()
		today = day["date"]
		open_periods = [r for r in cover.uncovered(today) if periods.get(r["period_no"]) and school_today.when(periods[r["period_no"]], now) != "done"]
		pending, _exam = school_today.missing_marks()
		return [
			card("Periods without cover", len(open_periods), to="/desk/cover-assignment", alert=bool(open_periods)),
			card("Marks pending", len(pending), to="/desk/mark-entry", alert=bool(pending)),
			card("Teachers away", len(cover.away_instructors(today)), to="/desk/attendance"),
		]
	if board == "Class Teacher" and school_today.instructor_of(user):
		section = lambda key: next((s for s in day["sections"] if s["key"] == key), {"items": []})["items"]  # noqa: E731
		periods = section("now_next")
		left = [i for i in periods if i.get("sub") != "done" and i.get("action")]
		todo = section("todo")
		return [card("My periods today", len(periods), to="/desk/timetable-slot"), card("Periods left", len(left)), card("To do", len(todo), alert=bool(todo))]
	return []


def card(title, value, fieldtype="Int", to=None, alert=False, color=None):
	return {"title": title, "value": value, "fieldtype": fieldtype, "to": to, "alert": alert, "color": color}


def card_value(name):
	from frappe.desk.doctype.number_card.number_card import get_result

	try:
		doc = frappe.get_doc("Number Card", name)
		if doc.document_type and not frappe.has_permission(doc.document_type, "read"):
			return None
		if doc.type == "Custom":
			result = frappe.get_attr(doc.method)(filters=None)
			return card(doc.label, result.get("value"), result.get("fieldtype") or "Int", list_route(doc.document_type), color=doc.color)
		filters = frappe.parse_json(doc.filters_json or "[]")
		value = get_result(doc, filters)
		fieldtype = "Currency" if doc.function == "Sum" else "Float" if doc.function == "Average" else "Int"
		return card(doc.label, flt(value), fieldtype, list_route(doc.document_type, filters), color=doc.color)
	except frappe.PermissionError:
		frappe.clear_last_message()
		return None


def list_route(doctype, filters=None):
	if not doctype:
		return None
	query = []
	for f in filters or []:
		field, op, value = (f[1], f[2], f[3]) if len(f) >= 4 else (None, None, None)
		if op == "=" and not isinstance(value, list | dict) and field != "docstatus":
			query.append(f"{field}={frappe.utils.quote(str(value))}")
	return f"/desk/{slug(doctype)}" + (("?" + "&".join(query)) if query else "")


# ---- charts ------------------------------------------------------------------------------------------------------


def chart_data(name):
	from frappe.desk.doctype.dashboard_chart.dashboard_chart import get

	try:
		doc = frappe.get_doc("Dashboard Chart", name)
		if not frappe.has_permission(doc.document_type, "read"):
			return None
		result = get(chart_name=name)
	except frappe.PermissionError:
		frappe.clear_last_message()
		return None
	labels = result.get("labels") or []
	values = ((result.get("datasets") or [{}])[0]).get("values") or []
	rows = sort_rows([{"label": str(lbl), "value": flt(v, 2)} for lbl, v in zip(labels, values, strict=False)])
	money = doc.chart_type == "Sum" or doc.group_by_type == "Sum"
	return {
		"title": name, "kind": {"Donut": "donut", "Pie": "donut", "Line": "line"}.get(doc.type, "bar"),
		"rows": rows, "color": doc.color, "money": money, "time": doc.chart_type != "Group By", "to": list_route(doc.document_type),
	}


CLASSES = ["LKG", "UKG", "Std I", "Std II", "Std III", "Std IV", "Std V", "Std VI", "Std VII", "Std VIII", "Std IX", "Std X", "Std XI", "Std XII"]
GRADES = ["A1", "A2", "B1", "B2", "C1", "C2", "D", "E", "AB"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


def class_of(label):
	"""Position of the class a label names: "Std XI - Science" is Std XI."""
	head = label.split(" - ")[0].strip()
	return CLASSES.index(head) if head in CLASSES else None


def sort_rows(rows):
	"""Classes, sections and grades read in school order, not by size."""
	labels = [r["label"] for r in rows]
	if labels and all(class_of(lbl) is not None for lbl in labels):
		return sorted(rows, key=lambda r: (class_of(r["label"]), r["label"]))
	if labels and all(lbl in GRADES for lbl in labels):
		return sorted(rows, key=lambda r: GRADES.index(r["label"]))
	if labels and all(lbl.split(" - ")[0] in ROMAN for lbl in labels):
		return sorted(rows, key=lambda r: (ROMAN.index(r["label"].split(" - ")[0]), r["label"]))
	return rows


# ---- quick actions -----------------------------------------------------------------------------------------------


def shortcut_of(s):
	target = s["link_to"]
	if s["type"] == "Report":
		to = f"/desk/query-report/{target}"
	else:
		view = s.get("doc_view")
		to = f"/desk/{slug(target)}" + ("/new" if view == "New" else "/view/report" if view == "Report Builder" else "")
	return {"label": s["label"], "to": to, "primary": s.get("color") in ("Green", "Blue") or s.get("doc_view") == "New"}
