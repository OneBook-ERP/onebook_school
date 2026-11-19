"""Custom fields OneBook School adds to Education DocTypes (prefix obs_): the school's own and government IDs on
Student, and the class teacher on a section (Student Group)."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

SOCIAL_CATEGORIES = "\nOC\nBC\nBCM\nMBC\nSC\nSCA\nST"
RELIGIONS = "\nHindu\nMuslim\nChristian\nOthers"

STUDENT = [
	{"fieldname": "obs_school_ids", "label": "School and Government IDs", "fieldtype": "Section Break", "insert_after": "student_email_id", "collapsible": 1},
	{"fieldname": "obs_admission_no", "label": "Admission No", "fieldtype": "Data", "insert_after": "obs_school_ids", "unique": 1, "in_standard_filter": 1},
	{"fieldname": "obs_emis_id", "label": "EMIS ID", "fieldtype": "Data", "insert_after": "obs_admission_no"},
	{"fieldname": "obs_pen", "label": "PEN (UDISE+)", "fieldtype": "Data", "insert_after": "obs_emis_id"},
	{"fieldname": "obs_ids_col", "fieldtype": "Column Break", "insert_after": "obs_pen"},
	{"fieldname": "obs_apaar_id", "label": "APAAR ID", "fieldtype": "Data", "insert_after": "obs_ids_col"},
	{"fieldname": "obs_apaar_consent", "label": "APAAR Consent", "fieldtype": "Select", "options": "\nPending\nGiven\nRefused", "insert_after": "obs_apaar_id"},
	{"fieldname": "obs_profile_section", "label": "UDISE+ Profile", "fieldtype": "Section Break", "insert_after": "obs_apaar_consent", "collapsible": 1},
	{"fieldname": "obs_mother_tongue", "label": "Mother Tongue", "fieldtype": "Data", "insert_after": "obs_profile_section"},
	{"fieldname": "obs_social_category", "label": "Social Category", "fieldtype": "Select", "options": SOCIAL_CATEGORIES, "insert_after": "obs_mother_tongue"},
	{"fieldname": "obs_religion", "label": "Religion", "fieldtype": "Select", "options": RELIGIONS, "insert_after": "obs_social_category"},
	{"fieldname": "obs_profile_col", "fieldtype": "Column Break", "insert_after": "obs_religion"},
	{"fieldname": "obs_rte", "label": "RTE Admission (25% quota)", "fieldtype": "Check", "insert_after": "obs_profile_col", "in_standard_filter": 1},
	{"fieldname": "obs_cwsn", "label": "Child with Special Needs (CWSN)", "fieldtype": "Check", "insert_after": "obs_rte"},
]  # fmt: skip

STUDENT_GROUP = [
	{"fieldname": "obs_class_teacher", "label": "Class Teacher", "fieldtype": "Link", "options": "Instructor", "insert_after": "batch", "in_list_view": 1},
]  # fmt: skip


SALES_INVOICE = [
	{"fieldname": "obs_program", "label": "Class", "fieldtype": "Link", "options": "Program", "insert_after": "student", "read_only": 1, "in_standard_filter": 1},
]  # fmt: skip


def create_all():
	create_custom_fields({"Student": STUDENT, "Student Group": STUDENT_GROUP, "Sales Invoice": SALES_INVOICE}, update=True)
